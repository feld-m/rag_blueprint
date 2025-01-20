import sys
from unittest.mock import Mock

sys.path.append("./src")

from typing import List

from embedding.datasources.confluence.document import ConfluenceDocument
from embedding.datasources.core.cleaner import Cleaner


class Fixtures:

    def __init__(self):
        self.confluence_documents: List[ConfluenceDocument] = []
        self.confluence_cleaned_documents: List[ConfluenceDocument] = []

    def with_document(self) -> "Fixtures":
        document = Mock(spec=ConfluenceDocument)
        document.text = "This is page document"
        self.confluence_documents.append(document)

        cleaned_document = Mock(spec=ConfluenceDocument)
        cleaned_document.text = "This is page document"
        self.confluence_cleaned_documents.append(cleaned_document)

        return self

    def with_empty_document(self) -> "Fixtures":
        document = Mock(spec=ConfluenceDocument)
        document.text = " \n   \t\n\t "
        self.confluence_documents.append(document)

        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.service = Cleaner()


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_cleaned_documents(
        self, cleaned_documents: List[ConfluenceDocument]
    ) -> None:
        assert len(cleaned_documents) == len(
            self.fixtures.confluence_cleaned_documents
        )
        for cleaned_document, expected_cleaned_document in zip(
            cleaned_documents, self.fixtures.confluence_cleaned_documents
        ):
            assert cleaned_document.text == expected_cleaned_document.text


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> Cleaner:
        return self.arrangements.service


class TestConfluenceCleaner:

    def test_given_documents_when_clean_then_documents_are_cleaned(self):
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_document().with_empty_document()),
        )
        service = manager.get_service()

        # Act
        cleaned_documents = service.clean(manager.fixtures.confluence_documents)

        # Assert
        manager.assertions.assert_cleaned_documents(cleaned_documents)
