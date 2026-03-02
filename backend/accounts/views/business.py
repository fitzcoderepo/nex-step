from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.serializers import(BusinessSerializer, BusinessUpdateSerializer, RegenerateApiKeySerializer)
from accounts.permissions import IsOwner, IsAdminOrOwner


class BusinessView(APIView):
    """
    Retrieve and update the authenticated user's business.

    Business creation is handled automatically during registration.
    Only admins and owners can access this endpoint.

    GET:
        Returns full business details including capacity information.

    PATCH:
        Updates the business name. Only the name field is exposed for updating.

    Raises:
        serializers.ValidationError: If the name field is missing or invalid on PATCH.

    Returns:
        dict: Serialized business data.
    """

    permission_classes = [IsAdminOrOwner]

    def get(self, request):
        business = request.user.business # the business is always derived from the logged in user
        serializer = BusinessSerializer(business)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = BusinessUpdateSerializer(request.user.business, data=request.data, partial=True) # using partial as not all fields required here

        if serializer.is_valid():
            serializer.save()

            # pass the full business details here to give frontend everything it needs to refresh its state
            return Response(BusinessSerializer(request.user.business).data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegenerateApiKeyView(APIView):
    """
    Handles API key rotation for a business.

    Generates a new API key for the business while keeping the old key
    valid for the duration of the grace period. This allows the owner
    time to update live widget embeds without causing disruption.
    Restricted to the business owner only.

    Args:
        confirm (bool): Must be True to proceed.
        grace_period_hours (int): How long the old key remains valid.
                                  Defaults to 48 hours, maximum 168 hours.

    Raises:
        serializers.ValidationError: If confirm is False or not provided.
        serializers.ValidationError: If grace_period_hours is outside 1-168.

    Returns:
        dict: Updated business details including the new api_key,
              old_api_key, and old_api_key_expires_at.
    """
    
    permission_classes = [IsOwner]

    def post(self, request):
        business = request.user.business
        serializer = RegenerateApiKeySerializer(business, data=request.data)

        if serializer.is_valid():
            updated_business = serializer.save()

            return Response({
                'business': {
                    'name': business.name,
                    'api_key': updated_business.api_key,
                    'old_api_key': updated_business.old_api_key,
                    'old_api_key_expires_at': updated_business.old_api_key_expires_at
                },

            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

