from django.urls import path
from .views import create_user_view, get_user_view, update_user_view, delete_user_view

urlpatterns = [
    path('users', create_user_view, name="create_user"),         # POST /users
    path('users/<str:user_id>', get_user_view, name="get_user"),     # GET /users/{user_id}
    path('users/<str:user_id>', update_user_view, name="update_user"), # PUT /users/{user_id}
    path('users/<str:user_id>', delete_user_view, name="delete_user"), # DELETE /users/{user_id}
]
