from django.urls import path

from users import views as users_views

urlpatterns = [
    path('token', users_views.MyTokenObtainPairView.as_view()),
    path('register', users_views.RegisterView.as_view()),
]