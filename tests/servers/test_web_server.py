import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock # Import MagicMock

from enhanced_crawler.servers.web_server import WebServer
from enhanced_crawler.servers.models import vHost, Mount
from unittest.mock import mock_open


@pytest.fixture
def temp_web_content_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def web_server_instance(mock_adapter_instance): # Add mock_adapter_instance fixture
    # Inject the mock adapter instance
    return WebServer(host="127.0.0.1", port=8081, dry_run=True, file_system_adapter=mock_adapter_instance)




@pytest.fixture()
def mock_os_path_exists():
    with patch("enhanced_crawler.servers.web_server.os.path.exists") as mock_exists:
        yield mock_exists


@pytest.fixture()
def mock_os_path_isdir():
    with patch("enhanced_crawler.servers.web_server.os.path.isdir") as mock_isdir:
        yield mock_isdir


@pytest.fixture()
def mock_os_listdir():
    with patch("enhanced_crawler.servers.web_server.os.listdir") as mock_listdir:
        yield mock_listdir


@pytest.fixture()
def mock_serve_mounted_file():
    with patch.object(WebServer, "_serve_mounted_file") as mock_serve_file:
        yield mock_serve_file


@pytest.fixture()
def mock_serve_mounted_directory():
    with patch.object(WebServer, "_serve_mounted_directory") as mock_serve_directory:
        yield mock_serve_directory


@pytest.fixture()
def mock_handle_mounted_resource():
    with patch.object(WebServer, "_handle_mounted_resource") as mock_handle_resource:
        yield mock_handle_resource

@pytest.fixture()
def mock_adapter_instance():
    """Provides a MagicMock instance simulating FileSystemAdapter."""
    return MagicMock(spec=FileSystemAdapter)

@pytest.fixture()
def mock_generate_directory_listing_html():
    # Patch the method on the WebServer class
    with patch.object(WebServer, "_generate_directory_listing_html") as mock_generate_html:
        yield mock_generate_html


class TestModels:
    def test_mount_creation(self):
        mount = Mount(url_path="/app", local_path="/path/to/app")
        assert mount.url_path == "/app"
        assert mount.local_path == "/path/to/app"
        assert repr(mount) == "Mount(url_path='/app', local_path='/path/to/app')"

    def test_vhost_creation(self):
        mount1 = Mount(url_path="/app", local_path="/path/to/app")
        mount2 = Mount(url_path="/data", local_path="/path/to/data")
        vhost = vHost(name="example.com", mounts=[mount1, mount2])
        assert vhost.name == "example.com"
        assert len(vhost.mounts) == 2
        assert vhost.mounts[0] == mount1
        assert vhost.mounts[1] == mount2
        assert repr(vhost) == "vHost(name='example.com', mounts=[Mount(url_path='/app', local_path='/path/to/app'), Mount(url_path='/data', local_path='/path/to/data')])"


class TestAddVhostMount:
    def test_add_vhost_mount_new_vhost(self, web_server_instance):
        """Test adding a new vhost and mount."""
        hostname = "new.example.com"
        url_path = "/app"
        local_path = "/path/to/app"
        web_server_instance.add_vhost_mount(hostname, url_path, local_path)
        assert len(web_server_instance._vhosts) == 1
        vhost = web_server_instance._vhosts[0]
        assert vhost.name == hostname
        assert len(vhost.mounts) == 1
        mount = vhost.mounts[0]
        assert mount.url_path == url_path
        assert mount.local_path == local_path

    def test_add_vhost_mount_existing_vhost(self, web_server_instance):
        """Test adding a mount to an existing vhost."""
        hostname = "existing.example.com"
        local_path_1 = "/path/to/mount1"
        local_path_2 = "/path/to/mount2"
        web_server_instance.add_vhost_mount(hostname, "/mount1", local_path_1)
        web_server_instance.add_vhost_mount(hostname, "/mount2", local_path_2)
        assert len(web_server_instance._vhosts) == 1
        vhost = web_server_instance._vhosts[0]
        assert vhost.name == hostname
        assert len(vhost.mounts) == 2
        mount1 = next((m for m in vhost.mounts if m.url_path == "/mount1"), None)
        mount2 = next((m for m in vhost.mounts if m.url_path == "/mount2"), None)
        assert mount1 is not None
        assert mount1.local_path == local_path_1
        assert mount2 is not None
        assert mount2.local_path == local_path_2

    @patch("enhanced_crawler.servers.web_server.os.path.exists", return_value=False)
    @patch("enhanced_crawler.servers.web_server.logger")
    def test_add_vhost_mount_non_existent_mount_point(self, mock_logger, mock_exists, web_server_instance):
        """Test adding a mount with a non-existent local path (should log a warning)."""
        hostname = "warn.example.com"
        url_path = "/data"
        local_path = "/non/existent/path"
        web_server_instance.add_vhost_mount(hostname, url_path, local_path)
        mock_logger.warning.assert_called_once_with(f"Mount point not found for {hostname}{url_path}: {local_path}")
        # Verify vhost and mount are still added despite the warning
        assert len(web_server_instance._vhosts) == 1
        vhost = web_server_instance._vhosts[0]
        assert vhost.name == hostname
        assert len(vhost.mounts) == 1
        mount = vhost.mounts[0]
        assert mount.url_path == url_path
        assert mount.local_path == local_path


