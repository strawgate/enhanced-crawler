import pytest
import threading
import time

# Assuming the WebServer class will be in this path
# from enhanced_crawler.servers.web_server import WebServer
# from enhanced_crawler.services.web import WebServerService


# Mock the WebServerService interface and the concrete WebServer class for testing purposes
class MockWebServerService:
    def start(self):
        pass

    def stop(self):
        pass

    def cleanup(self):
        pass

    def add_vhost_root(self, hostname: str, root_dir: str):
        pass

    def add_vhost_mount(self, hostname: str, mount_path: str, mount_point: str):
        pass


class MockWebServer(MockWebServerService):
    def __init__(self, host="127.0.0.1", port=8080):
        self._host = host
        self._port = port
        self._is_running = False
        self._vhosts = {}
        self._server_thread = None

    def start(self):
        if not self._is_running:
            self._is_running = True
            # Simulate server start in a thread
            self._server_thread = threading.Thread(target=self._run_server)
            self._server_thread.start()
            print(f"Mock server started on {self._host}:{self._port}")

    def _run_server(self):
        # Simulate server running
        while self._is_running:
            time.sleep(0.1)  # Keep the thread alive

    def stop(self):
        if self._is_running:
            self._is_running = False
            if self._server_thread and self._server_thread.is_alive():
                self._server_thread.join(timeout=1)  # Wait for thread to finish
            print("Mock server stopped")

    def cleanup(self):
        print("Mock server cleanup")
        self._vhosts = {}

    def add_vhost_root(self, hostname: str, root_dir: str):
        self._vhosts[hostname] = {"type": "root", "path": root_dir}
        print(f"Added vhost root: {hostname} -> {root_dir}")

    def add_vhost_mount(self, hostname: str, mount_path: str, mount_point: str):
        if hostname not in self._vhosts:
            self._vhosts[hostname] = {"type": "mounts", "mounts": {}}
        if self._vhosts[hostname]["type"] == "mounts":
            self._vhosts[hostname]["mounts"][mount_path] = mount_point
            print(f"Added vhost mount: {hostname}{mount_path} -> {mount_point}")
        else:
            print(f"Cannot add mount to vhost {hostname} with root type")


@pytest.fixture
def web_server():
    # Use the mock server for unit tests
    server = MockWebServer()
    yield server
    server.stop()
    server.cleanup()


def test_add_vhost_root(web_server):
    hostname = "example.com"
    root_dir = "/path/to/example"
    web_server.add_vhost_root(hostname, root_dir)
    assert hostname in web_server._vhosts
    assert web_server._vhosts[hostname]["type"] == "root"
    assert web_server._vhosts[hostname]["path"] == root_dir


def test_add_vhost_mount(web_server):
    hostname = "example.org"
    mount_path = "/docs"
    mount_point = "/path/to/docs"
    web_server.add_vhost_mount(hostname, mount_path, mount_point)
    assert hostname in web_server._vhosts
    assert web_server._vhosts[hostname]["type"] == "mounts"
    assert mount_path in web_server._vhosts[hostname]["mounts"]
    assert web_server._vhosts[hostname]["mounts"][mount_path] == mount_point


def test_add_multiple_vhost_mounts_to_same_host(web_server):
    hostname = "example.net"
    mount_path1 = "/api"
    mount_point1 = "/path/to/api"
    mount_path2 = "/data"
    mount_point2 = "/path/to/data"

    web_server.add_vhost_mount(hostname, mount_path1, mount_point1)
    web_server.add_vhost_mount(hostname, mount_path2, mount_point2)

    assert hostname in web_server._vhosts
    assert web_server._vhosts[hostname]["type"] == "mounts"
    assert mount_path1 in web_server._vhosts[hostname]["mounts"]
    assert web_server._vhosts[hostname]["mounts"][mount_path1] == mount_point1
    assert mount_path2 in web_server._vhosts[hostname]["mounts"]
    assert web_server._vhosts[hostname]["mounts"][mount_path2] == mount_point2


def test_start_and_stop_server(web_server):
    assert not web_server._is_running
    web_server.start()
    assert web_server._is_running
    assert web_server._server_thread is not None
    assert web_server._server_thread.is_alive()

    web_server.stop()
    assert not web_server._is_running
    # Give the thread a moment to potentially finish
    web_server._server_thread.join(timeout=2)
    assert not web_server._server_thread.is_alive()
