import os
import logging
import shutil
from git import Repo, GitCommandError

from enhanced_crawler.servers.base_server import BaseServer

logger = logging.getLogger(__name__)


class GitServer(BaseServer):
    """
    Manages Git operations using GitPython.
    """

    def __init__(self, repository_directory, dry_run=False):
        """
        Initializes the GitServer with a specified repository directory.

        Args:
            repository_directory: The directory where Git repositories will be cloned.
        """
        super().__init__(dry_run=dry_run)
        self.repository_directory = repository_directory
        logger.debug(f"GitServer initialized with repository directory: {repository_directory}")

    async def start(self):
        # clean out the repository directory if dry_run is True
        if self.dry_run:
            if os.path.exists(self.repository_directory):
                logger.debug(f"Cleaning out repository directory: {self.repository_directory}")
                for item in os.listdir(self.repository_directory):
                    item_path = os.path.join(self.repository_directory, item)
                    # Remove directory even if it is not empty
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)

    def clone_repository(self, repo_url: str, clone_dir: str) -> str:
        """
        Clones a Git repository into a specified directory using GitPython.

        Args:
            repo_url: The URL of the Git repository to clone.
            clone_dir: The local directory path where the repository should be cloned.

        Returns:
            The path to the cloned repository if successful.

        Raises:
            GitCommandError: If a Git command fails during cloning.
            Exception: For any other unexpected errors.
        """
        logger.debug(f"Attempting to clone repository '{repo_url}' into '{clone_dir}'")
        try:
            clone_path = os.path.join(self.repository_directory, clone_dir)

            if not os.path.exists(clone_path):
                os.makedirs(clone_path, exist_ok=True)
                logger.debug(f"Created parent directory: {clone_path}")

            Repo.clone_from(repo_url, clone_path)
            logger.debug(f"Successfully cloned repository '{repo_url}'")
            return clone_path

        except GitCommandError as e:
            logger.error(f"Git command failed during cloning '{repo_url}': {e}")
            raise

        except Exception as e:
            logger.error(f"An unexpected error occurred during cloning '{repo_url}': {e}")
            raise
