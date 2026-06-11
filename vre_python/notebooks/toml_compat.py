#!/usr/bin/env python3

from __future__ import annotations

try:
    import tomllib as tomllib  # type: ignore[no-redef]
except ModuleNotFoundError:  # pragma: no cover
    try:
        import tomli as tomllib  # type: ignore[assignment,import-not-found]
    except ModuleNotFoundError:
        import types

        def _parse_simple_toml(text: str) -> dict[str, object]:
            payload: dict[str, object] = {}
            current = payload
            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("[") and line.endswith("]"):
                    table_name = line[1:-1].strip()
                    current = payload
                    for part in table_name.split("."):
                        current = current.setdefault(part, {})  # type: ignore[assignment]
                        if not isinstance(current, dict):
                            raise ValueError(f"invalid TOML table '{table_name}'")
                    continue
                key, separator, value = line.partition("=")
                if not separator:
                    continue
                key = key.strip()
                value = value.strip()
                if value.startswith('"') and value.endswith('"'):
                    parsed_value: object = value[1:-1]
                elif value.lower() in {"true", "false"}:
                    parsed_value = value.lower() == "true"
                else:
                    parsed_value = value
                current[key] = parsed_value
            return payload

        def _tomllib_load(handle) -> dict[str, object]:
            raw = handle.read()
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return _parse_simple_toml(raw)

        tomllib = types.ModuleType("tomllib")  # type: ignore[assignment]
        tomllib.load = _tomllib_load  # type: ignore[attr-defined]
        tomllib.loads = _parse_simple_toml  # type: ignore[attr-defined]
