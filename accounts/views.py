from django.contrib.auth import views as default_auth_views
from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView

from .forms import (
    AuthenticationForm,
    ProfileForm,
)
from . import queries

class LoginView(default_auth_views.LoginView):
    form_class = AuthenticationForm

class LogoutView(default_auth_views.LogoutView):
    pass

class EditProfileView(UpdateView):
    template_name = 'accounts/edit_profile.html'
    form_class = ProfileForm
    success_url = '/'

    def get_object(self):
        return queries.get_or_create_user_profile(self.request.user)

def staff_login_prompt(request):
    return render(request, 'accounts/staff_login_prompt.html')
