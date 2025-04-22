import os
import sys
import logging

from enhanced_crawler.servers.base_server import BaseServer

logger = logging.getLogger(__name__)


def execute_crawler(standard_crawler_path: str, transformed_config_path: str):
    """
    Executes the standard crawler by replacing the current process.

    Args:
        standard_crawler_path: The path to the standard crawler executable.
        transformed_config_path: The path to the transformed configuration file.
    """
    # Construct the command list for os.execv
    # The first element in the list should be the program name itself.
    command = [standard_crawler_path, "--config", transformed_config_path]

    logger.info(f"Executing crawler with command: {' '.join(command)}")

    # Replace the current process with the standard crawler process
    # os.execv takes the path to the executable and a list/tuple of arguments.
    # The arguments list should start with the name of the executable.
    try:
        os.execv(standard_crawler_path, command)
    except OSError as e:
        # Handle potential errors, e.g., executable not found
        logger.error(f"Error executing crawler: {e}")
        sys.exit(1)


class CrawlerServer(BaseServer):
    """
    Manages the execution of the standard crawler.
    """

    def execute(self, transformed_config: dict, service_instances: dict):
        """
        Executes the standard crawler.

        Args:
            transformed_config: The transformed configuration dictionary.
            service_instances: A dictionary of service instances.

        Returns:
            The result of the execution (or None, as os.execv replaces the process).
        """
        # Assuming the transformed_config contains the path to the standard crawler
        # and the path where the transformed config file was saved by the orchestrator.
        # This part needs to be aligned with the actual transformed config structure.
        # For now, using placeholder paths.
        standard_crawler_path = transformed_config.get("standard_crawler_path", "bin/crawler")  # Placeholder
        transformed_config_file_path = transformed_config.get("transformed_config_path", "/tmp/transformed_config.yml")  # Placeholder

        execute_crawler(standard_crawler_path, transformed_config_file_path)

        # os.execv replaces the current process, so this part is not reachable on success.
        # If it is reached, it means os.execv failed.
        return None  # Or raise an exception if execute_crawler didn't exit
