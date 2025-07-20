from django.urls import path
from . import views

urlpatterns = [
    path('', views.ask, name='ask'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('api/ask/', views.ask_api, name='ask_api'),  # Optional API endpoint
]
