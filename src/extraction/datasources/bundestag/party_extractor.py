"""Extract parliamentary composition metadata from Bundestag documents.

This module uses DYNAMIC extraction without hardcoded party names,
making it future-proof for new parties and changing compositions.
"""

import re
from collections import Counter
from datetime import datetime
from typing import Dict, List, Set

from core.logger import LoggerConfiguration


class PartyExtractor:
    """Extracts party/fraction composition dynamically from protocol text.

    Design principle: Extract ALL party mentions using pattern matching
    and heuristics, without hardcoding specific party names.
    """

    logger = LoggerConfiguration.get_logger(__name__)

    # Non-party keywords to filter out (roles, locations, organizations, etc.)
    NON_PARTY_KEYWORDS = {
        # Governmental roles
        "Bundeskanzler",
        "Bundeskanzlerin",
        "Bundesminister",
        "Bundesministerin",
        "Bundespräsident",
        "Bundespräsidentin",
        "Präsident",
        "Präsidentin",
        "Staatsminister",
        "Staatsministerin",
        "Staatssekretär",
        "Staatssekretärin",
        # Locations
        "Berlin",
        "Bonn",
        # Status
        "parteilos",
        "fraktionslos",
        "Gast",  # Guest speakers
        # Common organizational abbreviations (NOT parties)
        "EU",
        "UN",
        "NATO",
        "OSZE",
        "WHO",
        "IWF",
        "EZB",
        "BMWE",
        "BMI",
        "BMF",
        "BMAS",
        "BMZ",
        "BMVI",
        "BMVg",  # German ministries
        "BT",
        "BR",  # Bundestag/Bundesrat abbreviations
        "USA",
        "UK",
        "FR",  # Countries
        # Procedural terms
        "TOP",
        "ZP",  # Tagesordnungspunkt, Zusatzpunkt
    }

    @classmethod
    def extract_from_protocol_text(cls, text: str) -> Dict:
        """Extract party composition from DIP protocol text dynamically.

        Uses pattern matching and heuristics to identify parties
        WITHOUT hardcoded party names.

        Args:
            text: Full protocol text from DIP API

        Returns:
            Parliamentary composition metadata dictionary
        """
        if not text:
            return cls._empty_result()

        # Pattern: Matches "Name (PARTY)" speaker attributions
        # More flexible pattern that matches various name formats:
        # - "Hans Müller (CDU/CSU)"
        # - "Dr. Maria Schmidt (SPD)"
        # - "Speaker1 (CDU)" (for tests)
        # Captures name and content in parentheses
        pattern = r"(\b[A-ZÄÖÜa-zäöüß][A-ZÄÖÜa-zäöüß0-9\.\s]*?)\s+\(([^)]+)\)"

        matches = re.findall(pattern, text)

        # Extract candidates: text in parentheses after names
        candidates = [match[1].strip() for match in matches]

        # Filter to likely parties using heuristics
        party_candidates = []
        for candidate in candidates:
            if cls._is_likely_party(candidate):
                party_candidates.append(candidate)

        if not party_candidates:
            cls.logger.debug("No party candidates found in protocol text")
            return cls._empty_result()

        # Count occurrences for confidence scoring
        party_counts = Counter(party_candidates)

        cls.logger.debug(
            f"Found {len(party_counts)} unique party variations "
            f"with {sum(party_counts.values())} total mentions"
        )

        # CRITICAL FILTER: Remove noise by requiring minimum mentions
        # Real parties appear throughout the protocol (many mentions)
        # Noise abbreviations (government agencies, technical terms) appear rarely (1 mention)
        # Threshold: At least 2 mentions to be considered a party
        # This filters out single-occurrence noise while catching real parties
        MIN_MENTIONS = 2
        filtered_party_counts = Counter(
            {
                name: count
                for name, count in party_counts.items()
                if count >= MIN_MENTIONS
            }
        )

        if not filtered_party_counts:
            cls.logger.debug(
                f"After filtering for min {MIN_MENTIONS} mentions, no parties remain"
            )
            return cls._empty_result()

        cls.logger.debug(
            f"After filtering for min {MIN_MENTIONS} mentions: "
            f"{len(filtered_party_counts)} candidates remain"
        )

        # Group related party names (e.g., CDU, CSU, CDU/CSU → CDU/CSU)
        party_groups = cls._group_related_parties(filtered_party_counts)

        cls.logger.info(f"Grouped into {len(party_groups)} distinct fractions")

        # Build fractions list
        fractions = []
        for primary_name, related_names in party_groups.items():
            total_mentions = sum(
                filtered_party_counts[name] for name in related_names
            )

            fractions.append(
                {
                    "name": primary_name,
                    "variations": sorted(list(related_names)),
                    "type": "fraction",
                    "mention_count": total_mentions,
                }
            )

        # Sort by mention count (most mentioned first)
        fractions.sort(key=lambda f: f["mention_count"], reverse=True)

        confidence = cls._calculate_confidence(fractions, filtered_party_counts)

        cls.logger.info(
            f"Extracted {len(fractions)} fractions with {confidence} confidence: "
            f"{', '.join(f['name'] for f in fractions)}"
        )

        return {
            "fractions": fractions,
            "extraction_source": "protocol_text",
            "extracted_at": datetime.utcnow().isoformat(),
            "confidence": confidence,
        }

    @classmethod
    def extract_from_speaker_party(cls, party: str) -> Dict:
        """Extract party metadata from a single speech's speaker.party field.

        Stores raw party name without normalization.

        Args:
            party: Party abbreviation from speaker metadata

        Returns:
            Single-party composition metadata
        """
        if not party:
            return cls._empty_result()

        # Store raw party name - NO hardcoded normalization
        fractions = [
            {
                "name": party,
                "variations": [party],
                "type": "fraction",
                "mention_count": 1,
            }
        ]

        return {
            "fractions": fractions,
            "extraction_source": "speaker_metadata",
            "extracted_at": datetime.utcnow().isoformat(),
            "confidence": "low",  # Single speech doesn't show full composition
        }

    @classmethod
    def _is_likely_party(cls, text: str) -> bool:
        """Determine if text is likely a party/fraction name using heuristics.

        CONSERVATIVE approach: Only match text that strongly resembles party names.

        Heuristics (NO hardcoded party names):
        1. Length between 2-20 characters (parties are concise)
        2. Not a common non-party phrase (roles, locations, organizations)
        3. Matches specific party-name patterns:
           a) 2-4 char ALL-CAPS abbreviations (SPD, AfD, CDU, CSU, FDP)
           b) Compound party names with "/" (CDU/CSU, BÜNDNIS 90/DIE GRÜNEN)
           c) Party names starting with "Die " followed by capitalized word
           d) Party names starting with "Bündnis" or "Bund"

        Args:
            text: Candidate text from parentheses

        Returns:
            True if text is likely a party name
        """
        text_clean = text.strip()

        # Must have content
        if not text_clean or len(text_clean) < 2:
            return False

        # STRICTER length check (parties are typically 2-25 chars)
        # Allow up to 25 to accommodate "BÜNDNIS 90/DIE GRÜNEN" (23 chars)
        if len(text_clean) > 25:
            return False

        # Exclude known non-party phrases FIRST
        if any(keyword in text_clean for keyword in cls.NON_PARTY_KEYWORDS):
            return False

        # Must contain at least one uppercase letter
        if not any(c.isupper() for c in text_clean):
            return False

        # Calculate character composition
        uppercase_count = sum(1 for c in text_clean if c.isupper())
        alpha_count = sum(1 for c in text_clean if c.isalpha())

        if alpha_count == 0:
            return False

        uppercase_ratio = uppercase_count / alpha_count

        # PATTERN 1: Short abbreviations (2-6 characters)
        # Examples: SPD, AfD, CDU, CSU, FDP, BSW, GRÜNE, LINKE
        if 2 <= len(text_clean) <= 6:
            # Must be all letters (no numbers) and at least 2 uppercase letters
            # This allows "AfD" (2 uppercase out of 3) but rejects "EU", "UK" (too international)
            if alpha_count == len(text_clean) and uppercase_count >= 2:
                return True
            return (
                False  # Reject short strings with numbers or too few uppercase
            )

        # PATTERN 2: Compound names with slash "/"
        # Examples: "CDU/CSU", "BÜNDNIS 90/DIE GRÜNEN"
        if "/" in text_clean:
            # Must have at least 50% uppercase
            if uppercase_ratio >= 0.5:
                # Additional check: both sides of "/" should have letters
                parts = text_clean.split("/")
                if len(parts) == 2 and all(
                    any(c.isalpha() for c in p) for p in parts
                ):
                    return True
            return False

        # PATTERN 3: Names starting with "Die " or "DIE "
        # Examples: "Die Linke", "DIE LINKE"
        if text_clean.startswith("Die ") or text_clean.startswith("DIE "):
            # After "Die ", should have at least one more capitalized word
            remaining = text_clean[4:].strip()
            if remaining and remaining[0].isupper():
                return True
            return False

        # PATTERN 4: Names starting with "Bündnis" or "Bund"
        # Examples: "BÜNDNIS 90", "Bündnis"
        if (
            text_clean.startswith("Bündnis")
            or text_clean.startswith("BÜNDNIS")
            or text_clean.startswith("Bund")
        ):
            return True

        # All other patterns rejected
        return False

    @classmethod
    def _group_related_parties(
        cls, party_counts: Counter
    ) -> Dict[str, Set[str]]:
        """Group related party name variations dynamically.

        Groups variations like:
        - "CDU", "CSU", "CDU/CSU" → "CDU/CSU" (longest/compound)
        - "GRÜNE", "DIE GRÜNEN", "BÜNDNIS 90/DIE GRÜNEN" → longest variant
        - "Die Linke", "DIE LINKE" → most common variant

        Strategy: Use Union-Find algorithm to merge related parties.

        Args:
            party_counts: Counter of party name occurrences

        Returns:
            Dict mapping canonical name to set of related names
        """
        parties = list(party_counts.keys())

        # Build Union-Find structure
        # parent[party] = canonical representative of its group
        parent = {p: p for p in parties}

        def find(party):
            """Find root of party's group."""
            if parent[party] != party:
                parent[party] = find(parent[party])  # Path compression
            return parent[party]

        def union(party1, party2):
            """Merge groups of party1 and party2."""
            root1 = find(party1)
            root2 = find(party2)
            if root1 != root2:
                # Merge: prefer party with slash, then longer, then more frequent
                if (
                    1 if "/" in root1 else 0,
                    len(root1),
                    party_counts[root1],
                ) >= (
                    1 if "/" in root2 else 0,
                    len(root2),
                    party_counts[root2],
                ):
                    parent[root2] = root1
                else:
                    parent[root1] = root2

        # Find all related pairs and union them
        for i, party1 in enumerate(parties):
            party1_upper = party1.upper()
            for party2 in parties[i + 1 :]:
                party2_upper = party2.upper()

                # Check if related
                is_substring = (
                    party1_upper in party2_upper or party2_upper in party1_upper
                )
                are_related = cls._are_related_parties(party1, party2)

                if is_substring or are_related:
                    union(party1, party2)

        # Build groups from Union-Find structure
        groups: Dict[str, Set[str]] = {}
        for party in parties:
            root = find(party)
            if root not in groups:
                groups[root] = set()
            groups[root].add(party)

        return groups

    @classmethod
    def _are_related_parties(cls, party1: str, party2: str) -> bool:
        """Check if two party names are related variations.

        Uses word overlap heuristic WITHOUT hardcoded party knowledge.

        Args:
            party1: First party name
            party2: Second party name

        Returns:
            True if parties are related
        """
        p1_upper = party1.upper()
        p2_upper = party2.upper()

        # Extract significant words (length >= 3, all caps)
        words1 = {w for w in re.findall(r"\b[A-ZÄÖÜ]{3,}\b", p1_upper)}
        words2 = {w for w in re.findall(r"\b[A-ZÄÖÜ]{3,}\b", p2_upper)}

        # Check for shared significant words
        # BUT: "DIE" and "LINKE" are both 3+ chars, so we need to be more careful
        # Only consider them related if they share a MEANINGFUL word
        shared_words = words1 & words2
        if shared_words:
            # Exclude common articles/connectors: DIE, DER, DAS, UND, VON
            meaningful_shared = shared_words - {
                "DIE",
                "DER",
                "DAS",
                "UND",
                "VON",
            }
            if meaningful_shared:
                return True

        return False

    @classmethod
    def _calculate_confidence(
        cls, fractions: List[Dict], party_counts: Counter
    ) -> str:
        """Calculate confidence level based on extraction results.

        Confidence based on:
        - Number of fractions (typical Bundestag has 4-7 fractions)
        - Total mention count (more mentions = higher confidence)

        Args:
            fractions: List of extracted fractions
            party_counts: Counter of raw party mentions

        Returns:
            "high", "medium", or "low"
        """
        num_fractions = len(fractions)
        total_mentions = sum(party_counts.values())

        # Typical Bundestag has 4-7 fractions
        # High confidence: 4+ distinct fractions (typical composition)
        # OR: 2+ fractions with many mentions (confirms representative sample)
        if num_fractions >= 4 or (num_fractions >= 2 and total_mentions >= 20):
            return "high"
        elif num_fractions >= 2 or total_mentions >= 10:
            return "medium"
        else:
            return "low"

    @classmethod
    def _empty_result(cls) -> Dict:
        """Return empty composition metadata for documents with no parties."""
        return {
            "fractions": [],
            "extraction_source": "none",
            "extracted_at": datetime.utcnow().isoformat(),
            "confidence": "low",
        }
