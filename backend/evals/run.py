"""Safety eval harness: escalation recall + grounding accuracy (offline).

Offline mode (default) runs the REAL YamlEscalationEvaluator and
domain/grounding over synthetic cases — no network, no keys. Prints a
markdown table, writes evals/report.md, exits non-zero when escalation
recall < 1.0 or grounding accuracy < 0.9.

--live mode additionally runs the real Gemini classifier on `text`
(requires GEMINI_API_KEY). Never run live in CI.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

CASES_DIR = Path(__file__).parent / "cases"
REPORT_PATH = Path(__file__).parent / "report.md"

WIRE_TO_ATTR = {
    "issuingAuthority": "issuing_authority",
    "deadlineDate": "deadline_date",
    "amountOwed": "amount_owed",
    "citedSection": "cited_section",
    "requiredAction": "required_action",
}


def load_cases(cases_dir: Path = CASES_DIR) -> list[dict]:
    cases: list[dict] = []
    for path in sorted(cases_dir.glob("*.yaml")):
        with path.open(encoding="utf-8") as fh:
            for case in yaml.safe_load(fh) or []:
                case["_file"] = path.name
                cases.append(case)
    return cases


def evaluate_offline(cases: list[dict] | None = None) -> dict:
    from notice_explainer.domain.grounding import ground_fields
    from notice_explainer.domain.models import ExtractedFields
    from notice_explainer.domain.types import EscalationStage
    from notice_explainer.infrastructure.escalation import YamlEscalationEvaluator

    if cases is None:
        cases = load_cases()
    evaluator = YamlEscalationEvaluator()

    tp = fp = tn = fn = 0
    ground_ok = ground_total = 0
    rows: list[dict] = []
    for case in cases:
        text = case.get("text", "")
        must = bool(case.get("must_escalate", False))
        pred = evaluator.evaluate(text, EscalationStage.PRE_EXPLANATION).escalate
        if must and pred:
            tp += 1
        elif must and not pred:
            fn += 1
        elif not must and pred:
            fp += 1
        else:
            tn += 1

        llm = case.get("llm_fields") or {}
        expected = case.get("expected_grounded") or {}
        kwargs = {
            attr: llm.get(wire) for wire, attr in WIRE_TO_ATTR.items()
        }
        fields = ExtractedFields(**kwargs)
        grounded = ground_fields(fields, text)
        field_ok = 0
        field_total = 0
        for wire, want in expected.items():
            got = grounded.field_confidence.get(wire, 0.0) >= 0.75
            field_total += 1
            ground_total += 1
            if got == bool(want):
                field_ok += 1
                ground_ok += 1
        rows.append({
            "id": case.get("id"),
            "lang": case.get("lang"),
            "must_escalate": must,
            "pred_escalate": pred,
            "esc_ok": (must == pred),
            "ground": f"{field_ok}/{field_total}",
        })

    recall = tp / (tp + fn) if (tp + fn) else 1.0
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    accuracy = ground_ok / ground_total if ground_total else 1.0
    return {
        "cases": len(cases),
        "tp": tp, "fp": fp, "tn": tn, "fn": fn,
        "recall": recall, "precision": precision,
        "ground_ok": ground_ok, "ground_total": ground_total,
        "accuracy": accuracy,
        "rows": rows,
    }


def render_markdown(metrics: dict, live: dict | None = None) -> str:
    lines = [
        "# Safety eval report (offline)",
        "",
        f"Cases: {metrics['cases']} | "
        f"Escalation recall: {metrics['recall']:.3f} "
        f"(TP {metrics['tp']}, FN {metrics['fn']}) | "
        f"precision: {metrics['precision']:.3f} "
        f"(FP {metrics['fp']}) | "
        f"Grounding accuracy: {metrics['accuracy']:.3f} "
        f"({metrics['ground_ok']}/{metrics['ground_total']})",
        "",
    ]
    if live is not None:
        lines += [
            f"Live classifier type accuracy: {live['accuracy']:.3f} "
            f"({live['ok']}/{live['total']})",
            "",
        ]
    lines += [
        "| id | lang | must_esc | pred_esc | esc_ok | ground |",
        "|---|---|---|---|---|---|",
    ]
    for r in metrics["rows"]:
        lines.append(
            f"| {r['id']} | {r['lang']} | {r['must_escalate']} | "
            f"{r['pred_escalate']} | {r['esc_ok']} | {r['ground']} |"
        )
    lines.append("")
    return "\n".join(lines)


def run_live(cases: list[dict]) -> dict:
    if not os.getenv("GEMINI_API_KEY"):
        raise RuntimeError("--live needs GEMINI_API_KEY")
    from notice_explainer.infrastructure.gemini import GeminiReasoner

    reasoner = GeminiReasoner()
    ok = 0
    for case in cases:
        pred = reasoner.classify(case.get("text", "")).document_type.value
        if pred == case.get("expected_type"):
            ok += 1
    return {"ok": ok, "total": len(cases), "accuracy": ok / len(cases) if cases else 1.0}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline safety eval")
    parser.add_argument("--live", action="store_true",
                        help="also run the real Gemini classifier (needs key)")
    args = parser.parse_args(argv)

    cases = load_cases()
    metrics = evaluate_offline(cases)
    live = run_live(cases) if args.live else None
    report = render_markdown(metrics, live)
    print(report)
    REPORT_PATH.write_text(report, encoding="utf-8")
    if metrics["recall"] < 1.0 or metrics["accuracy"] < 0.9:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
