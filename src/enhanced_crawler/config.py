import subprocess
import tempfile
import os
import json
from typing import Dict, Any

from enhanced_crawler.errors.errors import ConfigValidationError
from typing import Tuple
from urllib.parse import urlparse

import yaml
from pathlib import Path


def load_config_from_yaml(file_path: Path) -> dict:
    """
    Loads configuration from a YAML file.

    Args:
        file_path: The path to the YAML configuration file.

    Returns:
        A dictionary containing the configuration data.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Config file not found at {file_path}")

    try:
        with open(file_path, "r") as f:
            config_data = yaml.safe_load(f)
        return config_data if config_data is not None else {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Invalid YAML syntax in {file_path}: {e}")


def raise_on_invalid_url(url: str) -> bool:
    """Validates if the given url is a valid URL. Raises an error if not."""

    if url is None:
        raise ValueError("url cannot be None")

    if not isinstance(url, str):
        raise TypeError("string required")

    try:
        parsed_url = urlparse(url)
    except ValueError:
        return False

    if parsed_url.scheme not in ["http", "https", "ftp", "file", "git", "ssh"]:
        raise ValueError("Invalid url scheme")
    if not parsed_url.netloc:
        raise ValueError("Invalid url: missing netloc")

    return True


def raise_on_invalid_local_path(path: str) -> bool:
    """Validates if the given local path is a valid filesystem path."""
    if path is None:
        raise ValueError("Local path cannot be None")

    if not isinstance(path, str):
        raise TypeError("string required")

    if not path.startswith("/"):
        raise ValueError("Invalid local path: must be an absolute path starting with /")

    if not os.path.exists(path):
        raise ValueError(f"Local path does not exist: {path}")

    if not os.path.isdir(path):
        raise ValueError(f"Local path is not a directory: {path}")

    if not os.listdir(path):
        raise ValueError(f"Local path is empty: {path}")

    return True


def get_mount_string_parts(v: str) -> Tuple[str, str]:
    """Parses a mount string like '/local/path:http://remote/path' and returns a tuple of (local_path, dest_url_str)."""

    local_path, dest_url_str = v.split(":", 1)

    raise_on_invalid_local_path(local_path)

    raise_on_invalid_url(dest_url_str)

    return local_path, dest_url_str


def validate_git_url(url: str) -> str:
    """Validates a Git URL for SSH or HTTP(S) protocols. Returns the URL if valid, raises ValueError otherwise."""

    raise_on_invalid_url(url)

    if url.startswith(("http://", "https://", "git://")):
        return url

    if "@" not in url or ":" not in url:
        raise ValueError("Invalid Git URL for SSH: must contain @ and : symbols")

    return url


def transform_configuration(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms the enhanced crawler configuration (as a dictionary) into the
    format expected by the standard crawler.

    Args:
        config: The enhanced configuration loaded as a dictionary.

    Returns:
        A dictionary representing the configuration in the standard crawler format.
    """
    domains = []

    # Include existing standard domains
    if "domains" in config and isinstance(config["domains"], list):
        domains.extend(config["domains"])

    # Process repositories entry (single dictionary)
    if repositories := config.get("repositories"):
        if not isinstance(repositories, list):
            raise TypeError("Repositories must be a list")

        for repository in repositories:
            if not isinstance(repository, dict):
                ("Each repository entry must be a dictionary")

            if not repository.get("git_urls"):
                raise TypeError("Repositories entry must contain git_urls")

            repository["seed_urls"] = repository.get("git_urls")
            del repository["git_urls"]

        domains.extend(repositories)

    if directories := config.get("directories"):
        if not isinstance(directories, list):
            raise TypeError("Directories must be a list")

        for directory in directories:
            if not isinstance(directory, dict):
                raise TypeError("Each directory entry must be a dictionary")

            if not directory.get("mounts"):
                raise TypeError("Directories entry must contain mounts")

            seed_urls = [
                get_mount_string_parts(mount_string)[1]
                for mount_string in directory.get("mounts", [])
            ]

            directory["seed_urls"] = seed_urls
            del directory["mounts"]

    # Create the final standard configuration dictionary
    standard_config = {"domains": domains}

    # Pass through other top-level fields from the original config
    for key, value in config.items():
        if key not in ["repositories", "directories", "domains"]:
            standard_config[key] = value

    return standard_config


def validate_config(config: Dict[str, Any]):
    """
    Validates the transformed configuration using the external standard_crawler process.

    Args:
        config: The transformed configuration dictionary.

    Raises:
        ConfigValidationError: If the external validation process fails.
    """
    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w+", delete=False, suffix=".json"
        ) as tmp:
            temp_file_path = tmp.name
            json.dump(config, tmp)
            tmp.flush()

        result = subprocess.run(
            ["bin/crawler", "validate", temp_file_path],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            error_message = f"Standard crawler validation failed with exit code {result.returncode}.\n"
            error_message += f"Stderr: {result.stderr}\n"
            error_message += f"Stdout: {result.stdout}"
            raise ConfigValidationError(error_message)

        error_keywords = ["Error:", "Failed:", "Invalid"]
        output = result.stdout + result.stderr
        if any(keyword in output for keyword in error_keywords):
            error_message = "Standard crawler validation output indicates failure.\n"
            error_message += f"Stderr: {result.stderr}\n"
            error_message += f"Stdout: {result.stdout}"
            raise ConfigValidationError(error_message)

    except FileNotFoundError:
        raise ConfigValidationError(
            "Error: 'standard_crawler' command not found. Is it installed and in your PATH?"
        )
    except Exception as e:
        raise ConfigValidationError(
            f"An unexpected error occurred during configuration validation: {e}"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    return config  # Return the validated config
