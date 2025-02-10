class CollectionExistsException(Exception):
    """Exception raised when attempting to create a vector store collection that already exists.

    Attributes:
        collection_name: Name of the existing collection.
        message: Explanation of the error.
    """

    def __init__(self, collection_name: str) -> None:
        """Initialize the exception.

        Args:
            collection_name: Name of the collection that already exists.
        """
        self.collection_name = collection_name
        self.message = f"Collection with name {collection_name} already exists"
        super().__init__(self.message)


class TraceNotFoundException(Exception):
    """Exception raised when a trace for a given message ID cannot be found.

    Attributes:
        message_id: ID of the message whose trace was not found.
        message: Explanation of the error.
    """

    def __init__(self, message_id: str) -> None:
        """Initialize the exception.

        Args:
            message_id: ID of the message whose trace was not found.
        """
        self.message_id = message_id
        self.message = f"Trace for message with id {message_id} not found"
        super().__init__(self.message)
