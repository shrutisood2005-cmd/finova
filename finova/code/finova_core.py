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

# Gemini models tried in order (used only if GEMINI_API_KEY is set). Set GEMINI_MODEL to override.
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
# Provider order: Cerebras (CEREBRAS_API_KEY), then Groq (GROQ_API_KEY), then OpenRouter (OPENROUTER_API_KEY), then Gemini (GEMINI_API_KEY);
# only providers with a key are used. Users of the app never need an account.
DEFAULT_GROQ_MODELS = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
DEFAULT_OPENROUTER_MODELS = ["meta-llama/llama-3.3-70b-instruct:free"]
DEFAULT_CEREBRAS_MODELS = ["llama-3.3-70b", "llama3.1-8b"]


def _secret(name: str) -> str | None:
    val = os.environ.get(name)
    if not val:
        try:
            import streamlit as st
            val = st.secrets.get(name)
        except Exception:
            val = None
    if not val:
        return None
    val = str(val).strip().strip('"').strip("'").strip()
    if val.lower().startswith("bearer "):
        val = val[7:].strip()
    return val or None


def _api_key() -> str | None:
    return _secret("GEMINI_API_KEY")


def _clean_model(m: str) -> str:
    m = m.strip().strip('"').strip("'").replace("\U0001f193", ":free").replace(" ", "")
    return m.replace("::free", ":free")


def _model_list(var: str, default: list[str]) -> list[str]:
    forced = _secret(var)
    if forced:
        # Several models can be given, separated by commas; they are tried in order.
        return [_clean_model(m) for m in str(forced).split(",") if m.strip()]
    return default


def _models() -> list[str]:
    return _model_list("GEMINI_MODEL", DEFAULT_MODELS)


_RETRYABLE = ("429", "RESOURCE_EXHAUSTED", "503", "UNAVAILABLE", "500", "502", "INTERNAL", "rate_limit", "timed out")
_SKIP_MODEL = ("404", "NOT_FOUND", "PERMISSION_DENIED", "403", "is not found", "not supported",
               "no longer available", "model_not_found", "decommissioned", "does not exist")


def _openai_compat_call(url: str, model: str, key: str, system: str | None, user: str, temperature, want_json: bool) -> str:
    """One call to an OpenAI-compatible chat API such as Groq or OpenRouter (standard library only)."""
    import urllib.request
    import urllib.error

    messages = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user}]
    body = {"model": model, "messages": messages}
    if temperature is not None:
        body["temperature"] = temperature
    if want_json:
        body["response_format"] = {"type": "json_object"}
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "finova/1.0",
                 "HTTP-Referer": "https://github.com/shrutisood2005-cmd/finova", "X-Title": "Finova"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:400]
        raise RuntimeError(f"{e.code} {detail}") from None
    return (data["choices"][0]["message"]["content"] or "").strip()


def _groq_call(model, key, system, user, temperature, want_json):
    return _openai_compat_call("https://api.groq.com/openai/v1/chat/completions", model, key, system, user, temperature, want_json)


def _openrouter_call(model, key, system, user, temperature, want_json):
    return _openai_compat_call("https://openrouter.ai/api/v1/chat/completions", model, key, system, user, temperature, want_json)


def _cerebras_call(model, key, system, user, temperature, want_json):
    return _openai_compat_call("https://api.cerebras.ai/v1/chat/completions", model, key, system, user, temperature, want_json)


def _gemini_call(model: str, key: str, system: str | None, user: str, temperature, want_json: bool) -> str:
    from google import genai
    from google.genai import types

    cfg = {}
    if system:
        cfg["system_instruction"] = system
    if temperature is not None:
        cfg["temperature"] = temperature
    if want_json:
        cfg["response_mime_type"] = "application/json"
    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model=model, contents=user,
                                          config=types.GenerateContentConfig(**cfg) if cfg else None)
    return (resp.text or "").strip()


def call_model(prompt: dict, values: dict) -> dict:
    """Run one prompt. Returns {text, model, seconds, system, user}."""
    system = fill(prompt["system"], values)
    user = fill(prompt["user"], values)

    plans = []
    groq_key, or_key, gemini_key = _secret("GROQ_API_KEY"), _secret("OPENROUTER_API_KEY"), _api_key()
    cb_key = _secret("CEREBRAS_API_KEY")
    if cb_key:
        plans += [("Cerebras", _cerebras_call, m, cb_key) for m in _model_list("CEREBRAS_MODEL", DEFAULT_CEREBRAS_MODELS)]
    if groq_key:
        plans += [("Groq", _groq_call, m, groq_key) for m in _model_list("GROQ_MODEL", DEFAULT_GROQ_MODELS)]
    if or_key:
        plans += [("OpenRouter", _openrouter_call, m, or_key) for m in _model_list("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODELS)]
    if gemini_key:
        plans += [("Gemini", _gemini_call, m, gemini_key) for m in _models()]
    if not plans:
        raise RuntimeError("No API key found. Set CEREBRAS_API_KEY, GROQ_API_KEY, OPENROUTER_API_KEY or GEMINI_API_KEY in Streamlit secrets or your environment.")

    last_err = None
    errors = []
    for provider, fn, model, key in plans:
        for attempt in range(3):
            try:
                t0 = time.time()
                text = fn(model, key, system, user, prompt["temperature"], prompt["json"])
                return {"text": text, "model": f"{model} ({provider})", "seconds": round(time.time() - t0, 1),
                        "system": system, "user": user}
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                last_err = e
                if attempt == 0 or any(s in msg for s in _SKIP_MODEL):
                    errors.append(f"{provider} {model}: {msg[:160]}")
                if any(s in msg for s in _SKIP_MODEL):
                    break  # try the next model
                if any(s in msg for s in _RETRYABLE):
                    if attempt == 2:
                        break  # still busy after 3 tries: move on to the next model
                    time.sleep(5 * (attempt + 1))
                    continue
                if provider in ("Cerebras", "Groq", "OpenRouter"):
                    break  # unexpected Groq error: fall back to the next option
                raise
    tried = ", ".join(sorted({p for p, *_ in plans}))
    raise RuntimeError(f"All models failed (providers tried: {tried}). Errors: " + " | ".join(errors[-6:]) if errors else f"All models failed. Last error: {last_err}")


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
