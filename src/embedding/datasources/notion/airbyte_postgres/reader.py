import logging
from typing import Any, Iterator, List

from sqlalchemy import Integer, func, select
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm import Session
from tqdm import tqdm

from common.bootstrap.configuration.pipeline.embedding.datasources.datasources_configuration import (
    DatasourceName,
    NotionPostgresAirbyteDatasourceConfiguration,
)
from embedding.datasources.core.reader import BaseReader
from embedding.datasources.notion.airbyte_postgres.models import (
    Block,
    Database,
    Page,
)
from embedding.datasources.notion.document import NotionDocument
from embedding.datasources.notion.parser import NotionParser


class NotionPostgresAirbyteReader(BaseReader):
    """
    Reader for Notion pages and databases extracted by airbyte in row format.
    Parser requires reader to pass pages in JSON format along with corresponding `blocks` field.
    Analogically, databases have to be passed with correspodning `pages` field.

    Note: Tested with PostgresSQL only.
    """

    def __init__(
        self,
        configuration: NotionPostgresAirbyteDatasourceConfiguration,
        engine: Engine,
        parser: NotionParser,
    ):
        """Initialize the reader with a database connection URL.

        Args:
            connection_url: SQLAlchemy connection URL. Defaults to local Notion database.
        """
        self.engine = engine
        self.parser = parser
        self.export_limit = configuration.export_limit

    async def get_all_documents_async(self) -> List[NotionDocument]:
        return self.get_all_documents()

    def get_all_documents(self) -> Iterator[NotionDocument]:
        """Fetch all documents from the Airbyte-synced Notion database."""
        logging.info(
            f"{[DatasourceName.NOTION_POSTGRES_AIRBYTE.value]} Fetching documents with export limit: {self.export_limit}."
        )

        with Session(self.engine) as session:
            databases_count = session.query(Database).count()
            limit = (
                min(self.export_limit, databases_count)
                if self.export_limit
                else databases_count
            )
            all_databases = self.get_all(
                session=session, table=Database, limit=limit
            )

            for database in tqdm(
                all_databases,
                total=limit,
                desc=f"[{DatasourceName.NOTION_POSTGRES_AIRBYTE.value}] Loading databases",
            ):
                database_pages = self.get_database_pages(
                    session=session, parent_id=database[0]["id"]
                )
                database[0]["pages"] = [page[0] for page in database_pages]
                yield self.parser.parse_database(database[0])

            pages_count = session.query(Page).count()
            limit = (
                max(0, self.export_limit - limit)
                if self.export_limit
                else pages_count
            )
            all_pages = self.get_all(session=session, table=Page, limit=limit)

            for page in tqdm(
                all_pages,
                total=limit,
                desc=f"[{DatasourceName.NOTION_POSTGRES_AIRBYTE.value}] Loading pages",
            ):
                page_blocks = self.get_children_blocks(
                    session=session, parent_id=page[0]["id"]
                )
                page[0]["blocks"] = [block[0] for block in page_blocks]
                yield self.parser.parse_page(page[0])

    def get_all(self, session: Session, table: Any, limit: int) -> dict:
        query = select(func.row_to_json(table.__table__.table_valued())).limit(
            limit
        )
        result = session.execute(query)
        return result.all()

    def get_database_pages(
        self, session: Session, parent_id: str
    ) -> Iterator[dict]:
        query = select(func.row_to_json(Page.__table__.table_valued())).where(
            func.jsonb_extract_path_text(Page.parent, "database_id")
            == parent_id
        )

        for page in session.execute(query):
            yield page

    def get_children_blocks(
        self, session: Session, parent_id: str, parent_type: str = "page_id"
    ) -> Iterator[dict]:
        query = (
            select(func.row_to_json(Block.__table__.table_valued()))
            .where(
                func.jsonb_extract_path_text(Block.parent, parent_type)
                == parent_id
            )
            .order_by(
                func.cast(
                    func.jsonb_extract_path_text(
                        Block.parent, "sequence_number"
                    ),
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
