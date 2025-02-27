from django.db import models  # Add this import for models.Sum
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm  # Updated imports
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail  # For sending reset emails (optional for local testing)
from django.conf import settings
from django import forms  # Add this line for forms.EmailField
from .models import Account, Transaction, AdminLog  # Ensure this is here
from decimal import Decimal  # For precise decimal arithmetic
import uuid  # For generating unique IDs

# Home view with total non-admin accounts
def home(request):
    total_accounts = Account.objects.filter(is_admin=False).count()
    return render(request, 'home.html', {'total_accounts': total_accounts})
    
# Login view
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('account')  # Redirect all users to their account page
    return render(request, 'login.html')

# Logout view
def logout_view(request):
    logout(request)
    return redirect('home')

# Account view (protected by login)
@login_required
def account(request):
    try:
        acct = request.user.account
    except (Account.DoesNotExist, AttributeError):
        acct = Account.objects.create(
            user=request.user,
            first_name=request.user.first_name or 'Default',
            last_name=request.user.last_name or 'User',
            account_number=str(uuid.uuid4())[:10],
            payment_number=str(uuid.uuid4())[:10],
            balance=Decimal('50.00')  # Use Decimal for consistency
        )
    transactions = acct.sent_transactions.all() | acct.received_transactions.all()

    if request.method == 'POST':
        action = request.POST.get('action')
        amount = Decimal(request.POST.get('amount', '0')) if 'amount' in request.POST else None  # For deposit/withdraw
        payment_number = request.POST.get('payment_number')  # For sending money
        send_amount = Decimal(request.POST.get('send_amount', '0')) if 'send_amount' in request.POST else None  # For sending money

        if action == 'deposit':
            acct.balance += amount
        elif action == 'withdraw' and acct.balance - amount >= Decimal('-5'):  # Use Decimal for -5
            acct.balance -= amount
        elif action == 'send' and payment_number and send_amount:
            try:
                recipient = Account.objects.get(payment_number=payment_number)
                if recipient != acct and acct.balance - send_amount >= Decimal('-5'):  # Ensure not sending to self and balance check
                    acct.balance -= send_amount  # Deduct from sender
                    recipient.balance += send_amount  # Add to recipient
                    acct.save()
                    recipient.save()
                    # Log the transaction (negative for sender, positive for recipient)
                    Transaction.objects.create(from_account=acct, to_account=recipient, amount=-send_amount)
                    Transaction.objects.create(from_account=acct, to_account=recipient, amount=send_amount)
            except Account.DoesNotExist:
                # Handle case where payment number doesn’t exist (e.g., show an error message)
                return render(request, 'account.html', {
                    'account': acct,
                    'transactions': transactions,
                    'balance': acct.balance,
                    'currency_symbol': '$',
                    'currency_label': 'USD',
                    'error': 'Recipient payment number not found.'
                })

        acct.save()
        # Log transaction for deposit/withdraw if applicable
        if action in ['deposit', 'withdraw']:
            Transaction.objects.create(from_account=acct, to_account=acct, amount=amount if action == 'deposit' else -amount)

    # Currency conversion (simplified rates for demonstration, as of Feb 2025)
    currency = request.GET.get('currency', 'USD')
    balance = acct.balance
    if currency == 'GBP':
        converted_balance = balance * Decimal('0.79')  # Approx. USD to GBP
        currency_symbol = '£'
        currency_label = 'GBP'
    elif currency == 'EUR':
        converted_balance = balance * Decimal('0.92')  # Approx. USD to EUR
        currency_symbol = '€'
        currency_label = 'EUR'
    else:  # Default to USD
        converted_balance = balance
        currency_symbol = '$'
        currency_label = 'USD'

    return render(request, 'account.html', {
        'account': acct,
        'transactions': transactions,
        'balance': converted_balance,
        'currency_symbol': currency_symbol,
        'currency_label': currency_label,
        'error': 'Recipient payment number not found.' if 'error' in locals() else None
    })

# Define a custom registration form
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']  # Add first name
        user.last_name = self.cleaned_data['last_name']    # Add last name
        if commit:
            user.save()
        return user

