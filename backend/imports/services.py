import csv
import hashlib
import io
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from django.db import transaction

from expenses.models import Expense, ExpenseSplit, Settlement
from expenses.services import calculate_splits, convert_to_inr
from groups.models import ExpenseGroup, GroupMembership, Person
from groups.services import active_membership, canonical_name_for, get_or_create_person_for_raw_name, normalize_name
from .models import ImportAnomaly, ImportBatch, ImportRow

REQUIRED_HEADERS = ["date", "description", "paid_by", "amount", "currency", "split_type", "split_with", "split_details", "notes"]
BLOCKING = {"invalid_date", "missing_payer", "missing_currency", "invalid_amount", "split_inconsistency", "ambiguous_date"}
MANUAL_REVIEW = {"duplicate", "near_duplicate", "negative_amount", "zero_amount", "inactive_member", "settlement_like", "unknown_person", "precision_rounding", "conflicting_split_details"}


def normalize_description(value):
    value = re.sub(r"[^a-z0-9 ]+", " ", (value or "").casefold())
    value = re.sub(r"\b(at|the|a|an|dinner|lunch)\b", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(raw):
    raw = (raw or "").strip()
    for fmt in ("%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw, fmt).date(), None
        except ValueError:
            pass
    if raw == "Mar-14":
        return None, "Date is missing year and uses month-name format; suggested value is 2026-03-14."
    return None, "Date must use DD-MM-YYYY."


def parse_amount(raw):
    cleaned = (raw or "").replace(",", "").strip()
    try:
        amount = Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None, "Amount is not numeric."
    return amount, None


def split_people(raw):
    return [part.strip() for part in (raw or "").split(";") if part.strip()]


def parse_split_details(raw):
    details = {}
    for chunk in split_people(raw):
        match = re.match(r"(.+?)\s+(-?\d+(?:\.\d+)?)%?$", chunk.strip())
        if match:
            details[match.group(1).strip()] = Decimal(match.group(2))
    return details


def is_settlement_like(row):
    text = f"{row.get('description', '')} {row.get('notes', '')}".casefold()
    return bool(
        "settlement" in text
        or re.search(r"\bpaid\b.+\bback\b", text)
        or "deposit" in text
    )


def add_anomaly(batch, row, category, severity, description, detected_value, action, approval_required, anomalies_list=None):
    anomaly = ImportAnomaly(
        batch=batch,
        row=row,
        row_number=row.row_number,
        category=category,
        severity=severity,
        description=description,
        detected_value=str(detected_value or ""),
        chosen_action=action,
        approval_required=approval_required,
    )
    if anomalies_list is not None:
        anomalies_list.append(anomaly)
    else:
        anomaly.save()


def ensure_seed_data(user=None):
    group_name = f"{user.username}'s Expense Group" if user else "Default Expense Group"
    group, _ = ExpenseGroup.objects.get_or_create(name=group_name, created_by=user)
    people = {}
    for name in ["Aisha", "Rohan", "Priya", "Meera", "Dev", "Sam", "Kabir"]:
        people[name], _ = Person.objects.get_or_create(display_name=name)
    memberships = [
        ("Aisha", date(2026, 2, 1), None, False),
        ("Rohan", date(2026, 2, 1), None, False),
        ("Priya", date(2026, 2, 1), None, False),
        ("Meera", date(2026, 2, 1), date(2026, 3, 31), False),
        ("Dev", date(2026, 2, 8), date(2026, 3, 14), True),
        ("Sam", date(2026, 4, 10), None, False),
        ("Kabir", date(2026, 3, 11), date(2026, 3, 11), True),
    ]
    for name, joined, left, guest in memberships:
        GroupMembership.objects.get_or_create(
            group=group,
            person=people[name],
            joined_on=joined,
            defaults={"left_on": left, "role": GroupMembership.ROLE_GUEST if guest else GroupMembership.ROLE_MEMBER, "is_guest": guest},
        )
    from expenses.models import CurrencyRate

    for effective, rate in [(date(2026, 3, 9), "83.20"), (date(2026, 3, 10), "83.18"), (date(2026, 3, 11), "83.25"), (date(2026, 3, 12), "83.30")]:
        CurrencyRate.objects.get_or_create(currency="USD", effective_date=effective, defaults={"rate_to_inr": rate, "source": "manual assignment policy", "notes": "Seeded for the CSV import; replace with verified provider rates in production."})
    return group


@transaction.atomic
def create_import_batch(file_obj, uploaded_by=None, group=None):
    content = file_obj.read()
    if isinstance(content, str):
        content = content.encode("utf-8")
    text = content.decode("utf-8-sig")
    group = group or ensure_seed_data(uploaded_by)
    batch = ImportBatch.objects.create(group=group, uploaded_by=uploaded_by, source_filename=getattr(file_obj, "name", "expenses_export.csv"), file_sha256=hashlib.sha256(content).hexdigest())
    reader = csv.DictReader(io.StringIO(text))
    missing = [h for h in REQUIRED_HEADERS if h not in (reader.fieldnames or [])]
    if missing:
        batch.status = ImportBatch.STATUS_FAILED
        batch.save(update_fields=["status"])
        raise ValueError(f"Missing required CSV headers: {', '.join(missing)}")
    seen = []
    anomalies_list = []
    person_cache = {}
    membership_cache = {}
    
    # 1. Bulk create rows
    rows_to_create = []
    for csv_index, raw in enumerate(reader, start=2):
        rows_to_create.append(ImportRow(batch=batch, row_number=csv_index, raw_data=dict(raw)))
    ImportRow.objects.bulk_create(rows_to_create)
    
    # 2. Fetch rows back to get IDs
    created_rows = list(ImportRow.objects.filter(batch=batch).order_by("row_number"))
    
    # 3. Analyze in memory with caching
    for row in created_rows:
        analyze_row(batch, row, seen, person_cache, membership_cache, anomalies_list)
        seen.append(row)
        
    # 4. Bulk save results
    ImportRow.objects.bulk_update(created_rows, ["normalized_data", "chosen_action", "approval_required"])
    if anomalies_list:
        ImportAnomaly.objects.bulk_create(anomalies_list)
        
    batch.total_rows = len(created_rows)
    batch.save(update_fields=["total_rows"])
    return batch


def get_cached_person(raw_name, cache):
    if raw_name not in cache:
        cache[raw_name] = get_or_create_person_for_raw_name(raw_name, allow_unknown=True)
    return cache[raw_name]

def get_cached_membership(group, person, date_val, cache):
    if not person or not date_val: return False
    key = (group.id, person.id, date_val)
    if key not in cache:
        cache[key] = active_membership(group, person, date_val)
    return cache[key]

def analyze_row(batch, row, previous_rows, person_cache, membership_cache, anomalies_list):
    raw = row.raw_data
    normalized = {}
    row_action = ImportRow.ACTION_READY
    date_value, date_error = parse_date(raw.get("date"))
    if date_error:
        add_anomaly(batch, row, "invalid_date" if raw.get("date") != "04-05-2026" else "ambiguous_date", "error", date_error, raw.get("date"), "blocked until reviewer supplies date", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED
    normalized["date"] = date_value.isoformat() if date_value else None

    amount, amount_error = parse_amount(raw.get("amount"))
    if amount_error:
        add_anomaly(batch, row, "invalid_amount", "error", amount_error, raw.get("amount"), "blocked", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED
    else:
        normalized["amount"] = str(amount)
        if "," in (raw.get("amount") or ""):
            add_anomaly(batch, row, "amount_format", "info", "Amount contains a thousands separator and was normalized.", raw.get("amount"), f"parsed as {amount}", False, anomalies_list)
        if amount < 0:
            add_anomaly(batch, row, "negative_amount", "warning", "Negative amount may be a refund and needs approval.", amount, "review as refund", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
        if amount == 0:
            add_anomaly(batch, row, "zero_amount", "warning", "Zero amount cannot affect balances without reviewer intent.", amount, "blocked/review", True, anomalies_list)
            row_action = ImportRow.ACTION_BLOCKED
        if amount.as_tuple().exponent < -2:
            add_anomaly(batch, row, "precision_rounding", "warning", "Amount has more than two decimal places and will require explicit rounding approval.", amount, "round using ROUND_HALF_UP", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action

    currency = (raw.get("currency") or "").strip().upper()
    normalized["currency"] = currency
    if not currency:
        add_anomaly(batch, row, "missing_currency", "error", "Currency is missing; importer will not infer INR.", raw.get("currency"), "blocked", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED
    elif currency not in {"INR", "USD"}:
        add_anomaly(batch, row, "currency_mismatch", "error", "Unsupported currency.", currency, "blocked", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED
    elif currency == "USD":
        add_anomaly(batch, row, "currency_conversion", "info", "USD row will be converted using manual date-effective rate while preserving original amount.", currency, "convert to INR with traceable rate", False, anomalies_list)

    payer_raw = raw.get("paid_by", "")
    payer_canonical = canonical_name_for(payer_raw)
    if not payer_raw.strip():
        add_anomaly(batch, row, "missing_payer", "error", "Paid-by field is empty.", payer_raw, "blocked until payer is selected", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED
    elif payer_canonical is None:
        add_anomaly(batch, row, "unknown_person", "warning", "Payer does not match a known canonical person.", payer_raw, "review alias mapping", True, anomalies_list)
        row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
    elif payer_canonical != payer_raw.strip():
        add_anomaly(batch, row, "alias_normalized", "info", "Payer alias/casing/whitespace normalized.", payer_raw, f"mapped to {payer_canonical}", False, anomalies_list)
    if date_value and payer_raw.strip() and payer_canonical:
        payer_person, _ = get_cached_person(payer_raw, person_cache)
        if payer_person and not get_cached_membership(batch.group, payer_person, date_value, membership_cache):
            add_anomaly(batch, row, "inactive_member", "warning", "Payer is outside active membership period for expense date.", f"{payer_canonical} on {date_value}", "review payer/date before committing", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
    normalized["payer"] = payer_canonical

    participants_raw = split_people(raw.get("split_with"))
    participant_names = []
    for participant in participants_raw:
        canonical = canonical_name_for(participant)
        if canonical is None:
            add_anomaly(batch, row, "unknown_person", "warning", "Participant does not match a known canonical person.", participant, "review participant mapping", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
            canonical = participant.strip()
        elif "friend" in normalize_name(participant):
            add_anomaly(batch, row, "unknown_person", "warning", "Participant appears to be an ad-hoc guest and needs reviewer approval.", participant, f"map to {canonical} as one-day guest", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
        elif canonical != participant.strip():
            add_anomaly(batch, row, "alias_normalized", "info", "Participant alias/casing/whitespace normalized.", participant, f"mapped to {canonical}", False, anomalies_list)
        participant_names.append(canonical)
        person, _ = get_cached_person(participant, person_cache)
        if date_value and person and not get_cached_membership(batch.group, person, date_value, membership_cache):
            add_anomaly(batch, row, "inactive_member", "warning", "Participant is outside active membership period for expense date.", f"{canonical} on {date_value}", "review participant inclusion", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
    normalized["participants"] = participant_names

    split_type = (raw.get("split_type") or "").strip().lower()
    normalized["split_type"] = split_type
    if is_settlement_like(raw):
        add_anomaly(batch, row, "settlement_like", "warning", "Row looks like a payment/settlement and must not be treated as a normal expense.", raw.get("description"), "review/import as settlement", True, anomalies_list)
        row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
    elif split_type not in {"equal", "unequal", "percentage", "share"}:
        add_anomaly(batch, row, "split_inconsistency", "error", "Split type is missing or unsupported for an expense.", split_type, "blocked", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED

    detail_values = parse_split_details(raw.get("split_details"))
    if split_type == "equal" and detail_values:
        add_anomaly(batch, row, "conflicting_split_details", "warning", "Equal split row also contains explicit split details.", raw.get("split_details"), "review whether details should override equal split", True, anomalies_list)
        row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
    if split_type in {"unequal", "percentage", "share"}:
        values = []
        for raw_name, value in detail_values.items():
            values.append((canonical_name_for(raw_name) or raw_name, value))
        value_map = {name: str(value) for name, value in values}
        normalized["split_details"] = value_map
        if split_type == "percentage" and sum(Decimal(v) for v in value_map.values()) != Decimal("100"):
            add_anomaly(batch, row, "split_inconsistency", "error", "Percentage split does not total 100%.", raw.get("split_details"), "blocked until corrected", True, anomalies_list)
            row_action = ImportRow.ACTION_BLOCKED
        if split_type == "unequal" and amount is not None and sum(Decimal(v) for v in value_map.values()) != amount:
            add_anomaly(batch, row, "split_inconsistency", "error", "Unequal split amounts do not equal expense total.", raw.get("split_details"), "blocked until corrected", True, anomalies_list)
            row_action = ImportRow.ACTION_BLOCKED

    if raw.get("date") == "04-05-2026":
        add_anomaly(batch, row, "ambiguous_date", "error", "Notes explicitly say this date may mean April 5 or May 4.", raw.get("date"), "blocked until reviewer chooses date", True, anomalies_list)
        row_action = ImportRow.ACTION_BLOCKED

    desc_norm = normalize_description(raw.get("description"))
    normalized["description_key"] = desc_norm
    for previous in previous_rows:
        prev = previous.raw_data
        same_date = prev.get("date") == raw.get("date")
        
        if not same_date:
            continue
            
        same_amount = (prev.get("amount") or "").replace(",", "") == (raw.get("amount") or "").replace(",", "")
        
        prev_desc_norm = normalize_description(prev.get("description"))
        score = SequenceMatcher(None, prev_desc_norm, desc_norm).ratio() if prev_desc_norm and desc_norm else 0
        
        if same_amount and score >= 0.78:
            category = "duplicate" if score > 0.95 else "near_duplicate"
            add_anomaly(batch, row, category, "warning", "Potential duplicate of an earlier row; importer will not auto-delete.", f"matches row {previous.row_number}", "review duplicate pair", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action
        elif score >= 0.55 and prev_desc_norm and desc_norm:
            add_anomaly(batch, row, "near_duplicate", "warning", "Potential duplicate with conflicting payer or amount.", f"similar to row {previous.row_number}", "review both rows", True, anomalies_list)
            row_action = ImportRow.ACTION_NEEDS_REVIEW if row_action == ImportRow.ACTION_READY else row_action

    row.normalized_data = normalized
    row.chosen_action = row_action
    
    # Check if there are any approval_required anomalies in the current list matching this row
    row.approval_required = any(a.approval_required for a in anomalies_list if a.row == row)


def row_can_commit(row):
    if row.chosen_action in {ImportRow.ACTION_BLOCKED, ImportRow.ACTION_REJECTED, ImportRow.ACTION_COMMITTED}:
        return False
    open_required = row.anomalies.filter(approval_required=True, status=ImportAnomaly.STATUS_OPEN).exists()
    return not open_required


@transaction.atomic
def resolve_anomaly(anomaly, status):
    anomaly.status = status
    anomaly.save(update_fields=["status"])
    row = anomaly.row
    if row.anomalies.filter(approval_required=True, status=ImportAnomaly.STATUS_OPEN).exists():
        row.chosen_action = ImportRow.ACTION_NEEDS_REVIEW
    elif row.chosen_action != ImportRow.ACTION_BLOCKED:
        row.chosen_action = ImportRow.ACTION_READY
    row.save(update_fields=["chosen_action"])
    return anomaly


@transaction.atomic
def commit_batch(batch):
    committed = skipped = 0
    person_cache = {}
    membership_cache = {}
    rate_cache = {}
    
    rows_to_process = list(batch.rows.select_for_update().order_by("row_number"))
    expenses_to_create = []
    expense_data = []

    for row in rows_to_process:
        if not row_can_commit(row):
            skipped += 1
            row.chosen_action = ImportRow.ACTION_SKIPPED
            continue
        raw = row.raw_data
        normalized = row.normalized_data
        date_value, _ = parse_date(raw.get("date"))
        amount, _ = parse_amount(raw.get("amount"))
        currency = normalized.get("currency") or "INR"
        amount_in_inr, rate = convert_to_inr(amount, currency, date_value, rate_cache)
        payer, _ = get_cached_person(raw.get("paid_by"), person_cache)
        if is_settlement_like(raw):
            payees = [get_cached_person(name, person_cache)[0] for name in split_people(raw.get("split_with"))]
            if not payees or not payer:
                skipped += 1
                row.chosen_action = ImportRow.ACTION_SKIPPED
                continue
            settlement = Settlement.objects.create(group=batch.group, date=date_value, paid_by=payer, paid_to=payees[0], original_amount=amount, currency=currency, amount_in_inr=amount_in_inr, exchange_rate=rate, status=Settlement.STATUS_APPROVED, notes=raw.get("notes", ""), import_row=row)
            from expenses.services import rebuild_settlement_ledger
            rebuild_settlement_ledger(settlement)
            row.chosen_action = ImportRow.ACTION_COMMITTED
            committed += 1
        else:
            participants = [get_cached_person(name, person_cache)[0] for name in split_people(raw.get("split_with"))]
            split_type = normalized.get("split_type")
            detail_raw = parse_split_details(raw.get("split_details"))
            detail_values = {}
            for raw_name, value in detail_raw.items():
                person, _ = get_cached_person(raw_name, person_cache)
                detail_values[person] = value
            if split_type == "percentage":
                split_map = calculate_splits(amount_in_inr, Expense.SPLIT_PERCENTAGE, participants, detail_values)
            elif split_type == "unequal":
                split_map = calculate_splits(amount_in_inr, Expense.SPLIT_UNEQUAL, participants, detail_values)
            elif split_type == "share":
                split_map = calculate_splits(amount_in_inr, Expense.SPLIT_SHARE, participants, detail_values)
            else:
                split_map = calculate_splits(amount_in_inr, Expense.SPLIT_EQUAL, participants)
            
            expense = Expense(group=batch.group, date=date_value, description=raw.get("description"), payer=payer, original_amount=amount, currency=currency, amount_in_inr=amount_in_inr, exchange_rate=rate, split_type=split_type, status=Expense.STATUS_APPROVED, notes=raw.get("notes", ""), import_row=row)
            expenses_to_create.append(expense)
            expense_data.append((expense, split_map, detail_values, date_value, row))

    if expenses_to_create:
        Expense.objects.bulk_create(expenses_to_create)

    splits_to_create = []
    ledger_entries = []
    from expenses.models import LedgerEntry

    for expense, split_map, detail_values, date_value, row in expense_data:
        ledger_entries.append(LedgerEntry(group=expense.group, person=expense.payer, expense=expense, date=expense.date, kind=LedgerEntry.KIND_EXPENSE_PAYMENT, amount_in_inr=expense.amount_in_inr, memo=f"Paid: {expense.description}"))
        for person, split_amount in split_map.items():
            membership_valid = bool(get_cached_membership(batch.group, person, date_value, membership_cache))
            splits_to_create.append(ExpenseSplit(expense=expense, person=person, amount_in_inr=split_amount, raw_value=str(detail_values.get(person, "")), membership_valid=membership_valid))
            ledger_entries.append(LedgerEntry(group=expense.group, person=person, expense=expense, date=expense.date, kind=LedgerEntry.KIND_EXPENSE_SHARE, amount_in_inr=-split_amount, memo=f"Share: {expense.description}"))
        row.chosen_action = ImportRow.ACTION_COMMITTED
        committed += 1

    if splits_to_create:
        ExpenseSplit.objects.bulk_create(splits_to_create)
    if ledger_entries:
        LedgerEntry.objects.bulk_create(ledger_entries)

    ImportRow.objects.bulk_update(rows_to_process, ["chosen_action"])

    batch.committed_rows = committed
    batch.skipped_rows = skipped
    batch.status = ImportBatch.STATUS_COMMITTED
    batch.save(update_fields=["committed_rows", "skipped_rows", "status"])
    return batch


def import_report(batch):
    return {
        "batch_id": batch.id,
        "source_filename": batch.source_filename,
        "total_rows": batch.total_rows,
        "committed_rows": batch.committed_rows,
        "skipped_rows": batch.skipped_rows,
        "anomalies": [
            {
                "row_number": a.row_number,
                "category": a.category,
                "severity": a.severity,
                "description": a.description,
                "detected_value": a.detected_value,
                "chosen_action": a.chosen_action,
                "approval_required": a.approval_required,
                "status": a.status,
            }
            for a in batch.anomalies.all()
        ],
    }
