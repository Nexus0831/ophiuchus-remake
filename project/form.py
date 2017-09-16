from django import forms
from .models import CustomUser


class UserForm(forms.Form):
    username = forms.CharField(max_length=256)


class ErrorForm(forms.Form):
    decoy = forms.CharField(max_length=0)


class UserCreationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch':"パスワードが正しくありません",
    }
    password1 = forms.CharField(label="パスワード",
        widget=forms.PasswordInput)
    password2 = forms.CharField(label="パスワード確認",
        widget=forms.PasswordInput,
        help_text="確認のため上記と同じパスワードを入力してください")

    class Meta:
        model = CustomUser
        fields = ("username",)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user