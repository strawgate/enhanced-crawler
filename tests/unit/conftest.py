import pytest
import yaml
from pathlib import Path
from unittest.mock import MagicMock

from enhanced_crawler.servers.dns_server import DnsServer
from enhanced_crawler.servers.git_server import GitServer
from enhanced_crawler.servers.web_server import WebServer
from enhanced_crawler.servers.crawler_server import CrawlerServer


@pytest.fixture
def load_config_scenario():
    """
    Fixture to load a configuration scenario from a YAML file.
    """

    def _loader(scenario_name: str):
        scenario_path = Path(__file__).parent / "scenarios" / f"{scenario_name}.yml"
        with open(scenario_path, "r") as f:
            return yaml.safe_load(f)

    return _loader


@pytest.fixture
def mock_git_server():
    """Fixture for a mock GitServer."""

    mock_git_server = MagicMock(spec=GitServer)

    return mock_git_server


@pytest.fixture
def mock_dns_server():
    """Fixture for a mock DnsServer."""

    mock_dns_server = MagicMock(spec=DnsServer)

    return mock_dns_server


@pytest.fixture
def mock_web_server():
    """Fixture for a mock WebServer."""
    mock_web_server = MagicMock(spec=WebServer)

    return mock_web_server


@pytest.fixture
def mock_crawler_server():
    """Fixture for a mock CrawlerServer."""
    mock_crawler_server = MagicMock(spec=CrawlerServer)


# class MockGitServer(MagicMock):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.clone_repository = MagicMock()
#         self.start = MagicMock()
#         self.stop = MagicMock()
#         self.manage_lifecycle = MagicMock()
#         self.manage_lifecycle.return_value.__enter__.return_value = self

# class MockDnsServer(AsyncMock):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.install_dns_resolve_conf = AsyncMock()
#         self.add_host = AsyncMock()
#         self.start = AsyncMock()
#         self.stop = AsyncMock()
#         self.manage_lifecycle = MagicMock()
#         self.manage_lifecycle.return_value.__aenter__ = AsyncMock(return_value=self)
#         self.manage_lifecycle.return_value.__aexit__ = AsyncMock(return_value=None)


# class MockWebServer(MagicMock):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)

#         self.start = MagicMock()
#         self.stop = MagicMock()
#         self.manage_lifecycle = MagicMock()
#         self.manage_lifecycle.return_value.__enter__.return_value = self
