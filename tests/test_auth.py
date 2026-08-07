from pathlib import Path
import threading

import pytest

from openlp_vault import auth


def test_has_reusable_token_returns_false_when_file_is_missing(tmp_path, monkeypatch):
    credentials = type("Credentials", (), {})
    monkeypatch.setattr(auth, "Credentials", credentials)

    assert not auth.has_reusable_token(tmp_path / "missing.json")


def test_has_reusable_token_accepts_refreshable_credentials(tmp_path, monkeypatch):
    token_path = tmp_path / "token.json"
    token_path.write_text("{}")

    saved_credentials = type("SavedCredentials", (), {"valid": False, "refresh_token": "refresh-token"})()

    class FakeCredentials:
        
        def from_authorized_user_file(path, scopes):
            assert path == str(token_path)
            assert scopes == auth.SCOPES
            return saved_credentials

    monkeypatch.setattr(auth, "Credentials", FakeCredentials)

    assert auth.has_reusable_token(token_path)


def test_has_reusable_token_rejects_invalid_token_file(tmp_path, monkeypatch):
    token_path = tmp_path / "token.json"
    token_path.write_text("invalid")

    class FakeCredentials:
        
        def from_authorized_user_file(path, scopes):
            raise ValueError("invalid token")

    monkeypatch.setattr(auth, "Credentials", FakeCredentials)

    assert not auth.has_reusable_token(token_path)


def test_default_token_path_uses_application_directory():
    assert auth.default_token_path() == Path.home() / ".openlp-vault" / "token.json"


def test_cancelled_oauth_does_not_write_token(tmp_path, monkeypatch):
    credentials_path = tmp_path / "credentials.json"
    credentials_path.write_text("{}")
    token_path = tmp_path / "token.json"
    cancel_event = threading.Event()
    returned_credentials = type("Credentials", (), {"to_json": lambda self: "{}"})()

    class FakeFlow:
        
        def from_client_secrets_file(path, scopes):
            assert path == str(credentials_path)
            assert scopes == auth.SCOPES
            return FakeFlow()

        def run_local_server(self, port, timeout_seconds):
            assert port == 0
            assert timeout_seconds == 120
            cancel_event.set()
            return returned_credentials

    monkeypatch.setattr(auth, "InstalledAppFlow", FakeFlow)

    with pytest.raises(auth.AuthenticationCancelledError):
        auth.authenticate(
            client_secrets_file=credentials_path,
            token_path=token_path,
            oauth_timeout_seconds=120,
            cancel_event=cancel_event,
        )

    assert not token_path.exists()
