import re
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import GroupMembership, Person, PersonAlias

NAME_ALIASES = {
    "aisha": "Aisha",
    "rohan": "Rohan",
    "priya": "Priya",
    "priya s": "Priya",
    "meera": "Meera",
    "dev": "Dev",
    "sam": "Sam",
    "dev's friend kabir": "Kabir",
    "kabir": "Kabir",
}


def normalize_name(value):
    return re.sub(r"\s+", " ", (value or "").strip()).casefold()


def canonical_name_for(raw_name):
    return NAME_ALIASES.get(normalize_name(raw_name))


def get_or_create_person_for_raw_name(raw_name, allow_unknown=False):
    canonical = canonical_name_for(raw_name)
    if canonical is None and allow_unknown:
        canonical = (raw_name or "").strip()
    if not canonical:
        return None, False
    person, _ = Person.objects.get_or_create(display_name=canonical)
    normalized = normalize_name(raw_name)
    if raw_name and normalized:
        PersonAlias.objects.get_or_create(
            raw_name=raw_name,
            defaults={"normalized_name": normalized, "person": person, "confidence": 100 if canonical == raw_name.strip() else 90},
        )
    return person, canonical != (raw_name or "").strip()


def active_membership(group, person, on_date):
    return GroupMembership.objects.filter(group=group, person=person, joined_on__lte=on_date).filter(Q(left_on__isnull=True) | Q(left_on__gte=on_date)).first()


def validate_membership_period(group, person, joined_on, left_on, exclude_id=None):
    if left_on and left_on < joined_on:
        raise ValidationError("left_on must be on or after joined_on.")
    qs = GroupMembership.objects.filter(group=group, person=person)
    if exclude_id:
        qs = qs.exclude(id=exclude_id)
    for existing in qs:
        existing_end = existing.left_on
        new_end = left_on
        overlaps = joined_on <= (existing_end or joined_on) and existing.joined_on <= (new_end or existing.joined_on)
        if existing_end is None and (new_end is None or new_end >= existing.joined_on):
            overlaps = True
        if new_end is None and joined_on <= (existing_end or joined_on):
            overlaps = True
        if overlaps:
            raise ValidationError("Membership periods for the same person and group cannot overlap.")
