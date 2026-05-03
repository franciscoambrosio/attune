#!/usr/bin/env python3
"""
Attune evaluation — 25 mock emails, ground-truth labels, measure accuracy.

Run from the attune project root:
  python eval/run_eval.py
"""

import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Run from project root so config/goals.yaml resolves
ROOT = Path(__file__).parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from attune.connectors.mock import mock_emails, mock_calendar_context
from attune.agent.judge import TriageAgent
from attune.models.email import TriageLabel

# ─────────────────────────────────────────────────────────────────────────────
# GROUND TRUTH
# ─────────────────────────────────────────────────────────────────────────────

EXPECTED = {
    # URGENT — action required, delay has immediate cost
    "mock-001": "URGENT",   # Supervisor: Chapter 3 revise before Thursday or lose committee slot
    "mock-002": "URGENT",   # Veni grant portal closes in 48 hours, status: draft not submitted

    # SOON — action needed today or tomorrow
    "mock-003": "SOON",     # Postdoc: need reply by Friday, competitive position
    "mock-004": "SOON",     # Prof. Kim: question on methods, committee Friday
    "mock-005": "SOON",     # ICML deadline in 5 days
    "mock-006": "SOON",     # Defense confirmed, need to reply + thesis due June 28
    "mock-007": "SOON",     # JMLR review: accept/decline within 3 days

    # LATER — worth reading this week, no immediate pressure
    "mock-008": "LATER",    # Jamie: side project idea, no deadline
    "mock-009": "LATER",    # Library books due in 5 days (easy renewal)
    "mock-010": "LATER",    # Lab social Friday
    "mock-011": "LATER",    # Bengio lecture next Tuesday
    "mock-012": "LATER",    # NeurIPS 2026 abstract opens May 15
    "mock-013": "LATER",    # Anna: collaboration catchup, 2 weeks
    "mock-014": "LATER",    # VPN maintenance Sunday
    "mock-015": "LATER",    # ResearchGate: 3 new citations
    "mock-016": "LATER",    # Travel grant, May 31 deadline

    # IGNORE — noise, no action needed
    "mock-017": "IGNORE",   # Medium digest
    "mock-018": "IGNORE",   # Dependabot bump
    "mock-019": "IGNORE",   # LinkedIn profile views
    "mock-020": "IGNORE",   # Overleaf renewal in 30 days
    "mock-021": "IGNORE",   # arXiv mailing list
    "mock-022": "IGNORE",   # Canteen menu
    "mock-023": "IGNORE",   # Slack AI promo
    "mock-024": "IGNORE",   # Google Scholar citation alert
    "mock-025": "IGNORE",   # Zoom recording available
}


# ─────────────────────────────────────────────────────────────────────────────
# RUN
# ─────────────────────────────────────────────────────────────────────────────

def run_eval():
    print("\n" + "=" * 65)
    print("Attune Evaluation — 25 mock emails")
    print("=" * 65)

    emails  = mock_emails()
    context = mock_calendar_context()
    agent   = TriageAgent()

    results = []
    labels  = ["URGENT", "SOON", "LATER", "IGNORE"]

    print(f"\n  {'#':<4}  {'Subject':<42}  {'Expected':<8}  {'Got':<8}  OK?")
    print(f"  {'─'*4}  {'─'*42}  {'─'*8}  {'─'*8}  {'─'*3}")

    icons = {"URGENT": "🔴", "SOON": "🟡", "LATER": "🔵", "IGNORE": "⚪"}

    for i, email in enumerate(emails, 1):
        expected = EXPECTED[email.id]
        try:
            result  = agent.triage(email, context)
            got     = result.label.value
            reasoning = result.reasoning
        except Exception as e:
            got       = "ERROR"
            reasoning = str(e)

        match  = got == expected
        marker = "✓" if match else "✗"
        short  = email.subject[:42] if len(email.subject) <= 42 else email.subject[:39] + "..."

        print(f"  {i:<4}  {short:<42}  {icons[expected]} {expected:<6}  {icons.get(got, '?')} {got:<6}  {marker}")

        results.append({
            "id":        email.id,
            "subject":   email.subject,
            "expected":  expected,
            "predicted": got,
            "correct":   match,
            "reasoning": reasoning,
        })

        # Respect Groq free-tier rate limit
        time.sleep(0.5)

    # ── Summary ──────────────────────────────────────────────────────────────

    correct = sum(r["correct"] for r in results)
    total   = len(results)
    accuracy = correct / total

    print(f"\n  Overall accuracy: {correct}/{total}  ({accuracy:.0%})")

    # Per-label breakdown
    print(f"\n  {'Label':<8}  {'Expected':>8}  {'Correct':>7}  {'Precision':>9}  {'Recall':>7}")
    print(f"  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*9}  {'─'*7}")

    for label in labels:
        n_expected  = sum(1 for r in results if r["expected"]  == label)
        n_predicted = sum(1 for r in results if r["predicted"] == label)
        n_correct   = sum(1 for r in results if r["expected"] == label and r["predicted"] == label)

        precision = n_correct / n_predicted if n_predicted > 0 else 0.0
        recall    = n_correct / n_expected  if n_expected  > 0 else 0.0

        print(f"  {label:<8}  {n_expected:>8}  {n_correct:>7}  {precision:>9.0%}  {recall:>7.0%}")

    # Failures
    failures = [r for r in results if not r["correct"]]
    if failures:
        print(f"\n  Misclassifications ({len(failures)}):")
        for f in failures:
            short = f["subject"][:50]
            print(f"    ✗ [{f['id']}] {short}")
            print(f"       expected {f['expected']} → got {f['predicted']}")
            print(f"       reason: {f['reasoning']}")
    else:
        print(f"\n  ✓ Perfect score — no misclassifications")

    # ── Save results ─────────────────────────────────────────────────────────

    output = {
        "timestamp":       datetime.now().isoformat(),
        "model":           os.getenv("LLM_PROVIDER", "groq"),
        "total":           total,
        "correct":         correct,
        "accuracy":        round(accuracy, 4),
        "per_label":       {},
        "emails":          results,
    }

    for label in labels:
        n_exp   = sum(1 for r in results if r["expected"]  == label)
        n_pred  = sum(1 for r in results if r["predicted"] == label)
        n_corr  = sum(1 for r in results if r["expected"] == label and r["predicted"] == label)
        output["per_label"][label] = {
            "expected":  n_exp,
            "correct":   n_corr,
            "precision": round(n_corr / n_pred, 4) if n_pred > 0 else 0.0,
            "recall":    round(n_corr / n_exp,  4) if n_exp  > 0 else 0.0,
        }

    out_path = Path("eval/results.json")
    out_path.write_text(json.dumps(output, indent=2))
    print(f"\n  Results saved to {out_path}")
    print("=" * 65)

    return output


if __name__ == "__main__":
    run_eval()
