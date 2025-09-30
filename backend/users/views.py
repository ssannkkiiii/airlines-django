from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import User
from .serializers import (
    UserRegisterSerializer, 
    UserLoginSerializer, 
    UserProfileSerializer,
    LogoutSerializer
)
from .permissions import IsAdminUser 
from rest_framework import generics
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
import requests

class UserRegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': 'Login successful',
        })

class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user 
    
    
class UserUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]
    
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAdminUser]

class LogoutView(GenericAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    @extend_schema(request=LogoutSerializer)
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refresh_token = serializer.validated_data["refresh"]
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


class GoogleLoginInitView(APIView):
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        auth_url = (
            f"{settings.GOOGLE_AUTH_URI}"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URL}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
        )
        return Response({"auth_url": auth_url})
    
class GoogleAuthCallbackView(APIView):
    
    permission_classes = [AllowAny]
    
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            return Response({"error": "No code provided"}, status=400)

        token_data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URL,
            "grant_type": "authorization_code",
        }
        token_resp = requests.post(settings.GOOGLE_TOKEN_URI, data=token_data)
        token_json = token_resp.json()

        if "error" in token_json:
            return Response(token_json, status=400)

        access_token = token_json["access_token"]

        userinfo_resp = requests.get(
            settings.GOOGLE_USERINFO_URI,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo = userinfo_resp.json()

        email = userinfo.get("email")
        name = userinfo.get("name")
        picture = userinfo.get("picture")

        if not email:
            return Response({"error": "No email from Google"}, status=400)

        user, _ = User.objects.get_or_create(email=email, defaults={"username": email, "first_name": name})

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": {
                "email": email,
                "name": name,
                "picture": picture,
            }
        })