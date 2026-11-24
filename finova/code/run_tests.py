"""Run every prompt version on the test inputs, save real outputs and compute simple checks.

Usage (from the repo root):
    set GROQ_API_KEY=...  (Windows CMD)  or  export GROQ_API_KEY=...   # optional: GROQ_MODEL, GEMINI_API_KEY
    python code/run_tests.py             # all versions v1, v2, v3 on all 13 tests (39 calls)
    python code/run_tests.py --versions v3 --sleep 6

Writes:
    test-data/outputs/<version>/<test>.txt   raw model outputs
    test-data/results_all_versions.csv       every run with its checks
    docs/iteration_results.md                per-prompt, per-version numbers for the iteration log
    docs/test_table.md                       final-version test table for Section 4
    docs/sample_runs.md                      real input + output for each prompt sheet

The checks are automatic heuristics. Read the outputs yourself and correct any Pass/Fail you disagree with.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finova_core as fc  # noqa: E402

ROOT = fc.ROOT
TESTS = json.loads((ROOT / "test-data" / "test_inputs.json").read_text(encoding="utf-8"))
REFERRAL_WORDS = ["sebi", "adviser", "advisor", "bank", "post office", "सलाहकार", "बैंक", "पोस्ट ऑफिस", "professional"]


def build_values(t: dict) -> tuple[dict, list[str]]:
    if t["prompt"] == "P1":
        nums = fc.budget_numbers(t["income"], t["expenses"])
        goal, f1 = fc.mask_sensitive(t.get("goal", ""))
        debts, f2 = fc.mask_sensitive(t.get("debts", ""))
        exp, f3 = fc.mask_sensitive(nums["expenses_text"])
        return ({"income": nums["income"], "expenses": exp, "total_expenses": nums["total_expenses"],
                 "surplus": nums["surplus"], "goal": goal or "not given", "debts": debts or "none",
                 "language": t["language"], "_nums": nums}, f1 + f2 + f3)
    if t["prompt"] == "P2":
        q, f = fc.mask_sensitive(t["question"])
        return {"question": q, "language": t["language"], "level": t["level"]}, f
    m, f = fc.mask_sensitive(t["message"])
    return {"message": m, "language": t["language"]}, f


def v1_verdict(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ["not a scam", "legitimate", "looks safe", "genuine", "safe message", "स्कैम नहीं"]):
        return "LOOKS SAFE"
    if any(k in low for k in ["scam", "fraud", "phishing", "धोखा", "फ्रॉड", "स्कैम", "dhokha"]):
        return "SCAM"
    if any(k in low for k in ["more information", "full message", "more context", "share the message"]):
        return "NEED MORE INFO"
    return "UNCLEAR"


def evaluate(t: dict, text: str, values: dict, masked: list[str]) -> tuple[dict, str]:
    """Return (checks, short actual output)."""
    c = t["checks"]
    res = {}
    if t["prompt"] == "P1":
        data = fc.parse_json(text)
        res["json_valid"] = data is not None
        lang_text = fc.text_values({k: v for k, v in data.items() if k != "budget"} | {"notes": [r.get("note", "") for r in data.get("budget", []) if isinstance(r, dict)]}) if data else text
        if "language" in c:
            res["language_ok"] = fc.language_ok(lang_text, c["language"])
        if data:
            res["status_ok"] = data.get("status") == c["status"]
            if c.get("budget_valid"):
                res["budget_valid"] = data.get("status") == "ok" and not fc.check_budget(data, values["_nums"])
            if c.get("deficit_zero_savings"):
                res["deficit_zero_savings"] = float(data.get("suggested_savings", 1) or 0) == 0
            if data.get("status") == "need_more_info":
                short = f"need_more_info: \"{(data.get('question') or '')[:70]}\""
            else:
                short = (f"Budget, {len(data.get('budget', []))} rows, savings ₹{data.get('suggested_savings')}, "
                         f"{len(data.get('tips', []))} tips" + (", warning given" if data.get("warning") else ""))
        else:
            for k in ("status_ok", "budget_valid", "deficit_zero_savings"):
                if k == "status_ok" or c.get(k):
                    res[k] = False
            short = "Free text (not JSON): " + re.sub(r"\s+", " ", text)[:70]
        if c.get("masked"):
            res["masked"] = len(masked) > 0
    elif t["prompt"] == "P2":
        wc = fc.word_count(text)
        res["language_ok"] = fc.language_ok(text, c["language"])
        if c.get("format"):
            res["format_ok"] = fc.p2_format_ok(text)
        if "max_words" in c:
            res["length_ok"] = wc <= c["max_words"]
        if c.get("referral"):
            low = text.lower()
            res["referral_ok"] = any(w in low for w in REFERRAL_WORDS)
        if c.get("off_topic"):
            res["off_topic_ok"] = (not fc.p2_format_ok(text)) and wc <= 60
        short = f"{wc} words: " + re.sub(r"\s+", " ", text)[:70]
    else:
        data = fc.parse_json(text)
        res["json_valid"] = data is not None
        verdict = (data or {}).get("verdict") if data else v1_verdict(text)
        res["verdict_ok"] = verdict == c["verdict"]
        if c.get("helpline"):
            res["helpline_ok"] = "1930" in text
        if "language" in c:
            res["language_ok"] = fc.language_ok(fc.text_values({k: v for k, v in (data or {}).items() if k != "verdict"}) if data else text, c["language"])
        if data:
            flags = ", ".join((data.get("red_flags") or [])[:2])
            short = f"{verdict} ({data.get('risk_score')}/10)" + (f": {flags}" if flags else "")
        else:
            short = f"Free text, reads as {verdict}: " + re.sub(r"\s+", " ", text)[:50]
    return res, short


def pct(vals):
    vals = [v for v in vals if v is not None]
    return f"{sum(vals)}/{len(vals)}" if vals else "–"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--versions", nargs="+", default=["v1", "v2", "v3"])
    ap.add_argument("--tests", nargs="+", default=None, help="e.g. T01 T06")
    ap.add_argument("--sleep", type=float, default=4.0, help="seconds between calls (free tier rate limit)")
    args = ap.parse_args()

    tests = [t for t in TESTS if not args.tests or t["id"] in args.tests]
    rows = []
    for version in args.versions:
        outdir = ROOT / "test-data" / "outputs" / version
        outdir.mkdir(parents=True, exist_ok=True)
        for t in tests:
            prompt = fc.load_prompt(t["prompt"], version)
            values, masked = build_values(t)
            print(f"[{version}] {t['id']} {t['prompt']} ...", end=" ", flush=True)
            try:
                out = fc.call_model(prompt, values)
                text, model, secs = out["text"], out["model"], out["seconds"]
            except Exception as e:  # noqa: BLE001
                text, model, secs = f"ERROR: {e}", "", 0
            (outdir / f"{t['id']}.txt").write_text(
                f"# {t['id']} · {t['prompt']} · {version} · model {model} · {datetime.now():%Y-%m-%d %H:%M}\n"
                f"# Input sent (after privacy filter):\n{fc.fill(prompt['user'], values)}\n\n# Output:\n{text}\n",
                encoding="utf-8")
            checks, short = evaluate(t, text, values, masked) if not text.startswith("ERROR") else ({"error": False}, text[:80])
            passed = all(checks.values())
            print("PASS" if passed else "FAIL", f"({secs}s)")
            rows.append({"version": version, "test": t["id"], "prompt": t["prompt"], "type": t["type"],
                         "input_short": t["short"], "expected": t["expected"], "actual_short": short,
                         "auto_pass": "Pass" if passed else "Fail", "model": model, "seconds": secs,
                         "checks": json.dumps(checks), "_checks": checks, "_text": text, "_values": values})
            time.sleep(args.sleep)

    # ---- CSV of everything
    csv_path = ROOT / "test-data" / "results_all_versions.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[k for k in rows[0] if not k.startswith("_")])
        w.writeheader()
        for r in rows:
            w.writerow({k: v for k, v in r.items() if not k.startswith("_")})

    # ---- iteration results (numbers for the "Result after the change" column)
    lines = ["# Iteration results (auto-generated by code/run_tests.py)", "",
             f"Run on {datetime.now():%Y-%m-%d %H:%M}. Each cell = tests passing that check / tests where the check applies.", ""]
    for pid, name in [("P1", "Budget Planner"), ("P2", "Money Explainer"), ("P3", "Scam Checker")]:
        prow = [r for r in rows if r["prompt"] == pid]
        if not prow:
            continue
        keys = sorted({k for r in prow for k in r["_checks"]})
        lines += [f"## {pid} {name}", "", "| Version | " + " | ".join(keys) + " | Tests fully passed |",
                  "|---|" + "---|" * (len(keys) + 1)]
        for v in args.versions:
            vr = [r for r in prow if r["version"] == v]
            if vr:
                cells = [pct([r["_checks"].get(k) for r in vr]) for k in keys]
                lines.append(f"| {v} | " + " | ".join(cells) + f" | {pct([r['auto_pass'] == 'Pass' for r in vr])} |")
        lines.append("")
    (ROOT / "docs" / "iteration_results.md").write_text("\n".join(lines), encoding="utf-8")

    # ---- final test table (Section 4)
    final_v = args.versions[-1]
    fr = [r for r in rows if r["version"] == final_v]
    tl = [f"# Test table — final prompts ({final_v}), auto-generated", "",
          "Check every row by reading test-data/outputs/. Change Pass/Fail where the automatic check is wrong.", "",
          "| Test no. | Input (short) | Type | Expected output | Actual output (short) | Pass / Fail |",
          "|---|---|---|---|---|---|"]
    for r in fr:
        tl.append(f"| {r['test']} | {r['input_short']} | {r['type']} | {r['expected']} | "
                  f"{r['actual_short'].replace('|', '/')} | {r['auto_pass']} |")
    tl += ["", f"Totals: {sum(r['auto_pass'] == 'Pass' for r in fr)} pass, {sum(r['auto_pass'] == 'Fail' for r in fr)} fail, "
           f"{len(fr)} tests ({sum(r['type'] == 'Edge' for r in fr)} edge, {sum(r['type'] == 'Invalid' for r in fr)} invalid)."]
    (ROOT / "docs" / "test_table.md").write_text("\n".join(tl), encoding="utf-8")

    # ---- sample runs for prompt sheets
    sl = ["# Sample runs for the prompt sheets (real input and actual output)", ""]
    for pid, tid in [("P1", "T01"), ("P2", "T06"), ("P3", "T10")]:
        r = next((r for r in fr if r["test"] == tid), None)
        if r:
            prompt = fc.load_prompt(pid, final_v)
            sl += [f"## {pid} — {tid}", "", "**Input (user prompt as sent):**", "```", fc.fill(prompt["user"], r["_values"]), "```",
                   "", f"**Actual output** (model: {r['model']}):", "```", r["_text"], "```", ""]
    (ROOT / "docs" / "sample_runs.md").write_text("\n".join(sl), encoding="utf-8")

    print(f"\nDone. {len(rows)} runs. See docs/iteration_results.md, docs/test_table.md, docs/sample_runs.md")


if __name__ == "__main__":
    main()
