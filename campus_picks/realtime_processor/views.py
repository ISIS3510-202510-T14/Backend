from django.shortcuts import render
from django.http import JsonResponse

def get_websocket_url(request, user_id):
    return JsonResponse({
        'websocket_url': f'ws://yourdomain.com/ws/events/{user_id}/'
    })