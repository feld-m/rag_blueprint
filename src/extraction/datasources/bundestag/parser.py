from typing import Type, Union

from core.base_factory import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.bundestag.client import BundestagSpeech
from extraction.datasources.bundestag.client_dip import DIPDocument
from extraction.datasources.bundestag.configuration import (
    BundestagMineDatasourceConfiguration,
)
from extraction.datasources.bundestag.document import BundestagMineDocument
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
        return BundestagMineDocument(text=dip_doc.text, metadata=metadata)

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

        return {
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
