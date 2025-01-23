from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm


class IndexPage(TemplateView):
    template_name = 'home.html'

class SignupPageView(CreateView):
    
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'