from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm  # Import for user registration
from .models import Account, Transaction  # Import both models
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
            return redirect('account')
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
        amount = Decimal(request.POST.get('amount', '0'))  # Convert to Decimal
        if action == 'deposit':
            acct.balance += amount
        elif action == 'withdraw' and acct.balance - amount >= Decimal('-5'):  # Use Decimal for -5
            acct.balance -= amount
        acct.save()
        # Log transaction
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
        'currency_label': currency_label
    })

# Register view (updated)
def register(request):
    if request.method == 'POST':
        user_form = UserCreationForm(request.POST)
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
        user_form = UserCreationForm()
    return render(request, 'register.html', {'user_form': user_form})
