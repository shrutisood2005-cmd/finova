# Changelog

All changes since Milestone 1. Dates are YYYY-MM-DD. Add a line for every change you make.

## 2026-11-22
- Split the single Milestone 1 baseline prompt into three focused prompts: P1 Budget Planner, P2 Money Concept Explainer, P3 Scam Message Checker.
- Saved prompt versions v1, v2, v3 for each prompt in `prompts/v1`, `prompts/v2`, `prompts/v3`; final prompts in `prompts/final`. P1 v1 is the Milestone 1 baseline prompt, unchanged.
- P1: added a JSON output schema and language rule (v2); moved all arithmetic into Python, added deficit and no-loan rules, 1 worked example and temperature 0.2 (v3).
- P2: added role, reading levels, language/script rules and a 4-part emoji format (v2); added 2 few-shot examples, safety and off-topic rules, temperature 0.3 (v3).
- P3: added red-flag checklist, verdict labels and JSON schema (v2); added prompt-injection defence, 1930 helpline rule, 2 few-shot examples, temperature 0.1 (v3).
- Built the Streamlit prototype (`code/app.py`) with a privacy filter that hides OTP, account, card and Aadhaar-like numbers before calling the model.
- Added 13 test inputs (6 normal, 4 edge, 3 invalid) and an automatic test runner (`code/run_tests.py`).
- Added README, diagrams and prompt sheets.
