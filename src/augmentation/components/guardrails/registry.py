from typing import Type

from augmentation.bootstrap.configuration.components.guardrails_configuration import (
    GuardrailsName,
)
from core.base_factory import Registry


class GuardrailsRegistry(Registry):
    _key_class: Type = GuardrailsName
