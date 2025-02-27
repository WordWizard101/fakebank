from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),  # Correct login URL
    path('logout/', views.logout_view, name='logout'),
    path('account/', views.account, name='account'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('create/', views.create_admin, name='create_admin'),
    path('reset/', views.reset_bank, name='reset_bank'),
    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    path('password_reset/done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    path('transactions/', views.view_transactions, name='view_transactions'),
    path('manage/accounts/', views.manage_accounts, name='manage_accounts'),
    path('manage/account/<int:account_id>/edit_balance/', views.edit_balance, name='edit_balance'),
    path('manage/account/<int:account_id>/close/', views.close_account, name='close_account'),
    path('manage/account/<int:account_id>/suspend/', views.suspend_account, name='suspend_account'),
    path('manage/account/<int:account_id>/delete/', views.delete_account, name='delete_account'),
]
