from typing import Type

from core.base_factory import Factory
from extraction.datasources.core.manager import BasicDatasourceManager
from extraction.datasources.pdf.reader import PDFDatasourceReaderFactory
from extraction.datasources.pdf_sales.configuration import (
    PDFSalesDatasourceConfiguration,
)
from extraction.datasources.pdf_sales.parser import (
    PDFSalesDatasourceParserFactory,
)


class PDFSalesDatasourceManagerFactory(Factory):
    """Factory for creating PDF Sales datasource managers.

    Provides type-safe creation of datasource managers based on configuration.

    Attributes:
        _configuration_class: Type of configuration object
    """

    _configuration_class: Type = PDFSalesDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: PDFSalesDatasourceConfiguration
    ) -> BasicDatasourceManager:
        """Create an instance of the PDF Sales datasource manager.

        This method constructs a BasicDatasourceManager by creating the appropriate
        reader and parser based on the provided configuration.

        Args:
            configuration: Configuration specifying how to set up the PDF Sales datasource
                          manager, reader, and parser.

        Returns:
            A configured BasicDatasourceManager instance for handling PDF Sales documents.
        """
        reader = PDFDatasourceReaderFactory.create(configuration)
        parser = PDFSalesDatasourceParserFactory.create(configuration)
        return BasicDatasourceManager(
            configuration=configuration,
            reader=reader,
            parser=parser,
        )
