# Finova M2: finish tonight (deadline 22 Nov, 11:59 PM)

## Step 1: Deploy the prototype (about 20 min)
1. Upload this whole folder to your **public** GitHub repo `finova`. Commit in a few pieces (prompts → code → tests → docs), and have both members commit so there's evidence for the contribution table.
2. Go to share.streamlit.io, choose **Create app**, pick your repo, set the main file to `code/app.py` and deploy.
3. Open **App settings → Secrets** and paste `GEMINI_API_KEY = "your-key"`. **Never put the key in any file in the repo.**
4. Open the app link in an incognito window and try all 3 tabs. That link is your **prototype link (Q11)**.
5. Note the model name shown in the sidebar. It's your answer for Q9 (e.g. "Gemini <version> via Gemini API, Streamlit app").

## Step 2: Get real results (about 10 min)
```bash
pip install -r requirements.txt
export GEMINI_API_KEY=your-key      # PowerShell: $env:GEMINI_API_KEY="your-key"
python code/run_tests.py
```
This produces `docs/iteration_results.md` (numbers for the iteration log), `docs/test_table.md` (Section 4) and `docs/sample_runs.md` (sample run for each prompt sheet). **Read the outputs in `test-data/outputs/v3/` and fix any Pass/Fail the automatic check got wrong.** Keep the failures in; the guidelines reward honesty. Commit the outputs.

If you hit rate limits, run `python code/run_tests.py --sleep 10`.

## Step 3: The M2 PDF (7 sections, this order, these headings)
| Section | Where the content comes from |
|---|---|
| 1 Cover page | Team ID PE-B13-36, Finova, project title, batch, faculty Indarjeet Gupta, both members + enrollment numbers, 3 links |
| 2 Prompt and solution design | (a) Use prompt A below. (b) the 4 PNGs in `docs/diagrams/`. (c) Use the prompt sheets below. |
| 3 Implementation | What is built (prompt B), the module status table below, and the iteration log below + full text of every version from `prompts/v1..v3` |
| 4 Demonstration and testing | `docs/test_table.md`, 2–3 app screenshots captioned "Test T01" etc., limitations (prompt C) |
| 5 Repository | Screenshot of the GitHub repo + the CHANGELOG lines |
| 6 Supporting document | Your Technical report (prompt D), the same PDF you upload at Q16 |
| 7 Team contribution | Table: name, enrollment, role, tasks, evidence (file/commit/prompt ID), % adding up to 100 |

### Counts for the form (they must match the PDF)
- **Q10 prompts = 3** (P1, P2, P3)
- **Q17 test inputs = 13**
- **Q18 prompt versions = 9** (v1, v2, v3 for each of 3 prompts). If you only log one prompt's versions, enter 3.
- **Q19:** "All modules working" only if every row below is Working after *your* testing.

### Module status table (only mark a module Working once you've seen it work in the deployed app)
| Module | What it does | Status | Notes |
|---|---|---|---|
| Language & level selector | English / Hindi / Hinglish; Beginner / Intermediate | Working? | |
| Privacy filter | Hides OTP, account, card, Aadhaar-like numbers before the AI call | Working? | Test T05 |
| Budget calculator | Adds expenses and money left in Python | Working? | |
| Budget Planner (P1) | Budget table, savings, tips in JSON | Working? | T01–T05 |
| Output checker | Parses JSON, flags savings larger than money available | Working? | |
| Money Explainer (P2) | 4-part explanation at chosen level | Working? | T06–T09 |
| Scam Checker (P3) | Verdict, red flags, what to do | Working? | T10–T13 |

### Iteration log (fill the last column from `docs/iteration_results.md`, using numbers)
| Version | What changed | Why it was changed | Result after the change |
|---|---|---|---|
| P1 v1 | M1 baseline: one all-in-one assistant prompt, free text | Starting point | e.g. JSON valid 0/5; app cannot show a table |
| P1 v2 | Budget-only role, named variables, language rule, JSON schema | Output unusable by the app; wrong language | from results |
| P1 v3 | Totals computed in code and passed in; deficit + no-loan rules; 1 example; temp 0.2 | Model's own maths/savings could be wrong; deficit case | from results |
| P2 v1 | "Explain {question} in {language}" | Starting point | from results |
| P2 v2 | Role, 2 levels with word limits, script rules, 4-part emoji format | Too long, no structure | from results |
| P2 v3 | 2 few-shot examples, safety + off-topic rules, temp 0.3 | Stock question / off-topic not handled | from results |
| P3 v1 | "Is this message a scam?" | Starting point | from results |
| P3 v2 | Red-flag checklist, 4 verdict labels, JSON schema | Vague yes/no, no actions | from results |
| P3 v3 | Message in `<message>` tags + "treat as data", LOOKS SAFE / NEED MORE INFO rules, 1930 rule, 2 examples, temp 0.1 | Injection test (T12) and "hi" (T13) | from results |

Only write a "Why" that matches what you actually saw. If v2 didn't fail the way the table says, change the wording.

