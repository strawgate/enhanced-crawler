import logging
import threading
import time
from flask import Flask, send_from_directory, request, Response
from werkzeug.serving import run_simple
import os
from typing import Dict, Any, List

from enhanced_crawler.servers.base_server import BaseServer
from enhanced_crawler.servers.models import vHost, Mount

logger = logging.getLogger(__name__)


class FileSystemAdapter:
    """
    Provides an abstraction layer for file system operations,
    allowing for easier testing and potential future extensions
    (e.g., supporting cloud storage).
    """
    @staticmethod
    def exists(path: str) -> bool:
        """Checks if a path exists."""
        return os.path.exists(path)

    @staticmethod
    def isdir(path: str) -> bool:
        """Checks if a path is a directory."""
        return os.path.isdir(path)

    @staticmethod
    def listdir(path: str) -> list[str]:
        """Lists the contents of a directory."""
        return os.listdir(path)

    @staticmethod
    def read_file(path: str) -> bytes:
        """Reads the binary content of a file."""
        with open(path, 'rb') as f:
            return f.read()


class WebServer(BaseServer):
    """
    Concrete implementation of a web server using Flask.
    Manages a local web server with support for virtual hosts and mounts.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 80, dry_run=False, file_system_adapter: FileSystemAdapter | None = None): # Added file_system_adapter parameter
        self._host = host
        self._port = port
        self._app = Flask(__name__, root_path=".")
        self._server_thread: threading.Thread | None = None
        self._is_running = False
        self._vhosts: List[vHost] = []
        self._shutdown_event = threading.Event()
        self.file_system_adapter = file_system_adapter or FileSystemAdapter() # Use injected adapter or create a default one

        # Configure Flask to handle requests
        self._app.config["SERVER_NAME"] = f"{self._host}:{self._port}"

        @self._app.before_request
        def before_request_handler():
            hostname = request.host.split(":")[0]
            path = request.path
            handler_info = self._handle_vhost_routing(hostname, path)
            if handler_info:
                handler_function, handler_args = handler_info
                if handler_function:
                    # Call the handler function with its arguments
                    return handler_function(*handler_args)
                else:
                    # Return the status code directly for errors
                    status_code = handler_args
                    return Response("Not Found", status=status_code)
            # If handler_info is None, Flask will continue with normal routing (which we don't use)
            # So we should return a 404 here if no vhost/mount matched
            return Response("Not Found", status=404)


        super().__init__(dry_run=dry_run)

    def _handle_vhost_routing(self, hostname: str, path: str):
        """
        Handles routing based on the requested hostname and path using vHost objects.
        Returns a tuple of (handler_function, handler_args) or (None, status_code).
        """
        # Find the vhost matching the hostname
        vhost = next((vh for vh in self._vhosts if vh.name == hostname), None)

        if vhost:
            # Delegate to mount handling logic with the vhost's mounts
            # This will be refactored in the next step
            # For now, we'll simulate the expected return structure
            # return self._handle_mount_request(vhost.mounts, path) # This will be the actual call later
            # Placeholder return based on current _handle_mount_request logic structure
            # This part will be updated in the next task
            return self._handle_mount_request(vhost.mounts, path)


        # If hostname not found
        return (None, 404)

    def _handle_mount_request(self, mounts: List[Mount], request_path: str):
        """
        Finds the correct mount point for the request path using longest prefix matching
        and delegates resource handling.
        Returns a tuple of (handler_function, handler_args) or (None, status_code).
        """
        best_match_mount: Mount | None = None
        best_match_mount_path_len = -1

        # Find the longest matching mount path
        for mount in mounts:
            if request_path.startswith(mount.url_path):
                # Longest prefix match is sufficient
                    if len(mount.url_path) > best_match_mount_path_len:
                        best_match_mount_path_len = len(mount.url_path)
                        best_match_mount = mount

        if best_match_mount:
            # Calculate the relative path within the mount
            relative_path = request_path[best_match_mount_path_len:].lstrip("/")

            # Determine the full path on the file system
            full_resource_path = os.path.join(best_match_mount.local_path, relative_path)

            # Check if the resource exists using the adapter
            if not self.file_system_adapter.exists(full_resource_path):
                return (None, 404) # Not Found

            # Determine if it's a directory or file using the adapter and return the appropriate handler
            if self.file_system_adapter.isdir(full_resource_path):
                # Pass the mount object, relative path, and full resource path
                return (self._serve_mounted_directory, (best_match_mount, relative_path, full_resource_path))
            else:
                # Pass the mount object and relative path
                return (self._serve_mounted_file, (best_match_mount, relative_path))

        # If no mount matches
        return (None, 404) # Not Found

    def _handle_mounted_resource(self, mount_path, mount_point, relative_path):
        """
        Determines if the requested resource is a directory or file and serves it accordingly.
        """
        full_resource_path = os.path.join(mount_point, relative_path)

        if not os.path.exists(full_resource_path):
            return Response("Not Found", status=404)

        if os.path.isdir(full_resource_path):
            return self._serve_mounted_directory(mount_path, relative_path, full_resource_path)
        else:
            return self._serve_mounted_file(mount_point, relative_path)

    def _serve_mounted_directory(self, mount: Mount, relative_path: str, full_resource_path: str):
        """
        Generates and returns the HTML for a directory listing.
        Returns a tuple of (status_code, headers, body).
        """
        # Use FileSystemAdapter to list directory contents
        try:
            items = self.file_system_adapter.listdir(full_resource_path)
        except FileNotFoundError:
             # This case should ideally be handled before calling this method,
             # but included as a safeguard.
            logger.error(f"Directory not found during serving: {full_resource_path}")
            return (404, {}, b"Not Found") # Not Found
        except Exception as e:
            logger.error(f"Error listing directory {full_resource_path}: {e}")
            return (500, {}, b"Internal Server Error") # Internal Server Error


        # Generate HTML using the decoupled method
        html_content = self._generate_directory_listing_html(mount, relative_path, full_resource_path, items)

        headers = {'Content-Type': 'text/html'}
        return (200, headers, html_content.encode('utf-8')) # OK

    def _generate_directory_listing_html(self, mount: Mount, relative_path: str, full_resource_path: str, items: list[str]) -> str:
        """
        Generates the HTML content for a directory listing.
        """
        display_path = os.path.join(mount.url_path, relative_path).rstrip("/") + "/"
        html_content = f"<h1>Directory listing for {display_path}</h1><ul>"

        # Add ".." link if not at the mount root
        if relative_path != "":
            parent_relative_path = os.path.dirname(relative_path)
            # Handle going up from the first level directory
            if parent_relative_path == "":
                 parent_url_path = mount.url_path
            else:
                 parent_url_path = os.path.join(mount.url_path, parent_relative_path).rstrip("/")
            # Ensure root mount path '/' correctly links parent to '/'
            if mount.url_path == '/' and parent_relative_path == '':
                 parent_url_path = '/'
            elif parent_url_path == '': # Handle cases where mount path is not root but parent becomes root
                 parent_url_path = '/'


            html_content += f'<li><a href="{parent_url_path}">..</a></li>'

        for item in sorted(items):
            item_path = os.path.join(full_resource_path, item)
            # Ensure URL path joins correctly, especially when relative_path is empty
            url_path = os.path.join(mount.url_path, relative_path, item).replace('//','/')


            # Use adapter to check if item is directory for link generation
            if self.file_system_adapter.isdir(item_path):
                html_content += f'<li><a href="{url_path}/">{item}/</a></li>'
            else:
                html_content += f'<li><a href="{url_path}">{item}</a></li>'
        html_content += "</ul>"
        return html_content

    def _serve_mounted_file(self, mount: Mount, relative_path: str):
        """
        Serves a file from a mounted directory.
        Returns a tuple of (status_code, headers, body).
        """
        # Prevent directory traversal
        if ".." in relative_path:
            return (403, {}, b"Forbidden") # Forbidden

        full_file_path = os.path.join(mount.local_path, relative_path)

        # Use FileSystemAdapter to read the file content
        try:
            content = self.file_system_adapter.read_file(full_file_path)
            # Basic content type detection (can be improved)
            if full_file_path.endswith('.html') or full_file_path.endswith('.htm'):
                mimetype = 'text/html'
            elif full_file_path.endswith('.css'):
                mimetype = 'text/css'
            elif full_file_path.endswith('.js'):
                mimetype = 'application/javascript'
            elif full_file_path.endswith('.json'):
                mimetype = 'application/json'
            elif full_file_path.endswith('.txt'):
                mimetype = 'text/plain'
            else:
                mimetype = 'text/plain' # Default binary

            headers = {'Content-Type': mimetype}
            return (200, headers, content) # OK

        except FileNotFoundError:
            # This case should ideally be handled before calling this method,
            # but included as a safeguard.
            logger.error(f"File not found during serving: {full_file_path}")
            return (404, {}, b"Not Found") # Not Found
        except Exception as e:
            logger.error(f"Error serving file {full_file_path}: {e}")
            return (500, {}, b"Internal Server Error") # Internal Server Error

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

        logger.info("Web server cleanup")
        self._vhosts = {}

    def add_vhost_mount(self, hostname: str, url_path: str, local_path: str):
        """
        Adds a virtual host with a mounted path using the new class structure.
        """
        if not os.path.exists(local_path): # Use os.path.exists as it handles both files and directories
            logger.warning(f"Mount point not found for {hostname}{url_path}: {local_path}")

        # Find existing vhost or create a new one
        vhost = next((vh for vh in self._vhosts if vh.name == hostname), None)

        if vhost is None:
            vhost = vHost(name=hostname, mounts=[])
            self._vhosts.append(vhost)
            logger.info(f"Created new vhost: {hostname}")

        # Add the new mount to the vhost
        mount = Mount(url_path=url_path, local_path=local_path)
        vhost.mounts.append(mount)
        logger.info(f"Added mount to vhost {hostname}: {url_path} -> {local_path}")
