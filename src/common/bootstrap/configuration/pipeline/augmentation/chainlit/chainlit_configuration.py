from pydantic import BaseModel, Field


class ChainlitConfiguration(BaseModel):

    port: int = Field(8000, description="Port to run the chainlit service on.")
