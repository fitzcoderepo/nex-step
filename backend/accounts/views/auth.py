from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import (BusinessRegistrationSerializer, LoginSerializer, InviteAcceptSerializer,)


class RegisterView(APIView):
    """
    Handles business and owner registration.

    Creates a new Business and owner User account in a single request.
    Returns user details, business details, and JWT tokens on success
    so the frontend can initialize the session immediately.

    Args:
        business_name (str): The name of the business.
        full_name (str): The full name of the owner.
        email (str): The owner's email address.
        password (str): The owner's password.
        confirm_password (str): Must match password.

    Raises:
        serializers.ValidationError: If any required fields are missing or invalid.

    Returns:
        dict: User details, business details, and JWT access and refresh tokens.
    """

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
    """
    Handles user authentication.

    Validates user credentials and returns JWT tokens on success
    along with user and business details for session initialization.

    Args:
        email (str): The user's email address.
        password (str): The user's password.

    Raises:
        serializers.ValidationError: If credentials are invalid or account is inactive.

    Returns:
        dict: User details, business details, and JWT access and refresh tokens.
    """

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
    """
    Handles user logout by blacklisting the refresh token.

    Requires the refresh token in the request body. Once blacklisted
    the token cannot be used to generate new access tokens.

    Args:
        refresh (str): The JWT refresh token to blacklist.

    Raises:
        serializers.ValidationError: If the refresh token is missing, invalid, or expired.

    Returns:
        dict: A success message confirming the logout.
    """

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
    """
    Handles invite acceptance and new user account creation.

    Validates the invite token, creates the user account, marks the
    invite as accepted, and returns JWT tokens so the new user is
    logged in immediately after accepting their invite.

    Args:
        token (UUID): The unique invite token from the invite link.
        full_name (str): The full name of the invited user.
        password (str): The new user's password.
        confirm_password (str): Must match password.

    Raises:
        serializers.ValidationError: If the token is invalid, expired, or already accepted.
        serializers.ValidationError: If password and confirm_password do not match.

    Returns:
        dict: User details, business details, and JWT access and refresh tokens.
    """
    
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