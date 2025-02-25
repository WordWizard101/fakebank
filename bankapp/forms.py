from django import forms
import uuid
class AccountForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ['first_name', 'last_name']
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.account_number = str(uuid.uuid4())[:10]
        instance.payment_number = str(uuid.uuid4())[:10]
        if commit:
            instance.save()
        return instance