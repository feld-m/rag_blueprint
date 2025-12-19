import chainlit as cl
from augmentation.bootstrap.initializer import AugmentationInitializer
from augmentation.components.chat_engines.langfuse.chat_engine import (
    LangfuseChatEngineFactory,
    SourceProcess,
)
import logging

# Initialize the system once at startup
initializer = AugmentationInitializer()
configuration = initializer.get_configuration()

@cl.on_chat_start
async def start():
    # Use the factory to create the chat engine
    chat_engine = LangfuseChatEngineFactory.create(configuration)
    
    # Store the chat engine in the user session
    cl.user_session.set("chat_engine", chat_engine)
    
    await cl.Message(content="Hello! I'm your RAG-powered assistant. How can I help you today?").send()

@cl.on_message
async def main(message: cl.Message):
    chat_engine = cl.user_session.get("chat_engine")
    
    # Process message with streaming support
    msg = cl.Message(content="")
    
    # Langfuse session ID can be linked here
    chat_engine.set_session_id(cl.user_session.get("id"))
    
    # Use the stream_chat method which includes Langfuse tracing
    response = chat_engine.stream_chat(
        message.content,
        chainlit_message_id=message.id,
        source_process=SourceProcess.CHAT_COMPLETION
    )
    
    # Check if response is streaming or static
    if hasattr(response, "response_gen") and response.response_gen:
        for token in response.response_gen:
            await msg.stream_token(token)
    else:
        msg.content = response.response
    
    await msg.send()
