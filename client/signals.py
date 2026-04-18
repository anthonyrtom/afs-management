from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Event, RecurringEvent, Client


@receiver(post_save, sender=Client)
def update_recurring_event_table(sender, instance, created, **kwargs):
    if created:
        print("Instance created")
    else:
        print("Instance updated")
