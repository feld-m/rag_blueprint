from typing import List

from chainlit import Message
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.schema import NodeWithScore


class ConversationUtils:
    """Utility class for handling conversation messages.

    Provides methods for managing welcome messages and reference handling in conversations.

    Attributes:
        WELCOME_TEMPLATE: Template string for welcome message.
        REFERENCES_TEMPLATE: Template string for formatting references section.
    """

    WELCOME_TEMPLATE = "Hello and welcome to our FELD M's Chat UI! 👋 We're here to help you find the information you need from our FELD M's knowledge base. To get started, simply type your question or statement into the chat box below and press enter. Enjoy your exploration and happy chatting! 😊"
    REFERENCES_TEMPLATE = "\n\n**References**:\n" "{references}\n"

    @staticmethod
    def get_welcome_message() -> Message:
        """Create and return a welcome message.

        Returns:
            Message: Configured welcome message object.
        """
        return Message(
            author="Assistant", content=ConversationUtils.WELCOME_TEMPLATE
        )

    @staticmethod
    def add_references(message: Message, response: StreamingResponse) -> None:
        """Add source references to a message.

        Args:
            message: Message object to append references to.
            response: StreamingResponse containing source nodes.
        """
        message.content += ConversationUtils._get_references_str(
            response.source_nodes
        )

    @staticmethod
    def _get_references_str(nodes: List[NodeWithScore]) -> str:
        """Generate formatted references string from source nodes.

        Args:
            nodes: List of source nodes with relevance scores.

        Returns:
            str: Formatted string of unique references.
        """
        raw_references = [
            ConversationUtils._get_reference_str(node) for node in nodes
        ]
        references = "\n".join(set(raw_references))
        return ConversationUtils.REFERENCES_TEMPLATE.format(
            references=references
        )

    @staticmethod
    def _get_reference_str(node: NodeWithScore) -> str:
        """Format a single node's reference as a string.

        Args:
            node: Source node with metadata containing title and optional URL.

        Returns:
            str: Formatted reference string, with URL link if available.
        """
        title = node.metadata.get("title")
        if not title:
            title = node.metadata.get("Title")

        url = node.metadata.get("url")

        if url:
            return "- [{}]({})".format(title, url)
        else:
            return f"- {title}"
