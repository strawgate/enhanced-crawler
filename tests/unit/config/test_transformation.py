import pytest

# Import the transformation function
from enhanced_crawler.config.to_crawler import transform_configuration


@pytest.mark.parametrize(
    "scenario_name",
    [
        "basic_mixed",
        "only_repos",
        "only_dirs",
        "missing_optional",
    ],
)
def test_transform_configuration_scenarios(
    load_config_scenario, snapshot, scenario_name
):
    """
    Test transformation of various configuration scenarios loaded from YAML files.
    """
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
    """
    Test transformation with invalid git_urls or mounts to ensure validation errors.
    """
    config_input = load_config_scenario(scenario_name)
    with pytest.raises(
        Exception
    ):  # Replace Exception with the specific validation error type if known
        transform_configuration(config_input)
