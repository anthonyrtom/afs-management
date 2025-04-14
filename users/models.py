from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class JobTitle(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.title = self.title.title()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['title']


class CustomUserManager(BaseUserManager):
    """Custom manager for CustomUser to use email instead of username."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email field is required")
        email = self.normalize_email(email)
        # Default new users as inactive
        extra_fields.setdefault("is_active", False)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(unique=True)  # Use email instead

    job_title = models.ForeignKey(
        JobTitle, on_delete=models.SET_NULL, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"  # Use email to log in
    REQUIRED_FIELDS = []  # Remove 'username' from required fields

    def save(self, *args, **kwargs):
        if not CustomUser.objects.exists():
            self.is_superuser = True
            self.is_staff = True
        else:
            if not self.pk:
                self.is_active = False
        super().save(*args, **kwargs)
