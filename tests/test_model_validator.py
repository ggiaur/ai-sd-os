"""Tests for sdk/model_validator.py — never call the real Anthropic API here."""

import sys
import types

from sdk.model_validator import validate_models


class _FakeModels:
    def __init__(self, valid_ids):
        self.valid_ids = valid_ids

    def retrieve(self, model_id):
        if model_id not in self.valid_ids:
            raise Exception(f"model not found: {model_id}")
        return {"id": model_id}


class _FakeAnthropicClient:
    def __init__(self, api_key=None, valid_ids=None):
        self.models = _FakeModels(valid_ids or set())


def _install_fake_anthropic_module(monkeypatch, valid_ids):
    fake_module = types.ModuleType("anthropic")
    fake_module.Anthropic = lambda api_key=None: _FakeAnthropicClient(api_key, valid_ids)
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)


def test_validate_models_reports_available_models_as_true(monkeypatch):
    _install_fake_anthropic_module(monkeypatch, valid_ids={"claude-haiku-4-5-20251001"})

    result = validate_models("fake-key", {"light_model": "claude-haiku-4-5-20251001"})

    assert result == {"light_model": True}


def test_validate_models_reports_deprecated_model_as_false(monkeypatch):
    _install_fake_anthropic_module(monkeypatch, valid_ids={"claude-haiku-4-5-20251001"})

    result = validate_models("fake-key", {"ai_model": "claude-sonnet-2-nonexistent"})

    assert result == {"ai_model": False}


def test_validate_models_checks_each_model_independently(monkeypatch):
    _install_fake_anthropic_module(monkeypatch, valid_ids={"claude-haiku-4-5-20251001"})

    result = validate_models("fake-key", {
        "light_model": "claude-haiku-4-5-20251001",
        "ai_model": "claude-does-not-exist",
    })

    assert result == {"light_model": True, "ai_model": False}


def test_validate_models_never_raises_when_client_init_fails(monkeypatch):
    fake_module = types.ModuleType("anthropic")

    def _boom(api_key=None):
        raise RuntimeError("network unreachable")

    fake_module.Anthropic = _boom
    monkeypatch.setitem(sys.modules, "anthropic", fake_module)

    # Must not raise — validation-infrastructure failure must not block startup.
    result = validate_models("fake-key", {"ai_model": "claude-sonnet-4-6"})
    assert result == {"ai_model": True}
