from augmentation.bootstrap.configuration.components.guardrails_configuration import (
    GuardrailsName,
    GurdrailsConfigurationRegistry,
)
from augmentation.components.guardrails.basic.configuration import (
    BasicGuardrailsConfiguration,
)
from augmentation.components.guardrails.basic.guardrails import (
    BasicGuardrailsEngineFactory,
)
from augmentation.components.guardrails.registry import GuardrailsRegistry


def register() -> None:
    """
    Registers the Basic guardrails components with the system.

    This function performs two registrations:
    1. Registers the Basic guardrails engine factory with the GuardrailsRegistry
    2. Registers the Basic guardrails configuration with the GurdrailsConfigurationRegistry
    """
    GurdrailsConfigurationRegistry.register(
        GuardrailsName.BASIC, BasicGuardrailsConfiguration
    )
    GuardrailsRegistry.register(
        GuardrailsName.BASIC, BasicGuardrailsEngineFactory
    )
