# Decision Log

## Django + DRF + PostgreSQL
Chosen because the assignment emphasizes Python, REST APIs, relational schema design, and query correctness. Alternatives considered: Node/Next/Prisma, rejected because they do not match the role expectations.

## Ledger-Based Balances
Balances are not stored as magic totals. Approved expenses and settlements generate ledger entries; summaries are sums over ledger entries. This makes every number traceable.

## Reviewable Import
Duplicates, refunds, aliases, inactive members, and settlement-like rows are not silently changed. They are stored as anomalies with severity, action, and approval state.

## Time-Aware Membership
Membership lives in `group_membership` with join/leave dates. Split validation logs participants outside their active period instead of mutating history.

## Currency Policy
INR is the reporting currency. USD rows use date-effective exchange rates and keep original currency/amount. Missing rates block commit.

## Frontend Style
The UI is a practical audit console rather than a decorative landing page. The main workflows are import review, balance summary, and trace ledger drilldown.