class TestServeMountedFile:
    def test_serve_mounted_file_success(self, web_server_instance, mock_adapter_instance): # Use mock_adapter_instance
        """Test serving an existing file."""
        mount = Mount(url_path="/data", local_path="/mnt/data")
        relative_path = "file.txt"
        file_content = b"This is the file content."
        mock_adapter_instance.read_file.return_value = file_content # Use mock_adapter_instance

        status_code, headers, body = web_server_instance._serve_mounted_file(mount, relative_path)

        mock_adapter_instance.read_file.assert_called_once_with(os.path.join(mount.local_path, relative_path)) # Use mock_adapter_instance
        assert status_code == 200
        assert headers == {'Content-Type': 'text/plain'} # Assuming text/plain for .txt
        assert body == file_content

    def test_serve_mounted_file_directory_traversal(self, web_server_instance):
        """Test directory traversal attempt (should return 403)."""
        mount = Mount(url_path="/data", local_path="/mnt/data")
        relative_path = "../sensitive/file.txt"

        status_code, headers, body = web_server_instance._serve_mounted_file(mount, relative_path)

        assert status_code == 403
        assert headers == {} # No specific headers for 403
        assert body == b"Forbidden" # Check the exact forbidden message


class TestServeMountedDirectory:
    def test_serve_mounted_directory_with_content(self, web_server_instance, mock_adapter_instance, mock_generate_directory_listing_html): # Use mock_adapter_instance
        """Test serving a directory with files and subdirectories."""
        mount = Mount(url_path="/web", local_path="/path/to/web")
        relative_path = "my_dir"
        full_resource_path = os.path.join(mount.local_path, relative_path)
        directory_contents = ["file1.txt", "subdir"]
        mock_adapter_instance.listdir.return_value = directory_contents # Use mock_adapter_instance
        # No need to mock is_directory here, as it's called within the mocked _generate_directory_listing_html
        generated_html = "<html>Directory listing for /web/my_dir/<ul><li>...</li></ul></html>"
        mock_generate_directory_listing_html.return_value = generated_html

        status_code, headers, body = web_server_instance._serve_mounted_directory(mount, relative_path, full_resource_path)

        mock_adapter_instance.listdir.assert_called_once_with(full_resource_path) # Use mock_adapter_instance
        # Assert the call to the mocked HTML generation method
        mock_generate_directory_listing_html.assert_called_once_with(mount, relative_path, full_resource_path, directory_contents)
        assert status_code == 200
        assert headers == {'Content-Type': 'text/html'}
        assert body == generated_html.encode('utf-8')

    def test_serve_mounted_directory_empty(self, web_server_instance, mock_adapter_instance, mock_generate_directory_listing_html): # Use mock_adapter_instance
        """Test serving an empty directory."""
        mount = Mount(url_path="/web", local_path="/path/to/web")
        relative_path = "empty_dir"
        full_resource_path = os.path.join(mount.local_path, relative_path)
        directory_contents = []
        mock_adapter_instance.listdir.return_value = directory_contents # Use mock_adapter_instance
        # No need to mock is_directory here
        generated_html = "<html>Directory listing for /web/empty_dir/<ul></ul></html>"
        mock_generate_directory_listing_html.return_value = generated_html

        status_code, headers, body = web_server_instance._serve_mounted_directory(mount, relative_path, full_resource_path)

        mock_adapter_instance.listdir.assert_called_once_with(full_resource_path) # Use mock_adapter_instance
        # Assert the call to the mocked HTML generation method
        mock_generate_directory_listing_html.assert_called_once_with(mount, relative_path, full_resource_path, directory_contents)
        assert status_code == 200
        assert headers == {'Content-Type': 'text/html'}
        assert body == generated_html.encode('utf-8')




