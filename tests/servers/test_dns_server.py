import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock, mock_open

from enhanced_crawler.servers.dns_server import DnsServer

# Define a temporary resolv.conf path for testing
TEST_RESOLV_CONF = "/tmp/test_resolv.conf"


@pytest.fixture
def mock_dns_resolver():
    """Fixture for a mock async_dns resolver."""
    with patch("enhanced_crawler.servers.dns_server.dns_resolver") as mock_resolver_module:
        mock_resolver_instance = AsyncMock()
        mock_resolver_module.Resolver.return_value = mock_resolver_instance
        yield mock_resolver_instance


@pytest.fixture
def mock_resolv_conf_path():
    """Fixture to patch the RESOLV_CONF_PATH to a temporary file."""
    # Ensure test directory exists
    os.makedirs(os.path.dirname(TEST_RESOLV_CONF), exist_ok=True)

    # Patch the actual resolv.conf path in the DnsServer module
    with patch("enhanced_crawler.servers.dns_server.RESOLV_CONF_PATH", TEST_RESOLV_CONF):
        yield

    # Clean up temporary file
    if os.path.exists(TEST_RESOLV_CONF):
        os.remove(TEST_RESOLV_CONF)


class TestDnsServer:
    @pytest.mark.asyncio
    @pytest.mark.usefixtures("mock_resolv_conf_path")
    @patch("enhanced_crawler.servers.dns_server.dns_server_lib.start_server")
    @patch("enhanced_crawler.servers.dns_server.open", new_callable=mock_open)
    async def test_install_dns_resolve_conf_writes_localhost(
        self, mock_start_server, mock_resolv_conf_path, mock_open_file, mock_dns_resolver
    ):
        mock_start_server.return_value = (MagicMock(), MagicMock(), MagicMock())  # Mock return value of start_server
        """Tests that install_dns_resolve_conf writes the localhost nameserver."""
        dns_server = DnsServer()
        await dns_server.install_dns_resolve_conf()

        mock_open_file.assert_called_once_with(TEST_RESOLV_CONF, "w")
        handle = mock_open_file()
        handle.write.assert_any_call("nameserver 127.0.0.1\n")

    @pytest.mark.asyncio
    @patch("enhanced_crawler.servers.dns_server.open", new_callable=mock_open)
    @patch("enhanced_crawler.servers.dns_server.dns_server_lib.start_server")
    @pytest.mark.usefixtures("mock_resolv_conf_path")
    async def test_remove_dns_resolve_conf_removes_localhost(
        self, mock_start_server, mock_resolv_conf_path, mock_open_file, mock_dns_resolver
    ):
        mock_start_server.return_value = (MagicMock(), MagicMock(), MagicMock())  # Mock return value of start_server
        """Tests that remove_dns_resolve_conf removes the localhost nameserver."""
        # Simulate existing resolv.conf content
        mock_open_file.return_value.__enter__.return_value.readlines.return_value = [
            "nameserver 127.0.0.1\n",
            "nameserver 8.8.8.8\n",
        ]

        dns_server = DnsServer()
        await dns_server.remove_dns_resolve_conf()

        mock_open_file.assert_any_call(TEST_RESOLV_CONF, "r")
        mock_open_file.assert_any_call(TEST_RESOLV_CONF, "w")
        handle = mock_open_file()
        handle.write.assert_called_once_with("nameserver 8.8.8.8\n")  # Only the non-localhost line should be written

    @pytest.mark.asyncio
    async def test_add_host(self, mock_dns_resolver):
        """Tests the add_host method."""
        dns_server = DnsServer()
        hostname = "testhost.local"
        ip = "192.168.1.100"

        await dns_server.add_host(hostname, ip)

        # Assert that the underlying resolver's cache.add method was called
        mock_dns_resolver.cache.add.assert_called_once_with(hostname, MagicMock(), ip)  # Use MagicMock for dns_types.A

    @pytest.mark.asyncio
    @patch("enhanced_crawler.servers.dns_server.dns_server_lib.start_server")
    async def test_start_and_stop(self, mock_start_server, mock_dns_resolver):
        """Tests the start and stop methods."""
        mock_start_server.return_value = (MagicMock(), MagicMock(), MagicMock())  # Mock return value of start_server
        dns_server = DnsServer()

        await dns_server.start()
        mock_dns_resolver.start_server.assert_called_once()  # start calls start_server

        with patch.object(dns_server, "remove_dns_resolve_conf", new_callable=AsyncMock) as mock_remove_conf:
            await dns_server.stop()
            mock_dns_resolver.close.assert_called_once()  # stop calls close
            mock_remove_conf.assert_called_once()  # stop calls remove_dns_resolve_conf

    # TODO: Add tests for hostname resolution scenarios (mocking resolver.resolve)
    # TODO: Add tests for add_host_by_url
    # TODO: Add tests for error handling in start, stop, add_host, install_dns_resolve_conf, remove_dns_resolve_conf
