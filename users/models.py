from django.db import models
from django.contrib.auth.models import AbstractUser


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


class CustomUser(AbstractUser):
    job_title = models.ForeignKey(
        JobTitle, on_delete=models.SET_NULL, null=True)
