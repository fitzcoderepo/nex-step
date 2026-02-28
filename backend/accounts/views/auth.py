from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import (BusinessRegistrationSerializer, LoginSerializer, InviteAcceptSerializer,)


class RegisterView(APIView):
    # using AllowAny here, login, and invite since endpoints need to be accessible before a user is authenticated
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = BusinessRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                },
                'business': {
                    'id': str(user.business.id),
                    'name': user.business.name,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }

            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                },
                'business': {
                    'id': str(user.business.id),
                    'name': user.business.name,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },

            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    # blacklisting refresh token here so it can't be used to generate a new access token after logout
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            
            if not refresh_token:
                return Response({'error': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
            
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        
        except Exception:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)
        

class InviteAcceptView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = InviteAcceptSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            return Response({
                'user': {
                    'id': str(user.id),
                    'email': user.email,
                    'full_name': user.full_name,
                    'role': user.role,
                },
                'business': {
                    'id': str(user.business.id),
                    'name': user.business.name,
                },
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }

            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)