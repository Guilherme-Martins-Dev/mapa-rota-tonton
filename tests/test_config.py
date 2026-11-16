import pytest

from tonton import config


def test_tomtom_key_lida_do_ambiente(monkeypatch):
    monkeypatch.setenv("TOMTOM_KEY", "abc123")
    assert config.tomtom_key() == "abc123"


def test_tomtom_key_ausente_levanta_erro(monkeypatch):
    monkeypatch.delenv("TOMTOM_KEY", raising=False)
    with pytest.raises(RuntimeError, match="TOMTOM_KEY"):
        config.tomtom_key()
