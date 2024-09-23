from django.contrib import admin
from django.urls import path
from .views import SignUpView, LoginView, SomeProtectedView

urlpatterns = [
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/check/', SomeProtectedView.as_view(), name='login'),

]