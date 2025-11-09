"""Configuration loading utilities for the Weekend Planner application."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

try:  # pragma: no cover - optional dependency
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback when python-dotenv is absent
    def load_dotenv() -> bool:  # type: ignore[return-type]
        return False


@dataclass
class ConnectorSettings:
    base_url: str
    page_size: int | None = None
    timeout_seconds: int = 5
    retries: int = 2


@dataclass
class AppSettings:
    currency: str = "EUR"
    locale: str = "en_GB"
    price_drop_days_threshold: int = 5
    price_drop_low_inventory_bonus: float = 0.25
    price_drop_high_inventory_penalty: float = -0.1
    cache_dir: str = "~/.weekend-planner/cache"


@dataclass
class FXSettings:
    base_url: str
    base_currency: str
    fallback_rates: Dict[str, float] = field(default_factory=dict)


@dataclass
class Settings:
    app: AppSettings
    connectors: Dict[str, ConnectorSettings]
    fx: FXSettings

    def connector(self, name: str) -> ConnectorSettings:
        return self.connectors[name]


def _expand_path(path: str) -> str:
    return str(Path(path).expanduser())


def _parse_value(value: str):
    value = value.strip()
    if value in {"", "null", "~"}:
        return None
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value.strip('"')


def _load_simple_yaml(path: Path) -> Dict:
    root: Dict[str, any] = {}
    stack: list[tuple[int, Dict]] = [(-1, root)]

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line:
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        key, _, value_part = line.partition(":")
        key = key.strip()
        value_part = value_part.strip()

        while stack and indent <= stack[-1][0]:
            stack.pop()

        current_dict = stack[-1][1]
        if value_part == "":
            new_dict: Dict[str, any] = {}
            current_dict[key] = new_dict
            stack.append((indent, new_dict))
        else:
            current_dict[key] = _parse_value(value_part)
    return root


def load_settings(settings_path: str | Path | None = None) -> Settings:
    """Load settings from YAML and environment overlays."""
    load_dotenv()
    if settings_path is None:
        settings_path = Path(__file__).with_name("settings.yaml")
    else:
        settings_path = Path(settings_path)

    raw_settings = _load_simple_yaml(settings_path)

    app_section = raw_settings.get("app", {})
    connectors_section = raw_settings.get("connectors", {})
    fx_section = raw_settings.get("fx", {})

    app_settings = AppSettings(**app_section)

    connectors: Dict[str, ConnectorSettings] = {}
    for name, cfg in connectors_section.items():
        connectors[name] = ConnectorSettings(**cfg)

    fx_settings = FXSettings(**fx_section)

    settings = Settings(app=app_settings, connectors=connectors, fx=fx_settings)

    vendor_a = os.getenv("VENDOR_A_TOKEN")
    vendor_b = os.getenv("VENDOR_B_TOKEN")
    dining_token = os.getenv("DINING_TOKEN")

    if vendor_a and "ticket_vendor_a" in connectors:
        connectors["ticket_vendor_a"].base_url = _inject_token(
            connectors["ticket_vendor_a"].base_url, vendor_a
        )
    if vendor_b and "ticket_vendor_b" in connectors:
        connectors["ticket_vendor_b"].base_url = _inject_token(
            connectors["ticket_vendor_b"].base_url, vendor_b
        )
    if dining_token and "dining" in connectors:
        connectors["dining"].base_url = _inject_token(
            connectors["dining"].base_url, dining_token
        )

    settings.app.cache_dir = _expand_path(settings.app.cache_dir)

    return settings


def _inject_token(url: str, token: str) -> str:
    if "{token}" in url:
        return url.format(token=token)
    if "token=" in url:
        return url
    joiner = "&" if "?" in url else "?"
    return f"{url}{joiner}token={token}"
