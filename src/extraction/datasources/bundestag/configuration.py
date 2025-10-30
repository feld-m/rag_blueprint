from typing import List, Literal, Optional

from pydantic import Field

from extraction.bootstrap.configuration.datasources import (
    DatasourceConfiguration,
    DatasourceName,
)


class BundestagMineDatasourceConfiguration(DatasourceConfiguration):
    """
    Configuration for the Bundestag datasource.

    Supports multiple data sources:
    - BundestagMine API: Individual speeches from parliamentary sessions
    - DIP API: Comprehensive parliamentary documents (protocols, drucksachen, proceedings)
    """

    name: Literal[DatasourceName.BUNDESTAG] = Field(
        ...,
        description="Identifier specifying this configuration is for the Bundestag datasource",
    )

    # BundestagMine settings
    include_bundestag_mine: bool = Field(
        default=True,
        description="Fetch speeches from BundestagMine API (bundestag-mine.de)",
    )

    # DIP API settings
    include_dip: bool = Field(
        default=True,
        description="Fetch data from DIP (Dokumentations- und Informationssystem) API",
    )

    dip_api_key: Optional[str] = Field(
        default=None,
        description="API key for DIP API. If not provided, uses public test key.",
    )

    dip_wahlperiode: int = Field(
        default=21,
        description="Electoral period (Wahlperiode) for DIP data",
    )

    dip_sources: List[str] = Field(
        default_factory=lambda: ["protocols"],
        description=(
            "DIP data sources to fetch. "
            "Options: 'protocols' (plenary transcripts), "
            "'drucksachen' (printed materials), "
            "'proceedings' (legislative processes)"
        ),
    )
