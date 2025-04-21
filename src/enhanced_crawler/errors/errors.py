class Error(Exception):
    """Base error class for EnhancedCrawler."""

    pass


class ConfigValidationError(Error):
    """Raised when configuration validation fails."""

    pass


class ConfigurationError(Error):
    """Raised for general configuration issues."""

    pass


class CleanupError(Error):
    """Raised when a cleanup operation fails."""

    pass


class CrawlerExecutionError(Error):
    """Raised when a crawler execution fails."""

    pass


class DnsServerError(Error):
    """Raised for DNS server related errors."""

    pass


class InitializationError(Error):
    """Raised when an initialization step fails."""

    pass


class GitCloneError(Error):
    """Raised when a git clone operation fails."""

    pass


class WebServerStartError(Error):
    """Raised when the web server fails to start."""

    pass
