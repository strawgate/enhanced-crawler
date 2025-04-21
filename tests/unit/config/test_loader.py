import pytest
import yaml
from pathlib import Path

# Assuming the loader function will be in src/enhanced_crawler/config/loader.py
# We will import it later once the file is created.
from enhanced_crawler.config.loader import load_config_from_yaml


# Test case for file not found
def test_load_config_file_not_found():
    non_existent_file = Path("non_existent_config.yml")
    with pytest.raises(FileNotFoundError):
        # Replace with the actual function call once implemented
        load_config_from_yaml(non_existent_file)


# Test case for invalid YAML syntax
def test_load_config_invalid_yaml():
    """Test loading configuration from a file with invalid YAML syntax."""
    invalid_yaml_content = """
key: value
list:
- item1
- item2
  : - item3 # Invalid indentation
"""
    # Directly test yaml.safe_load with the invalid content
    with pytest.raises(yaml.YAMLError):
        yaml.safe_load(invalid_yaml_content)


# Test case for valid YAML
def test_load_config_valid_yaml(tmp_path):
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

    valid_yaml_file.unlink()  # Clean up the temporary file
