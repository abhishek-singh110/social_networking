from .serializers import SignUpSerializer, LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from rest_framework.permissions import IsAuthenticated
from django.contrib.postgres.search import SearchVector
from .permissions import RoleBasedPermission
from rest_framework.response import Response
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from .pagination import UserPagination
from django.core.cache import cache
from rest_framework import status
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
from .models import *


# This api for sign up.
class SignUpView(APIView):
    def post(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "User registered successfully",
                "status_code": 201
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# This api for login.
class LoginView(APIView):
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email'].lower()
            password = serializer.validated_data['password']
            user = authenticate(request, email=email, password=password)

            if user is not None:
                # Generate JWT tokens (access and refresh)
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token

                return Response({
                    'message': 'Login successful!',
                    'access_token': str(access_token),
                    'refresh_token': str(refresh)
                }, status=status.HTTP_200_OK)
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# This api is for searching via email or named.
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get(self, request):
        search_keyword = request.query_params.get('q', '')

        if search_keyword:
            # Check if the keyword matches an exact email
            user_by_email = CustomUser.objects.filter(email__iexact=search_keyword).first()

            if user_by_email:
                # If an email matches, return the user
                return Response({
                    'id': user_by_email.id,
                    'email': user_by_email.email,
                    'first_name': user_by_email.first_name,
                    'last_name': user_by_email.last_name
                }, status=status.HTTP_200_OK)

            # If no email match, perform full-text search by name
            users_by_name = CustomUser.objects.annotate(
                search=SearchVector('first_name', 'last_name')
            ).filter(search=search_keyword)

            if users_by_name.exists():
                # Apply pagination to the name search results
                paginator = UserPagination()
                paginated_users = paginator.paginate_queryset(users_by_name, request)

                user_list = [{
                    'id': user.id,
                    'email': user.email,
                    'name': user.first_name
                } for user in paginated_users]

                # Return the paginated response
                return paginator.get_paginated_response(user_list)

        # If no users are found
        return Response({'message': 'No users found'}, status=status.HTTP_404_NOT_FOUND)


# This api is for send the friend request to the users and also for perform action like accept or reject.
class FriendRequestView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        # Sending a friend request
        receiver_email = request.data.get('receiver_email')

        try:
            receiver = CustomUser.objects.get(email=receiver_email)
            if receiver == request.user:
                return Response({"error": "You cannot send a friend request to yourself."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if the user is blocked or has blocked the receiver
            if Block.objects.filter(blocker=request.user, blocked=receiver).exists():
                return Response({"error": "You have blocked this user and cannot send a friend request."}, status=status.HTTP_403_FORBIDDEN)
            if Block.objects.filter(blocker=receiver, blocked=request.user).exists():
                return Response({"error": "You are blocked by this user and cannot send a friend request."}, status=status.HTTP_403_FORBIDDEN)

            # Check if the receiver has already sent a request to the user
            reverse_request = FriendRequest.objects.filter(sender=receiver, receiver=request.user).first()

            if reverse_request and reverse_request.status == 'pending':
                return Response({"message": "This user has already sent you a request. Please respond to their request."}, status=status.HTTP_200_OK)

            # Check if the sender has already sent a request to the receiver
            friend_request = FriendRequest.objects.filter(sender=request.user, receiver=receiver, ).first()

            if friend_request:
                if friend_request.status == 'rejected' and friend_request.rejected_at:
                    # Cooldown check: Ensure cooldown has passed after rejection
                    time_since_rejection = timezone.now() - friend_request.rejected_at
                    if time_since_rejection < settings.COOLDOWN_PERIOD:
                        cooldown_remaining = settings.COOLDOWN_PERIOD - time_since_rejection
                        return Response({"error": f"You cannot send a request to this user for another {cooldown_remaining.seconds // 3600} hours."},
                                        status=status.HTTP_403_FORBIDDEN)
                    else:
                        # Cooldown passed, delete the previous rejected request
                        friend_request.delete()
                else:
                    # If the request is pending or accepted, return error
                    return Response({"error": "Friend request already sent."}, status=status.HTTP_400_BAD_REQUEST)

            # Rate limiting: Check how many friend requests were sent by this user in the last minute
            one_minute_ago = timezone.now() - timedelta(minutes=1)
            recent_requests_count = FriendRequest.objects.filter(sender=request.user, created_at__gte=one_minute_ago).count()

            if recent_requests_count >= 3:
                return Response({"error": "You can only send 3 friend requests per minute. Please try again later."}, status=status.HTTP_429_TOO_MANY_REQUESTS)

            # Create a new friend request
            friend_request, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=receiver)

            if created:
                # Log the activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity=f"Sent a friend request to {receiver.email}"
                )
                return Response({"message": "Friend request sent."}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "Receiver not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk):
        # Accepting or rejecting a friend request
        try:
            friend_request = FriendRequest.objects.get(pk=pk, receiver=request.user)
            action = request.data.get('action')  # 'accept' or 'reject'

            # Check if the request is still pending
            if friend_request.status != 'pending':
                return Response({"message": f"You have already {friend_request.status} this friend request."}, status=status.HTTP_400_BAD_REQUEST)

            if action == 'accept':
                friend_request.status = 'accepted'
                friend_request.save()

                # Log the activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity=f"You have accepted the friend request of {friend_request.sender}"
                )
                # Invalidate cache for both users
                cache.delete(f"friends_list_{friend_request.sender.id}")
                cache.delete(f"friends_list_{friend_request.receiver.id}")
                return Response({"message": "Friend request accepted."}, status=status.HTTP_200_OK)
            elif action == 'reject':
                friend_request.status = 'rejected'
                friend_request.rejected_at = timezone.now()
                friend_request.save()
                # Log the activity
                UserActivityLog.objects.create(
                    user=request.user,
                    activity=f"You have rejected the friend request of {friend_request.sender__email}"
                )
                return Response({"message": "Friend request rejected."}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid action."}, status=status.HTTP_400_BAD_REQUEST)

        except FriendRequest.DoesNotExist:
            return Response({"error": "Friend request not found."}, status=status.HTTP_404_NOT_FOUND)


# This api is for blocked the users.
class BlockUserView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        blocked_email = request.data.get('blocked_email')

        try:
            blocked_user = CustomUser.objects.get(email=blocked_email)

            # Prevent self-blocking
            if blocked_user == request.user:
                return Response({"error": "You cannot block yourself."}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the user is already blocked
            if Block.objects.filter(blocker=request.user, blocked=blocked_user).exists():
                return Response({"error": "User is already blocked."}, status=status.HTTP_400_BAD_REQUEST)

            # Block the user
            Block.objects.create(blocker=request.user, blocked=blocked_user)

            # Log the activity
            UserActivityLog.objects.create(
                user=request.user,
                activity=f"You have blocked this {blocked_email}"
            )
            return Response({"message": "User blocked successfully."}, status=status.HTTP_201_CREATED)

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# This api is for unblock the user who has been blocked by you.
class UnblockUserView(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def post(self, request):
        blocked_email = request.data.get('blocked_email')

        try:
            blocked_user = CustomUser.objects.get(email=blocked_email)

            # Check if the user is blocked
            block_entry = Block.objects.filter(blocker=request.user, blocked=blocked_user).first()
            if not block_entry:
                return Response({"error": "User is not blocked."}, status=status.HTTP_400_BAD_REQUEST)

            # Unblock the user
            block_entry.delete()
            # Log the activity
            UserActivityLog.objects.create(
                user=request.user,
                activity=f"You have unblocked this {blocked_email}"
            )
            return Response({"message": "User unblocked successfully."}, status=status.HTTP_200_OK)

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)


# This api is for showing the friend list.
class FriendsListAPI(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    
    def get(self, request):
        user = request.user
        cache_key = f"friends_list_{user.id}"
        
        # Try fetching friends list from the cache
        friends_list = cache.get(cache_key)
        
        if not friends_list:
            # If not in cache, query the database
            accepted_friend_requests = FriendRequest.objects.filter(
                Q(sender=user, status='accepted') | Q(receiver=user, status='accepted')
            ).select_related('sender', 'receiver')
            
            # Get list of friends from the accepted requests
            friends_list = [
                request.receiver.email if request.sender == user else request.sender.email
                for request in accepted_friend_requests
            ]
            
            # Save the friends list to cache
            cache.set(cache_key, friends_list, settings.CACHE_TIMEOUT)
        
        return Response({"message":"Successfully fetched","friends": friends_list}, status=status.HTTP_200_OK)


# This api is for showing the pending friend list.
class PendingFriendRequestsAPI(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]
    pagination_class = UserPagination

    def get(self, request):
        user = request.user
        
        # Fetch pending friend requests where the receiver is the user
        pending_requests = FriendRequest.objects.filter(receiver=user, status='pending').order_by('-created_at')

        # Pagination
        paginator = UserPagination()
        paginated_requests = paginator.paginate_queryset(pending_requests, request)

        # Prepare the response data
        response_data = [
            {
                "request_id": request.id,
                "created_at": request.created_at,
                # Only include the sender's ID and status, not sensitive info like email
                "sender_id": request.sender.id,
                "status": request.status
            }
            for request in paginated_requests
        ]
        return paginator.get_paginated_response(response_data)


# This api is for showing the user activity.
class UserActivityLogAPI(APIView):
    permission_classes = [IsAuthenticated, RoleBasedPermission]

    def get(self, request):
        user = request.user
        # # Caching mechanism (optional) - we can perform the cache also there to make the performance better
        # cache_key = f"user_activity_log_{user.id}"
        # cached_activities = cache.get(cache_key)
        # if cached_activities is not None:
        #     return Response({"activities": cached_activities}, status=status.HTTP_200_OK)

        # Retrieve activity logs with related user details
        activity_logs = UserActivityLog.objects.filter(user=user).select_related('user').order_by('-created_at')
        activity_data = [
            {
                "activity": log.activity,
                "created_at": log.created_at,
                "user_email": log.user.email 
            }
            for log in activity_logs
        ]
        # cache.set(cache_key, activity_data, settings.CACHE_TIMEOUT)
        return Response({"message":"Successfully fetched user activity", "activities": activity_data}, status=status.HTTP_200_OK)
