from django.urls import path
from .views import IndexPage, SignupPageView

urlpatterns = [
    path('', IndexPage.as_view(), name='home'),
    path('signup/', SignupPageView.as_view(), name='signup')
]
