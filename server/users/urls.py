from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users import views as users_views

urlpatterns = [
    path('token', users_views.MyTokenObtainPairView.as_view()),
    path('token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('register', users_views.RegisterView.as_view()),
    path('password-reset/<str:email>', users_views.PasswordEmailVerifyView.as_view()),
    path('new-password', users_views.PasswordChangeView.as_view()),
]