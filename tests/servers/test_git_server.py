import pytest
import tempfile
import os
from unittest.mock import patch

# Import the actual GitServer and the exception it raises
from enhanced_crawler.servers.git_server import GitServer
from git import GitCommandError  # Import the actual exception raised by GitPython


# Mock GitPython's Repo class for tests that don't require actual cloning
# or for simulating specific GitPython behaviors/errors.
@pytest.fixture
def mock_git_repo():
    with patch("enhanced_crawler.servers.git_server.Repo") as mock_repo:
        yield mock_repo


# Fixture to create and clean up a temporary directory for cloning
@pytest.fixture
def temp_repo_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


class TestGitServer:
    def test_clone_repository_success_http(self, temp_repo_dir):
        """Tests successful HTTP repository cloning to a temporary directory."""
        # Use a known public repository for testing
        repo_url = "https://github.com/github/gitignore.git"
        clone_subdir = "gitignore_clone"  # Subdirectory within temp_repo_dir

        git_server = GitServer(repository_directory=temp_repo_dir)
        cloned_path = git_server.clone_repository(repo_url, clone_subdir)

        expected_clone_path = os.path.join(temp_repo_dir, clone_subdir)

        # Assert that the repository was cloned into the specified subdirectory
        assert cloned_path == expected_clone_path
        assert os.path.exists(cloned_path)
        assert os.path.isdir(cloned_path)
        # Check for a known file in the gitignore repo to confirm successful clone
        assert os.path.exists(os.path.join(cloned_path, "Python.gitignore"))

    # TODO: Add test for successful SSH cloning (requires SSH setup in test env or mocking)

    @pytest.mark.usefixtures("mock_git_repo")  # Use usefixtures instead of decorator
    def test_clone_repository_invalid_url(self, mock_git_repo, temp_repo_dir):
        """Tests cloning with an invalid repository URL."""
        repo_url = "invalid-url"
        clone_subdir = "invalid_clone"

        # Simulate GitPython raising GitCommandError for an invalid URL
        mock_git_repo.clone_from.side_effect = GitCommandError("Invalid URL")

        git_server = GitServer(repository_directory=temp_repo_dir)

        with pytest.raises(GitCommandError):  # Expect GitCommandError
            git_server.clone_repository(repo_url, clone_subdir)

        mock_git_repo.clone_from.assert_called_once_with(repo_url, os.path.join(temp_repo_dir, clone_subdir))

    @pytest.mark.usefixtures("mock_git_repo")  # Use usefixtures instead of decorator
    def test_clone_repository_network_error(self, mock_git_repo, temp_repo_dir):
        """Tests cloning when a network error occurs."""
        repo_url = "https://github.com/example/nonexistent.git"
        clone_subdir = "network_error_clone"

        # Simulate GitPython raising a generic Exception for a network error
        mock_git_repo.clone_from.side_effect = Exception("Network error")

        git_server = GitServer(repository_directory=temp_repo_dir)

        with pytest.raises(Exception):  # Expect generic Exception as per code
            git_server.clone_repository(repo_url, clone_subdir)

        mock_git_repo.clone_from.assert_called_once_with(repo_url, os.path.join(temp_repo_dir, clone_subdir))

    # TODO: Add tests for other error scenarios (e.g., authentication failure, insufficient permissions)
    # TODO: Add tests for cloning specific branches/tags (if GitServer supports it)
