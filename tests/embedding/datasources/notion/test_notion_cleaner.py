import sys
from unittest.mock import Mock

from embedding.datasources.notion.cleaner import NotionCleaner
from embedding.datasources.notion.document import NotionDocument

sys.path.append("./src")

import textwrap
from typing import List

from llama_index_client import Document


class Fixtures:

    def __init__(self):
        self.notion_documents: List[NotionDocument] = []
        self.notion_cleaned_documents: List[NotionDocument] = []

    def with_database_document(self) -> "Fixtures":
        document = Mock(spec=NotionDocument)
        document.text = textwrap.dedent(
            """
            This is a database document
            <!-- With HTML comment -->
            <div>
                <p>And some HTML content</p>
            </div>
            As well as normal text
        """
        )
        document.extra_info = {"type": "database"}
        self.notion_documents.append(document)

        cleaned_document = Mock(spec=NotionDocument)
        cleaned_document.text = textwrap.dedent(
            """
            This is a database document


                And some HTML content

            As well as normal text
        """
        )
        cleaned_document.extra_info = {"type": "database"}
        self.notion_cleaned_documents.append(cleaned_document)

        return self

    def with_page_document(self) -> "Fixtures":
        document = Mock(spec=NotionDocument)
        document.text = textwrap.dedent(
            """
            This is a database document
            <!-- With HTML comment -->
            <div attr="value">
                <a attr="href">And some HTML content</a>
            </div>
            As well as normal text
        """
        )
        document.extra_info = {"type": "page"}
        self.notion_documents.append(document)

        cleaned_document = Mock(spec=NotionDocument)
        cleaned_document.text = textwrap.dedent(
            """
            This is a database document


                And some HTML content

            As well as normal text
        """
        )
        cleaned_document.extra_info = {"type": "page"}
        self.notion_cleaned_documents.append(cleaned_document)

        return self

    def with_empty_document(self) -> "Fixtures":
        document = Mock(spec=NotionDocument)
        document.text = " \n   \t\n\t "
        document.extra_info = {"type": "page"}
        self.notion_documents.append(document)

        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures

        self.service = NotionCleaner()


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_cleaned_documents(
        self, cleaned_documents: List[Document]
    ) -> None:
        assert len(cleaned_documents) == len(
            self.fixtures.notion_cleaned_documents
        )
        for cleaned_document, expected_cleaned_document in zip(
            cleaned_documents, self.fixtures.notion_cleaned_documents
        ):
            assert cleaned_document.text == expected_cleaned_document.text


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> NotionCleaner:
        return self.arrangements.service


class TestNotionCleaner:

    def test_given_database_document_when_clean_then_document_is_cleaned(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_database_document(),
            ),
        )
        service = manager.get_service()

        # Act
        cleaned_documents = service.clean(manager.fixtures.notion_documents)

        # Assert
        manager.assertions.assert_cleaned_documents(cleaned_documents)

    def test_given_page_document_when_clean_then_document_is_cleaned(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_page_document(),
            ),
        )
        service = manager.get_service()

        # Act
        cleaned_documents = service.clean(manager.fixtures.notion_documents)

        # Assert
        manager.assertions.assert_cleaned_documents(cleaned_documents)

    def test_given_empty_document_when_clean_then_document_is_not_cleaned(
        self,
    ):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures().with_empty_document(),
            ),
        )
        service = manager.get_service()

        # Act
        cleaned_documents = service.clean(manager.fixtures.notion_documents)

        # Assert
        manager.assertions.assert_cleaned_documents(cleaned_documents)
