import sys

sys.path.append("./src")

import os
import socket
import subprocess
from argparse import ArgumentParser, Namespace
from datetime import datetime
from enum import Enum

from python_on_whales import DockerClient
from python_on_whales.exceptions import DockerException

from common.bootstrap.configuration.configuration import Configuration


class Logger(object):
    """Logger redirecting output to log file.

    Redirects all the output to the log file.

    Attributes:
        terminal: Represents the terminal output
        log_file: Log file to write the output
    """

    def __init__(self, filename: str):
        """Initialize the logger.

        Args:
            filename: The name of the log file
        """
        self.terminal = sys.stdout
        self.log_file = open(filename, "a")
        sys.stdout = self

    def write(self, message: str):
        """Write the message to the terminal and log file.

        Add the timestamp to the message and write it to the terminal and log file.

        Args:
            message: The message to write
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if message.strip():
            message = f"[{timestamp}] {message}\n"
            self.terminal.write(message)
            self.log_file.write(message)
            self.flush()

    def flush(self):
        """Flush the output to the terminal and log file."""
        self.terminal.flush()
        self.log_file.flush()


class CommandRunner:
    """Command runner for deployment and initialization.

    Runs commands for interacting with OS.

    Attributes:
        logger: Logger for the deployment
        build_name: The name of the build to deploy
        secrets_filename: The file containing the secrets
        configuration_filename: The file containing the configuration
        docker_compose_filename: The file containing the docker-compose configuration
        docker_client: Docker client for running the services
        configuration_json: The JSON configuration
        configuration: Pydantic model of configuration
    """

    def __init__(
        self,
        logger: Logger,
        build_name: str,
        secrets_filename: str,
        configuration_filename: str,
        docker_compose_filename: str,
    ):
        """Initialize the command runner.

        Args:
            logger: Logger for the deployment
            build_name: The name of the build to deploy
            secrets_filename: The file containing the secrets
            configuration_filename: The file containing the configuration
            docker_compose_filename: The file containing the docker-compose configuration
        """
        self.logger = logger
        self.build_name = build_name
        self.secrets_filename = secrets_filename
        self.configuration_filename = configuration_filename
        self.docker_compose_filename = docker_compose_filename

        self.docker_client = DockerClient(
            compose_files=[docker_compose_filename],
            compose_env_files=[self.secrets_filename],
        )
        self.logger.write(
            f"Deployment with build name {self.build_name} started."
        )
        with open(self.configuration_filename) as f:
            self.configuration_json = f.read()
        self.configuration = Configuration.model_validate_json(
            self.configuration_json
        )
        print(f"::{self.configuration_filename}")
        print(self.configuration.model_dump_json(indent=4))

        self.configuration.metadata.build_name = build_name
        self._export_port_configuration()

    def is_port_in_use(self, port: int) -> bool:
        """Check if the port is in use.

        Args:
            port: The port to check

        Returns:
            bool: True if the port is in use, False otherwise
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    def run_docker_service(
        self,
        service_name: str,
        detached: bool = False,
        build: bool = True,
    ) -> int:
        """Run the docker service.

        Run indicated docker service from the composer. If flagged, the service is built before running.
        Use detached mode for services that shouldn't be awaited.

        Args:
            service_name: The name of the service to run
            detached: Whether to run the service in detached mode
            build: Whether to build the service before running

        Returns:
            int: The return code of the command
        """
        try:
            if build:
                self.logger.write(f"Building docker service: {service_name}")
                self.docker_client.compose.build(
                    services=[service_name],
                    build_args={
                        "BUILD_NAME": self.build_name,
                        "CONFIGURATION_FILENAME": self.configuration_filename,
                        "SECRETS_FILENAME": self.secrets_filename,
                    },
                )

            self.logger.write(f"Running docker service: {service_name}")
            self.docker_client.compose.up(
                services=[service_name],
                detach=detached,
                abort_on_container_exit=not detached,
            )
            return 0
        except DockerException as e:
            self.logger.write(
                f"Error running docker service: {service_name}. Error: {e}. Args: {e.args}"
            )
            return e.return_code

    def cleanup(self) -> int:
        """Clean up the Docker resources.

        Clean up all the Docker resources, including volumes.

        Returns:
            int: The return code of the command
        """
        self.logger.write("Cleaning up Docker resources")
        self.docker_client.system.prune(all=True, volumes=True)

    def _export_port_configuration(self):
        """Export the port configuration.

        Export the port configuration to the environment variables.
        It is required for docker-compose, so it is able to use ports from the configuration.
        """
        vector_store_configuration = (
            self.configuration.pipeline.embedding.vector_store
        )
        os.environ["RAGKB__VECTOR_STORE__PORT_REST"] = str(
            vector_store_configuration.ports.rest
        )

        langfuse_configuration = (
            self.configuration.pipeline.augmentation.langfuse
        )
        os.environ["RAGKB__LANGFUSE__DATABASE__PORT"] = str(
            langfuse_configuration.database.port
        )
        os.environ["RAGKB__LANGFUSE__DATABASE__NAME"] = (
            langfuse_configuration.database.db
        )
        os.environ["RAGKB__LANGFUSE__DATABASE__USER"] = (
            langfuse_configuration.database.secrets.user.get_secret_value()
        )
        os.environ["RAGKB__LANGFUSE__DATABASE__PASSWORD"] = (
            langfuse_configuration.database.secrets.password.get_secret_value()
        )
        os.environ["RAGKB__LANGFUSE__PORT"] = str(langfuse_configuration.port)

        os.environ["RAGKB__CHAINLIT__PORT"] = str(
            self.configuration.pipeline.augmentation.chainlit.port
        )


