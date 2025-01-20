from injector import inject

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    PdfDatasourceConfiguration,
)
from common.bootstrap.configuration.pipeline.embedding.embedding_model.embedding_model_binding_keys import (
    BoundEmbeddingModelMarkdownSplitter,
)
from embedding.datasources.core.cleaner import Cleaner
from embedding.datasources.pdf.manager import PdfDatasourceManager
from embedding.datasources.pdf.reader import PdfReader


class PdfReaderBuilder:
    """Builder for creating PDF reader instances.

    Provides factory method to create configured PdfReader objects.
    """

    @staticmethod
    @inject
    def build(
        configuration: PdfDatasourceConfiguration,
    ) -> PdfReader:
        """Creates a configured PDF reader.

        Args:
            configuration: Settings for PDF processing

        Returns:
            PdfReader: Configured reader instance
        """
        return PdfReader(
            configuration=configuration,
        )


class PdfDatasourceManagerBuilder:
    """Builder for creating PDF datasource manager instances.

    Provides factory method to create configured PdfDatasourceManager
    with required components for content processing.
    """

    @staticmethod
    @inject
    def build(
        configuration: PdfDatasourceConfiguration,
        reader: PdfReader,
        cleaner: Cleaner,
        splitter: BoundEmbeddingModelMarkdownSplitter,
    ) -> PdfDatasourceManager:
        """Creates a configured PDF datasource manager.

        Args:
            configuration: Settings for PDF processing
            reader: Component for reading PDF content
            cleaner: Component for cleaning extracted content
            splitter: Component for splitting content into chunks

        Returns:
            PdfDatasourceManager: Configured manager instance
        """
        return PdfDatasourceManager(
            configuration=configuration,
            reader=reader,
            cleaner=cleaner,
            splitter=splitter,
        )


class PdfCleanerBuilder:
    """Builder for creating PDF content cleaner instances.

    Provides factory method to create Cleaner objects for PDF content.
    """

    @staticmethod
    @inject
    def build() -> Cleaner:
        """Creates a content cleaner for PDFs.

        Returns:
            Cleaner: Configured cleaner instance
        """
        return Cleaner()
