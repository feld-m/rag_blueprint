from typing import Type

from core import Factory
from extraction.datasources.core.base.manager import BasicDatasourceManager
from extraction.datasources.pdf.configuration import PDFDatasourceConfiguration
from extraction.datasources.pdf.parser import PDFDatasourceParserFactory
from extraction.datasources.pdf.reader import PDFDatasourceReaderFactory


class PDFDatasourceManagerFactory(Factory):
    """Factory for creating datasource managers.

    Provides type-safe creation of datasource managers based on configuration.

    Attributes:
        _configuration_class: Type of configuration object
    """

    _configuration_class: Type = PDFDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: PDFDatasourceConfiguration
    ) -> BasicDatasourceManager:
        """Create an instance of the PDF datasource manager.

        This method constructs a BasicDatasourceManager by creating the appropriate
        reader and parser based on the provided configuration.

        Args:
            configuration: Configuration specifying how to set up the PDF datasource
                          manager, reader, and parser.

        Returns:
            A configured BasicDatasourceManager instance for handling PDF documents.
        """
        reader = PDFDatasourceReaderFactory.create(configuration)
        parser = PDFDatasourceParserFactory.create(configuration)
        return BasicDatasourceManager(
            configuration=configuration,
            reader=reader,
            parser=parser,
        )
