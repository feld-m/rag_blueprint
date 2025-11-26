"""Temporal domain configuration for domain-specific temporal logic.

This module provides configuration for temporal filtering, query expansion,
and metadata handling that varies by deployment domain (e.g., Bundestag,
EU Parliament, etc.).
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TemporalKeywords(BaseModel):
    """Keywords for temporal filtering by language.

    Example:
        {
            "en": ["current", "recent", "latest"],
            "de": ["aktuell", "neueste", "jetzt"]
        }
    """

    en: List[str] = Field(default_factory=list, description="English keywords")
    de: List[str] = Field(default_factory=list, description="German keywords")
    fr: List[str] = Field(default_factory=list, description="French keywords")
    es: List[str] = Field(default_factory=list, description="Spanish keywords")


class PeriodDefinition(BaseModel):
    """Definition of a temporal period.

    Example:
        {
            "names": ["20. Wahlperiode", "WP20", "20th legislature"],
            "years": [2021, 2022, 2023, 2024],
            "temporal_type": "historical"
        }
    """

    names: List[str] = Field(
        default_factory=list, description="Period identifiers and variations"
    )
    years: List[int] = Field(
        default_factory=list, description="Years covered by this period"
    )
    temporal_type: str = Field(
        description="Temporal classification: 'current' or 'historical'"
    )


class QueryExpansionTerms(BaseModel):
    """Query expansion terms by language.

    Example:
        {
            "de": "Bundestag Fraktionen parlamentarische Gruppen",
            "en": "parliament fractions parliamentary groups"
        }
    """

    de: str = Field(default="", description="German expansion terms")
    en: str = Field(default="", description="English expansion terms")
    fr: str = Field(default="", description="French expansion terms")
    es: str = Field(default="", description="Spanish expansion terms")


class TemporalDomainConfiguration(BaseModel):
    """Domain-specific configuration for temporal RAG system.

    Configures temporal filtering, query expansion, and metadata handling
    for specific deployment domains (parliamentary systems, news archives, etc.).

    If not provided, the system runs in generic mode without temporal filtering.
    """

    name: str = Field(
        description="Domain identifier (e.g., 'bundestag', 'eu_parliament')"
    )

    metadata_schema: Dict[str, Any] = Field(
        description="Metadata field names and period definitions",
        examples=[
            {
                "temporal_field": "legislature_period",
                "current_period": 21,
                "historical_period": 20,
            }
        ],
    )

    temporal_keywords: Dict[str, TemporalKeywords] = Field(
        default_factory=dict,
        description="Keywords for 'current' and 'historical' filtering",
        examples=[
            {
                "current": {
                    "en": ["current", "recent"],
                    "de": ["aktuell", "neueste"],
                },
                "historical": {
                    "en": ["previous", "past"],
                    "de": ["vorherig", "vergangen"],
                },
            }
        ],
    )

    period_identifiers: Dict[str, PeriodDefinition] = Field(
        default_factory=dict,
        description="Period definitions with years and identifiers",
        examples=[
            {
                "20": {
                    "names": ["20. Wahlperiode", "WP20"],
                    "years": [2021, 2022, 2023, 2024],
                    "temporal_type": "historical",
                }
            }
        ],
    )

    query_expansion: Dict[str, QueryExpansionTerms] = Field(
        default_factory=dict,
        description="Query expansion templates for different query types",
        examples=[
            {
                "temporal_current": {
                    "de": "21. Wahlperiode 2025 aktuelle Bundesregierung"
                },
                "temporal_historical": {
                    "de": "20. Wahlperiode 2021-2024 frühere Bundesregierung"
                },
            }
        ],
    )

    language_detection: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Language detection patterns",
        examples=[
            {
                "de": ["wer", "was", "welche", "der", "die", "das"],
                "en": ["who", "what", "which", "the"],
            }
        ],
    )

    @property
    def current_period_value(self) -> Optional[int]:
        """Get current period number from metadata schema.

        Returns:
            Current period number, or None if not configured
        """
        return self.metadata_schema.get("current_period")

    @property
    def historical_period_value(self) -> Optional[int]:
        """Get historical period number from metadata schema.

        Returns:
            Historical period number, or None if not configured
        """
        return self.metadata_schema.get("historical_period")

    @property
    def temporal_field_name(self) -> str:
        """Get metadata field name for temporal filtering.

        Returns:
            Metadata field name (default: 'period')
        """
        return self.metadata_schema.get("temporal_field", "period")

    def get_all_current_keywords(self) -> List[str]:
        """Get all 'current' keywords across all configured languages.

        Returns:
            List of all current keywords
        """
        keywords = []
        current_kw = self.temporal_keywords.get("current")
        if current_kw:
            for lang_keywords in [
                current_kw.en,
                current_kw.de,
                current_kw.fr,
                current_kw.es,
            ]:
                keywords.extend(lang_keywords)
        return keywords

    def get_all_historical_keywords(self) -> List[str]:
        """Get all 'historical' keywords across all configured languages.

        Includes both language keywords and period identifiers.

        Returns:
            List of all historical keywords
        """
        keywords = []

        # Add language-specific keywords
        historical_kw = self.temporal_keywords.get("historical")
        if historical_kw:
            for lang_keywords in [
                historical_kw.en,
                historical_kw.de,
                historical_kw.fr,
                historical_kw.es,
            ]:
                keywords.extend(lang_keywords)

        # Add period identifiers for historical periods
        for period_id, period_def in self.period_identifiers.items():
            if period_def.temporal_type == "historical":
                keywords.extend(period_def.names)

        return keywords

    def detect_language(self, query: str) -> str:
        """Detect query language using configured patterns.

        Args:
            query: User query string

        Returns:
            Detected language code (default: 'en')
        """
        query_lower = query.lower()
        for lang, indicators in self.language_detection.items():
            if any(indicator in query_lower for indicator in indicators):
                return lang
        return "en"  # Default to English

    def get_expansion_terms(
        self, expansion_type: str, language: str = "en"
    ) -> str:
        """Get query expansion terms for a specific type and language.

        Args:
            expansion_type: Type of expansion ('temporal_current', 'temporal_historical', 'entity_terms')
            language: Language code ('en', 'de', 'fr', 'es')

        Returns:
            Expansion term string, or empty string if not found
        """
        expansion = self.query_expansion.get(expansion_type)
        if not expansion:
            return ""
        return getattr(expansion, language, "")