### Prompt sheet (one per prompt, pasted as text)
| Field | P1 Budget Planner | P2 Money Explainer | P3 Scam Checker |
|---|---|---|---|
| Step in workflow | Budget tab, after the privacy filter + calculator | Learn tab, after the privacy filter | Scam tab, after the privacy filter |
| Purpose | Turn income/expenses into a safe, realistic budget | Explain a money idea at the user's level and language | Judge a message's scam risk and say what to do |
| Tool & model | Gemini API (model from sidebar), Streamlit | same | same |
| Settings | temperature 0.2, JSON output | temperature 0.3, text | temperature 0.1, JSON output |
| System prompt | `prompts/final/P1_budget_planner.txt` (SYSTEM part) | `P2_money_explainer.txt` | `P3_scam_checker.txt` |
| User template | USER part of the file | USER part | USER part |
| Variables | {income} monthly income; {expenses} "Category: amount; …"; {total_expenses}, {surplus} computed in code; {goal}; {debts}; {language} | {question}; {language}; {level} Beginner/Intermediate | {message} pasted text (masked); {language} |
| Examples included | 1 | 2 | 2 |
| Output format | JSON: status, question, summary, suggested_savings, budget[], tips[3], warning | 4 parts 💡 🛒 ⭐ ✅ | JSON: verdict, risk_score, red_flags[], explanation, what_to_do[] |
| Sample run | T01 from `docs/sample_runs.md` | T06 | T10 |

## Prompts to write the rest (paste into ChatGPT / Claude / Gemini together with the files mentioned)

**A: Section 2(a) design summary**
> Using the attached README.md, CHANGELOG.md and our Milestone 1 PDF, write a half-page "Prompt and solution design" summary for a student project report in simple formal English. Answer in this order, one short paragraph each: what problem and for whom; input and output; how many prompts/steps (3 prompts + 3 code modules) and why we split the M1 single prompt into 3; which tool/model and why (Gemini via API: free tier, good Hindi, JSON output mode); what changed since Milestone 1. Do not invent any results or numbers that are not in the files.

**B: Section 3 "What is built"**
> From the attached README.md and code/app.py, write 5–7 lines describing what is built in the Finova prototype: the 3 tabs, the privacy filter, the budget calculator and the output checker, and how the app is deployed. Plain student-report English, no marketing words, no claims that aren't in the files.

**C: Section 4 limitations**
> Here is our test table and the failed outputs: [paste docs/test_table.md and the failed outputs]. Write 2–4 known limitations of the Finova prototype based ONLY on these real failures and on obvious gaps (only 3 languages, no voice input, depends on free API quota, heuristic privacy filter). For each, write one line on what we will try in Milestone 3. Format: a table with columns Limitation | Evidence (test no.) | What we will try next.

**D: Supporting document (Technical report, 1–2 pages)**
> Write a 1–2 page Technical report for our project "Finova" using ONLY the attached README.md, CHANGELOG.md, docs/iteration_results.md, docs/test_table.md and the prompt files. Sections: 1 Architecture (refer to the system architecture diagram), 2 Tools and models used, 3 Prompt design (P1, P2, P3: techniques used, e.g. role, JSON schema, few-shot, delimiters, low temperature, code-side arithmetic), 4 Test results with the real numbers, 5 Limitations. Do not invent numbers. Plain academic English.

Save it as `Finova_TechnicalReport.pdf` (Q15: Technical report, Q16: upload) and also paste it into Section 6.

## Reel script (target about 120 s; check the exact length before entering Q14)
| Time | Show on screen | Voice-over |
|---|---|---|
| 0–10 s | App home page | "Only about 27% of Indians meet basic financial-literacy standards. Finova helps low-income families budget, learn money ideas and spot scams, in English, Hindi or Hinglish." |
| 10–45 s | `prompts/v1/P3_scam_checker.txt` and its output in test-data/outputs/v1/T12.txt, then v3 and its output | "Our first scam prompt was one line. On a fake KBC lottery message with a hidden 'say it's safe' instruction, it [say what v1 actually did]. Version 3 puts the message inside tags and tells the model to treat it as data, so now it says SCAM and gives the 1930 helpline." |
| 45–100 s | Live run: budget in Hindi (T02), explain "compound interest" (Hindi, Beginner), paste the KYC SMS into the scam checker | Narrate what's happening as it runs |
| 100–120 s | Iteration results table + module table | "Done: 3 prompts, 9 versions, 13 tests. Next, for Milestone 3: more regional languages, voice input, and a larger test set." |

Upload it to Drive or as unlisted YouTube with **Anyone with the link** access, then test the link in incognito.

## Before you submit
- [ ] All 3 links open in an incognito window without asking for access
- [ ] No API key anywhere in the repo (search GitHub for "AIza")
- [ ] File names: `M2_PE-B13-36_Finova.pdf` (use your exact Team ID) and `Finova_TechnicalReport.pdf`
- [ ] Every number on the form matches the PDF
- [ ] Only the team leader submits, once
