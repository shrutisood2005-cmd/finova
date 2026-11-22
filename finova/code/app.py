"""Finova — money help in your language. Streamlit prototype for SCSE4041 Milestone 2.

Run locally:  streamlit run code/app.py   (with GEMINI_API_KEY in .streamlit/secrets.toml or env)
"""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
import finova_core as fc  # noqa: E402

st.set_page_config(page_title="Finova — money help in your language", page_icon="💰", layout="centered")

LANGS = {"English": "English", "हिंदी (Hindi)": "Hindi", "Hinglish": "Hinglish"}

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    language = LANGS[st.radio("Reply language", list(LANGS.keys()), index=0)]
    level = st.radio("Explanation level", ["Beginner", "Intermediate"], index=0)
    st.divider()
    st.caption(
        "🔒 **Privacy:** Finova never needs your bank account number, OTP, PIN, Aadhaar or card number. "
        "If you type one by mistake, the app hides it before anything is sent to the AI."
    )
    st.caption("ℹ️ Finova gives general information, not financial advice.")
    if "last_model" in st.session_state:
        st.caption(f"Model used: `{st.session_state.last_model}`")

st.title("💰 Finova")
st.write("Simple money help for every household: plan your budget, learn money words, and check scam messages.")


def run(prompt_id, values):
    prompt = fc.load_prompt(prompt_id, "final")
    with st.spinner("Finova is thinking..."):
        out = fc.call_model(prompt, values)
    st.session_state.last_model = out["model"]
    return out


def show_masked(found):
    if found:
        st.info(f"🔒 We hid {len(found)} private number(s) ({', '.join(sorted(set(found)))}) before sending your text to the AI.")


tab1, tab2, tab3 = st.tabs(["💰 Budget Planner", "📘 Learn a money word", "🛡️ Scam Checker"])

# ------------------------------------------------------------- P1 budget
with tab1:
    st.subheader("Plan your monthly budget")
    income = st.number_input("Monthly income (₹)", min_value=0, step=500, value=12000)
    st.caption("Edit the expense list. Add or delete rows as you like.")
    default = pd.DataFrame(
        {"Expense": ["Rent", "Groceries", "Transport", "Bills", "Other"], "Amount (₹)": [3000, 3000, 1000, 1000, 2000]}
    )
    table = st.data_editor(default, num_rows="dynamic", width="stretch", key="exp")
    goal = st.text_input("Savings goal (optional)", "Emergency fund")
    debts = st.text_input("Loans or EMIs (optional)", "None")

    if st.button("Make my budget", type="primary"):
        expenses = {str(r["Expense"]): r["Amount (₹)"] for _, r in table.iterrows() if pd.notna(r["Amount (₹)"])}
        nums = fc.budget_numbers(income, expenses)
        goal_m, f1 = fc.mask_sensitive(goal)
        debts_m, f2 = fc.mask_sensitive(debts)
        exp_m, f3 = fc.mask_sensitive(nums["expenses_text"])
        show_masked(f1 + f2 + f3)

        c1, c2, c3 = st.columns(3)
        c1.metric("Income", f"₹{nums['income']:,}")
        c2.metric("Expenses", f"₹{nums['total_expenses']:,}")
        c3.metric("Money left", f"₹{nums['surplus']:,}")

        values = {"income": nums["income"], "expenses": exp_m, "total_expenses": nums["total_expenses"],
                  "surplus": nums["surplus"], "goal": goal_m or "not given", "debts": debts_m or "none",
                  "language": language}
        try:
            out = run("P1", values)
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not reach the AI right now: {e}")
            st.stop()
        result = fc.parse_json(out["text"])
        if result is None:
            st.error("The AI reply was not in the expected format. Please try again.")
            st.code(out["text"])
        elif result.get("status") == "need_more_info":
            st.warning(result.get("question") or "Please add your income and expenses.")
        else:
            st.success(result.get("summary", ""))
            problems = fc.check_budget(result, nums)
            if problems:
                st.warning("⚠️ Finova's checker found a problem with the AI's numbers: " + "; ".join(problems)
                           + ". Use the suggested savings with care.")
            rows = result.get("budget", [])
            if rows:
                df = pd.DataFrame(rows).rename(columns={"category": "Expense", "current": "Now (₹)",
                                                        "suggested": "Suggested (₹)", "note": "Why"})
                st.dataframe(df, width="stretch", hide_index=True)
            st.metric("Suggested monthly savings", f"₹{int(float(result.get('suggested_savings', 0) or 0)):,}")
            if result.get("warning"):
                st.warning(result["warning"])
            st.markdown("**Saving tips**")
            for t in result.get("tips", []):
                st.markdown(f"- {t}")
        with st.expander("See the raw AI output"):
            st.code(out["text"], language="json")

# ---------------------------------------------------------- P2 explainer
with tab2:
    st.subheader("Learn a money word or ask a money question")
    st.caption("Examples: What is interest? · UPI kaise kaam karta hai? · Why should I keep an emergency fund?")
    question = st.text_input("Your question", "What is compound interest?")
    if st.button("Explain", type="primary"):
        q_m, found = fc.mask_sensitive(question)
        show_masked(found)
        if not q_m.strip():
            st.warning("Please type a question.")
        else:
            try:
                out = run("P2", {"question": q_m, "language": language, "level": level})
                st.markdown(out["text"])
            except Exception as e:  # noqa: BLE001
                st.error(f"Could not reach the AI right now: {e}")

# ------------------------------------------------------------- P3 scam check
with tab3:
    st.subheader("Is this message a scam?")
    st.caption("Paste an SMS or WhatsApp message, or describe a call you got.")
    message = st.text_area(
        "Message",
        "Dear Customer, your bank account will be blocked today. Update your KYC now: http://bit.ly/kyc-upd8",
        height=120,
    )
    if st.button("Check message", type="primary"):
        m_m, found = fc.mask_sensitive(message)
        show_masked(found)
        try:
            out = run("P3", {"message": m_m, "language": language})
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not reach the AI right now: {e}")
            st.stop()
        r = fc.parse_json(out["text"])
        if r is None:
            st.error("The AI reply was not in the expected format. Please try again.")
            st.code(out["text"])
        else:
            verdict = r.get("verdict", "?")
            show = {"SCAM": st.error, "SUSPICIOUS": st.warning, "LOOKS SAFE": st.success}.get(verdict, st.info)
            show(f"**{verdict}** · risk {r.get('risk_score', '?')}/10")
            st.write(r.get("explanation", ""))
            if r.get("red_flags"):
                st.markdown("**Red flags:** " + ", ".join(r["red_flags"]))
            st.markdown("**What to do**")
            for s in r.get("what_to_do", []):
                st.markdown(f"- {s}")
        with st.expander("See the raw AI output"):
            st.code(out["text"], language="json")

st.divider()
st.caption("Finova gives general money information only, not financial advice. Lost money to fraud? Call **1930** "
           "or report at **cybercrime.gov.in**. · SCSE4041 Mini Project · Team PE-B13-36")
