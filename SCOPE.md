# Scope and Anomaly Log

## Database Schema Summary
- `person`, `person_alias`: canonical participants and raw CSV aliases.
- `expense_group`, `group_membership`: group and time-aware membership periods.
- `currency_rate`: date-effective exchange rates to INR.
- `expense`, `expense_split`: approved/reviewable expenses and participant debits.
- `settlement`: direct payments, intentionally separate from expenses.
- `ledger_entry`: immutable trace lines used for balances.
- `import_batch`, `import_row`, `import_anomaly`: raw CSV import, row state, and anomaly audit trail.

## Import Policy
The CSV is imported unchanged. The importer parses rows, stores raw data, detects anomalies, and only commits clean or explicitly approved rows. It does not auto-delete duplicates or infer missing critical fields. Base currency is INR. USD rows preserve original values and use date-effective manual rates seeded for this assignment.

## Anomalies Found in `Expenses Export.csv`
| Row | Category | Handling |
| --- | --- | --- |
| 5/6 | duplicate / near duplicate Marina Bites | Review required; no auto-delete. |
| 7 | amount format `1,200` | Normalized to `1200`, logged as info. |
| 9 | alias `priya` | Mapped to Priya and logged. |
| 10 | precision `899.995` | Review required before ROUND_HALF_UP rounding. |
| 11 | alias `Priya S` | Mapped to Priya and logged. |
| 13 | missing payer | Blocked until reviewer supplies payer. |
| 14 | settlement-like row | Review/import as settlement, never expense. |
| 15 | percentage totals 110% | Blocked until corrected. |
| 20,21,23,26 | USD rows | Converted to INR using date-effective manual rate, original values preserved. |
| 23 | unknown participant Kabir wording | Requires review; Kabir seeded as one-day guest. |
| 24/25 | near duplicate Thalassa dinner | Review required because payer/amount conflict. |
| 26 | negative refund | Review required as refund. |
| 27 | malformed date and payer whitespace | Date blocked; payer normalized to Rohan. |
| 28 | missing currency | Blocked; no INR inference. |
| 31 | zero amount | Blocked/reviewed as correction row. |
| 32 | percentage totals 110% | Blocked until corrected. |
| 34 | ambiguous date | Blocked because notes question April 5 vs May 4. |
| 36 | Meera after move-out | Review required; suggested removal from split. |
| 38 | Sam deposit/settlement-like | Review/import as settlement. |
| 42 | equal split with share details | Review required to choose equal vs detail override. |