class TestHandleMountRequest:
    @pytest.fixture
    def mounts_fixture(self):
        """Fixture to provide a list of Mount objects for testing."""
        mount1 = Mount(url_path="/app", local_path="/path/to/app")
        mount2 = Mount(url_path="/app/docs", local_path="/path/to/docs")
        mount3 = Mount(url_path="/data", local_path="/path/to/data")
        mount_root = Mount(url_path="/", local_path="/path/to/root")
        return [mount1, mount2, mount3, mount_root]

    @pytest.mark.parametrize(
        "request_path, expected_mount_url_path, expected_relative_path, resource_exists, is_directory, expected_return",
        [
            ("/app/file.txt", "/app", "file.txt", True, False, ("_serve_mounted_file",)), # Existing file in /app
            ("/app/docs/doc1.txt", "/app/docs", "doc1.txt", True, False, ("_serve_mounted_file",)), # Existing file in /app/docs (longest prefix)
            ("/app/docs/", "/app/docs", "", True, True, ("_serve_mounted_directory",)), # Existing directory /app/docs
            ("/app/", "/app", "", True, True, ("_serve_mounted_directory",)), # Existing directory /app
            ("/data/image.png", "/data", "image.png", True, False, ("_serve_mounted_file",)), # Existing file in /data
            ("/nonexistent/path", None, None, False, False, (None, 404)), # No matching mount
            ("/app/nonexistent.txt", "/app", "nonexistent.txt", False, False, (None, 404)), # Matching mount, but resource not found
            ("/appliance/test.txt", "/app", "liance/test.txt", True, False, ("_serve_mounted_file",)), # Should match /app, not require full segment match
            ("/", "/", "", True, True, ("_serve_mounted_directory",)), # Root path match
            ("/index.html", "/", "index.html", True, False, ("_serve_mounted_file",)), # File in root mount
        ],
    )
    def test_handle_mount_request(
        self,
        web_server_instance,
        mounts_fixture,
        request_path,
        expected_mount_url_path,
        expected_relative_path,
        resource_exists,
        is_directory,
        expected_return,
        mock_adapter_instance, # Use the injected adapter mock
        # Remove os mocks: mock_os_path_exists, mock_os_path_isdir,
        mock_serve_mounted_file, # Keep these for verifying the *returned* handler
        mock_serve_mounted_directory, # Keep these for verifying the *returned* handler
    ):
        """Test mount request handling with various scenarios."""
        web_server_instance._vhosts = [vHost(name="test.com", mounts=mounts_fixture)]
        # Configure the mock adapter
        mock_adapter_instance.exists.return_value = resource_exists # Use mock_adapter_instance
        mock_adapter_instance.isdir.return_value = is_directory # Use mock_adapter_instance

        # Call the method under test
        # We need to simulate the call from _handle_vhost_routing, which passes the mounts list
        handler_info = web_server_instance._handle_mount_request(mounts_fixture, request_path)

        if expected_return[0] is None:
            # Expecting a (None, status_code) return
            assert handler_info == expected_return
            mock_serve_mounted_file.assert_not_called()
            mock_serve_mounted_directory.assert_not_called()
        else:
            # Expecting a (handler_function, handler_args) return
            handler_function, handler_args = handler_info
            assert handler_function.__name__ == expected_return[0]

            # Find the expected mount object based on the expected URL path
            expected_mount = next((m for m in mounts_fixture if m.url_path == expected_mount_url_path), None)
            assert expected_mount is not None # Should find a mount if expecting a handler

            # Assert that the adapter methods were called (or not) as expected
            if expected_mount: # Only check adapter calls if a mount was matched
                expected_full_path = os.path.join(expected_mount.local_path, expected_relative_path)
                mock_adapter_instance.exists.assert_called_once_with(expected_full_path) # Use mock_adapter_instance
                if resource_exists:
                    mock_adapter_instance.isdir.assert_called_once_with(expected_full_path) # Use mock_adapter_instance
                else:
                    mock_adapter_instance.isdir.assert_not_called() # Use mock_adapter_instance

            # Verify the returned handler and its arguments
            if expected_return[0] == "_serve_mounted_file":
                # mock_serve_mounted_file.assert_called_once_with(expected_mount, expected_relative_path) # Don't assert call here, just check return
                # mock_serve_mounted_directory.assert_not_called()
                assert handler_args == (expected_mount, expected_relative_path)
            elif expected_return[0] == "_serve_mounted_directory":
                expected_full_path = os.path.join(expected_mount.local_path, expected_relative_path)
                # mock_serve_mounted_directory.assert_called_once_with(expected_mount, expected_relative_path, expected_full_path) # Don't assert call here, just check return
                # mock_serve_mounted_file.assert_not_called()
                assert handler_args == (expected_mount, expected_relative_path, expected_full_path)


