# Finova — money help in your language

**SCSE4041 Prompt Engineering Mini Project · Team PE-B13-36 (Finova) · Faculty: Indarjeet Gupta**

Finova is a bilingual (English / Hindi / Hinglish) money helper for low-income households in India. It has three modules, each powered by its own engineered prompt:

| Module | Prompt | What it does |
|---|---|---|
| 💰 Budget Planner | `prompts/final/P1_budget_planner.txt` | Income + expenses → realistic budget, suggested savings, 3 tips (JSON) |
| 📘 Money Concept Explainer | `prompts/final/P2_money_explainer.txt` | Money question → 4-part explanation at Beginner/Intermediate level |
| 🛡️ Scam Message Checker | `prompts/final/P3_scam_checker.txt` | Pasted SMS/WhatsApp text → verdict, red flags, what to do (JSON) |

Supporting code modules: a **privacy filter** that hides OTPs, account, card and Aadhaar-like numbers before anything reaches the model, a **budget calculator** that does all the arithmetic in Python, and an **output checker** that validates the model's JSON and savings figure.

**Prototype:** _paste your Streamlit link here_
**Model:** Gemini (Flash) through the Google Gemini API (`google-genai` SDK). The app shows the exact model version in the sidebar.

## Team

| Name | Enrollment no. | Main task |
|---|---|---|
| Shruti Sood | S24CSEU1158 | _fill in_ |
| Pranav Mehta | S24CSEU1164 | _fill in_ |

## Repository layout

```
prompts/v1, v2, v3/   older prompt versions (one file per prompt)
prompts/final/        final prompts used by the app (= v3)
code/app.py           Streamlit prototype
code/finova_core.py   prompt loader, privacy filter, budget maths, Gemini call, checks
code/run_tests.py     runs every prompt version on the test inputs and scores them
test-data/            test inputs (test_inputs.json) and saved real outputs
docs/                 diagrams, prompt sheets, iteration results, test table, M2 PDF
CHANGELOG.md          dated changes since Milestone 1
```

Each prompt file has three parts: `### SETTINGS` (temperature, output type), `### SYSTEM` (system prompt) and `### USER` (user prompt template with `{variables}`).

## Run it locally

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your Gemini API key
streamlit run code/app.py
```

## Re-run the tests

```bash
export GEMINI_API_KEY=your-key        # Windows PowerShell: $env:GEMINI_API_KEY="your-key"
python code/run_tests.py              # 3 versions x 13 tests = 39 calls, about 4 minutes
```

Outputs are saved to `test-data/outputs/` and summarised in `docs/iteration_results.md` and `docs/test_table.md`.

## Responsible use

Finova gives general money information only. It is not financial, legal or investment advice and tells users to consult their bank, post office or a SEBI-registered adviser where needed. It never asks for OTPs, PINs, account or Aadhaar numbers, and hides them if typed. Test inputs are made-up data. If you lose money to fraud, call **1930** or report at **cybercrime.gov.in**.
