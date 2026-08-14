from __future__ import annotations

from typing import Any

# Mirrors DBackup 3.2.0 SENSITIVE_KEYS, plus generic Authorization/API-key aliases.
_SECRET_KEYS = {
    "password", "token", "secret", "secretkey", "secretaccesskey", "accesskey",
    "accesskeyid", "apikey", "api_key", "webhookurl", "uri", "passphrase",
    "privatekey", "sshpassword", "sshprivatekey", "sshpassphrase", "clientsecret",
    "refreshtoken", "authheader", "accountsid", "authtoken", "apptoken",
    "bottoken", "accesstoken", "authorization",
}
_SECRET_KEYS_NORMALIZED = {key.replace("_", "").lower() for key in _SECRET_KEYS}


def contains_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.replace("_", "").lower() in _SECRET_KEYS_NORMALIZED or contains_secret_key(item):
                return True
    elif isinstance(value, list):
        return any(contains_secret_key(item) for item in value)
    return False


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        clean: dict[str, Any] = {}
        for key, item in value.items():
            normalized = key.replace("_", "").lower()
            if normalized in _SECRET_KEYS_NORMALIZED:
                continue
            clean[key] = sanitize(item)
        return clean
    if isinstance(value, list):
        return [sanitize(item) for item in value]
    return value
