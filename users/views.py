from django.contrib.auth.views import LoginView
from .forms import CustomAuthenticationForm
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm


class IndexPage(TemplateView):
    template_name = 'home.html'


class SignupPageView(CreateView):

    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'


class CustomLoginView(LoginView):
    authentication_form = CustomAuthenticationForm
    template_name = "users/login.html"
