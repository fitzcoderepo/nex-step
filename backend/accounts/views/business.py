from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import(BusinessSerializer, BusinessUpdateSerializer, RegenerateApiKeySerializer)
from accounts.permissions import IsOwner, IsAdminOrOwner


class BusinessView(APIView):
    permission_classes = [IsAdminOrOwner]

    

