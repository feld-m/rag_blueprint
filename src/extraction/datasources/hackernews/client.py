from typing import Type
from core import SingletonFactory
from extraction.datasources.hackernews.configuration import HackerNewsDatasourceConfiguration

class HackerNewsClientFactory(SingletonFactory):
    _configuration_class: Type = HackerNewsDatasourceConfiguration

    @classmethod
    def _create_instance(cls, configuration: HackerNewsDatasourceConfiguration):
        # No secrets required, return a simple client instance
        return {
            "base_url": configuration.base_url,
        }
