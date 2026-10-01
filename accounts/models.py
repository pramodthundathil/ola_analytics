from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("SUPERUSER", "Superuser"),
        ("ADMIN", "Admin"),
        ("ANALYST", "Analyst"),
        ("VIEWER", "Viewer"),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="VIEWER")
    department = models.CharField(max_length=100, blank=True, null=True)

    def is_superuser_role(self):
        return self.role == "SUPERUSER" or self.is_superuser

    def is_analyst_role(self):
        return self.role in ["SUPERUSER", "ADMIN", "ANALYST"]
