"""Process-local model settings; loading settings never creates a client."""

from __future__ import annotations

import ipaddress
import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    base_url: str = field(default="https://api.openai.com/v1", repr=False)
    model: str = ""

    @property
    def is_local(self) -> bool:
        try:
            host = urlsplit(self.base_url).hostname or ""
            if host.lower() == "localhost":
                return True
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def configuration_error(self) -> str | None:
        """Validate only when natural-language execution is requested."""
        try:
            url = urlsplit(self.base_url)
            valid = bool(url.hostname) and url.scheme in {"http", "https"}
            valid = valid and not url.query and not url.fragment
            _ = url.port
        except ValueError:
            valid = False
        if not valid:
            return "Set OPENAI_BASE_URL to a valid OpenAI-compatible HTTP(S) API root."
        if url.scheme != "https" and not self.is_local:
            return "Use HTTPS for a hosted OPENAI_BASE_URL; HTTP is allowed for loopback endpoints."
        if not self.model.strip():
            return "Set OPENAI_MODEL in the process environment or the launch directory's .env."
        if not self.api_key.strip() and not self.is_local:
            return "Set OPENAI_API_KEY for this hosted endpoint, or configure an explicit loopback OPENAI_BASE_URL."
        return None

    def redact(self, text: str) -> str:
        """Remove configured credentials from persisted/displayed text."""
        secrets = [self.api_key]
        try:
            url = urlsplit(self.base_url)
            if url.username or url.password:
                secrets.extend([self.base_url, url.netloc, url.username or "", url.password or ""])
                secrets.extend(unquote(value) for value in list(secrets) if value)
        except ValueError:
            pass
        for value in sorted(set(secrets), key=len, reverse=True):
            if value:
                text = text.replace(value, "[redacted]")
        return text


def load_settings(env_file: Path | None = None) -> Settings:
    """Read exactly one .env, without searching parents or altering os.environ.

    Interpolation is disabled so neither parent files nor implicit environment
    interpolation can change the explicit blank-value precedence contract.
    """
    path = Path(env_file) if env_file is not None else Path.cwd() / ".env"
    values = dotenv_values(path, interpolate=False) if path.is_file() else {}

    def value(name: str, default: str = "") -> str:
        if name in os.environ:
            return os.environ[name]
        return values.get(name) or default

    # An explicitly blank URL is retained and diagnosed, not silently replaced.
    base_url = value("OPENAI_BASE_URL") if "OPENAI_BASE_URL" in os.environ or "OPENAI_BASE_URL" in values else "https://api.openai.com/v1"
    return Settings(api_key=value("OPENAI_API_KEY"), base_url=base_url, model=value("OPENAI_MODEL"))