from typing import Type, Union

from core.base_factory import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.bundestag.client import BundestagSpeech
from extraction.datasources.bundestag.client_dip import DIPDocument
from extraction.datasources.bundestag.configuration import (
    BundestagMineDatasourceConfiguration,
)
from extraction.datasources.bundestag.document import BundestagMineDocument
from extraction.datasources.bundestag.party_extractor import PartyExtractor
from extraction.datasources.core.parser import BaseParser


class BundestagMineDatasourceParser(BaseParser[BundestagMineDocument]):
    """Parser for Bundestag data from multiple sources.

    Handles parsing of:
    - BundestagMine speeches (individual speech data)
    - DIP documents (protocols, drucksachen, proceedings)
    """

    logger = LoggerConfiguration.get_logger(__name__)

    def parse(
        self, content: Union[BundestagSpeech, DIPDocument]
    ) -> BundestagMineDocument:
        """
        Parse content into a BundestagMineDocument object.

        Args:
            content: Raw content to be parsed (BundestagSpeech or DIPDocument)

        Returns:
            Parsed document of type BundestagMineDocument
        """
        if isinstance(content, BundestagSpeech):
            return self._parse_bundestag_speech(content)
        elif isinstance(content, DIPDocument):
            return self._parse_dip_document(content)
        else:
            raise ValueError(f"Unsupported content type: {type(content)}")

    def _parse_bundestag_speech(
        self, speech: BundestagSpeech
    ) -> BundestagMineDocument:
        """Parse a BundestagMine speech into a document.

        Args:
            speech: BundestagSpeech object

        Returns:
            BundestagMineDocument with speech data
        """
        metadata = self._extract_metadata_from_speech(speech)
        return BundestagMineDocument(text=speech.text, metadata=metadata)

    def _parse_dip_document(
        self, dip_doc: DIPDocument
    ) -> BundestagMineDocument:
        """Parse a DIP document into a BundestagMineDocument.

        Args:
            dip_doc: DIPDocument object

        Returns:
            BundestagMineDocument with DIP data
        """
        metadata = self._extract_metadata_from_dip(dip_doc)

        # Filter protocol text to remove non-informative sections
        text = dip_doc.text
        if dip_doc.source_type == "protocol":
            text = self._filter_protocol_text(text)

        return BundestagMineDocument(text=text, metadata=metadata)

    def _filter_protocol_text(self, text: str) -> str:
        """Filter protocol text to remove non-informative sections.

        Removes:
        - Anlage sections (attachments with attendance lists, voting records)
        - Content after "Anlagen zum Stenografischen Bericht" marker
        - Name list sections (lines with >80% proper nouns, no verbs)

        Args:
            text: Raw protocol text

        Returns:
            Filtered text with only substantive content
        """
        lines = text.split("\n")
        filtered_lines = []
        in_anlage_section = False
        in_name_list = False
        removed_lines = 0
        name_list_start = -1

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Check for start of Anlagen section (usually near the end)
            if stripped.startswith("Anlagen zum Stenografischen Bericht"):
                self.logger.debug(
                    f"Found 'Anlagen zum Stenografischen Bericht' at line {i}, "
                    f"removing remaining {len(lines) - i} lines"
                )
                removed_lines += len(lines) - i
                break

            # Check for individual Anlage markers followed by minimal content
            if stripped.startswith("Anlage"):
                # Look ahead to see if this is a low-content section
                next_lines = lines[i + 1 : min(i + 20, len(lines))]
                non_empty_next = [l.strip() for l in next_lines if l.strip()]

                # If Anlage is followed by very few words or just names/numbers,
                # it's likely an attachment section
                if len(non_empty_next) <= 3:
                    in_anlage_section = True
                    self.logger.debug(
                        f"Found standalone Anlage at line {i}: {stripped[:50]}"
                    )
                    removed_lines += 1
                    continue
                # Check if followed by attendance/voting list markers
                elif any(
                    marker in " ".join(non_empty_next[:5])
                    for marker in [
                        "Entschuldigte Abgeordnete",
                        "Namensverzeichnis",
                        "Ergebnis und Namensverzeichnis",
                    ]
                ):
                    in_anlage_section = True
                    self.logger.debug(
                        f"Found Anlage with attendance/voting list at line {i}"
                    )
                    removed_lines += 1
                    continue

            # Exit Anlage section when we hit substantive content
            if in_anlage_section:
                # Check for speaker pattern (name followed by colon)
                if (
                    ":" in line
                    and len(stripped) > 10
                    and stripped.endswith(":")
                ):
                    in_anlage_section = False
                    self.logger.debug(f"Exiting Anlage section at line {i}")
                # Check for long paragraph (likely substantive content)
                elif len(stripped) > 100:
                    in_anlage_section = False
                    self.logger.debug(f"Exiting Anlage section at line {i}")
                else:
                    removed_lines += 1
                    continue

            # NEW: Detect name list sections (lines with mostly proper nouns, no verbs)
            if not in_name_list and self._is_name_list_line(stripped):
                # Look ahead to see if this is start of a name list section
                next_lines = lines[i + 1 : min(i + 10, len(lines))]
                name_count = sum(
                    1
                    for l in next_lines
                    if l.strip() and self._is_name_list_line(l.strip())
                )

                # If 5+ consecutive name-like lines, it's a name list section
                if name_count >= 5:
                    in_name_list = True
                    name_list_start = i
                    removed_lines += 1
                    self.logger.debug(f"Entering name list section at line {i}")
                    continue

            # Exit name list when we hit substantive content
            if in_name_list:
                # Check for speaker pattern or long substantive text
                if (
                    (":" in line and stripped.endswith(":"))
                    or len(stripped) > 150
                    or self._has_verbs(stripped)
                ):
                    in_name_list = False
                    list_length = i - name_list_start
                    self.logger.debug(
                        f"Exited name list section at line {i} (removed {list_length} lines)"
                    )
                else:
                    removed_lines += 1
                    continue

            filtered_lines.append(line)

        filtered_text = "\n".join(filtered_lines)

        if removed_lines > 0:
            self.logger.info(
                f"Filtered protocol: removed {removed_lines} lines "
                f"({len(text) - len(filtered_text)} chars) of non-substantive content"
            )

        return filtered_text

    def _is_name_list_line(self, line: str) -> bool:
        """Check if a line looks like a name list entry.

        Name list characteristics:
        - Short line (< 80 chars)
        - 2-4 words
        - All words start with capital letter
        - No verbs or sentence structure

        Args:
            line: Line to check

        Returns:
            True if line looks like a name entry
        """
        if not line or len(line) > 80:
            return False

        words = line.split()
        if not (2 <= len(words) <= 5):
            return False

        # Check if all words are capitalized (typical for names)
        # Allow for common German particles: von, van, de, der
        particles = {"von", "van", "de", "der", "den", "zu"}
        capitalized_count = sum(
            1 for w in words if w[0].isupper() or w.lower() in particles
        )

        return (
            capitalized_count >= len(words) - 1
        )  # Allow one non-capitalized word

    def _has_verbs(self, text: str) -> bool:
        """Check if text contains common German verbs (indicates substantive content).

        Args:
            text: Text to check

        Returns:
            True if text contains verbs
        """
        # Common German verbs and verb patterns
        verb_indicators = [
            " ist ",
            " sind ",
            " war ",
            " waren ",
            " hat ",
            " haben ",
            " hatte ",
            " wird ",
            " werden ",
            " wurde ",
            " wurden ",
            " kann ",
            " können ",
            " soll ",
            " muss ",
            " möchte ",
            " sage ",
            " sagen ",
            " glaube ",
            " denke ",
            " meine ",
            " macht ",
            " machen ",
            " gibt ",
            " geht ",
        ]

        text_lower = f" {text.lower()} "
        return any(verb in text_lower for verb in verb_indicators)

    def _extract_metadata_from_speech(self, speech: BundestagSpeech) -> dict:
        """
        Extract metadata from a BundestagMine speech.

        Args:
            speech: BundestagSpeech object

        Returns:
            Dictionary containing extracted metadata
        """
        legislature_period = speech.protocol.legislaturePeriod
        protocol_number = speech.protocol.number
        agenda_item_number = speech.agendaItem.agendaItemNumber

        url = f"https://dserver.bundestag.de/btp/{legislature_period}/{legislature_period}{protocol_number}.pdf"
        title = f"Protocol/Legislature/AgendaItem {protocol_number}/{legislature_period}/{agenda_item_number}"
        speaker_name = f"{speech.speaker.firstName} {speech.speaker.lastName}"

        metadata = {
            "datasource": "bundestag",
            "source_client": "bundestag_mine",
            "language": "de",
            "url": url,
            "title": title,
            "format": "md",
            "created_time": speech.protocol.date,
            "last_edited_time": speech.protocol.date,
            "speaker_party": speech.speaker.party,
            "speaker": speaker_name,
            "agenda_item_number": agenda_item_number,
            "protocol_number": protocol_number,
            "document_number": f"{legislature_period}/{protocol_number}",  # Standardized identifier
            "legislature_period": legislature_period,
            "document_type": "speech",
        }

        # Extract party composition from speaker metadata
        if speech.speaker and speech.speaker.party:
            parliamentary_composition = (
                PartyExtractor.extract_from_speaker_party(speech.speaker.party)
            )
            metadata["parliamentary_composition"] = parliamentary_composition

        return metadata

    def _extract_metadata_from_dip(self, dip_doc: DIPDocument) -> dict:
        """
        Extract metadata from a DIP document.

        Args:
            dip_doc: DIPDocument object

        Returns:
            Dictionary containing extracted metadata
        """
        content = dip_doc.content
        source_type = dip_doc.source_type

        # Extract common fields present in all DIP documents
        metadata = {
            "datasource": "bundestag",
            "source_client": "dip",
            "language": "de",
            "format": "md",
            "document_type": source_type,
        }

        # Extract common metadata across all document types
        fundstelle = content.get("fundstelle", {})

        # Add document ID if available
        if "id" in content:
            metadata["document_id"] = str(content["id"])

        # Add publisher (herausgeber) if available
        if "herausgeber" in content:
            metadata["publisher"] = str(content["herausgeber"])

        # Add document art (dokumentart) if available
        if "dokumentart" in content:
            metadata["document_art"] = content["dokumentart"]

        # Extract type-specific metadata
        if source_type == "protocol":
            # Plenary protocol metadata
            dokumentnummer = content.get("dokumentnummer", "unknown")
            wahlperiode = content.get("wahlperiode", "")
            titel = content.get("titel", f"Plenary Protocol {dokumentnummer}")

            metadata.update(
                {
                    "title": titel,
                    "protocol_number": dokumentnummer,
                    "document_number": dokumentnummer,  # Standardized identifier (same as protocol_number for protocols)
                    "legislature_period": wahlperiode,
                    "url": fundstelle.get("pdf_url", ""),
                    "created_time": content.get("datum", ""),
                    "last_edited_time": content.get(
                        "aktualisiert", content.get("datum", "")
                    ),
                }
            )

            # Add fundstelle reference metadata
            if "verteildatum" in fundstelle:
                metadata["distribution_date"] = fundstelle["verteildatum"]
            if "xml_url" in fundstelle:
                metadata["xml_url"] = fundstelle["xml_url"]

            # Add vorgangsbezug (proceedings references) count
            if "vorgangsbezug_anzahl" in content:
                metadata["related_proceedings_count"] = content[
                    "vorgangsbezug_anzahl"
                ]

            # Extract parliamentary composition from protocol text
            text = content.get("text", "")
            parliamentary_composition = (
                PartyExtractor.extract_from_protocol_text(text)
            )
            metadata["parliamentary_composition"] = parliamentary_composition

            # Log extraction results
            num_fractions = len(parliamentary_composition.get("fractions", []))
            confidence = parliamentary_composition.get("confidence", "unknown")
            self.logger.info(
                f"Extracted {num_fractions} fractions from protocol {dokumentnummer} "
                f"(confidence: {confidence})"
            )

        elif source_type == "drucksache":
            # Printed material metadata
            dokumentnummer = content.get("dokumentnummer", "unknown")
            wahlperiode = content.get("wahlperiode", "")
            drucksachetyp = content.get("drucksachetyp", "")

            metadata.update(
                {
                    "title": f"Drucksache {dokumentnummer}",
                    "document_number": dokumentnummer,
                    "document_subtype": drucksachetyp,
                    "legislature_period": wahlperiode,
                    "url": fundstelle.get("pdf_url", ""),
                    "created_time": content.get("datum", ""),
                    "last_edited_time": content.get(
                        "aktualisiert", content.get("datum", "")
                    ),
                }
            )

            # Add fundstelle reference metadata
            if "verteildatum" in fundstelle:
                metadata["distribution_date"] = fundstelle["verteildatum"]
            if "xml_url" in fundstelle:
                metadata["xml_url"] = fundstelle["xml_url"]

        elif source_type == "proceeding":
            # Legislative proceeding metadata
            titel = content.get("titel", "")
            vorgangsnummer = content.get("vorgangsnummer", "unknown")
            wahlperiode = content.get("wahlperiode", "")

            metadata.update(
                {
                    "title": titel or f"Proceeding {vorgangsnummer}",
                    "document_number": vorgangsnummer,
                    "legislature_period": wahlperiode,
                    "url": fundstelle.get("url", ""),
                    "created_time": content.get("datum", ""),
                    "last_edited_time": content.get(
                        "aktualisiert", content.get("datum", "")
                    ),
                }
            )

        return metadata


class BundestagMineDatasourceParserFactory(Factory):
    """
    Factory for creating instances of BundestagMineDatasourceParser.

    Creates and configures BundestagMineDatasourceParser objects according to
    the provided configuration.
    """

    _configuration_class: Type = BundestagMineDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: BundestagMineDatasourceConfiguration
    ) -> BundestagMineDatasourceParser:
        """
        Create an instance of BundestagMineDatasourceParser.

        Args:
            configuration: Configuration for the parser (not used in this implementation)

        Returns:
            An instance of BundestagMineDatasourceParser
        """
        return BundestagMineDatasourceParser()
