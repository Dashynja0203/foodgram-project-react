from django.conf.urls import include
from django.urls import path
from djoser import views

urlpatterns = [
    path('', include('djoser.urls')),
    path('auth/token/login/', views.TokenCreateView.as_view(), name='login'),
    path('auth/token/logout/', views.TokenDestroyView.as_view(),
         name='logout')]
