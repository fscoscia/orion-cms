import pytest
from django.core.exceptions import ImproperlyConfigured

from orion.settings.env import (
    env_bool,
    env_int,
    env_list,
    env_str,
    load_env_file,
)


class TestEnvStr:
    def test_returns_value_without_surrounding_whitespace(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_VALUE", "  hello  ")
        assert env_str("ORION_TEST_VALUE") == "hello"

    def test_returns_default_when_absent(self, monkeypatch):
        monkeypatch.delenv("ORION_TEST_VALUE", raising=False)
        assert env_str("ORION_TEST_VALUE", "fallback") == "fallback"

    def test_returns_default_when_present_and_empty(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_VALUE", "")
        assert env_str("ORION_TEST_VALUE", "fallback") == "fallback"


class TestEnvBool:
    @pytest.mark.parametrize("raw_value", ["1", "true", "TRUE", "yes", "on"])
    def test_accepts_true_values(self, monkeypatch, raw_value):
        monkeypatch.setenv("ORION_TEST_FLAG", raw_value)
        assert env_bool("ORION_TEST_FLAG") is True

    @pytest.mark.parametrize("raw_value", ["0", "false", "False", "no", "off"])
    def test_accepts_false_values(self, monkeypatch, raw_value):
        monkeypatch.setenv("ORION_TEST_FLAG", raw_value)
        assert env_bool("ORION_TEST_FLAG", default=True) is False

    def test_uses_default_when_absent_or_empty(self, monkeypatch):
        monkeypatch.delenv("ORION_TEST_FLAG", raising=False)
        assert env_bool("ORION_TEST_FLAG", default=True) is True
        monkeypatch.setenv("ORION_TEST_FLAG", "")
        assert env_bool("ORION_TEST_FLAG") is False

    def test_rejects_unrecognised_values(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_FLAG", "ture")
        with pytest.raises(ImproperlyConfigured, match="ORION_TEST_FLAG"):
            env_bool("ORION_TEST_FLAG")


class TestEnvInt:
    def test_parses_integers(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_NUMBER", "465")
        assert env_int("ORION_TEST_NUMBER", 25) == 465

    def test_uses_default_when_absent(self, monkeypatch):
        monkeypatch.delenv("ORION_TEST_NUMBER", raising=False)
        assert env_int("ORION_TEST_NUMBER", 25) == 25

    def test_rejects_non_numeric_values(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_NUMBER", "abc")
        with pytest.raises(ImproperlyConfigured, match="ORION_TEST_NUMBER"):
            env_int("ORION_TEST_NUMBER", 25)


class TestEnvList:
    def test_splits_and_trims_items(self, monkeypatch):
        monkeypatch.setenv("ORION_TEST_LIST", "example.com, www.example.com ,,")
        assert env_list("ORION_TEST_LIST") == ["example.com", "www.example.com"]

    def test_returns_copy_of_default_when_absent(self, monkeypatch):
        monkeypatch.delenv("ORION_TEST_LIST", raising=False)
        default_hosts = ["localhost"]
        hosts = env_list("ORION_TEST_LIST", default_hosts)
        assert hosts == ["localhost"]
        assert hosts is not default_hosts


class TestLoadEnvFile:
    @pytest.fixture
    def env_file(self, tmp_path, monkeypatch):
        # Registers the variable so that monkeypatch removes it afterwards.
        monkeypatch.setenv("ORION_TEST_VALUE", "")
        monkeypatch.delenv("ORION_TEST_VALUE")
        return tmp_path / ".env"

    def test_loads_a_variable_only_in_the_file(self, env_file):
        env_file.write_text("ORION_TEST_VALUE=from-file\n")

        load_env_file(env_file)

        assert env_str("ORION_TEST_VALUE") == "from-file"

    def test_environment_wins_over_the_file(self, env_file, monkeypatch):
        env_file.write_text("ORION_TEST_VALUE=from-file\n")
        monkeypatch.setenv("ORION_TEST_VALUE", "from-environment")

        load_env_file(env_file)

        assert env_str("ORION_TEST_VALUE") == "from-environment"

    def test_missing_file_is_not_an_error(self, env_file):
        load_env_file(env_file)

        assert env_str("ORION_TEST_VALUE") == ""

    def test_keeps_special_characters(self, env_file):
        secret = "a#b$c(d)=e${HOME}%f"
        env_file.write_text(f"ORION_TEST_VALUE={secret}\n")

        load_env_file(env_file)

        assert env_str("ORION_TEST_VALUE") == secret
