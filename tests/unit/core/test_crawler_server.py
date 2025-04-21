from unittest.mock import patch
from enhanced_crawler.servers.crawler_server import execute_crawler

# Assuming the execution logic is in a function called 'execute_crawler'
# in the 'enhanced_crawler.execution' module.


@patch("os.execv")
def test_execute_crawler_calls_execv_with_correct_args(mock_execv):
    """
    Test that execute_crawler constructs the correct command and calls os.execv.
    """
    mock_command_args = ["--config", "/path/to/transformed_config"]
    mock_transformed_config_path = "/path/to/transformed_config"
    mock_standard_crawler_path = "/path/to/standard_crawler"

    # Call the function that will be implemented
    execute_crawler(mock_standard_crawler_path, mock_transformed_config_path)

    # The expected arguments for os.execv are (path, args)
    # path is the path to the executable (standard_crawler_path)
    # args is a tuple or list of strings representing the argument list,
    # starting with the name of the executable.
    expected_execv_args = (
        mock_standard_crawler_path,
        [mock_standard_crawler_path] + mock_command_args,
    )

    # Assert that os.execv was called with the expected arguments
    mock_execv.assert_called_once_with(*expected_execv_args)
