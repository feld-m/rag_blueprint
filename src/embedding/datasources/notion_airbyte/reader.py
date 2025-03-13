from typing import Iterator, List

from sqlalchemy import Integer, MetaData, Table, func, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from tqdm import tqdm

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    DatasourceName,
    NotionAirbyteDatasourceConfiguration,
)
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.notion_airbyte.document import NotionDocument
from embedding.datasources.notion_airbyte.parser import NotionParser


class NotionAirbyteReader(BaseReader):
    def __init__(
        self,
        configuration: NotionAirbyteDatasourceConfiguration,
        engine: Engine,
        parser: NotionParser,
    ):
        """Initialize the reader with a database connection URL.

        Args:
            connection_url: SQLAlchemy connection URL. Defaults to local Notion database.
        """
        self.engine = engine
        self.parser = parser
        self.configuration = configuration

        self.pages_table = Table(
            "pages", MetaData(), schema="public", autoload_with=self.engine
        )
        self.databases_table = Table(
            "databases", MetaData(), schema="public", autoload_with=self.engine
        )
        self.blocks_table = Table(
            "blocks", MetaData(), schema="public", autoload_with=self.engine
        )

    async def get_all_documents_async(self) -> List[NotionDocument]:
        return self.get_all_documents()

    def get_all_documents(self) -> Iterator[NotionDocument]:
        """Fetch all documents from the Airbyte-synced Notion database."""
        with Session(self.engine) as session:
            databases_count = session.query(self.databases_table).count()
            pages_count = session.query(self.pages_table).count()

            all_databases = self.get_all(
                session=session, table=self.databases_table
            )
            for database in tqdm(
                all_databases,
                total=databases_count,
                desc=f"[{DatasourceName.NOTION_AIRBYTE.value}] Loading databases",
            ):
                database_pages = self.get_children_pages(
                    session=session, parent_id=database[0]["id"]
                )
                database[0]["pages"] = [page[0] for page in database_pages]
                yield self.parser.parse_database(database[0])

            all_pages = self.get_all(session=session, table=self.pages_table)
            for page in tqdm(
                all_pages,
                total=pages_count,
                desc=f"[{DatasourceName.NOTION_AIRBYTE.value}] Loading pages",
            ):
                page_blocks = self.get_children_blocks(
                    session=session, parent_id=page[0]["id"]
                )
                page[0]["blocks"] = [block[0] for block in page_blocks]
                yield self.parser.parse_page(page[0])

    def get_all(self, session: Session, table: Table) -> dict:
        query = select(func.row_to_json(table.table_valued()))
        result = session.execute(query)
        return result.all()

    def get_children_pages(
        self, session: Session, parent_id: str
    ) -> Iterator[dict]:
        query = select(func.row_to_json(self.pages_table.table_valued())).where(
            self.pages_table.c.parent["database_id"].astext == parent_id
        )

        for page in session.execute(query):
            yield page

    def get_children_blocks(
        self, session: Session, parent_id: str, parent_type: str = "page_id"
    ) -> Iterator[dict]:
        query = (
            select(func.row_to_json(self.blocks_table.table_valued()))
            .where(self.blocks_table.c.parent[parent_type].astext == parent_id)
            .order_by(
                func.cast(
                    self.blocks_table.c.parent["sequence_number"].astext,
                    Integer,
                )
            )
        )

        for block in session.execute(query):
            yield block

            for child_block in self.get_children_blocks(
                session=session,
                parent_id=block[0]["id"],
                parent_type="block_id",
            ):
                yield child_block