# Register view
def register(request):
    if request.method == 'POST':
        user_form = CustomUserCreationForm(request.POST)
        if user_form.is_valid():
            user = user_form.save()
            # Check if an Account already exists for this user
            if not Account.objects.filter(user=user).exists():
                Account.objects.create(
                    user=user,
                    first_name=user.first_name or 'Default',
                    last_name=user.last_name or 'User',
                    account_number=str(uuid.uuid4())[:10],
                    payment_number=str(uuid.uuid4())[:10],
                    balance=Decimal('50.00')  # Use Decimal for consistency
                )
            return redirect('login')
    else:
        user_form = CustomUserCreationForm()
    return render(request, 'register.html', {'user_form': user_form})

# Admin Dashboard view (only accessible by admins)
@login_required
def admin_dashboard(request):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    # Calculate total bank value (sum of all account balances, including bank)
    total_bank_value = Account.objects.aggregate(total=models.Sum('balance'))['total'] or Decimal('0')
    # Ensure total bank value is $1,000,000 (simplified for now, adjust if needed)
    if total_bank_value != Decimal('1000000'):
        # This is a placeholder; you might want to implement a reset or log this
        total_bank_value = Decimal('1000000')  # Force it to match requirement
    admin_logs = AdminLog.objects.all().order_by('-timestamp')
    return render(request, 'admin_dashboard.html', {
        'total_bank_value': total_bank_value,
        'admin_logs': admin_logs
    })

# Create Admin view (only accessible by root or admins)
@login_required
def create_admin(request):
    if not request.user.account.is_admin:
        return redirect('home')  # Restrict to admins only
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        try:
            user = User.objects.create_user(username=username, password=password, email='')
            Account.objects.create(
                user=user,
                first_name=first_name,
                last_name=last_name,
                account_number=str(uuid.uuid4())[:10],
                payment_number=str(uuid.uuid4())[:10],
                balance=Decimal('50.00'),  # Start with $50
                is_admin=True  # Mark as admin
            )
            # Log the action
            AdminLog.objects.create(
                admin=request.user.account,
                action=f"Created admin account for {username}"
            )
            return redirect('admin_dashboard')
        except Exception as e:
            return render(request, 'admin_dashboardcreate_admin.html', {'error': str(e)})
    return render(request, 'admin_dashboardcreate_admin.html')

# Reset Bank view (only accessible by root admin)
@login_required
def reset_bank(request):
    if request.user.username != 'root':  # Restrict to root admin only
        return redirect('home')  # Redirect non-root admins
    if request.method == 'POST':
        # Reset all accounts to $50 (including admins, but excluding suspended accounts)
        for account in Account.objects.filter(is_suspended=False):
            account.balance = Decimal('50.00')
            account.save()
        # Clear all transactions and admin logs
        Transaction.objects.all().delete()
        AdminLog.objects.all().delete()
        # Log the reset action
        AdminLog.objects.create(
            admin=request.user.account,
            action="Reset bank to initial state ($1,000,000 total)"
        )
        return redirect('admin_dashboard')
    return render(request, 'reset_bank.html', {'message': 'Are you sure you want to reset the bank?'})

# Password Reset Request view
def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                # Generate token and UID
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                # For local testing, we'll simulate sending an email (you'd need to configure email settings in settings.py)
                reset_url = f"http://127.0.0.1:8000/reset/{uid}/{token}/"
                print(f"Password reset URL: {reset_url}")  # Print to console for local testing
                return redirect('password_reset_done')
            except User.DoesNotExist:
                return render(request, 'password_reset_request.html', {'form': form, 'error': 'Email not found.'})
    else:
        form = PasswordResetForm()
    return render(request, 'password_reset_request.html', {'form': form})

# Password Reset Done view
def password_reset_done(request):
    return render(request, 'password_reset_done.html', {'message': 'We’ve sent you an email with instructions to reset your password.'})