class Deployment:
    """Deployment of the services.

    Deployment of the services using the Docker Compose.

    Attributes:
        command_runner: Command runner for the deployment
        logger: Logger for the deployment
    """

    class ServiceName(str, Enum):
        """Service names for the deployment.

        It has to correspond to the names in docker compose yaml file."""

        UNIT_TESTS = "unit-tests"
        EMBEDDING = "embed"
        CHAT = "chat"
        EVALUATION = "evaluate"

    def __init__(self, command_runner: CommandRunner, logger: Logger):
        """Initialize the deployment.

        Args:
            command_runner: Command runner for the deployment
            logger: Logger for the deployment
        """
        self.command_runner = command_runner
        self.logger = logger

    def run(self) -> None:
        """Run the deployment.

        Run the deployment of the services using the Docker Compose.
        If the unit tests fail, the deployment is stopped.

        The services are run in the following order:
        - Unit tests
        - Embedding
        - Chat
        - Evaluation

        If the service is not detached, it is awaited and its logs are redirected to the log file.
        """
        return_code = self.command_runner.run_docker_service(
            Deployment.ServiceName.UNIT_TESTS.value
        )
        if return_code != 0:
            self.logger.write("Unit tests failed. Exiting deployment.")
            sys.exit(1)
        self.command_runner.run_docker_service(
            Deployment.ServiceName.EMBEDDING.value
        )
        self.command_runner.run_docker_service(
            Deployment.ServiceName.CHAT.value, detached=True
        )
        self.command_runner.run_docker_service(
            Deployment.ServiceName.EVALUATION.value
        )


