import sys
import uuid

sys.path.append("./src")


from extraction.datasources.bundestag.client import (
    AgendaItem,
    BundestagSpeech,
    Protocol,
    Speaker,
)
from extraction.datasources.bundestag.document import BundestagMineDocument
from extraction.datasources.bundestag.parser import (
    BundestagMineDatasourceParser,
)


class Fixtures:
    def __init__(self):
        self.speech = None

    def with_speech(self) -> "Fixtures":
        protocol = Protocol(
            id=str(uuid.uuid4()),
            legislaturePeriod="19",
            number="123",
            date="2023-01-01",
        )

        speaker = Speaker(
            id=str(uuid.uuid4()),
            firstName="John",
            lastName="Doe",
            party="Test Party",
        )

        agenda_item = AgendaItem(id=str(uuid.uuid4()), agendaItemNumber="42")

        self.speech = BundestagSpeech(
            id=str(uuid.uuid4()),
            text="This is a test markdown content.",
            speakerId=speaker.id,
            protocol=protocol,
            speaker=speaker,
            agendaItem=agenda_item,
        )

        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures
        self.parser = BundestagMineDatasourceParser()


class Assertions:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.parser = arrangements.parser

    def assert_metadata_extraction(self, metadata: dict) -> "Assertions":
        speech = self.fixtures.speech
        assert metadata["datasource"] == "bundestag"
        assert metadata["language"] == "de"
        assert (
            metadata["url"]
            == f"https://dserver.bundestag.de/btp/{speech.protocol.legislaturePeriod}/{speech.protocol.legislaturePeriod}{speech.protocol.number}.pdf"
        )
        assert (
            metadata["title"]
            == f"Protocol/Legislature/AgendaItem {speech.protocol.number}/{speech.protocol.legislaturePeriod}/{speech.agendaItem.agendaItemNumber}"
        )
        assert metadata["format"] == "md"
        assert metadata["created_time"] == speech.protocol.date
        assert metadata["last_edited_time"] == speech.protocol.date
        assert metadata["speaker_party"] == speech.speaker.party
        assert (
            metadata["speaker"]
            == f"{speech.speaker.firstName} {speech.speaker.lastName}"
        )
        assert (
            metadata["agenda_item_number"] == speech.agendaItem.agendaItemNumber
        )
        assert metadata["protocol_number"] == speech.protocol.number
        assert (
            metadata["legislature_period"] == speech.protocol.legislaturePeriod
        )
        return self

    def assert_none_metadata(self, metadata) -> "Assertions":
        assert metadata is None
        return self

    def assert_document_parsing(
        self, document: BundestagMineDocument
    ) -> "Assertions":
        speech = self.fixtures.speech
        assert isinstance(document, BundestagMineDocument)
        assert document.text == speech.text
        assert document.metadata["datasource"] == "bundestag"
        assert (
            document.metadata["speaker"]
            == f"{speech.speaker.firstName} {speech.speaker.lastName}"
        )
        assert (
            document.metadata["title"]
            == f"Protocol/Legislature/AgendaItem {speech.protocol.number}/{speech.protocol.legislaturePeriod}/{speech.agendaItem.agendaItemNumber}"
        )
        return self

    def assert_none_document(self, document) -> "Assertions":
        assert document is None
        return self


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_parser(self) -> BundestagMineDatasourceParser:
        return self.arrangements.parser


class TestBundestagMineDatasourceParser:

    def test_extract_metadata(self):
        """Test the _extract_metadata_from_speech method."""
        # Arrange
        manager = Manager(Arrangements(Fixtures().with_speech()))
        parser = manager.get_parser()

        # Act
        metadata = parser._extract_metadata_from_speech(manager.fixtures.speech)

        # Assert
        manager.assertions.assert_metadata_extraction(metadata)

    def test_parse(self):
        """Test the parse method."""
        # Arrange
        manager = Manager(Arrangements(Fixtures().with_speech()))
        parser = manager.get_parser()

        # Act
        document = parser.parse(manager.fixtures.speech)

        # Assert
        manager.assertions.assert_document_parsing(document)
