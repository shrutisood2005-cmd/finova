# Iteration results (Finova web app Test runner, model: Claude quick tier, 24 Nov 2026)

## P1 Budget Planner

| Version | json_valid | language_ok | status_ok | budget_valid | deficit_zero_savings | masked | Tests fully passed |
|---|---|---|---|---|---|---|---|
| v1 | 0/5 | 4/4 | 0/5 | 0/4 | 0/1 | 1/1 | 0/5 |
| v2 | 5/5 | 4/4 | 5/5 | 1/4 | 1/1 | 1/1 | 2/5 |
| v3 | 5/5 | 4/4 | 5/5 | 3/4 | 1/1 | 1/1 | 4/5 |

## P2 Money Concept Explainer

| Version | language_ok | format_ok | length_ok | referral_ok | off_topic_ok | Tests fully passed |
|---|---|---|---|---|---|---|
| v1 | 4/4 | 0/2 | 0/2 | 1/1 | 0/1 | 1/4 |
| v2 | 4/4 | 2/2 | 2/2 | 1/1 | 0/1 | 3/4 |
| v3 | 4/4 | 2/2 | 1/2 | 1/1 | 1/1 | 3/4 |

## P3 Scam Message Checker

| Version | json_valid | verdict_ok | helpline_ok | language_ok | Tests fully passed |
|---|---|---|---|---|---|
| v1 | 0/4 | 3/4 | 2/3 | 3/3 | 0/4 |
| v2 | 4/4 | 4/4 | 2/3 | 3/3 | 3/4 |
| v3 | 4/4 | 4/4 | 3/3 | 3/3 | 4/4 |

## All prompts

| Version | Tests fully passed (of 13) |
|---|---|
| v1 | 1 |
| v2 | 8 |
| v3 | 11 |
