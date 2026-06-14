# AI Usage

## Tools Used
- OpenAI Codex as implementation collaborator.

## Key Prompts
- Build the assignment as a production-grade Django REST + React + PostgreSQL app.
- Inspect the assignment PDF and CSV before planning.
- Implement explicit anomaly handling and traceable balances.

## Cases Where AI Was Wrong
1. Initially considered the old `traveleo-expense-history.csv`. This was caught by comparing the PDF requirement with available files and searching Downloads for the real `Expenses Export.csv`.
2. A generated import commit branch created a settlement without rebuilding ledger entries. This was caught during targeted service review and fixed by calling `rebuild_settlement_ledger`.
3. A Windows inline write command exceeded command-length limits. This was detected by the shell error and changed to temporary generator scripts.

## Engineer-of-Record Notes
Every generated section was reviewed against the assignment requirements: no silent duplicate deletion, settlements separate from expenses, USD conversion traceable, membership periods checked, and raw import rows preserved.
