import sys

from embedding.datasources.core.cleaner import Cleaner
from embedding.datasources.pdf.document import PdfDocument

sys.path.append("./src")

from typing import List


class Fixtures:
    def __init__(self):
        self.pdf_documents: List[PdfDocument] = []
        self.pdf_cleaned_documents: List[PdfDocument] = []

    def with_document(self) -> "Fixtures":
        """
        Adds a valid document with text to the fixtures.
        """
        document = PdfDocument(text="This is page document", metadata={})
        self.pdf_documents.append(document)

        cleaned_document = PdfDocument(
            text="This is page document", metadata={}
        )
        self.pdf_cleaned_documents.append(cleaned_document)

        return self

    def with_empty_document(self) -> "Fixtures":
        """
        Adds an empty document to the fixtures.
        """
        document = PdfDocument(text=" \n   \t\n\t ", metadata={})
        self.pdf_documents.append(document)
        # No corresponding cleaned document for empty input
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures
        self.service = Cleaner()  # Instance of the cleaner service


class Assertions:
    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.service = arrangements.service

    def assert_cleaned_documents(
        self, cleaned_documents: List[PdfDocument]
    ) -> None:
        """
        Verifies that the cleaned documents match the expected cleaned documents in the fixtures.
        """
        assert len(cleaned_documents) == len(
            self.fixtures.pdf_cleaned_documents
        )
        for cleaned_document, expected_cleaned_document in zip(
            cleaned_documents, self.fixtures.pdf_cleaned_documents
        ):
            assert cleaned_document.text == expected_cleaned_document.text


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> Cleaner:
        return self.arrangements.service


class TestCleaner:
    def test_given_documents_when_clean_then_documents_are_cleaned(self):
        # Arrange
        manager = Manager(
            Arrangements(Fixtures().with_document().with_empty_document()),
        )
        service = manager.get_service()

        # Act
        cleaned_documents = service.clean(manager.fixtures.pdf_documents)

        # Assert
        manager.assertions.assert_cleaned_documents(cleaned_documents)
