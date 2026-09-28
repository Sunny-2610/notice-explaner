"""JSON-backed free legal-aid directory (no user data stored).

Reads backend/data/legal_aid.json. Only the two seeded national entries exist
until a maintainer populates 'states' from official SLSA/DLSA sources.
"""
from __future__ import annotations

import json
from pathlib import Path

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "data" / "legal_aid.json"


class JsonLegalAidDirectory:
    def __init__(self, path: str | Path = _DEFAULT_PATH) -> None:
        self.path = Path(path)
        with self.path.open(encoding="utf-8") as fh:
            self._data = json.load(fh)

    def national(self) -> list[dict]:
        return [dict(e) for e in self._data.get("national", [])]

    def states(self) -> list[dict]:
        states = self._data.get("states", {}) or {}
        return [
            {"code": code, "name": info.get("name", code)}
            for code, info in states.items()
        ]

    def lookup(
        self, state: str | None = None, district: str | None = None
    ) -> dict:
        """National entries plus any matching state/district entries.

        Unknown state/district falls back to national only.
        """
        matches: list[dict] = []
        if state:
            states = self._data.get("states", {}) or {}
            hit = None
            for code, info in states.items():
                if code.lower() == state.lower():
                    hit = info
                    break
            if hit is not None:
                slsa = hit.get("slsa") or {}
                if slsa:
                    matches.append(dict(slsa))
                districts = hit.get("districts", {}) or {}
                if district:
                    for name, info in districts.items():
                        if name.lower() == district.lower():
                            dlsa = (info or {}).get("dlsa") or {}
                            if dlsa:
                                matches.append(dict(dlsa))
                            break
        return {"national": self.national(), "entries": matches}
