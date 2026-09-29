"""Configuration tests require no model or network."""

import os

import pytest

from chat_crystal_forge.config import Settings, load_settings


@pytest.fixture(autouse=True)
def clean_model_env(monkeypatch):
    for key in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL"):
        monkeypatch.delenv(key, raising=False)


def test_explicit_file_precedence_and_no_environment_mutation(tmp_path, monkeypatch):
    env = tmp_path / "custom.env"
    env.write_text("OPENAI_API_KEY=file-secret\nOPENAI_MODEL=file-model\nOPENAI_BASE_URL=http://localhost:8000/v1\n")
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.setenv("OPENAI_MODEL", "process-model")
    before = dict(os.environ)
    settings = load_settings(env)
    assert settings.api_key == ""
    assert settings.model == "process-model"
    assert settings.base_url == "http://localhost:8000/v1"
    assert settings.configuration_error() is None
    assert dict(os.environ) == before


def test_only_cwd_dotenv_not_parents(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("OPENAI_API_KEY=parent-secret\nOPENAI_MODEL=parent\n")
    child = tmp_path / "child"
    child.mkdir()
    monkeypatch.chdir(child)
    assert load_settings().model == ""
    (child / ".env").write_text("OPENAI_MODEL=child\n")
    assert load_settings().model == "child"
    assert load_settings().api_key == ""


def test_explicit_missing_file_does_not_fall_back(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text("OPENAI_MODEL=unwanted\n")
    assert load_settings(tmp_path / "absent.env").model == ""


def test_repr_and_redaction_hide_key_and_url_credentials():
    settings = Settings(api_key="key-secret", base_url="https://alice:pass%40word@example.com/v1", model="test")
    assert "key-secret" not in repr(settings)
    assert "alice" not in repr(settings)
    cleaned = settings.redact("key-secret alice pass%40word pass@word " + settings.base_url)
    assert all(secret not in cleaned for secret in ("key-secret", "alice", "pass%40word", "pass@word"))


def test_hosted_missing_key_is_actionable():
    assert "OPENAI_API_KEY" in Settings(model="test").configuration_error()
    assert "OPENAI_MODEL" in Settings(api_key="present").configuration_error()
    assert Settings(api_key="present", model="test").configuration_error() is None


@pytest.mark.parametrize("url", ["http://localhost:1234/v1", "http://127.0.0.1:8000/v1", "http://[::1]:8000/v1"])
def test_explicit_loopback_does_not_need_auth(url):
    assert Settings(base_url=url, model="test").configuration_error() is None


@pytest.mark.parametrize("url", ["", "file:///tmp/model", "http://host.example/v1", "https://example.com:bad/v1"])
def test_invalid_or_insecure_endpoint(url):
    assert Settings(base_url=url, model="test").configuration_error()


def test_blank_url_and_model_override_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("OPENAI_MODEL=file-model\nOPENAI_BASE_URL=https://example.com/v1\n")
    monkeypatch.setenv("OPENAI_MODEL", "")
    monkeypatch.setenv("OPENAI_BASE_URL", "")
    settings = load_settings(env)
    assert settings.model == settings.base_url == ""


def test_interpolation_is_not_implicit(tmp_path, monkeypatch):
    monkeypatch.setenv("OTHER_SECRET", "must-not-expand")
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=${OTHER_SECRET}\n")
    assert load_settings(env).api_key == "${OTHER_SECRET}"