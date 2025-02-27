from django.db import models
from django.contrib.auth.models import User
import uuid

# Example for a user named "testuser"
# user = User.objects.get(username='testuser')
# Account.objects.create(
#     user=user,
#     first_name=user.first_name or 'Default',  # Use default if empty
#     last_name=user.last_name or 'User',
#     account_number=str(uuid.uuid4())[:10],    # Generate a unique 10-character ID
#     payment_number=str(uuid.uuid4())[:10],    # Generate a unique 10-character ID
#     balance=50.00
# )
#
# user = User.objects.get(username='root')
# Account.objects.create(
#     user=user,
#     first_name=user.first_name or 'Root',
#     last_name=user.last_name or 'User',
#     account_number=str(uuid.uuid4())[:10],
#     payment_number=str(uuid.uuid4())[:10],
#     balance=50.00
# )

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Links to Django’s built-in User model
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=10, unique=True, default=uuid.uuid4)  # Unique account number
    payment_number = models.CharField(max_length=10, unique=True, default=uuid.uuid4)  # Unique payment number
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=50.00)  # Starts with $50 promo
    is_admin = models.BooleanField(default=False)  # For admin accounts
    is_suspended = models.BooleanField(default=False)  # For suspended accounts
    is_closed = models.BooleanField(default=False)  # For closed accounts (new field)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.account_number})"

class Transaction(models.Model):
    from_account = models.ForeignKey(Account, related_name='sent_transactions', on_delete=models.CASCADE)
    to_account = models.ForeignKey(Account, related_name='received_transactions', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)  # Positive for incoming, negative for outgoing
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set when created

    def __str__(self):
        return f"{self.from_account} -> {self.to_account}: ${self.amount}"

class AdminLog(models.Model):
    admin = models.ForeignKey(Account, on_delete=models.CASCADE)
    action = models.CharField(max_length=200)  # e.g., "Added $100 to user XYZ"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.admin} - {self.action}"
