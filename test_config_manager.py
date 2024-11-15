# test_config_manager.py
import pytest


@pytest.fixture
def config_manager(trader):
    yield trader.config_manager


def default_test_get_api_key(config_manager):
    assert config_manager.get_api_key() == ""


def test_get_api_key(config_manager):
    config_manager.set_api_key("test_key")
    assert config_manager.get_api_key() == "test_key"


def default_test_get_secret_key(config_manager):
    assert config_manager.get_secret_key() == ""


def test_get_secret_key(config_manager):
    config_manager.set_secret_key("test_secret_key")
    assert config_manager.get_secret_key() == "test_secret_key"


def default_test_get_is_production(config_manager):
    assert config_manager.get_is_production() is True


def test_get_is_production(config_manager):
    config_manager.set_is_production(False)
    assert config_manager.get_is_production() is False


def default_test_get_debug(config_manager):
    assert config_manager.get_debug() is False


def test_get_debug(config_manager):
    config_manager.set_debug(True)
    assert config_manager.get_debug() is True


def default_test_get_appearance_mode(config_manager):
    assert config_manager.get_appearance_mode() == "Light"


def test_get_appearance_mode(config_manager):
    config_manager.set_appearance_mode("Dark")
    assert config_manager.get_appearance_mode() == "Dark"


def default_test_get_window_size(config_manager):
    assert config_manager.get_window_size() == (800, 600)


def test_get_window_size(config_manager):
    config_manager.set_window_size(1024, 768)
    assert config_manager.get_window_size() == (1024, 768)
