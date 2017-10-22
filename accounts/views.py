from django.contrib.auth import views as default_auth_views
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from django.views.generic.edit import CreateView

class LoginView(default_auth_views.LoginView):
    pass

class LogoutView(default_auth_views.LogoutView):
    pass

class RegistrationView(CreateView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = '/'


def staff_login_prompt(request):
    return render(request, 'accounts/staff_login_prompt.html')
