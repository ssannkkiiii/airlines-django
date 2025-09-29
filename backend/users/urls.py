from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.UserRegisterView.as_view(), name='user-register'),
    path('login/', views.UserLoginView.as_view(), name='user-login'),
    path('logout/', views.LogoutView.as_view(), name='user-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    
    path('google/login/', views.GoogleLoginInitView.as_view(), name='google-oauth'),
    path('google/callback/', views.GoogleAuthCallbackView.as_view(), name='google-token'),
      
    path('profile/', views.UserProfileView.as_view(), name='user-profile'),
    path('profile/update/', views.UserUpdateView.as_view(), name='user-profile-update'),
    
    path('users/', views.UserListView.as_view(), name='users-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
]



