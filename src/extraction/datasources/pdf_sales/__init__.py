"""
Requires extraction.datasources.pdf package
"""

from extraction.bootstrap.configuration.datasources import (
    DatasourceConfigurationRegistry,
    DatasourceName,
)
from extraction.datasources.pdf_sales.configuration import (
    PDFSalesDatasourceConfiguration,
)
from extraction.datasources.pdf_sales.manager import (
    PDFSalesDatasourceManagerFactory,
)
from extraction.datasources.registry import DatasourceManagerRegistry


def register() -> None:
    """
    Registers PDF Sales datasource components with the system.

    This function performs two registrations:
    1. Registers the PDF Sales datasource manager factory with the DatasourceManagerRegistry
    2. Registers the PDF Sales datasource configuration with the DatasourceConfigurationRegistry

    Both registrations use DatasourceName.PDF_SALES as the identifier.
    """
    DatasourceManagerRegistry.register(
        DatasourceName.PDF_SALES, PDFSalesDatasourceManagerFactory
    )
    DatasourceConfigurationRegistry.register(
        DatasourceName.PDF_SALES, PDFSalesDatasourceConfiguration
    )
