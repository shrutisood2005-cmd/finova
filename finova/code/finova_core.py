"""Finova core: prompt loading, privacy filter, budget maths, Gemini calls and output checks.

Shared by app.py (the Streamlit prototype) and run_tests.py (the test runner).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"

PROMPT_FILES = {
    "P1": "P1_budget_planner.txt",
    "P2": "P2_money_explainer.txt",
    "P3": "P3_scam_checker.txt",
}

# Models tried in order. Set GEMINI_MODEL (Streamlit secret or env var) to force one.
DEFAULT_MODELS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-flash-lite-latest"]


# ---------------------------------------------------------------- prompts
def load_prompt(prompt_id: str, version: str = "final") -> dict:
    """Read prompts/<version>/<file> and split it into settings, system and user parts."""
    path = PROMPTS_DIR / version / PROMPT_FILES[prompt_id]
    sections, current = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("### "):
            current = line[4:].strip().upper()
            sections[current] = []
        elif current:
            sections[current].append(line)
    settings = {}
    for line in sections.get("SETTINGS", []):
        if ":" in line:
            k, v = line.split(":", 1)
            settings[k.strip()] = v.strip()
    system = "\n".join(sections.get("SYSTEM", [])).strip()
    temp = settings.get("temperature", "default")
    return {
        "id": prompt_id,
        "version": version,
        "system": None if system.lower() == "none" else system,
        "user": "\n".join(sections.get("USER", [])).strip(),
        "temperature": None if temp == "default" else float(temp),
        "json": settings.get("output", "text") == "json",
        "path": str(path.relative_to(ROOT)),
    }


def fill(template: str | None, values: dict) -> str | None:
    """Replace {name} only for names we know, so JSON braces in prompts are left alone."""
    if template is None:
        return None
    return re.sub(
        r"\{(\w+)\}",
        lambda m: str(values[m.group(1)]) if m.group(1) in values else m.group(0),
        template,
    )


# ---------------------------------------------------------- privacy filter
_PATTERNS = [
    ("OTP/PIN/CVV", re.compile(r"(?i)\b(otp|pin|cvv|password|passcode|mpin)\b(\W{0,3}\w{0,6}\W{0,3})(\d{3,8})\b")),
    ("card number", re.compile(r"\b(?:\d[ -]?){15,18}\d\b")),
    ("Aadhaar-like number", re.compile(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b")),
    ("account/phone number", re.compile(r"\b\d{9,18}\b")),
]


def mask_sensitive(text: str) -> tuple[str, list[str]]:
    """Hide OTPs, card, Aadhaar-like and long account/phone numbers before text goes to the model."""
    found = []
    if not text:
        return text, found
    for label, pat in _PATTERNS:
        def _sub(m, label=label):
            found.append(label)
            if label == "OTP/PIN/CVV":
                return f"{m.group(1)}{m.group(2)}[hidden number]"
            return "[hidden number]"
        text = pat.sub(_sub, text)
    return text, found


# ------------------------------------------------------------ budget maths
def budget_numbers(income: float, expenses: dict[str, float]) -> dict:
    """All arithmetic is done here, in code, never by the model."""
    clean = {k.strip(): float(v) for k, v in expenses.items() if k and str(k).strip() and v is not None and float(v) > 0}
    total = sum(clean.values())
    return {
        "income": int(round(income or 0)),
        "expenses": clean,
        "expenses_text": "; ".join(f"{k}: {int(round(v))}" for k, v in clean.items()) or "none given",
        "total_expenses": int(round(total)),
        "surplus": int(round((income or 0) - total)),
    }


def check_budget(result: dict, nums: dict) -> list[str]:
    """Validate the model's budget JSON against the code-calculated numbers. Returns a list of problems."""
    problems = []
    if result.get("status") != "ok":
        return problems
    try:
        suggested_total = sum(float(r.get("suggested", 0) or 0) for r in result.get("budget", []))
        savings = float(result.get("suggested_savings", 0) or 0)
    except (TypeError, ValueError):
        return ["budget numbers are not numeric"]
    available = nums["income"] - suggested_total
    if savings > available + 1:
        problems.append(f"suggested savings ({savings:.0f}) is more than income minus suggested spending ({available:.0f})")
    if nums["surplus"] <= 0 and savings > 0:
        problems.append("expenses are more than income but savings is not 0")
    return problems


