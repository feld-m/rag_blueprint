"""
This script is used to handle chat interactions using the ChainLit library and a query engine from the RAG (Retrieval-Augmented Generation) model.
To make it work vector storage should be filled with the embeddings of the documents.
To run the script execute the following command from the root directory of the project:

> python src/chat.py
"""

import chainlit as cl
from chainlit.cli import run_chainlit
from llama_index.core.base.base_query_engine import BaseQueryEngine

from augmentation.utils import ConversationUtils
from common.bootstrap.initializer import AugmentationInitializer

injector = AugmentationInitializer().init_injector()


@cl.on_chat_start
async def start():
    """Initialize chat session with query engine.

    Sets up session-specific query engine and displays welcome message.
    """
    query_engine = injector.get(BaseQueryEngine)
    query_engine.set_session_id(cl.user_session.get("id"))
    cl.user_session.set("query_engine", query_engine)
    await ConversationUtils.get_welcome_message().send()


@cl.on_message
async def main(user_message: cl.Message):
    """Process user messages and generate responses.

    Args:
        user_message: Message received from user

    Note:
        Streams tokens for real-time response generation
        Adds source references to responses
    """
    query_engine = cl.user_session.get("query_engine")
    assistant_message = cl.Message(content="", author="Assistant")
    response = await cl.make_async(query_engine.query)(
        user_message.content, assistant_message.parent_id
    )
    for token in response.response_gen:
        await assistant_message.stream_token(token)
    # await cl.Message(author="Assistant", content=response.source_nodes).send()
    ConversationUtils.add_references(assistant_message, response)
    await assistant_message.send()


if __name__ == "__main__":
    run_chainlit(__file__)
