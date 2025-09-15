import sys
from typing import Callable
from unittest.mock import Mock

sys.path.append("./src")

from markitdown import MarkItDown

from extraction.datasources.pdf_sales.document import PDFSalesDocument
from extraction.datasources.pdf_sales.parser import PDFSalesDatasourceParser


class Fixtures:

    def __init__(self):
        self.file_path: str = None
        self.markdown_content: str = None
        self.expected_metadata: dict = None

    def with_file_path(self) -> "Fixtures":
        self.file_path = "/fake/path/document.pdf"
        return self

    def with_basic_markdown_content(self) -> "Fixtures":
        self.markdown_content = """
        # Test Document
        Client: Test Client
        Quote: Test Quote
        Project Lead: John Doe
        Valid until: 01/01/2024
        """
        return self

    def with_complex_markdown_content(self) -> "Fixtures":
        self.markdown_content = """
        # Test Document
        Client: Complex Client Corporation
        Date: 15.03.2023
        Project
        Lead: Jane Smith
        Valid until: 31/12/2024
        Some other text
        """
        return self

    def with_missing_fields_markdown_content(self) -> "Fixtures":
        self.markdown_content = """
        # Test Document
        Some text without any of the required fields
        """
        return self

    def with_expected_metadata(self, **kwargs) -> "Fixtures":
        self.expected_metadata = {
            "datasource": "pdf_sales",
            "format": "pdf",
            "url": None,
            "title": "document.pdf",
            "created_date": "2023-01-01",
            "last_edited_date": "2023-01-01",
            "valid_until": "01/01/2024",
            "client_name": "Unknown Client",
            "offer_name": "Generic Offer",
            "project_lead": "Not Assigned",
        }
        self.expected_metadata.update(kwargs)
        return self


class Arrangements:

    def __init__(self, fixtures: Fixtures) -> None:
        self.fixtures = fixtures
        self.markitdown_mock = Mock(spec=MarkItDown)
        self.metadata_extractor = Mock(spec=Callable)
        self.parser = PDFSalesDatasourceParser(
            parser=self.markitdown_mock,
            metadata_extractor=self.metadata_extractor,
        )

    def on_markitdown_convert_return_content(self) -> "Arrangements":
        class MarkdownContent:
            def __init__(self, content):
                self.text_content = content

        self.markitdown_mock.convert.return_value = MarkdownContent(
            self.fixtures.markdown_content
        )
        return self

    def on_file_metadata_func_return_basic_metadata(self) -> "Arrangements":
        self.metadata_extractor.return_value = {
            "creation_date": "2023-01-01",
            "last_modified_date": "2023-01-01",
            "file_path": self.fixtures.file_path,
        }
        return self


class Assertions:

    def __init__(self, arrangements: Arrangements) -> None:
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements

    def assert_document_metadata(self, document: PDFSalesDocument) -> None:
        """Verify that the document's metadata matches the expected values"""
        for key, expected_value in self.fixtures.expected_metadata.items():
            assert (
                document.metadata.get(key) == expected_value
            ), f"Metadata {key} does not match expected value"

    def assert_document_text(self, document: PDFSalesDocument) -> None:
        """Verify that the document's text has been preprocessed correctly"""
        # Verify the basic content is preserved
        assert (
            document.text is not None and len(document.text) > 0
        ), "Document text should not be empty"

        # Check for specific preprocessing transformations
        if "Projektl eiter" in self.fixtures.markdown_content:
            assert (
                "Projektleiter" in document.text
            ), "Text preprocessing failed for 'Projektleiter'"

        if "Project\nLead" in self.fixtures.markdown_content:
            assert (
                "Project Lead" in document.text
            ), "Text preprocessing failed for 'Project Lead'"


class Manager:

    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements)

    def get_service(self) -> PDFSalesDatasourceParser:
        return self.arrangements.parser


class TestPDFSalesParser:

    def test_given_basic_markdown_when_parse_then_fields_extracted(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_file_path()
                .with_basic_markdown_content()
                .with_expected_metadata(
                    client_name="Test Client",
                    offer_name="Test Quote",
                    project_lead="John Doe",
                    valid_until="01/01/2024",
                )
            )
            .on_markitdown_convert_return_content()
            .on_file_metadata_func_return_basic_metadata()
        )
        service = manager.get_service()

        # Act
        document = service.parse(manager.fixtures.file_path)

        # Assert
        manager.assertions.assert_document_metadata(document)
        manager.assertions.assert_document_text(document)

    def test_given_complex_markdown_when_parse_then_fields_extracted(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_file_path()
                .with_complex_markdown_content()
                .with_expected_metadata(
                    client_name="Complex Client Corporation",
                    project_lead="Jane Smith",
                    valid_until="31/12/2024",
                )
            )
            .on_markitdown_convert_return_content()
            .on_file_metadata_func_return_basic_metadata()
        )
        service = manager.get_service()

        # Act
        document = service.parse(manager.fixtures.file_path)

        # Assert
        manager.assertions.assert_document_metadata(document)
        manager.assertions.assert_document_text(document)

    def test_given_missing_fields_when_parse_then_default_values_used(self):
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_file_path()
                .with_missing_fields_markdown_content()
                .with_expected_metadata()
            )
            .on_markitdown_convert_return_content()
            .on_file_metadata_func_return_basic_metadata()
        )
        service = manager.get_service()

        # Act
        document = service.parse(manager.fixtures.file_path)

        # Assert
        manager.assertions.assert_document_metadata(document)
        manager.assertions.assert_document_text(document)

    def test_extract_fields_extracts_valid_fields(self):
        # Arrange
        markdown = """
        Valid until: 15/03/2024
        Client: Test Corporation
        Quote: Special Offer
        Project Lead: Jane Manager
        """
        metadata = {"existing": "value"}
        parser = PDFSalesDatasourceParser()

        # Act
        result = parser._extract_fields(
            markdown, metadata, PDFSalesDatasourceParser.FIELDS_TO_EXTRACT
        )

        # Assert
        assert result["valid_until"] == "15/03/2024"
        assert result["client_name"] == "Test Corporation"
        assert result["offer_name"] == "Special Offer"
        assert result["project_lead"] == "Jane Manager"
        assert result["existing"] == "value"  # Preserves existing metadata
