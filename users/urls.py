from django.urls import path
from .views import IndexPage, SignupPageView
from .views import CustomLoginView

urlpatterns = [
    path('', IndexPage.as_view(), name='home'),
    path('signup/', SignupPageView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
]
