# How to Add a New Datasource Implementation

This guide demonstrates how to add support for a new datasource implementation, using Confluence as an example.

## Step 1: Add Dependencies

Add the required packages to `pyproject.toml`:

```toml
...
atlassian-python-api==3.41.11
...
```

## Step 2: Define the Datasource Type

In [datasources_configuration.py](https://github.com/feld-m/rag_blueprint/blob/main/src/common/bootstrap/configuration/pipeline/embedding/datasources/datasources_configuration.py), add the new datasource to the `DatasourceName` enumeration:

```py
class DatasourceName(str, Enum):
    ...
    CONFLUENCE = "confluence"
```

## Step 3: Configure Datasource Secrets

Create a secrets class for the new datasource:

```py
class ConfluenceSecrets(BaseSettings):
    model_config = ConfigDict(
        env_file_encoding="utf-8",
        env_prefix="RAG__DATASOURCES__CONFLUENCE__",
        env_nested_delimiter="__",
        extra="ignore",
    )

    username: SecretStr = Field(
        ...,
        description="The username for the confluence data source",
    )
    password: SecretStr = Field(
        ...,
        description="The password for the confluence data source",
    )
```

Add the corresponding environment variables to `configurations/secrets.{environment}.env`:

```sh
RAG__DATASOURCES__CONFLUENCE__USERNAME=<confluence_username>
RAG__DATASOURCES__CONFLUENCE__PASSWORD=<confluence_password>
```

## Step 4: Implement the Datasource Configuration

Define the configuration class for the new datasource:

```py
class ConfluenceDatasourceConfiguration(DatasourceConfiguration):
    host: str = Field(
        "127.0.0.1", description="Host of the vector store server"
    )
    protocol: Union[Literal["http"], Literal["https"]] = Field(
        "http", description="The protocol for the vector store."
    )
    name: Literal[DatasourceName.CONFLUENCE] = Field(
        ..., description="The name of the data source."
    )
    secrets: ConfluenceSecrets = Field(
        None, description="The secrets for the data source."
    )

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}"
```

Add it to `AVAILABLE_DATASOURCES`:

```py
AVAIALBLE_DATASOURCES = Union[
    ...,
    ConfluenceDatasourceConfiguration,
]
```

## Step 5: Project Structure
Create the following structure for your new datasource:
```
src/
└── embedding/
    └── datasources/
        └── confluence/
            ├── document.py
            ├── reader.py
            ├── cleaner.py
            ├── splitter.py
            ├── builders.py
            └── manager.py
```

## Step 6: Create Core Components

### Document Class
Create a new file `src/embedding/datasources/confluence/document.py`:

```py
class ConfluenceDocument(BaseDocument):

    @classmethod
    def from_page(
        cls, markdown: str, page: dict, base_url: str
    ) -> "ConfluenceDocument":
        """Create ConfluenceDocument instance from page data.

        Args:
            page: Dictionary containing Confluence page details
            base_url: Base URL of the Confluence instance

        Returns:
            ConfluenceDocument: Configured document instance
        """
        document = cls(
            text=markdown,
            attachments={},  # TBD
            metadata=ConfluenceDocument._get_metadata(page, base_url),
        )
        document._set_excluded_embed_metadata_keys()
        document._set_excluded_llm_metadata_keys()
        return document
```

### Reader Component
Create a new file `src/embedding/datasources/confluence/reader.py`:

```py
class ConfluenceReader(BaseReader):
    def __init__(
        self,
        configuration: ConfluenceDatasourceConfiguration,
        confluence_client: Confluence,
    ):
        self.export_limit = configuration.export_limit
        self.confluence_client = confluence_client

    async def get_all_documents_async(self) -> List[ConfluenceDocument]:
        """Fetch from Confluence and parse them to markdown format."""
        # Implementation for fetching documents
```

### Cleaner Component
Create a new file `src/embedding/datasources/confluence/cleaner.py`:

```py
class ConfluenceCleaner(BaseCleaner):
    def clean(
        self, documents: List[ConfluenceDocument]
    ) -> List[ConfluenceDocument]:
        """Clean and filter documents."""
        # Implementation for cleaning documents
```

### Splitter Component
Create a new file `src/embedding/datasources/confluence/splitter.py`:

```py
class ConfluenceSplitter(BaseSplitter):
    def __init__(
        self,
        markdown_splitter: BoundEmbeddingModelMarkdownSplitter,
    ):
        self.markdown_splitter = markdown_splitter

    def split(self, documents: List[ConfluenceDocument]) -> List[TextNode]:
        """Split documents into text nodes."""
        return self.markdown_splitter.split(documents)
```

## Step 7: Create Component Builders
Create a new file `src/embedding/datasources/confluence/builders.py`:

```py
class ConfluenceClientBuilder:
    @staticmethod
    @inject
    def build(configuration: ConfluenceDatasourceConfiguration) -> Confluence:
        return Confluence(
            url=configuration.base_url,
            username=configuration.secrets.username.get_secret_value(),
            password=configuration.secrets.password.get_secret_value(),
        )

class ConfluenceReaderBuilder:
    @staticmethod
    @inject
    def build(
        configuration: ConfluenceDatasourceConfiguration,
        confluence_client: Confluence,
    ) -> ConfluenceReader:
        return ConfluenceReader(
            configuration=configuration,
            confluence_client=confluence_client,
        )

# Similar builders for Cleaner and Splitter components
```

## Step 8: Create Datasource Binder
Update the existing [datasources_binder.py](https://github.com/feld-m/rag_blueprint/blob/main/src/common/bootstrap/configuration/pipeline/embedding/datasources/datasources_binder.py) file:

```py
class ConfluenceBinder(BaseBinder):
    def bind(self) -> Type:
        self._bind_confluence_cofuguration()
        self._bind_client()
        self._bind_reader()
        self._bind_cleaner()
        self._bind_splitter()
        self._bind_manager()
        return ConfluenceDatasourceManager

    # Internal methods implementation...

class DatasourcesBinder(BaseBinder):
    mapping = {
        ...
        DatasourceName.CONFLUENCE: ConfluenceBinder,
    }
```

## Step 9: Example Configuration

Add your datasource configuration to `configurations/configuration.{environment}.json`:

```json
{
    "pipeline": {
        "embedding": {
            "datasources": [
                {
                    "name": "confluence",
                    "host": "confluence.example.com",
                    "protocol": "https",
                    "export_limit": 100
                }
            ]
        }
    }
}
```

This structure follows the existing pattern used for other datasources in the project.

After completing these steps, the new datasource will be available for use in the RAG system, capable of extracting, cleaning, and processing content for embeddings.
