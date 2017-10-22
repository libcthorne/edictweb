from django.conf.urls import url

from . import views

app_name = 'accounts'

urlpatterns = [
    url(r'^login', views.LoginView.as_view(), name='login'),
    url(r'^logout', views.LogoutView.as_view(), name='logout'),
    url(r'^register', views.RegistrationView.as_view(), name='register'),
    url(r'^staff-login-prompt$', views.staff_login_prompt, name='staff-login-prompt'),
]
