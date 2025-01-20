import logging
import sys
import warnings


class LoggerConfiguration:
    """Utility class for configuring application-wide logging.

    Provides static methods to set up logging formats, handlers, and warning filters.
    Configures both root logger and specific module loggers (e.g., httpx).

    Attributes:
        None - all methods are static
    """

    @staticmethod
    def config():
        """Configure application logging settings.

        Sets up logging with the following configuration:
        - Formats logs with timestamp, logger name, level, and message
        - Directs output to stdout
        - Sets root logger level to INFO
        - Configures httpx logger with WARN level
        """
        # Define log format
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        # Create formatters
        formatter = logging.Formatter(log_format)

        # Create handlers
        screen_handler = logging.StreamHandler(sys.stdout)
        screen_handler.setFormatter(formatter)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(screen_handler)

        # Configure httpx logger
        httpx_logger = logging.getLogger("httpx")
        httpx_logger.setLevel(logging.WARN)
        httpx_logger.propagate = True  # Allow propagation to parent logger
        httpx_logger.addHandler(screen_handler)

    @staticmethod
    def filterwarnings():
        """Configure warning filters for the application.

        Suppresses specific warnings:
        - DeprecationWarnings from langchain module
        """
        # Suppress specific warnings from external dependencies
        warnings.filterwarnings(
            "ignore", category=DeprecationWarning, module="langchain"
        )