class TestHandleVhostRouting:
    @pytest.fixture
    def vhosts_fixture(self):
        """Fixture to provide a list of vHost objects for testing."""
        mount1 = Mount(url_path="/app", local_path="/path/to/app")
        mount2 = Mount(url_path="/data", local_path="/path/to/data")
        vhost1 = vHost(name="existing.example.com", mounts=[mount1, mount2])
        vhost2 = vHost(name="another.example.com", mounts=[Mount(url_path="/files", local_path="/path/to/files")])
        return [vhost1, vhost2]

    def test_handle_vhost_routing_existing_vhost_match(self, web_server_instance, vhosts_fixture):
        """Test with a request to an existing vhost that has a matching mount."""
        web_server_instance._vhosts = vhosts_fixture
        hostname = "existing.example.com"
        path = "/app/file.txt"
        # Mock the _handle_mount_request to control its return value
        with patch.object(WebServer, "_handle_mount_request", return_value=("mock_handler", ("arg1",))) as mock_handle_mount_request:
            handler_info = web_server_instance._handle_vhost_routing(hostname, path)
            # Assert that _handle_mount_request was called with the correct mounts and path
            expected_mounts = next((vh.mounts for vh in vhosts_fixture if vh.name == hostname), None)
            mock_handle_mount_request.assert_called_once_with(expected_mounts, path)
            # Assert that the return value is as expected from the mock
            assert handler_info == ("mock_handler", ("arg1",))

    def test_handle_vhost_routing_existing_vhost_no_mount_match(self, web_server_instance, vhosts_fixture):
        """Test with a request to an existing vhost that has no matching mount."""
        web_server_instance._vhosts = vhosts_fixture
        hostname = "existing.example.com"
        path = "/images/img.png"
        # Mock the _handle_mount_request to return None, 404 (no mount match)
        with patch.object(WebServer, "_handle_mount_request", return_value=(None, 404)) as mock_handle_mount_request:
            handler_info = web_server_instance._handle_vhost_routing(hostname, path)
            # Assert that _handle_mount_request was called with the correct mounts and path
            expected_mounts = next((vh.mounts for vh in vhosts_fixture if vh.name == hostname), None)
            mock_handle_mount_request.assert_called_once_with(expected_mounts, path)
            # Assert that the return value is None, 404
            assert handler_info == (None, 404)

    def test_handle_vhost_routing_non_existent_vhost(self, web_server_instance, vhosts_fixture):
        """Test with a request to a non-existent vhost."""
        web_server_instance._vhosts = vhosts_fixture
        hostname = "nonexistent.example.com"
        path = "/some/path"
        # Ensure _handle_mount_request is not called
        with patch.object(WebServer, "_handle_mount_request") as mock_handle_mount_request:
            handler_info = web_server_instance._handle_vhost_routing(hostname, path)
            mock_handle_mount_request.assert_not_called()
            # Assert that the return value is None, 404
            assert handler_info == (None, 404)

    # Note: The test for unexpected vhost type is no longer applicable
    # as the _vhosts attribute now stores vHost objects directly.

    def test_handle_vhost_routing_hostname_with_port(self, web_server_instance, vhosts_fixture):
        """Test with a request to an existing vhost with port in hostname."""
        web_server_instance._vhosts = vhosts_fixture
        # The _handle_vhost_routing method now expects just the hostname without the port
        hostname_with_port = "existing.example.com:8081"
        hostname_without_port = "existing.example.com"
        path = "/app/file.txt"
        with patch.object(WebServer, "_handle_mount_request", return_value=("mock_handler", ("arg1",))) as mock_handle_mount_request:
             # Simulate the before_request handler extracting the hostname without the port
            handler_info = web_server_instance._handle_vhost_routing(hostname_without_port, path)
            expected_mounts = next((vh.mounts for vh in vhosts_fixture if vh.name == hostname_without_port), None)
            mock_handle_mount_request.assert_called_once_with(expected_mounts, path)
            assert handler_info == ("mock_handler", ("arg1",))


