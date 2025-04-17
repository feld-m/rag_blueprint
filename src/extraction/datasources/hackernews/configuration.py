class HackerNewsDatasourceConfiguration(DatasourceConfiguration):
    """
    Configuration for the HackerNews datasource.
    """

    api_base_url: str = Field(
        "https://hacker-news.firebaseio.com/v0",
        description="Base URL for the HackerNews API",
    )
    name: Literal[DatasourceName.HACKERNEWS] = Field(
        ...,
        description="Identifier specifying this configuration is for a HackerNews datasource",
    )
    stories_endpoint: str = Field(
        "/topstories.json",
        description="Endpoint for fetching top HackerNews stories",
    )
    max_stories: int = Field(
        20,
        description="Maximum number of stories to fetch",
    )

    @property
    def stories_url(self) -> str:
        return f"{self.api_base_url}{self.stories_endpoint}"
