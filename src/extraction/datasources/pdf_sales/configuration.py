from typing import Literal

from pydantic import Field

from extraction.bootstrap.configuration.datasources import DatasourceName
from extraction.datasources.pdf.configuration import PDFDatasourceConfiguration


class PDFSalesDatasourceConfiguration(PDFDatasourceConfiguration):
    """
    Configuration for the PDF Sales datasource.
    """

    name: Literal[DatasourceName.PDF_SALES] = Field(
        ..., description="The name of the data source."
    )
