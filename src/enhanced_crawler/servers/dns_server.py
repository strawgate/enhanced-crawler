import logging
import asyncio
import urllib.parse
import async_dns.resolver as dns_resolver
import async_dns.server as dns_server_lib
import async_dns.core.types as dns_types
import urllib
from enhanced_crawler.errors import DnsServerError
from enhanced_crawler.servers.base_server import BaseServer

logger = logging.getLogger(__name__)

RESOLV_CONF_PATH = "/etc/resolv.conf"
BACKUP_RESOLV_CONF_PATH = "/etc/resolv.conf.enhanced_crawler_backup"


class DnsServer(BaseServer):
    """
    DNS service implementation using async-dns.
    """

    _resolver: dns_resolver.Resolver
    _dns_server: asyncio.Server
    _udp_transports: list

    async def start(self):
        """
        Starts the DnsServer by initializing the async-dns resolver and starting the DNS server.
        """
        logger.debug("DnsServer start method called")

        # Start the async-dns server programmatically
        server_address = "127.0.0.1"
        server_port = 53
        try:
            # start_server returns server, transport_arr, resolver. Use the returned resolver.
            dns_server, udp_transports, resolver = await dns_server_lib.start_server(
                host=server_address,
                port=server_port,
                hosts=None,  # We manage hosts via add_host
                proxies=None,  # Configure proxies based on config if needed
            )

            logger.debug(f"Async-dns server started on {server_address}:{server_port}")

            if not dns_server:
                raise DnsServerError(
                    "Failed to start async-dns server: No server instance returned"
                )
            if not udp_transports:
                raise DnsServerError(
                    "Failed to start async-dns server: No UDP transports returned"
                )
            if not resolver:
                raise DnsServerError(
                    "Failed to start async-dns server: No resolver instance returned"
                )

            self._dns_server = dns_server
            self._udp_transports = udp_transports
            self._resolver = resolver

            logger.debug("Async-dns server and resolver initialized successfully")

        except Exception as e:
            logger.error(f"Error starting async-dns server: {e}")
            raise DnsServerError(f"Failed to start async-dns server: {e}") from e

    async def stop(self):
        """
        Stops the DnsServer, stops the DNS server, and restores the original resolv.conf.
        """
        logger.debug("DnsServer stop method called")

        self._dns_server.close()

        await self.remove_dns_resolve_conf()

        logger.debug("Async-dns server stopped.")

    async def install_dns_resolve_conf(self):
        """
        Configures the system's DNS resolver to use this DnsServer by modifying resolv.conf.
        This functionality might be complex and platform-dependent.
        """
        if self.dry_run:
            logger.debug("Dry run mode: Skipping DNS resolver configuration")
            return
        
        logger.debug(f"Attempting to configure {RESOLV_CONF_PATH} to use localhost:53")

        with open(RESOLV_CONF_PATH, "w") as f:
            f.write("nameserver 127.0.0.1\n")

        logger.debug(f"Updated {RESOLV_CONF_PATH} to point to localhost")

    async def remove_dns_resolve_conf(self):
        """
        Removes the 127.0.0.1 entry from the system's DNS resolver configuration.
        """
        if self.dry_run:
            logger.debug("Dry run mode: Skipping DNS resolver configuration")
            return
        
        logger.debug(
            f"Attempting to remove the DNS Resolve configuration at {RESOLV_CONF_PATH}"
        )

        with open(RESOLV_CONF_PATH, "r") as f:
            content = f.readlines()

        # Filter out the line containing 'nameserver 127.0.0.1'

        with open(RESOLV_CONF_PATH, "w") as f:
            for line in content:
                if "nameserver 127.0.0.1" not in line:
                    f.write(line)

        logger.debug(f"Removed the DNS Resolve configuration at {RESOLV_CONF_PATH}")

    async def add_host_by_url(self, url: str, ip_address: str = "127.0.0.1") -> tuple[str, str]:
        """
        Adds a host entry to the async-dns resolver's internal host list using a url.

        Args:
            url: The URL to extract the hostname from.
            ip_address: The IP address associated with the hostname.
        """
    
        parsed_url = urllib.parse.urlparse(url)
        hostname = parsed_url.hostname

        if not hostname:
            raise DnsServerError(f"Invalid URL: {url} does not contain a hostname")

        return await self.add_host(
            hostname, ip_address
        )


    async def add_host(self, hostname: str, ip_address: str = "127.0.0.1"):
        """
        Adds a host entry to the async-dns resolver's internal host list.

        Args:
            hostname: The hostname to add.
            ip_address: The IP address associated with the hostname.
        """
        if not self._resolver:
            raise DnsServerError("DNS resolver is not initialized")

        logger.debug(f"Adding host entry: {ip_address} {hostname}")

        # Use the resolver's cache to add the host entry (Assuming A record for simplicity)
        self._resolver.cache.add(hostname, dns_types.A, ip_address)

        return hostname, ip_address
