from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from imports.services import ensure_seed_data


class Command(BaseCommand):
    help = "Seed the assignment group, people, memberships, aliases, and USD rates."

    def handle(self, *args, **options):
        User = get_user_model()
        user, created = User.objects.get_or_create(username="demo", defaults={"email": "demo@example.com"})
        if created:
            user.set_password("demo12345")
            user.save(update_fields=["password"])
        group = ensure_seed_data(user)
        self.stdout.write(self.style.SUCCESS(f"Seeded {group.name}. Demo login: demo / demo12345"))
