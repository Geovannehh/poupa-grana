from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password


class MemberForm(forms.Form):
    username = forms.CharField(label="Usuário", max_length=150)
    password = forms.CharField(label="Senha inicial", widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if get_user_model().objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Escolha outro nome de usuário.")
        get_user_model()._meta.get_field("username").run_validators(username)
        return username

    def clean(self):
        data = super().clean()
        if data.get("password"):
            user = get_user_model()(username=data.get("username", ""))
            validate_password(data["password"], user)
        return data
