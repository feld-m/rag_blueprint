from typing import List

from chainlit import Message
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.schema import NodeWithScore


class ChainlitUtils:
    """Utility class for handling conversation messages.

    Provides methods for managing welcome messages and reference handling in conversations.

    Attributes:
        WELCOME_TEMPLATE: Template string for welcome message.
        REFERENCES_TEMPLATE: Template string for formatting references section.
    """

    WELCOME_TEMPLATE = WELCOME_TEMPLATE = (
        "Hello and welcome to our FELD M's Chat UI! 👋 We're here to help you find the information you need from our FELD M's knowledge base. To get started, simply type your question or statement into the chat box below and press enter. Enjoy your exploration and happy chatting! 😊"
    )
    REFERENCES_TEMPLATE = "\n\n**References**:\n" "{references}\n"

    @staticmethod
    def get_welcome_message() -> Message:
        """Create and return a welcome message for the chat interface.

        Creates a Message object with predefined content from the WELCOME_TEMPLATE
        to greet users when they start a conversation.

        Returns:
            Message: A chainlit Message object with the Assistant as author
                    and the welcome template as content.
        """
        return Message(
            author="Assistant", content=ChainlitUtils.WELCOME_TEMPLATE
        )

    @staticmethod
    def add_references(message: Message, response: StreamingResponse) -> None:
        """Append source references to a message from a streaming response.

        Takes a message object and a streaming response containing source nodes,
        then appends formatted references to the message content.

        Args:
            message (Message): The chainlit Message object to modify by adding references.
            response (StreamingResponse): A response object containing source_nodes
                                          with reference information.
        """
        message.content += ChainlitUtils._get_references_str(
            response.source_nodes
        )

    @staticmethod
    def _get_references_str(nodes: List[NodeWithScore]) -> str:
        """Generate a formatted references section from source nodes.

        Processes a list of source nodes to create a deduplicated,
        formatted string of references.

        Args:
            nodes (List[NodeWithScore]): List of source nodes with relevance scores
                                         and metadata containing reference information.

        Returns:
            str: A formatted string containing unique references in the
                 structure defined by REFERENCES_TEMPLATE.
        """
        raw_references = [
            ChainlitUtils._get_reference_str(node) for node in nodes
        ]
        references = "\n".join(set(raw_references))
        return ChainlitUtils.REFERENCES_TEMPLATE.format(references=references)

    @staticmethod
    def _get_reference_str(node: NodeWithScore) -> str:
        """Format a single node's reference as a markdown string.

        Extracts title and URL from a node's metadata and formats it
        as a markdown list item, with link formatting if a URL is available.

        Args:
            node (NodeWithScore): A source node containing metadata with
                                 title and optional URL information.

        Returns:
            str: A formatted markdown list item representing the reference,
                 with a clickable link if URL is available.
        """
        title = node.metadata.get("title")
        if not title:
            title = node.metadata.get("Title")

        url = node.metadata.get("url")

        if url:
            return "- [{}]({})".format(title, url)
        else:
            return f"- {title}"
