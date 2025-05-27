from typing import Literal

from pydantic import Field

from augmentation.bootstrap.configuration.components.guardrails_configuration import (
    GuardrailsConfiguration,
    GuardrailsName,
)


class BasicGuardrailsConfiguration(GuardrailsConfiguration):

    name: Literal[GuardrailsName.BASIC] = Field(
        GuardrailsName.BASIC,
        description="Name of the guardrails configuration.",
    )
