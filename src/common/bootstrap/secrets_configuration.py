from abc import ABC
from typing import Any

from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings


class EmptySecrets(BaseSettings):
    model_config = ConfigDict(
        extra="ignore",
    )


class ConfigurationWithSecrets(BaseModel, ABC):
    """
    Abstract model for configuration's secrets handling. Extending class has to implement `secrets` field with correspodning type.
    """

    secrets: EmptySecrets = Field(
        None,
        description="`EmptySecrets` is meant for the the configuration that does not require secrets."
        "In other case `EmptySecrets` should be replaced with the corresponding secrets class.",
    )

    def model_post_init(self, context: Any) -> None:
        """
        Function is invoked after the model is initialized. It is used to initialize secrets.

        Args:
            context (Any): The context passed to the pydantic model.
        """
        self.secrets = self.get_secrets(secrets_file=context["secrets_file"])

    def get_secrets(self, secrets_file: str) -> BaseSettings:
        """
        Function to initialize secrets.

        Args:
            secrets_file (str): The path to the secrets file.

        Returns:
            BaseSettings: The secrets object.

        Raises:
            ValueError: If secrets are not found.
        """
        secrets_class = self.model_fields["secrets"].annotation
        secrets = secrets_class(_env_file=secrets_file)
        if secrets is None:
            raise ValueError(f"Secrets for {self.name} not found.")
        return secrets
