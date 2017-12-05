from django.contrib.auth import forms as default_auth_forms
from django.forms import ModelForm

from .models import Profile

class AuthenticationForm(default_auth_forms.AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = "Username"
        self.fields['username'].widget.attrs['class'] = "form-control"

        self.fields['password'].widget.attrs['placeholder'] = "Password"
        self.fields['password'].widget.attrs['class'] = "form-control"

class UserCreationForm(default_auth_forms.UserCreationForm):
    def __init__(self, *args, **kwargs):
        super(UserCreationForm, self).__init__(*args, **kwargs)

        self.fields['username'].widget.attrs['placeholder'] = "Username"
        self.fields['username'].widget.attrs['class'] = "form-control"

        self.fields['password1'].widget.attrs['placeholder'] = "Password"
        self.fields['password1'].widget.attrs['class'] = "form-control"

        self.fields['password2'].widget.attrs['placeholder'] = "Password (confirmation)"
        self.fields['password2'].widget.attrs['class'] = "form-control"

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['display_name', 'image']

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)

        self.fields['display_name'].widget.attrs['class'] = "form-control"
        self.fields['image'].widget.attrs['class'] = "form-control-file"
