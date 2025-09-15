"""
This script is used to handle chat interactions using the ChainLit library and a chat engine.
Actions are observed by Langfuse.
To make it work vector storage should be filled with the embeddings of the documents.
To run the script execute the following command from the root directory of the project:

> python src/chat.py
"""

from typing import Callable

import chainlit as cl
from chainlit.cli import run_chainlit
from chainlit.server import app as chainlit_app
from starlette.concurrency import iterate_in_threadpool
from starlette.requests import Request
from starlette.responses import StreamingResponse

from augmentation.bootstrap.initializer import AugmentationInitializer
from augmentation.chainlit.service import (
    ChainlitService,
    ChainlitServiceFactory,
)
from augmentation.chainlit.utils import ChainlitUtilsFactory
from augmentation.components.chat_engines.registry import ChatEngineRegistry
from core.logger import LoggerConfiguration

logger = LoggerConfiguration.get_logger(__name__)

# Initialize configuration early to avoid NameError in get_data_layer
initializer = None
configuration = None


@chainlit_app.middleware("http")
async def patch_index_html_inline(
    request: Request, call_next: Callable
) -> StreamingResponse:
    """
    Remove external CSS links from the HTML response to avoid loading them.
    This is necesary regarding privacy policy.
    """
    if request.scope["type"] != "http":
        return await call_next(request)

    response: StreamingResponse = await call_next(request)

    if request.url.path in ("/", "/index.html") and response.headers.get(
        "content-type", ""
    ).startswith("text/html"):
        response_body = [
            section.replace(
                b"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap",
                b"#",
            ).replace(
                b"https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css",
                b"#",
            )
            async for section in response.body_iterator
        ]
        response.body_iterator = iterate_in_threadpool(iter(response_body))
        total_length = sum(len(chunk) for chunk in response_body)
        response.headers["content-length"] = str(total_length)
        return response

    return response


@cl.on_app_startup
async def app_startup() -> None:
    """
    Initialize the application on startup.
    Sets up the augmentation initializer and configuration, and starts the scheduler.
    """
    global initializer, configuration
    initializer = AugmentationInitializer()
    configuration = initializer.get_configuration()
    initializer.get_scheduler().start()


@cl.data_layer
def get_data_layer() -> ChainlitService:
    """
    Initialize Chainlit's data layer with the custom service.

    Note: This function may be called before app_startup(), so we need to
    initialize configuration lazily if it's not already set.

    Returns:
        ChainlitService: The custom service for data layer.
    """
    global initializer, configuration
    if configuration is None:
        initializer = AugmentationInitializer()
        configuration = initializer.get_configuration()
    return ChainlitServiceFactory.create(configuration.augmentation)


@cl.on_chat_start
async def start() -> None:
    """
    Initialize chat session with chat engine.
    Sets up session-specific chat engine and displays welcome message.
    """
    chat_engine = ChatEngineRegistry.get(
        configuration.augmentation.chat_engine.name
    ).create(configuration)
    chat_engine.set_session_id(cl.user_session.get("id"))
    cl.user_session.set("chat_engine", chat_engine)

    utils = ChainlitUtilsFactory.create(configuration.augmentation.chainlit)
    await utils.get_disclaimer_message().send()
    await utils.get_welcome_message().send()


@cl.on_message
async def main(user_message: cl.Message) -> None:
    """
    Process user messages and generate responses.

    Args:
        user_message: Message received from user
    """
    try:
        chat_engine = cl.user_session.get("chat_engine")
        assistant_message = cl.Message(content="", author="Assistant")
        response = await cl.make_async(chat_engine.stream_chat)(
            message=user_message.content,
            chainlit_message_id=assistant_message.parent_id,
        )
        for token in response.response_gen:
            await assistant_message.stream_token(token)

        utils = ChainlitUtilsFactory.create(configuration.augmentation.chainlit)
        utils.add_references(assistant_message, response)
        await assistant_message.send()
    except Exception as e:
        # It is imprecise to catch all exceptions, but llamaindex doesn't provide unified RateLimitError
        logger.error(f"Error in main: {e}", exc_info=True)
        await cl.ErrorMessage(
            content="You have reached the request rate limit. Please try again later.",
        ).send()


@cl.on_app_shutdown
async def app_shutdown() -> None:
    """
    Clean up resources on application shutdown.
    Stops the scheduler if it is running.
    """
    try:
        initializer.get_scheduler().stop()
        logger.info("Scheduler stopped successfully")
    except Exception as e:
        logger.warning(f"Failed to stop scheduler: {e}")


if __name__ == "__main__":
    run_chainlit(__file__)
