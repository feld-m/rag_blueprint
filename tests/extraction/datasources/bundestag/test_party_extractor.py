"""Unit tests for PartyExtractor."""

import sys

sys.path.append("./src")

from extraction.datasources.bundestag.party_extractor import PartyExtractor


class TestPartyExtractor:
    """Tests for dynamic party extraction from protocol text."""

    def test_extract_from_protocol_text_21st_bundestag(self):
        """Test extraction from 21st Bundestag protocol sample."""
        text = """
        Steffen Bilger (CDU/CSU) sprach über das Thema...
        Jens Spahn (CDU/CSU) erklärte den Antrag...
        Alexander Dobrindt (CDU/CSU) widersprach...
        Dr. Bernd Baumann (AfD) erklärte seine Position...
        Alice Weidel (AfD) kritisierte...
        Tino Chrupalla (AfD) betonte...
        Katja Mast (SPD) betonte die Wichtigkeit...
        Lars Klingbeil (SPD) stimmte zu...
        Esken Saskia (SPD) fügte hinzu...
        Dr. Irene Mihalic (BÜNDNIS 90/DIE GRÜNEN) forderte Maßnahmen...
        Robert Habeck (BÜNDNIS 90/DIE GRÜNEN) unterstützte...
        Annalena Baerbock (BÜNDNIS 90/DIE GRÜNEN) ergänzte...
        Christian Görke (Die Linke) kritisierte den Vorschlag...
        Dietmar Bartsch (Die Linke) stimmte zu...
        Gregor Gysi (Die Linke) schloss ab...
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        # Verify basic structure
        assert "fractions" in result
        assert "extraction_source" in result
        assert "confidence" in result
        assert "extracted_at" in result

        # Verify extraction source
        assert result["extraction_source"] == "protocol_text"

        # Verify confidence
        assert result["confidence"] in ["high", "medium", "low"]
        assert result["confidence"] == "high"  # Should be high with 5 fractions

        # Verify number of fractions
        fractions = result["fractions"]
        assert len(fractions) == 5

        # Extract fraction names
        fraction_names = [f["name"] for f in fractions]

        # Verify all expected parties are present (case-insensitive substring match)
        # CDU/CSU might be CDU/CSU, or just "CDU/CSU"
        assert any(
            "CDU" in name.upper() and "CSU" in name.upper()
            for name in fraction_names
        )
        assert any("AFD" in name.upper() for name in fraction_names)
        assert any("SPD" in name.upper() for name in fraction_names)
        assert any(
            "GRÜN" in name.upper() or "BÜNDNIS" in name.upper()
            for name in fraction_names
        )
        assert any("LINKE" in name.upper() for name in fraction_names)

        # Verify each fraction has required fields
        for fraction in fractions:
            assert "name" in fraction
            assert "variations" in fraction
            assert "type" in fraction
            assert "mention_count" in fraction
            assert fraction["type"] == "fraction"
            assert isinstance(fraction["variations"], list)
            assert len(fraction["variations"]) >= 1
            assert fraction["mention_count"] >= 1

    def test_extract_from_protocol_text_20th_bundestag(self):
        """Test extraction from 20th Bundestag protocol (includes FDP)."""
        text = """
        Speaker1 (CDU/CSU) said...
        Speaker2 (CDU/CSU) added...
        Speaker3 (CDU/CSU) concluded...
        Speaker4 (SPD) mentioned...
        Speaker5 (SPD) agreed...
        Speaker6 (SPD) supported...
        Speaker7 (FDP) explained...
        Speaker8 (FDP) proposed...
        Speaker9 (FDP) argued...
        Speaker10 (AfD) argued...
        Speaker11 (AfD) criticized...
        Speaker12 (AfD) opposed...
        Speaker13 (Die Linke) criticized...
        Speaker14 (Die Linke) demanded...
        Speaker15 (Die Linke) suggested...
        Speaker16 (BÜNDNIS 90/DIE GRÜNEN) proposed...
        Speaker17 (BÜNDNIS 90/DIE GRÜNEN) supported...
        Speaker18 (BÜNDNIS 90/DIE GRÜNEN) advocated...
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        fractions = result["fractions"]
        fraction_names = [f["name"] for f in fractions]

        # Verify FDP is included (was in 20th Bundestag)
        assert any("FDP" in name.upper() for name in fraction_names)

        # Should have 6 fractions for 20th Bundestag
        assert len(fractions) == 6

    def test_extract_variations_grouped_correctly(self):
        """Test that party name variations are grouped correctly."""
        text = """
        Hans Müller (CDU) said...
        Johann Schmidt (CDU) added...
        Maria Schmidt (CSU) added...
        Franz Weber (CSU) continued...
        Peter Weber (CDU/CSU) concluded...
        Alexander Dobrindt (CDU/CSU) agreed...
        Anna Klein (GRÜNE) mentioned...
        Sophie Bauer (GRÜNE) agreed...
        Thomas Bauer (DIE GRÜNEN) explained...
        Katrin Göring-Eckardt (DIE GRÜNEN) supported...
        Lisa Wagner (BÜNDNIS 90/DIE GRÜNEN) proposed...
        Robert Habeck (BÜNDNIS 90/DIE GRÜNEN) concluded...
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        fractions = result["fractions"]

        # Should have 2 fractions (CDU/CSU group and Grüne group)
        assert len(fractions) == 2

        # Find CDU/CSU fraction
        cdu_csu_fraction = None
        for f in fractions:
            if "CDU" in f["name"].upper() and "/" in f["name"]:
                cdu_csu_fraction = f
                break

        assert cdu_csu_fraction is not None
        # Should have variations: CDU, CSU, CDU/CSU
        assert len(cdu_csu_fraction["variations"]) == 3
        # Total mentions should be 6 (CDU: 2, CSU: 2, CDU/CSU: 2)
        assert cdu_csu_fraction["mention_count"] == 6

        # Find Grüne fraction
        grune_fraction = None
        for f in fractions:
            if "GRÜN" in f["name"].upper() or "BÜNDNIS" in f["name"].upper():
                grune_fraction = f
                break

        assert grune_fraction is not None
        # Should have variations (GRÜNE, DIE GRÜNEN, BÜNDNIS 90/DIE GRÜNEN)
        assert len(grune_fraction["variations"]) >= 2
        # Total mentions should be 6 (GRÜNE: 2, DIE GRÜNEN: 2, BÜNDNIS 90/DIE GRÜNEN: 2)
        assert grune_fraction["mention_count"] == 6

    def test_extract_from_speaker_party(self):
        """Test extraction from speech speaker metadata."""
        result = PartyExtractor.extract_from_speaker_party("CDU")

        # Verify basic structure
        assert "fractions" in result
        assert "extraction_source" in result
        assert "confidence" in result

        # Verify extraction source
        assert result["extraction_source"] == "speaker_metadata"

        # Verify confidence is low (single speech)
        assert result["confidence"] == "low"

        # Should have 1 fraction
        fractions = result["fractions"]
        assert len(fractions) == 1

        # Verify fraction structure
        fraction = fractions[0]
        assert fraction["name"] == "CDU"
        assert fraction["variations"] == ["CDU"]
        assert fraction["type"] == "fraction"
        assert fraction["mention_count"] == 1

    def test_empty_text(self):
        """Test extraction from empty text."""
        result = PartyExtractor.extract_from_protocol_text("")

        assert result["fractions"] == []
        assert result["extraction_source"] == "none"
        assert result["confidence"] == "low"

    def test_no_parties_found(self):
        """Test text with no party mentions."""
        text = """
        This is just some random text without any party attributions.
        It talks about policies but mentions no parties.
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        assert result["fractions"] == []
        assert result["extraction_source"] == "none"
        assert result["confidence"] == "low"

    def test_filters_non_party_keywords(self):
        """Test that non-party keywords are filtered out."""
        text = """
        Bundeskanzler Friedrich Merz (CDU/CSU) sprach...
        Markus Söder (CDU/CSU) fügte hinzu...
        Bundesminister Lars Klingbeil (SPD) erklärte...
        Saskia Esken (SPD) stimmte zu...
        Präsident Julia Klöckner diskutierte...
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        fractions = result["fractions"]
        fraction_names = [f["name"] for f in fractions]

        # Should only have CDU/CSU and SPD, not "Bundeskanzler", "Bundesminister", "Präsident"
        assert len(fractions) == 2
        assert not any("Bundeskanzler" in name for name in fraction_names)
        assert not any("Bundesminister" in name for name in fraction_names)
        assert not any("Präsident" in name for name in fraction_names)

    def test_is_likely_party_heuristics(self):
        """Test the _is_likely_party heuristic function."""
        # Valid parties
        assert PartyExtractor._is_likely_party("CDU/CSU")
        assert PartyExtractor._is_likely_party("SPD")
        assert PartyExtractor._is_likely_party("AfD")
        assert PartyExtractor._is_likely_party("Die Linke")
        assert PartyExtractor._is_likely_party("BÜNDNIS 90/DIE GRÜNEN")
        assert PartyExtractor._is_likely_party("FDP")

        # Invalid - non-party keywords
        assert not PartyExtractor._is_likely_party("Bundeskanzler")
        assert not PartyExtractor._is_likely_party("Präsident")
        assert not PartyExtractor._is_likely_party("Berlin")
        assert not PartyExtractor._is_likely_party("parteilos")

        # Invalid - too long
        assert not PartyExtractor._is_likely_party(
            "This is a very long text that is definitely not a party name"
        )

        # Invalid - too short
        assert not PartyExtractor._is_likely_party("X")

        # Invalid - no uppercase
        assert not PartyExtractor._is_likely_party("lowercase")

    def test_confidence_scoring(self):
        """Test confidence scoring based on extraction results."""
        # High confidence: 5 fractions, many mentions
        text_high = """
        Speaker1 (CDU/CSU) said... Speaker2 (CDU/CSU) added...
        Speaker3 (SPD) mentioned... Speaker4 (SPD) explained...
        Speaker5 (AfD) argued... Speaker6 (AfD) criticized...
        Speaker7 (BÜNDNIS 90/DIE GRÜNEN) proposed... Speaker8 (BÜNDNIS 90/DIE GRÜNEN) agreed...
        Speaker9 (Die Linke) discussed... Speaker10 (Die Linke) concluded...
        """

        result_high = PartyExtractor.extract_from_protocol_text(text_high)
        assert result_high["confidence"] == "high"

        # Medium confidence: 2-3 fractions, moderate mentions
        text_medium = """
        Speaker1 (CDU/CSU) said... Speaker2 (CDU/CSU) added...
        Speaker3 (SPD) mentioned... Speaker4 (SPD) explained...
        Speaker5 (AfD) argued...
        """

        result_medium = PartyExtractor.extract_from_protocol_text(text_medium)
        assert result_medium["confidence"] in [
            "medium",
            "high",
        ]  # Could be either

        # Low confidence: 1 fraction, few mentions
        text_low = """
        Speaker (CDU/CSU) said something.
        """

        result_low = PartyExtractor.extract_from_protocol_text(text_low)
        assert result_low["confidence"] == "low"

    def test_mention_count_accuracy(self):
        """Test that mention counts are accurate."""
        text = """
        Speaker1 (CDU/CSU) first...
        Speaker2 (CDU/CSU) second...
        Speaker3 (CDU/CSU) third...
        Speaker4 (SPD) first...
        Speaker5 (SPD) second...
        """

        result = PartyExtractor.extract_from_protocol_text(text)

        fractions = result["fractions"]

        # Find CDU/CSU
        cdu_csu = next(
            (f for f in fractions if "CDU" in f["name"] and "/" in f["name"]),
            None,
        )
        assert cdu_csu is not None
        assert cdu_csu["mention_count"] == 3

        # Find SPD
        spd = next((f for f in fractions if f["name"] == "SPD"), None)
        assert spd is not None
        assert spd["mention_count"] == 2
