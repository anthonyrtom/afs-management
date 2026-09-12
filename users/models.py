from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class JobTitle(models.Model):
    title = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title

    @classmethod
    def search(cls, query):
        """
        Searches job titles using case-insensitive partial matching.

        :param query: str (The search keyword)
        :return: QuerySet of JobTitle objects
        """
        if not query or not str(query).strip():
            return cls.objects.none()

        return cls.objects.filter(title__icontains=str(query).strip())

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

    # class Meta:
    #     ordering = ['first_name', 'last_name', 'email']
    #     verbose_name = 'User'
    #     verbose_name_plural = 'Users'

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

    @classmethod
    def filter_by_status_and_job(cls, is_active=None, job_title=None, get_full_name=False):
        """
        Filters CustomUser records by active status and job title.

        :param is_active: bool (True for active only, False for inactive only, None for all)
        :param job_title: int (JobTitle ID) or str (JobTitle title)
        :param get_full_name: bool (If True, returns a list of full names instead of a QuerySet)
        :return: QuerySet of CustomUser OR list of full name strings
        """
        queryset = cls.objects.all().order_by('first_name', 'last_name')

        if is_active is not None:
            queryset = queryset.filter(is_active=is_active)

        if job_title is not None:
            if isinstance(job_title, int) or (isinstance(job_title, str) and job_title.isdigit()):
                queryset = queryset.filter(job_title_id=int(job_title))
            elif isinstance(job_title, str):
                queryset = queryset.filter(
                    job_title__title__iexact=job_title.strip())

        if get_full_name:
            # Returns full names; falls back to email if first/last name are blank
            return [
                user.get_full_name() or user.email
                for user in queryset
            ]

        return queryset
