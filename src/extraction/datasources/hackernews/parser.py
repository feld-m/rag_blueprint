from core.base_factory import Factory
from extraction.datasources.core.parser import BaseParser

from extraction.datasources.hackernews.document import HackerNewsDocument
from extraction.datasources.hackernews.configuration import HackerNewsDatasourceConfiguration

from typing import Dict, Type, Tuple, Optional, Any
from datetime import datetime, timezone





class HackerNewsDatasourceParser(BaseParser[HackerNewsDocument]):
    """Parser for Hackernews content.

    Transforms Hackernews response data into structured HackerNewsDocument objects.
    """  
    def parse(self, story_data: Dict[str, Any]) -> HackerNewsDocument | None: # Use story_data consistently
        """Parses HackerNews story data into a HackerNewsStoryDocument."""
        story_id = story_data.get("id")
        if not story_id:
            self.logger.error(f"Received story data with missing ID: {story_data}")
            return None

        # Get timestamp conversion results
        created_time_iso, created_date_str = self._get_datetime_from_timestamp(story_data.get("time"))

        # Define metadata dictionary
        metadata = {                        
            "author": story_data.get("by"),
            "url": story_data.get("url"),
            "created_time": created_time_iso,
            "created_date": created_date_str,
            "last_edited_time": created_time_iso,
            "last_edited_date": created_date_str,
            "score": story_data.get("score"),
            "story_id": story_id, 
            "page_id": str(story_id), 
            "title": story_data.get("title"), 
            "kids": story_data.get("kids"), 
            "descendants": story_data.get("descendants"), 
            "type": "story",            
        }
        
        text = f"{story_data.get('title','')}\n{story_data.get('text', '')}"

        return HackerNewsDocument(text, metadata)


    def _get_datetime_from_timestamp(self, timestamp: Optional[int]) -> Tuple[Optional[str], Optional[str]]:
        """Converts Unix timestamp to ISO string and date string."""
        if timestamp:
            try:
                # Use UTC timezone for consistency
                dt_object = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                created_time_iso = dt_object.isoformat()
                created_date_str = dt_object.strftime("%Y-%m-%d")
                return (created_time_iso, created_date_str)
            except (TypeError, ValueError, OSError) as e: # Catch specific errors
                 # Log the problematic timestamp and the error
                 self.logger.warning(f"Failed to parse timestamp '{timestamp}': {e}")
        # Return None tuple if timestamp is missing or parsing fails
        return (None, None)

class HackerNewsDatasourceParserFactory(Factory):
    """Factory for creating HackernewsDatasourceParser instances.

    Creates and configures parser instances for Hackernews content.
    """

    _configuration_class: Type = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(
        cls, configuration: HackerNewsDatasourceConfiguration
    ) -> HackerNewsDatasourceParser:
        return HackerNewsDatasourceParser()