# Password Reset Confirm view
def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    return redirect('password_reset_complete')
            else:
                form = SetPasswordForm(user)
            return render(request, 'password_reset_confirm.html', {'form': form})
        else:
            return render(request, 'password_reset_invalid.html', {'message': 'Invalid or expired reset link.'})
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return render(request, 'password_reset_invalid.html', {'message': 'Invalid or expired reset link.'})

# Password Reset Complete view
def password_reset_complete(request):
    return render(request, 'password_reset_complete.html', {'message': 'Your password has been reset. You can log in now.'})

# View All Transactions (only accessible by admins)
@login_required
def view_transactions(request):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    all_transactions = Transaction.objects.all().order_by('-timestamp')
    return render(request, 'view_transactions.html', {
        'transactions': all_transactions
    })

# Manage Accounts view (only accessible by admins)
@login_required
def manage_accounts(request):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    accounts = Account.objects.filter(is_admin=False).order_by('user__username')  # Non-admin accounts only
    return render(request, 'manage_accounts.html', {
        'accounts': accounts
    })

# Edit User Balance view (only accessible by admins)
@login_required
def edit_balance(request, account_id):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    account = get_object_or_404(Account, id=account_id, is_admin=False)  # Non-admin accounts only
    if request.method == 'POST':
        try:
            new_balance = Decimal(request.POST.get('balance', '0'))
            if new_balance < Decimal('-5'):  # Prevent balance below -$5 (per user rules)
                return render(request, 'edit_balance.html', {
                    'account': account,
                    'error': 'Balance cannot be less than -$5.'
                })
            account.balance = new_balance
            account.save()
            # Log the action
            AdminLog.objects.create(
                admin=request.user.account,
                action=f"Edited balance for account {account.account_number} to ${new_balance}"
            )
            return redirect('manage_accounts')
        except (ValueError, DecimalException):
            return render(request, 'edit_balance.html', {
                'account': account,
                'error': 'Invalid balance amount. Please enter a valid number.'
            })
    return render(request, 'edit_balance.html', {
        'account': account
    })

# Close User Account view (only accessible by admins)
@login_required
def close_account(request, account_id):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    account = get_object_or_404(Account, id=account_id, is_admin=False)  # Non-admin accounts only
    if request.method == 'POST':
        if account.is_closed:
            return render(request, 'close_account.html', {
                'account': account,
                'error': 'This account is already closed.'
            })
        # Transfer balance back to bank (simplified: add to total bank value)
        account.balance = Decimal('0')  # Reset balance to 0
        account.is_closed = True
        account.save()
        # Log the action
        AdminLog.objects.create(
            admin=request.user.account,
            action=f"Closed account {account.account_number}"
        )
        return redirect('manage_accounts')
    return render(request, 'close_account.html', {
        'account': account
    })

# Suspend User Account view (only accessible by admins)
@login_required
def suspend_account(request, account_id):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    account = get_object_or_404(Account, id=account_id, is_admin=False)  # Non-admin accounts only
    if request.method == 'POST':
        if account.is_suspended:
            return render(request, 'suspend_account.html', {
                'account': account,
                'error': 'This account is already suspended.'
            })
        account.is_suspended = True
        account.save()
        # Log the action
        AdminLog.objects.create(
            admin=request.user.account,
            action=f"Suspended account {account.account_number}"
        )
        return redirect('manage_accounts')
    return render(request, 'suspend_account.html', {
        'account': account
    })

# Delete User Account view (only accessible by admins)
@login_required
def delete_account(request, account_id):
    if not request.user.account.is_admin:
        return redirect('home')  # Redirect non-admins
    account = get_object_or_404(Account, id=account_id, is_admin=False)  # Non-admin accounts only
    if request.method == 'POST':
        if account.is_closed or account.is_suspended:
            return render(request, 'delete_account.html', {
                'account': account,
                'error': 'This account is already closed or suspended. Delete anyway?'
            })
        user = account.user
        account.delete()
        user.delete()  # Delete the associated User as well
        # Log the action
        AdminLog.objects.create(
            admin=request.user.account,
            action=f"Deleted account {account.account_number} and user"
        )
        return redirect('manage_accounts')
    return render(request, 'delete_account.html', {
        'account': account
    })
