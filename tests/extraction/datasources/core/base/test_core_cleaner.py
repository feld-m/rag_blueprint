import sys
from unittest.mock import Mock

import pytest

sys.path.append("./src")


from extraction.datasources.confluence.document import ConfluenceDocument
from extraction.datasources.core.base.cleaner import BasicMarkdownCleaner


class Fixtures:
    def __init__(self):
        self.confluence_document: ConfluenceDocument = None
        self.confluence_cleaned_document: ConfluenceDocument = None

    def with_document(self, text: str) -> "Fixtures":
        document = Mock(spec=ConfluenceDocument)
        document.text = text
        self.confluence_document = document

        cleaned_document = Mock(spec=ConfluenceDocument)
        cleaned_document.text = "This is page document"
        self.confluence_cleaned_document = cleaned_document

        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures
        self.service = BasicMarkdownCleaner()


class Assertions:
    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def with_expected_document(self, text) -> "Assertions":
        if text is None:
            self.expected_document = None
        else:
            self.expected_document = Mock(spec=ConfluenceDocument)
            self.expected_document.text = text
        return self

    def assert_cleaned_documents(
        self, cleaned_document: ConfluenceDocument
    ) -> "Assertions":
        if self.expected_document is None:
            assert self.expected_document == cleaned_document
        else:
            assert cleaned_document.text == self.expected_document.text
        return self


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> BasicMarkdownCleaner:
        return self.arrangements.service


class TestConfluenceCleaner:
    @pytest.mark.parametrize(
        "document_text, expected_document_text",
        [
            ("This is page document", "This is page document"),
            (" \n   \t\n\t ", None),
        ],
    )
    def test_given_documents_when_clean_then_documents_are_cleaned(
        self, document_text: str, expected_document_text: str
    ):
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_document(document_text)),
        )
        service = manager.get_service()

        # Act
        cleaned_document = service.clean(manager.fixtures.confluence_document)

        # Assert
        manager.assertions.with_expected_document(
            expected_document_text
        ).assert_cleaned_documents(cleaned_document)
