import pytest
from unittest.mock import MagicMock, AsyncMock


class MockGitServer(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.clone_repository = MagicMock()
        self.start = MagicMock()
        self.stop = MagicMock()
        self.manage_lifecycle = MagicMock()
        self.manage_lifecycle.return_value.__enter__.return_value = self


class MockDnsServer(AsyncMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.install_dns_resolve_conf = AsyncMock()
        self.add_host = AsyncMock()
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.manage_lifecycle = MagicMock()
        self.manage_lifecycle.return_value.__aenter__ = AsyncMock(return_value=self)
        self.manage_lifecycle.return_value.__aexit__ = AsyncMock(return_value=None)


class MockWebServer(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start = MagicMock()
        self.stop = MagicMock()
        self.manage_lifecycle = MagicMock()
        self.manage_lifecycle.return_value.__enter__.return_value = self


@pytest.fixture
def mock_git_server():
    """Fixture for a mock GitServer."""
    return MockGitServer()


@pytest.fixture
def mock_dns_server():
    """Fixture for a mock DnsServer."""
    return MockDnsServer()


@pytest.fixture
def mock_web_server():
    """Fixture for a mock WebServer."""
    return MockWebServer()
