import argparse
from pathlib import Path
import sys
import logging
from copy import deepcopy
import asyncio
from urllib.parse import urlparse
from enhanced_crawler.config import (
    validate_config,
    load_config_from_yaml,
    transform_configuration,
    get_mount_string_parts
)
#from enhanced_crawler.servers.crawler_server import CrawlerServer
from enhanced_crawler.errors import Error
from enhanced_crawler.servers.git_server import GitServer
from enhanced_crawler.servers.dns_server import DnsServer
from enhanced_crawler.servers.web_server import WebServer

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_args(args=None):
    """
    Parses command-line arguments for the enhanced crawler.

    Args:
        args (list, optional): A list of arguments to parse. If None,
                                sys.argv[1:] is used. Defaults to None.

    Returns:
        argparse.Namespace: An object containing the parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="Enhanced Crawler CLI",
        add_help=False,
    )

    parser.add_argument("command", help="The command to execute (e.g., crawl, serve)")

    # The config path should be a positional argument after the command, and it is optional.
    # Do not change this to use a flag like --config.
    parser.add_argument(
        "config_path",
        nargs="?",
        default=None,
        help="Path to the configuration file (e.g., config.yml)",
    )
    
    parser.add_argument(
        "--dry-run",
        nargs="?",
        default=False,
        help="whether we're doing a dry run or not.)",
    )


    known_args, unknown_args = parser.parse_known_args(args)

    return known_args, unknown_args


async def run(args):
    """
    Main entry point for the enhanced crawler.

    Args:
        args (argparse.Namespace): Parsed command-line arguments.
    """

    config_path = Path(args.config_path)
    dry_run = args.dry_run

    logging.info(f"Loading configuration from {config_path}")
    raw_config = load_config_from_yaml(config_path)

    if dry_run:
        logging.info("Dry run mode enabled. Skipping passthrough validation.")
        validated_config = deepcopy(raw_config)
    else:
        logging.info("Validating configuration")
        validated_config = validate_config(deepcopy(raw_config))

    logging.info("Transforming configuration")
    transformed_config = transform_configuration(deepcopy(validated_config))

    web_server = WebServer(dry_run=dry_run)
    git_server = GitServer(dry_run=dry_run,repository_directory="./web/repositories")
    dns_server = DnsServer(dry_run=dry_run)
    #crawler_server = CrawlerServer()

    async with (
        dns_server.manage_lifecycle(),
        web_server.manage_lifecycle(),
        git_server.manage_lifecycle(),
        #crawler_server.manage_lifecycle(),
    ):
        logging.info("Orchestrating services and executing crawler")

        for directory in raw_config.get("directories", []):
            logging.info(f"Processing directory: {directory}")
            domain_url = directory.get("url")

            hostname, ip_address = await dns_server.add_host_by_url(url=domain_url)

            for raw_mount in directory.get("mounts", []):
                local_path, desired_uri = get_mount_string_parts(raw_mount)
                mount_path = urlparse(desired_uri).path
                web_server.add_vhost_mount(hostname, mount_path=mount_path, mount_point=local_path)
                web_server.add_vhost_mount("localhost", mount_path=mount_path, mount_point=local_path)

        for i, repository in enumerate(raw_config.get("repositories", [])):
            logging.info(f"Processing repository: {repository}")
            domain_url = repository.get("url")

            hostname, ip_address = await dns_server.add_host_by_url(url=domain_url)

            for j, git_url in enumerate(repository.get("git_urls", [])):
                mount_path = urlparse(git_url).path
                logging.info(f"Adding Git URL: {git_url}")
                clone_path = git_server.clone_repository(
                    repo_url=git_url,
                    clone_dir=str(f"domain_{i}_repository_{j}"),
                )
                web_server.add_vhost_mount(hostname, mount_path=mount_path, mount_point=clone_path)
                web_server.add_vhost_mount("localhost", mount_path=mount_path, mount_point=clone_path)

        logging.info("Sleeping for 60 seconds to allow manual inspection of the running services.")
        await asyncio.sleep(240)

        logging.info("Execution completed successfully.")

        return

    # sleep for 60 seconds to allow manual inspection of the running services

async def run_wrapper(args):
    try:
        await run(args)
    except KeyboardInterrupt:
        logging.info("Execution interrupted by user.")
        sys.exit(0)
    except Error as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        sys.exit(1)

    finally:
        logging.info("Main run function finished.")


def main():
    args, unknown = parse_args(sys.argv[1:])

    asyncio.run(run(args))


if __name__ == "__main__":
    main()
