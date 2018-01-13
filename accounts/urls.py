from django.conf.urls import url

from . import views

app_name = 'accounts'

urlpatterns = [
    url(r'^login', views.LoginView.as_view(), name='login'),
    url(r'^logout', views.LogoutView.as_view(), name='logout'),
    url(r'^staff-login-prompt', views.staff_login_prompt, name='staff-login-prompt'),
    url(r'^edit-profile', views.EditProfileView.as_view(), name='edit-profile'),
]
