from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)


class BaseServer:
    """
    Mixin to provide start and stop methods and a context manager for resource lifecycle management.
    """

    dry_run: bool

    def __init__(self, dry_run=False):
        """
        Initializes the BaseServer. This method can be overridden by subclasses for custom initialization.
        """
        self.dry_run = dry_run

        logger.debug(f"{self.__class__.__name__} initialized")

    async def start(self):
        """
        Starts the resource. This method should be overridden by subclasses.
        """
        logger.debug(f"Default start method called for {self.__class__.__name__}")

    async def stop(self):
        """
        Stops the resource and performs cleanup. This method should be overridden by subclasses.
        """
        logger.debug(f"Default stop method called for {self.__class__.__name__}")

    @asynccontextmanager
    async def manage_lifecycle(self):
        """
        Context manager to manage the lifecycle of the resource. Calls start() on entry and stop() on exit.
        """
        logger.debug(f"Entering context for {self.__class__.__name__}")
        try:
            await self.start()
            yield self
        finally:
            logger.debug(f"Exiting context for {self.__class__.__name__}")
            await self.stop()
