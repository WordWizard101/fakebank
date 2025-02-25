from django.db.models.signals import post_save
from django.contrib.auth.models import User
import uuid

def create_account(sender, instance, created, **kwargs):
    from .models import Account
    if created:
        Account.objects.create(
            user=instance,
            first_name=instance.first_name,
            last_name=instance.last_name,
            account_number=str(uuid.uuid4())[:10],
            payment_number=str(uuid.uuid4())[:10],
            balance=50.00  # $50 promo
        )

post_save.connect(create_account, sender=User)
