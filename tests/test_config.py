import pytest
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from enhanced_crawler.config import load_config_from_yaml, transform_configuration, validate_config
from enhanced_crawler.errors.errors import ConfigValidationError


def test_load_config_file_not_found():
    """Test loading configuration from a non-existent file."""
    non_existent_file = Path("non_existent_config.yml")
    with pytest.raises(FileNotFoundError):
        load_config_from_yaml(non_existent_file)


def test_load_config_invalid_yaml():
    """Test loading configuration from a file with invalid YAML syntax."""
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load("""
key: value
list:
- item1
- item2
  : - item3 # Invalid indentation
""")


def test_load_config_valid_yaml(tmp_path):
    """Test loading configuration from a valid YAML file."""
    valid_yaml_content = """
key: value
list:
  - item1
  - item2
"""
    valid_yaml_file = tmp_path / "valid_config.yml"
    valid_yaml_file.write_text(valid_yaml_content)

    config_data = load_config_from_yaml(valid_yaml_file)
    assert config_data == {"key": "value", "list": ["item1", "item2"]}

    valid_yaml_file.unlink()


@pytest.mark.parametrize(
    "scenario_name",
    [
        "basic_mixed",
        "only_repos",
        "only_dirs",
        "missing_optional",
    ],
)
def test_transform_configuration_scenarios(load_config_scenario, snapshot, scenario_name):
    """Test transformation of various configuration scenarios loaded from YAML files."""
    config_input = load_config_scenario(scenario_name)
    transformed_config = transform_configuration(config_input)
    assert transformed_config == snapshot


@pytest.mark.parametrize(
    "scenario_name",
    [
        "empty_lists",
        "invalid_input",
    ],
)
def test_transform_configuration_invalid_input(load_config_scenario, scenario_name):
    """Test transformation with invalid git_urls or mounts to ensure validation errors."""
    config_input = load_config_scenario(scenario_name)
    with pytest.raises(Exception):
        transform_configuration(config_input)


def test_transform_configuration_valid_enhanced_features():
    """Test transformation with valid git_urls and mounts."""
    config_input = {
        "repositories": [{"git_urls": ["https://github.com/valid/repo.git", "git@github.com:valid/repo2.git"]}],
        "directories": [{"mounts": ["/local/path:/http://remote/path", "/another/path:/https://another/path"]}],
    }
    try:
        transform_configuration(config_input)
    except Exception as e:
        pytest.fail(f"Valid enhanced features raised an unexpected exception: {e}")


def test_transform_configuration_invalid_git_urls():
    """Test transformation with invalid git_urls to ensure validation errors."""
    config_input = {"repositories": [{"git_urls": ["invalid-url", "ftp://invalid/repo.git"]}]}
    with pytest.raises(Exception):
        transform_configuration(config_input)


def test_transform_configuration_invalid_mounts():
    """Test transformation with invalid mounts to ensure validation errors."""
    config_input = {"directories": [{"mounts": ["/local/path", "invalid-path:http://remote/path", "/local/path:invalid-url"]}]}
    with pytest.raises(Exception):
        transform_configuration(config_input)


@patch("enhanced_crawler.config.subprocess.run")
def test_validate_config_success(mock_subprocess_run):
    """Test validate_config with a successful external crawler validation."""
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Validation successful", stderr="")
    config_input = {"domains": [{"url": "http://example.com"}]}
    try:
        validate_config(config_input)
    except Exception as e:
        pytest.fail(f"validate_config raised an unexpected exception on success: {e}")
    mock_subprocess_run.assert_called_once()


@patch("enhanced_crawler.config.subprocess.run")
def test_validate_config_failure_exit_code(mock_subprocess_run):
    """Test validate_config with a failed external crawler validation (non-zero exit code)."""
    mock_subprocess_run.return_value = MagicMock(returncode=1, stdout="Validation failed", stderr="Error details")
    config_input = {"domains": [{"url": "http://example.com"}]}
    with pytest.raises(ConfigValidationError):
        validate_config(config_input)
    mock_subprocess_run.assert_called_once()


@patch("enhanced_crawler.config.subprocess.run")
def test_validate_config_failure_output_keywords(mock_subprocess_run):
    """Test validate_config with a failed external crawler validation (error keywords in output)."""
    mock_subprocess_run.return_value = MagicMock(returncode=0, stdout="Something went wrong: Error:", stderr="")
    config_input = {"domains": [{"url": "http://example.com"}]}
    with pytest.raises(ConfigValidationError):
        validate_config(config_input)
    mock_subprocess_run.assert_called_once()
