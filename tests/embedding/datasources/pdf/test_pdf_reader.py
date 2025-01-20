import os
import sys
from typing import List
from unittest.mock import Mock, patch

import pytest

sys.path.append("./src")

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    PdfDatasourceConfiguration,
)
from embedding.datasources.pdf.document import PdfDocument
from embedding.datasources.pdf.reader import PdfReader


class Fixtures:
    def __init__(self):
        self.export_limit: int = None
        self.base_path: str = None
        self.file_names: List[str] = []
        self.pdf_contents: dict = {}

    def with_export_limit(self, export_limit: int) -> "Fixtures":
        self.export_limit = export_limit
        return self

    def with_base_path(self) -> "Fixtures":
        self.base_path = "/fake/path"
        return self

    def with_pdf_files(self, number_of_files: int) -> "Fixtures":
        for i in range(number_of_files):
            file_name = f"document_{i}.pdf"
            self.file_names.append(file_name)
            self.pdf_contents[file_name] = f"Content of PDF {i}"
        return self

    def with_non_pdf_files(self, number_of_files: int) -> "Fixtures":
        for i in range(number_of_files):
            file_name = f"document_{i}.txt"
            self.file_names.append(file_name)
        return self


class Arrangements:
    def __init__(self, fixtures: Fixtures):
        self.fixtures = fixtures
        self.configuration = Mock(spec=PdfDatasourceConfiguration)
        self.configuration.export_limit = self.fixtures.export_limit
        self.configuration.base_path = self.fixtures.base_path
        self.configuration.nlm_parser_enabled = False
        self.service = PdfReader(configuration=self.configuration)

    def on_os_listdir(self) -> "Arrangements":
        self.listdir_patcher = patch(
            "os.listdir", return_value=self.fixtures.file_names
        )
        self.mock_listdir = self.listdir_patcher.start()
        return self

    def on_pdf_document_creation(self) -> "Arrangements":
        def isfile_side_effect(path):
            return path.endswith(
                ".pdf"
            )  # Ensure only PDF files are considered valid.

        def parse_side_effect(file_path: str) -> List[PdfDocument]:
            file_name = os.path.basename(file_path)
            content = self.fixtures.pdf_contents.get(file_name, "")
            return [PdfDocument(text=content, metadata={}, attachments=None)]

        self.isfile_patcher = patch(
            "os.path.isfile", side_effect=isfile_side_effect
        )
        self.parse_patcher = patch(
            "embedding.datasources.pdf.reader.DefaultPDFParser.parse",
            side_effect=parse_side_effect,
        )

        self.mock_isfile = self.isfile_patcher.start()
        self.mock_parse = self.parse_patcher.start()

        return self

    def stop_patches(self):
        self.listdir_patcher.stop()
        self.isfile_patcher.stop()
        self.create_document_patcher.stop()


class Assertions:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.service = arrangements.service

    def assert_documents(self, documents: List[PdfDocument]):
        expected_pdf_files = [
            f for f in self.fixtures.file_names if f.endswith(".pdf")
        ]
        if self.fixtures.export_limit is not None:
            expected_num_documents = min(
                self.fixtures.export_limit, len(expected_pdf_files)
            )
        else:
            expected_num_documents = len(expected_pdf_files)
        assert len(documents) == expected_num_documents
        for i, actual_document in enumerate(documents):
            expected_file_name = expected_pdf_files[i]
            expected_content = self.fixtures.pdf_contents[expected_file_name]
            assert actual_document.text == expected_content


class Manager:
    def __init__(self, arrangements: Arrangements):
        self.fixtures = arrangements.fixtures
        self.arrangements = arrangements
        self.assertions = Assertions(arrangements=arrangements)

    def get_service(self) -> PdfReader:
        return self.arrangements.service


class TestPdfReader:
    @pytest.mark.parametrize(
        "export_limit,number_of_pdfs,number_of_non_pdfs",
        [
            (5, 10, 5),
            (10, 15, 10),
            (None, 8, 2),
            (3, 5, 5),
            (20, 25, 5),
            (None, 0, 10),
            (5, 0, 10),
        ],
    )
    def test(
        self, export_limit: int, number_of_pdfs: int, number_of_non_pdfs: int
    ) -> None:
        # Arrange
        manager = Manager(
            Arrangements(
                Fixtures()
                .with_export_limit(export_limit)
                .with_base_path()
                .with_pdf_files(number_of_pdfs)
                .with_non_pdf_files(number_of_non_pdfs)
            )
            .on_os_listdir()
            .on_pdf_document_creation()
        )
        service = manager.get_service()

        # Act
        documents = service.get_all_documents()

        # Assert
        manager.assertions.assert_documents(documents)
