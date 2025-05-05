# api/urls.py
from django.urls import path
from .views import location_update_view, get_events, get_recommended_events, create_bet, list_bets, bet_detail,create_user_endpoint,get_user_endpoint,update_user_endpoint,delete_user_endpoint, trigger_sports_polling
from .views import login_probe 

urlpatterns = [
    path('location', location_update_view, name='location_update'),
    path('events', get_events, name="get_events"),
    path('events/recommended/', get_recommended_events, name="get_recommended_events"),
    path('bets', create_bet, name='create_bet'),        # POST /bets
    path('bets/history', list_bets, name='list_bets'),            # GET /bets/history?userId=...
    path('betsA/<str:bet_id>', bet_detail, name='bet_detail'),  # GET /bets/{betId}
    path('users', create_user_endpoint, name="create_user"),          # POST /users,
    path('users/<str:userId>', get_user_endpoint, name="get_user"),       # GET /users/{userId}
    path('usersU/<str:userId>', update_user_endpoint, name="update_user"), # PUT /users/{userId}
    path('usersD/<str:userId>', delete_user_endpoint, name="delete_user"), # DELETE /users/{userId}
    path('polling', trigger_sports_polling, name='trigger_sports_polling'),
    path('auth/login', login_probe, name='auth_login'),
]

