from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path('api/signup/', SignUpView.as_view(), name='signup'),
    path('api/login/', LoginView.as_view(), name='login'),
    path('api/user-search', UserSearchView.as_view(), name='user_search'),
    path('api/friend-request/', FriendRequestView.as_view(), name='send_friend_request'),
    path('api/friend-request/<int:pk>/', FriendRequestView.as_view(), name='respond_friend_request'),
    path('api/blocked/', BlockUserView.as_view(), name='blocking_user'),
    path('api/unblocked/', UnblockUserView.as_view(), name='unblock_user'),
    path('api/friend-list/', FriendsListAPI.as_view(), name='friend_list'),
    path('api/pending-list/', PendingFriendRequestsAPI.as_view(), name='pending_list'),
    path('api/user-activity/', UserActivityLogAPI.as_view(), name="user-activity"),
]