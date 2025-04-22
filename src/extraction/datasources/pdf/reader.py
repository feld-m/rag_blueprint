import logging
import os
from typing import AsyncIterator, Type

from tqdm import tqdm

from core import Factory
from core.logger import LoggerConfiguration
from extraction.datasources.core.base.reader import BaseReader
from extraction.datasources.pdf.configuration import PDFDatasourceConfiguration


class PDFDatasourceReader(BaseReader):
    def __init__(
        self,
        configuration: PDFDatasourceConfiguration,
        logger: logging.Logger = LoggerConfiguration.get_logger(__name__),
    ):
        """Initialize PDF reader.

        Args:
            configuration: Settings for PDF processing
            logger: Logger instance for logging messages
        """
        super().__init__()
        self.export_limit = configuration.export_limit
        self.base_path = configuration.base_path
        self.logger = logger

    async def read_all_async(self) -> AsyncIterator[str]:
        """Asynchronously yield PDF file paths from the configured directory.

        Retrieves a list of PDF files from the base path, applies any configured
        export limit, and yields each file path individually.

        Returns:
            AsyncIterator[str]: An asynchronous iterator of PDF file paths
        """
        self.logger.info(
            f"Fetching PDF files from '{self.base_path}' with limit {self.export_limit}"
        )

        pdf_files = [f for f in os.listdir(self.base_path) if f.endswith(".pdf")]
        files_to_load = (
            pdf_files if self.export_limit is None else pdf_files[: self.export_limit]
        )

        for file_name in tqdm(files_to_load, desc="[PDF] Loading files", unit="files"):
            file_path = os.path.join(self.base_path, file_name)
            if os.path.isfile(file_path):
                yield file_path


class PDFDatasourceReaderFactory(Factory):
    """Factory for creating PDF reader instances.

    Implements the factory pattern to produce configured PDFDatasourceReader
    objects based on the provided configuration settings.
    """

    _configuration_class: Type = PDFDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: PDFDatasourceConfiguration
    ) -> PDFDatasourceReader:
        """Create a new PDFDatasourceReader with the specified configuration.

        Args:
            configuration: Settings that control PDF processing behavior including
                           base path and export limits

        Returns:
            PDFDatasourceReader: A fully configured reader instance ready for use
        """
        return PDFDatasourceReader(configuration=configuration)
