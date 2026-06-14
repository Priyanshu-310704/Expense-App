# AI Usage

## Tools Used

* **OpenAI Codex** — used as an implementation collaborator for scaffolding, code generation, refactoring suggestions, and review assistance.
* AI-generated outputs were treated as draft implementations and were manually validated against assignment requirements before integration.

## Representative Prompts

* Build the assignment as a production-grade **Django REST Framework + React + PostgreSQL** application.
* Analyze the assignment specification and dataset before proposing architecture or implementation details.
* Design a traceable financial ledger system with explicit anomaly handling and auditable balance calculations.
* Ensure settlements, expenses, memberships, imports, and currency conversions conform to all documented business rules.
* Generate comprehensive test cases covering imports, ledger reconstruction, settlements, and edge conditions.

## AI-Generated Issues Identified and Corrected

### 1. Incorrect Source Dataset Selection

An early implementation referenced an outdated dataset (`traveleo-expense-history.csv`) instead of the required `Expenses Export.csv`.

**Detection**

* Cross-checked assignment requirements against available files.
* Verified dataset names and formats before import implementation.

**Resolution**

* Replaced the incorrect dataset source.
* Revalidated the import pipeline using the correct export file.

### 2. Settlement Ledger Inconsistency

A generated import workflow created settlement records without rebuilding the corresponding ledger entries.

**Detection**

* Service-layer review revealed balance discrepancies after settlement imports.
* Ledger reconstruction tests exposed the issue.

**Resolution**

* Added an explicit call to `rebuild_settlement_ledger`.
* Verified post-import balances through ledger reconciliation tests.

### 3. Windows Command-Length Limitation

An AI-generated Windows command attempted to write large content inline and exceeded shell command-length limits.

**Detection**

* Execution failed with a shell command-length error.

**Resolution**

* Replaced inline generation with temporary script-based file generation.
* Improved reliability for large-file creation workflows.

## Engineering Review Process

All AI-generated code and design suggestions underwent manual review before acceptance. Validation focused on the assignment's core requirements:

* No silent deletion or modification of duplicate records.
* Settlements modeled independently from expenses.
* Fully traceable USD conversion and exchange-rate calculations.
* Membership validity enforced through period-based checks.
* Preservation of raw imported records for auditability.
* Deterministic ledger reconstruction and balance calculations.
* Explicit handling of anomalies, invalid data, and edge cases.
* End-to-end verification through targeted testing and manual review.

## Engineer-of-Record Statement

AI assistance accelerated implementation and review workflows, but all architectural decisions, requirement interpretations, bug fixes, and final code acceptance were performed through independent engineering review. The submitted solution reflects deliberate validation against the assignment specification, with correctness, traceability, and auditability prioritized over generated output.