class Initialization:
    """Initialization of the services.

    Initialization of the services using the Docker Compose.

    Attributes:
        command_runner: Command runner for the initialization
        logger: Logger for the initialization
    """

    class ServiceName(str, Enum):
        """Service names for the initialization.

        It has to correspond to the names in docker compose yaml file.
        For vector stores, it has to correspond to VectorStoreName."""

        LANGFUSE = "langfuse"
        LANGFUSE_DB = "langfuse-db"

    def __init__(self, command_runner: CommandRunner, logger: Logger):
        """Initialize the initialization.

        Args:
            command_runner: Command runner for the initialization
            logger: Logger for the initialization
        """
        self.command_runner = command_runner
        self.logger = logger

    def run(self) -> None:
        """Run the initialization.

        Run the initialization of the services using the Docker Compose.

        The services are run in the following order:
        - Vector store
        - Langfuse database
        - Langfuse
        """
        self._init_vector_store()
        self._init_langfuse_database()
        self._init_langfuse()

    def _init_vector_store(self) -> None:
        """Initialize the vector store.

        Initialize the vector store service using the Docker Compose.
        If the ports are already in use, the initialization is skipped."""
        vector_store_configuration = (
            self.command_runner.configuration.pipeline.embedding.vector_store
        )
        vector_store_port_rest = vector_store_configuration.ports.rest

        if self.command_runner.is_port_in_use(vector_store_port_rest):
            self.logger.write(
                f"REST port {vector_store_port_rest} is already in use. Skipping {vector_store_configuration.name.value} initialization."
            )
            return
        else:
            self.command_runner.run_docker_service(
                vector_store_configuration.name.value, detached=True
            )

    def _init_langfuse_database(self) -> None:
        """Initialize the langfuse database.

        Initialize the langfuse database service using the Docker Compose."""
        langfuse_configuration = (
            self.command_runner.configuration.pipeline.augmentation.langfuse
        )
        langfuse_db_port = langfuse_configuration.database.port

        if self.command_runner.is_port_in_use(langfuse_db_port):
            self.logger.write(
                f"Port {langfuse_db_port} is already in use. Skipping langfuse database server initialization."
            )
            return
        else:
            self.command_runner.run_docker_service(
                Initialization.ServiceName.LANGFUSE_DB.value, detached=True
            )

    def _init_langfuse(self) -> None:
        """Initialize the langfuse.

        Initialize the langfuse service using the Docker Compose."""
        langfuse_configuration = (
            self.command_runner.configuration.pipeline.augmentation.langfuse
        )
        langfuse_port = langfuse_configuration.port

        if self.command_runner.is_port_in_use(langfuse_port):
            self.logger.write(
                f"Port {langfuse_port} is already in use. Skipping langfuse initialization."
            )
            return
        else:
            self.command_runner.run_docker_service(
                Initialization.ServiceName.LANGFUSE.value, detached=True
            )


def arg_parser() -> Namespace:
    """Parse the arguments.

    Parse the arguments from the command line."""
    parser = ArgumentParser()
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--init", action="store_true", help="Run initialization"
    )
    mode_group.add_argument(
        "--deploy", action="store_true", help="Run deployment"
    )
    parser.add_argument(
        "--build-name",
        type=str,
        help="The name of the build to deploy",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        help="The file to log the deployment output",
    )
    parser.add_argument(
        "--secrets-file",
        type=str,
        help="The file containing the secrets",
    )
    parser.add_argument(
        "--configuration-file",
        type=str,
        help="The file containing the configuration",
    )
    parser.add_argument(
        "--docker-compose-file",
        type=str,
        help="The file containing the docker-compose configuration used for setting up the services",
    )
    return parser.parse_args()


def initialize(logger: Logger, command_runner: CommandRunner) -> None:
    """
    Initialize the services.

    Args:
        logger: Logger for the initialization
        command_runner: Command runner for the initialization
    """
    logger.write("Start base services initialization.")
    Initialization(command_runner=command_runner, logger=logger).run()
    logger.write("Base services initialization finished.")


def deploy(logger: Logger, command_runner: CommandRunner) -> None:
    """
    Deploy the services.

    Args:
        logger: Logger for the deployment
        command_runner: Command runner for the deployment
    Note:
        Returns 1 if the unit tests fail.
    """
    try:
        logger.write("Start deployment.")
        Deployment(command_runner=command_runner, logger=logger).run()
        logger.write(
            f"Deployment with build name {command_runner.build_name} finished."
        )
    finally:
        command_runner.cleanup()
        logger.write(
            f"Deployment with build name {command_runner.build_name} finished."
        )


def main():
    """Main function for the deployment.

    If `--init` flag is passed initialization of the base services is run.
    Otherwise, if `--deploy` flag is passed deployment of the services is run.
    """
    args = arg_parser()
    logger = Logger(args.log_file)
    command_runner = CommandRunner(
        logger=logger,
        build_name=args.build_name,
        secrets_filename=args.secrets_file,
        configuration_filename=args.configuration_file,
        docker_compose_filename=args.docker_compose_file,
    )

    if args.init:
        initialize(logger, command_runner)
    if args.deploy:
        deploy(logger, command_runner)


if __name__ == "__main__":
    main()
