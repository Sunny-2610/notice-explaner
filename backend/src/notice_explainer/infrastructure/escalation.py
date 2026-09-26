"""Versioned escalation-rule loader + evaluator (LLD §2.5.1).

Reads backend/escalation_rules.yaml (hot-reloadable: call reload()).
Every evaluate() records rules_version for the audit log.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from ..domain import escalation as engine
from ..domain.models import EscalationResult, EscalationRule
from ..domain.types import EscalationStage

_DEFAULT_PATH = Path(__file__).resolve().parents[3] / "escalation_rules.yaml"


class YamlEscalationEvaluator:
    def __init__(self, path: str | Path = _DEFAULT_PATH) -> None:
        self.path = Path(path)
        self._version = 0
        self._rules: list[EscalationRule] = []
        self.reload()

    @property
    def version(self) -> int:
        return self._version

    def active_rules(self) -> list[EscalationRule]:
        return list(self._rules)

    def reload(self) -> None:
        data = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        self._version = int(data.get("version", 0))
        self._rules = [EscalationRule(id=r["id"], pattern=r["pattern"],
                                      severity=r.get("severity", "medium"),
                                      description=r.get("description", ""))
                       for r in data.get("rules", [])]

    def evaluate(self, text: str, stage: EscalationStage) -> EscalationResult:
        return engine.evaluate(text, stage, self._rules, self._version)
