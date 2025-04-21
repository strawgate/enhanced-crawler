import logging
import threading
import time
from flask import Flask, send_from_directory, request, Response
from flask_autoindex import AutoIndex
from werkzeug.serving import run_simple
import os
from typing import Dict, Any

from enhanced_crawler.servers.base_server import BaseServer

logger = logging.getLogger(__name__)


class WebServer(BaseServer):
    """
    Concrete implementation of a web server using Flask.
    Manages a local web server with support for virtual hosts and mounts.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 80, dry_run=False):
        self._host = host
        self._port = port
        self._app = Flask(__name__)
        self._server_thread: threading.Thread | None = None
        self._is_running = False
        self._vhosts: Dict[str, Dict[str, Any]] = {}
        self._shutdown_event = threading.Event()

        # Configure Flask to handle requests
        self._app.config["SERVER_NAME"] = f"{self._host}:{self._port}"
        self._app.before_request(self._handle_vhost_routing)

        super().__init__(dry_run=dry_run)
        self._autoindex = AutoIndex(self._app)

    def _serve_from_root(self, root_dir, path):
        """
        Serves files directly from the root directory for a vhost.
        """
        try:
            # Prevent directory traversal
            if ".." in path:
                return Response("Forbidden", status=403)
            return send_from_directory(root_dir, path.lstrip("/"))
        except FileNotFoundError:
            return Response("Not Found", status=404)

    def _handle_mount_routing(self, mounts, path):
        """
        Handles routing for vhosts with mounted paths, including directory listing.
        """
        for mount_path, mount_point in mounts.items():
            if path.startswith(mount_path):
                relative_path = path[len(mount_path) :].lstrip("/")

                # Check if it's the root of the mount for directory listing
                if not relative_path:
                     return self._autoindex.render_autoindex(browse_root=mount_point, path='/')

                # Serve files from the mounted directory
                try:
                    # Prevent directory traversal
                    if ".." in relative_path:
                        return Response("Forbidden", status=403)

                    return send_from_directory(mount_point, relative_path)
                except FileNotFoundError:
                    return Response("Not Found", status=404)
        # If no mount matches, return 404
        return Response("Not Found", status=404)

    def _handle_vhost_routing(self):
        """
        Handles routing based on the requested hostname and path.
        """
        hostname = request.host.split(":")[0]
        path = request.path

        if hostname in self._vhosts:
            vhost_config = self._vhosts[hostname]
            if vhost_config["type"] == "root":
                root_dir = vhost_config["path"]
                return self._serve_from_root(root_dir, path)
            elif vhost_config["type"] == "mounts":
                mounts = vhost_config["mounts"]
                return self._handle_mount_routing(mounts, path)

        # If hostname not found, return 404
        return Response("Not Found", status=404)

    async def start(self):
        """
        Starts the web server service in a separate thread.
        """
        if not self._is_running:
            self._is_running = True
            self._shutdown_event.clear()
            self._server_thread = threading.Thread(
                target=run_simple,
                kwargs={
                    "hostname": self._host,
                    "port": self._port,
                    "application": self._app,
                    "threaded": True,
                    "use_reloader": False,
                    "use_debugger": False,
                },
            )
            self._server_thread.daemon = True
            self._server_thread.start()
            logger.info(f"Web server started on {self._host}:{self._port}")

    async def stop(self):
        """
        Stops the web server service and performs cleanup.
        """
        if self._is_running:
            self._is_running = False
            self._shutdown_event.set()
            # A small delay to allow the server thread to potentially see the event
            time.sleep(0.1)
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=5)  # Wait for thread to finish
            logger.info("Web server stopped")

        # Cleanup logic moved from cleanup()
        logger.info("Web server cleanup")
        self._vhosts = {}

    def add_vhost_root(self, hostname: str, root_dir: str):
        """
        Adds a virtual host with a root directory.
        """
        if not os.path.isdir(root_dir):
            logger.warning(f"Root directory not found for {hostname}: {root_dir}")

        self._vhosts[hostname] = {"type": "root", "path": root_dir}
        logger.info(f"Added vhost root: {hostname} -> {root_dir}")

    def add_vhost_mount(self, hostname: str, mount_path: str, mount_point: str):
        """
        Adds a virtual host with a mounted path.
        """
        if not os.path.isdir(mount_point):
            logger.warning(
                f"Mount point not found for {hostname}{mount_path}: {mount_point}"
            )

        if hostname not in self._vhosts:
            self._vhosts[hostname] = {"type": "mounts", "mounts": {}}
        elif self._vhosts[hostname]["type"] == "root":
            logger.warning(
                f"Cannot add mount to vhost {hostname} with root type. Ignoring mount."
            )
            return  # Cannot mix root and mounts for the same hostname

        if self._vhosts[hostname]["type"] == "mounts":
            self._vhosts[hostname]["mounts"][mount_path] = mount_point
            logger.info(f"Added vhost mount: {hostname}{mount_path} -> {mount_point}")
        else:
            # This case should be covered by the check above, but as a safeguard:
            logger.error(
                f"Unexpected vhost type for {hostname}: {self._vhosts[hostname]['type']}"
            )