class TestGenerateDirectoryListingHTML:
    @pytest.mark.parametrize(
        "mount_url_path, mount_local_path, relative_path, items, isdir_map, expected_html_substrings",
        [
            # Case 1: Empty directory at mount root
            ("/", "/root", "", [], {}, ["<h1>Directory listing for /</h1><ul></ul>"]),
            # Case 2: Empty directory in subdir
            ("/web", "/var/www", "subdir", [], {}, ['<h1>Directory listing for /web/subdir/</h1><ul>', '<li><a href="/web">..</a></li>', '</ul>']),
            # Case 3: Directory with files and subdirs at mount root
            ("/", "/root", "", ["file.txt", "sub"], {"/root/sub": True}, ['<h1>Directory listing for /</h1><ul>', '<li><a href="/sub/">sub/</a></li>', '<li><a href="/file.txt">file.txt</a></li>', '</ul>']),
            # Case 4: Directory with files and subdirs in subdir
            ("/web", "/var/www", "data", ["img.png", "docs"], {"/var/www/data/docs": True}, ['<h1>Directory listing for /web/data/</h1><ul>', '<li><a href="/web">..</a></li>', '<li><a href="/web/data/docs/">docs/</a></li>', '<li><a href="/web/data/img.png">img.png</a></li>', '</ul>']),
            # Case 5: Directory with special characters (ensure basic rendering)
            ("/files", "/mnt", "", ["a&b.txt", "c<d>"], {}, ['<h1>Directory listing for /files/</h1><ul>', '<li><a href="/files/a&b.txt">a&b.txt</a></li>', '<li><a href="/files/c<d>">c<d></a></li>', '</ul>']), # Assuming basic HTML escaping happens implicitly or is not required by spec yet
             # Case 6: Mount path is not root, relative path is empty
            ("/app", "/srv/app", "", ["index.html", "static"], {"/srv/app/static": True}, ['<h1>Directory listing for /app/</h1><ul>', '<li><a href="/app/static/">static/</a></li>', '<li><a href="/app/index.html">index.html</a></li>', '</ul>']), # No ".." link here
             # Case 7: Mount path is not root, relative path is subdir
            ("/app", "/srv/app", "static", ["style.css"], {}, ['<h1>Directory listing for /app/static/</h1><ul>', '<li><a href="/app">..</a></li>', '<li><a href="/app/static/style.css">style.css</a></li>', '</ul>']),
        ]
    )
    def test_generate_html(self, web_server_instance, mock_adapter_instance, mount_url_path, mount_local_path, relative_path, items, isdir_map, expected_html_substrings): # Use mock_adapter_instance
        """Test HTML generation for various directory scenarios."""
        mount = Mount(url_path=mount_url_path, local_path=mount_local_path)
        full_resource_path = os.path.join(mount_local_path, relative_path)

        # Configure the mock adapter's isdir based on the map
        mock_adapter_instance.isdir.side_effect = lambda p: isdir_map.get(p, False) # Use mock_adapter_instance

        # Call the method under test
        html_result = web_server_instance._generate_directory_listing_html(mount, relative_path, full_resource_path, items)

        # Assert that all expected substrings are present in the generated HTML
        for substring in expected_html_substrings:
            assert substring in html_result

        # Verify isdir was called for each item
        for item in items:
             item_path = os.path.join(full_resource_path, item)
             mock_adapter_instance.isdir.assert_any_call(item_path) # Use mock_adapter_instance


# Keep existing fixtures if they are still needed for potential integration tests or other purposes
# If not needed, they can be removed later.
# @pytest.fixture
# async def running_web_server(temp_web_content_dir):
#     # Use a fixed port for testing
#     port = 8081
#     server = WebServer(host="127.0.0.1", port=port)

#     # Start the server
#     await server.start()

#     # Wait a moment for the server to start
#     await asyncio.sleep(0.1)

#     yield server # Yield the server instance

#     # Stop the server
#     await server.stop()
