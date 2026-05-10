from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = os.getenv("DJANGO_ADMIN_USERNAME")
        password = os.getenv("DJANGO_ADMIN_PASSWORD")
        email = os.getenv("DJANGO_ADMIN_EMAIL", "admin@example.com")

        if not username or not password:
            self.stdout.write("No admin env vars set")
            return

        user, created = User.objects.get_or_create(username=username)
        user.email = email
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

        self.stdout.write(
            f"{'Created' if created else 'Updated'} admin user"
        )