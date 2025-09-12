from django.contrib.auth.views import LoginView, LogoutView
from django.urls import reverse_lazy

class UserLoginView(LoginView):
    template_name = "users/login.html"

class UserLogoutView(LogoutView):
    next_page = reverse_lazy("home")