# ------------------------------------------------------------- model call
def _api_key() -> str | None:
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        return st.secrets.get("GEMINI_API_KEY")
    except Exception:
        return None


def _models() -> list[str]:
    forced = os.environ.get("GEMINI_MODEL")
    if not forced:
        try:
            import streamlit as st
            forced = st.secrets.get("GEMINI_MODEL")
        except Exception:
            forced = None
    return [forced] if forced else DEFAULT_MODELS


_RETRYABLE = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "INTERNAL")
_SKIP_MODEL = ("404", "NOT_FOUND", "PERMISSION_DENIED", "403", "is not found", "not supported")


def call_model(prompt: dict, values: dict) -> dict:
    """Run one prompt. Returns {text, model, seconds, system, user}."""
    from google import genai
    from google.genai import types

    key = _api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to Streamlit secrets or your environment.")
    client = genai.Client(api_key=key)

    system = fill(prompt["system"], values)
    user = fill(prompt["user"], values)
    cfg = {}
    if system:
        cfg["system_instruction"] = system
    if prompt["temperature"] is not None:
        cfg["temperature"] = prompt["temperature"]
    if prompt["json"]:
        cfg["response_mime_type"] = "application/json"
    config = types.GenerateContentConfig(**cfg) if cfg else None

    last_err = None
    for model in _models():
        for attempt in range(3):
            try:
                t0 = time.time()
                resp = client.models.generate_content(model=model, contents=user, config=config)
                return {
                    "text": (resp.text or "").strip(),
                    "model": getattr(resp, "model_version", None) or model,
                    "seconds": round(time.time() - t0, 1),
                    "system": system,
                    "user": user,
                }
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                last_err = e
                if any(s in msg for s in _SKIP_MODEL):
                    break  # try the next model
                if any(s in msg for s in _RETRYABLE):
                    time.sleep(8 * (attempt + 1))
                    continue
                raise
    raise RuntimeError(f"All models failed. Last error: {last_err}")


# ------------------------------------------------------------ parsing
def parse_json(text: str) -> dict | None:
    """Parse model JSON, tolerating ```json fences or extra text around it."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    for candidate in (t, t[t.find("{") : t.rfind("}") + 1] if "{" in t else ""):
        try:
            obj = json.loads(candidate)
            return obj if isinstance(obj, dict) else None
        except (json.JSONDecodeError, ValueError):
            continue
    return None


# --------------------------------------------------- language & format checks
DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")
HINGLISH_WORDS = {"hai", "hain", "aap", "aapka", "aapke", "apne", "ke", "ka", "ki", "ko", "mein", "se", "karo", "karein",
                  "paise", "paisa", "bachat", "kharcha", "kharche", "nahi", "mat", "agar", "toh", "to", "bhi", "har", "yeh", "ye"}


def text_values(obj) -> str:
    """Join all string values of a JSON object (keys excluded) for language checks."""
    if isinstance(obj, dict):
        return " ".join(text_values(v) for v in obj.values())
    if isinstance(obj, list):
        return " ".join(text_values(v) for v in obj)
    return obj if isinstance(obj, str) else ""


def language_ok(text: str, language: str) -> bool:
    deva = len(DEVANAGARI.findall(text))
    latin = len(LATIN.findall(text))
    letters = max(deva + latin, 1)
    lang = language.lower()
    if lang.startswith("hindi"):
        return deva / letters >= 0.6
    words = set(re.findall(r"[a-z]+", text.lower()))
    if lang.startswith("hinglish"):
        return deva / letters < 0.05 and len(words & HINGLISH_WORDS) >= 3
    # English
    return deva / letters < 0.05 and len(words & HINGLISH_WORDS - {"to", "se", "ke"}) < 4


P2_EMOJIS = ["💡", "🛒", "⭐", "✅"]


def p2_format_ok(text: str) -> bool:
    return all(e in text for e in P2_EMOJIS)


def word_count(text: str) -> int:
    return len(re.findall(r"\S+", text))
