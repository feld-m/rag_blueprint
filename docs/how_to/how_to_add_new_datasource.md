# How to Add a New Datasource Implementation

This guide demonstrates how to add support for a new datasource implementation, using Confluence as an example.

## Architecture

Datasources are managed by the `DatasourceManager`, which aggregates required components and orchestrates them to retrieve documents, clean them, and parse them to markdown format - which is strictly required by the embedding process. The general datasource manager flow is:

**Reader** -> **Parser** (Optional) -> **Cleaner** (Optional) -> **Splitter** (Optional).

Therefore, adding support for a new datasource requires implementing these components and their respective manager.

# Implementation

## Step 1: Dependencies

Add the required packages to `pyproject.toml` under the following section:

```toml
[project.optional-dependencies]
extraction = [
    "atlassian-python-api>=3.41.19",
    ...
]
```

## Step 2: Datasource Enum
In [datasources.py](https://github.com/feld-m/rag_blueprint/blob/main/src/extraction/bootstrap/configuration/datasources.py), add the new datasource to the `DatasourceName` enumeration:

```py
class DatasourceName(str, Enum):
    ...
    CONFLUENCE = "confluence"
```

## Step 3: Datasource Secrets

Create a new directory `src/extraction/datasources/confluence` and create a `configuration.py` file in it. This configuration file will contain necessary fields and secrets for setup.

```py
from typing import Literal, Union
from pydantic import ConfigDict, Field, SecretStr
from core.base_configuration import BaseSecrets
from extraction.bootstrap.configuration.datasources import (
    DatasourceConfiguration,
    DatasourceName,
)

class ConfluenceDatasourceConfiguration(DatasourceConfiguration):
    class Secrets(BaseSecrets):
        model_config = ConfigDict(
            env_file_encoding="utf-8",
            env_prefix="RAG__DATASOURCES__CONFLUENCE__",
            env_nested_delimiter="__",
            extra="ignore",
        )

        username: SecretStr = Field(
            ...,
            description="Username credential used to authenticate with the Confluence instance",
        )
        password: SecretStr = Field(
            ...,
            description="Password credential used to authenticate with the Confluence instance",
        )

    secrets: Secrets = Field(
        None,
        description="Authentication credentials required to access the Confluence instance",
    )
```

The first part is to create a configuration that extends `DatasourceConfiguration`. The `Secrets` inner class defines secret fields that will be present in the environment secret file under the `RAG__DATASOURCES__CONFLUENCE__` prefix. Add the corresponding environment variables to `configurations/secrets.{environment}.env`:

```sh
RAG__DATASOURCES__CONFLUENCE__USERNAME=<confluence_username>
RAG__DATASOURCES__CONFLUENCE__PASSWORD=<confluence_password>
```

> **Note**: If your datasource doesn't require secrets, you can skip this step.

## Step 4: Datasource Configuration

Finish up `ConfluenceDatasourceConfiguration` implementation and add the rest of the configuration required for the datasource:

```py
...

class ConfluenceDatasourceConfiguration(DatasourceConfiguration):
    ...

    host: str = Field(
        "127.0.0.1",
        description="Hostname or IP address of the Confluence server instance",
    )
    protocol: Union[Literal["http"], Literal["https"]] = Field(
        "http",
        description="Communication protocol used to connect to the Confluence server",
    )
    name: Literal[DatasourceName.CONFLUENCE] = Field(
        ...,
        description="Identifier specifying this configuration is for a Confluence datasource",
    )

    @property
    def base_url(self) -> str:
        return f"{self.protocol}://{self.host}"
```

`provider` field constraints the value to `DatasourceName.CONFLUENCE`, which serves as an indicator for pydantic validator.

## Step 5: Confluence Document

The next step is to create a Confluence document data class in `document.py`:

```py
from extraction.datasources.core.base.document import BaseDocument

class ConfluenceDocument(BaseDocument):
    """Document representation for Confluence page content.

    Extends BaseDocument to handle Confluence-specific document processing including
    content extraction, metadata handling, and exclusion configuration.
    """

    pass
```

In our case, we don't need anything beyond the `BaseDocument` implementation.

## Step 6: Confluence Client

To create a Confluence client, we implement `ConfluenceClientFactory` in `client.py`. It extends `SingletonFactory`,
which provides an interface for initializing a single instance for the duration of the application runtime.

```py
from typing import Type
from atlassian import Confluence
from core import SingletonFactory
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)

class ConfluenceClientFactory(SingletonFactory):
    _configuration_class: Type = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> Confluence:
        return Confluence(
            url=configuration.base_url,
            username=configuration.secrets.username.get_secret_value(),
            password=configuration.secrets.password.get_secret_value(),
        )
```

The field `_configuration_class` defines the required configuration type. The rest involves implementing
the required `_create_instance` method with the corresponding client initialization.

## Step 7: Datasource Reader

Create a Confluence reader in `reader.py` that implements the BaseReader interface:

```py
from extraction.datasources.core.reader import BaseReader
...

class ConfluenceDatasourceReader(BaseReader):

    async def read_all_async(
        self,
    ) -> AsyncIterator[dict]:
        # read Confluence pages implementation
```

This method returns an iterator, which improves runtime memory management. Next, implement a factory that defines how the `ConfluenceDatasourceReader` is initialized:

```py
from core import Factory
...

class ConfluenceDatasourceReaderFactory(Factory):
    _configuration_class = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> ConfluenceDatasourceReader:
        client = ConfluenceClientFactory.create(configuration)
        return ConfluenceDatasourceReader(
            configuration=configuration,
            client=client,
        )
```

Note that instead of initializing the Confluence client directly, the factory uses `ConfluenceClientFactory` to handle this task.

## Step 8: Datasource Parser

In `parser.py` implement a parser responsible for converting the raw Confluence page to markdown format:

```py
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)
from extraction.datasources.confluence.document import ConfluenceDocument
from extraction.datasources.core.parser import BaseParser


class ConfluenceDatasourceParser(BaseParser[ConfluenceDocument]):

    def parse(self, page: str) -> ConfluenceDocument:
        # parse Confluence page implementation
```

As before, define a factory for the parser:

```py
class ConfluenceDatasourceParserFactory(Factory):
    _configuration_class: Type = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> ConfluenceDatasourceParser:
        return ConfluenceDatasourceParser(configuration)
```

## Step 9: Datasource Manager

To orchestrate all the previous components, we will reuse `BasicDatasourceManager` and implement a factory for it in `manager.py`:

```py
class ConfluenceDatasourceManagerFactory(Factory):
    """Factory for creating Confluence datasource managers.

    This factory generates managers that handle the extraction of content from
    Confluence instances. It ensures proper configuration, reading, and parsing
    of Confluence content.

    Attributes:
        _configuration_class: Configuration class used for validating and processing
            Confluence-specific settings.
    """

    _configuration_class: Type = ConfluenceDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: ConfluenceDatasourceConfiguration
    ) -> BasicDatasourceManager:
        """Create a configured Confluence datasource manager.

        Sets up the necessary reader and parser components based on the provided
        configuration and assembles them into a functional manager.

        Args:
            configuration: Configuration object containing Confluence-specific
                parameters including authentication details, spaces to extract,
                and other extraction options.

        Returns:
            A fully initialized datasource manager that can extract and process
            data from Confluence.
        """
        reader = ConfluenceDatasourceReaderFactory.create(configuration)
        parser = ConfluenceDatasourceParserFactory.create(configuration)
        return BasicDatasourceManager(configuration, reader, parser)
```

Following the design pattern, `ConfluenceDatasourceManagerFactory` uses reader and parser factories to obtain the instances needed for the manager.

## Step 10: Datasource Integration

Create an `__init__.py` file as follows:

```py
from extraction.bootstrap.configuration.datasources import (
    DatasourceConfigurationRegistry,
    DatasourceName,
)
from extraction.datasources.confluence.configuration import (
    ConfluenceDatasourceConfiguration,
)
from extraction.datasources.confluence.manager import (
    ConfluenceDatasourceManagerFactory,
)
from extraction.datasources.registry import DatasourceManagerRegistry


def register() -> None:
    DatasourceManagerRegistry.register(
        DatasourceName.CONFLUENCE, ConfluenceDatasourceManagerFactory
    )
    DatasourceConfigurationRegistry.register(
        DatasourceName.CONFLUENCE, ConfluenceDatasourceConfiguration
    )
```

The initialization file includes a `register()` method responsible for registering our configuration and manager factories. Registries are used to dynamically inform the system about available implementations. This way, with the following Confluence configuration in `configurations/configuration.{environment}.json` file:

```json
    "extraction": {
        "datasources": [
            {
                "name": "confluence",
                "host": "wissen.feld-m.de",
                "protocol": "https"
            }
        ]
        ...
    }
    ...
```

We can dynamically retrieve the corresponding manager implementation by using the name specified in the configuration:

```py
datasource_config = read_datasource_from_config()
datasource_manager = DatasourceManagerRegistry.get(datasource_config.name).create(datasource_config)
```

This mechanism is later used by `DatasourceOrchestrator` to initialize datasources defined in the configuration. These steps conclude the implementation, resulting in the following file structure:

```
src/
└── extraction/
    └── datasources/
        └── confluence/
            ├── __init__.py
            ├── client.py
            ├── configuration.py
            ├── document.py
            ├── manager.py
            ├── parser.py
            └── reader.py
```

## Notes

Below is the `__init__` method of `BasicDatasourceManager` used in our tutorial:

```py
class BasicDatasourceManager(BaseDatasourceManager, Generic[DocType]):

    def __init__(
        self,
        configuration: ExtractionConfiguration,
        reader: BaseReader,
        parser: BaseParser = BasicMarkdownParser(),
        cleaner: BaseCleaner = BasicMarkdownCleaner(),
        splitter: BaseSplitter = BasicMarkdownSplitter(),
    ):
```

Note that in this guide we skipped the implementation of custom `cleaner` and `splitter` components, instead using the default ones. When building a new datasource integration, you might need to implement custom versions of these components based on your specific requirements.
