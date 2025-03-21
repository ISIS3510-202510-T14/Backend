# api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from location_processor.views import process_location_update
from bet_management.views import placeBet, getBetHistory, getBetDetails, listEvents, listRecommendedBets
# api/views.py
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from rest_framework.response import Response
from location_processor.views import process_location_update
from user_management.views import createUser, getUser, updateUser, deleteUser

#from modules.auth_service import verify_token

# @api_view(['POST'])
# def location_update_view(request):
#     """
#     Endpoint for processing a location update.
#     Expects:
#       {
#         "lat": number,
#         "lng": number,
#         "timestamp": "ISO8601 string"
#       }
#     The user's token is used to obtain the user id.
#     """
#     # Get token from Authorization header (expects 'Bearer <token>')
#     token = request.headers.get('Authorization', '').replace('Bearer ', '')
#     try:
#         auth_user = verify_token(token)
#     except Exception as e:
#         return Response({"error": "Invalid token"}, status=401)
    
#     user_id = auth_user.get('uid')
    
#     # Retrieve location data from request body
#     lat = request.data.get('lat')
#     lng = request.data.get('lng')
#     timestamp = request.data.get('timestamp')  # Expected as ISO8601 string

#     if lat is None or lng is None or timestamp is None:
#         return Response({"error": "Missing required fields: lat, lng, and timestamp are required."}, status=400)
    
#     # Call the location processor function
#     process_location_update(user_id, {'lat': lat, 'lng': lng}, timestamp)
    
#     return Response(status=200)



@api_view(['POST'])
def create_user_endpoint(request):
    """
    POST /users
    Request Body:
      {
        "email": "test@example.com",
        "phone": "555-1234",
        "name": "John Doe",
        "balance": 100.0
      }
    Response Body:
      {
         "userId": "userABC"
      }
    """
    try:
        user_data = request.data
        user_id = createUser(user_data)
        return Response({"userId": user_id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_endpoint(request, userId):
    """
    GET /users/{userId}
    Response Body:
      {
         "user": { ... }
      }
    """
    try:
        user = getUser(userId)
        return Response(user, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
def update_user_endpoint(request, userId):
    """
    PUT /users/{userId}
    Request Body (example):
      {
         "phone": "555-9999",
         "name": "Johnny D"
      }
    Response: No content, HTTP 204 if success.
    """
    try:
        user_data = request.data
        updateUser(userId, user_data)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_user_endpoint(request, userId):
    """
    DELETE /users/{userId}
    Response: No content, HTTP 204 if success.
    """
    try:
        deleteUser(userId)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# class UserDetail(APIView):
#     def get(self, request, userId):
#         try:
#             user = getUser(userId)
#             return Response(user, status=status.HTTP_200_OK)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

#     def put(self, request, userId):
#         try:
#             user_data = request.data
#             updateUser(userId, user_data)
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     def delete(self, request, userId):
#         try:
#             deleteUser(userId)
#             return Response(status=status.HTTP_204_NO_CONTENT)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def location_update_view(request):
    """
    Endpoint for processing a location update without authentication.
    Expects a JSON payload like:
    {
        "userId": "string",
        "lat": number,
        "lng": number,
        "timestamp": "ISO8601 string"
    }
    """
    # Retrieve data from request body
    user_id = request.data.get('userId')
    lat = request.data.get('lat')
    lng = request.data.get('lng')
    timestamp = request.data.get('timestamp')  # Expected as ISO8601 string

    # Validate required fields
    if not user_id or lat is None or lng is None or timestamp is None:
        return Response({"error": "Missing required fields: userId, lat, lng, and timestamp."}, status=400)
    
    # Call the location processor function with the provided data
    process_location_update(user_id, {'lat': lat, 'lng': lng}, timestamp)
    
    return Response(status=200)




@api_view(['POST'])
def create_bet(request):
    """
    POST /bets
    Request Body example:
    {
      "userId": "userABC",
      "eventId": "sql-evt001",
      "stake": 50.0,
      "odds": 1.85
    }
    Response example:
    {
      "betId": "bet555",
      "status": "placed",
      "timestamp": "2025-03-19T19:05:00Z"
    }
    """
    user_id = request.data.get("userId")
    if not user_id:
        return Response({"error": "userId is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    bet_info = {
        "eventId": request.data.get("eventId"),
        "stake": request.data.get("stake"),
        "odds": request.data.get("odds")
    }
    result = placeBet(user_id, bet_info)
    return Response(result, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def list_bets(request):
    """
    GET /bets
    Expects a query parameter: userId
    Response example:
    {
      "bets": [
        { ... },
        ...
      ]
    }
    """
    user_id = request.query_params.get("userId")
    if not user_id:
        return Response({"error": "userId query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    bets = getBetHistory(user_id)

    print(bets)
    return Response({"bets": bets}, status=status.HTTP_200_OK)

@api_view(['GET'])
def bet_detail(request, bet_id):
    """
    GET /bets/{betId}
    Response example:
    {
      "bet": {
        "betId": "bet555",
        "userId": "userABC",
        "eventId": "sql-evt001",
        "stake": 50.0,
        "odds": 1.85,
        "status": "placed",
        "created_at": "2025-03-19T19:05:00Z",
        "updated_at": "2025-03-19T19:05:00Z"
      }
    }
    """
    if not bet_id:
        return Response({"error": "betId is required"}, status=status.HTTP_400_BAD_REQUEST)
    
    bet = getBetDetails(bet_id)
    return Response(bet, status=status.HTTP_200_OK)


from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status


@api_view(['GET'])
def get_events(request):
    """
    GET /events
    Query Parameters (opcional): sport, startDate, endDate
    Ejemplo de respuesta:
    {
      "events": [
        {
          "eventId": "evt001",
          "acidEventId": "sql-evt001",
          "name": "Team A vs Team B",
          "sport": "soccer",
          "location": {"lat": 40.7128, "lng": -74.0060},
          "startTime": "2025-03-19T19:00:00Z",
          "status": "upcoming",
          "providerId": "extProvider001",
          "team1": "Los Andes",
          "team2": "La javeriana"
        },
        ...
      ]
    }
    """
    filterParams = {}
    if 'sport' in request.query_params:
        filterParams['sport'] = request.query_params['sport']
    if 'startDate' in request.query_params:
        filterParams['startDate'] = request.query_params['startDate']
    if 'endDate' in request.query_params:
        filterParams['endDate'] = request.query_params['endDate']
    events = listEvents(filterParams)
    print(events[0])
    return Response({"events": events}, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_recommended_events(request):
    """
    GET /events/recommended
    Se espera el parámetro de consulta userId (obligatorio) y opcionalmente otros filtros.
    Ejemplo de respuesta:
    {
      "recommendedBets": [
        {
          "recommendationId": "r001",
          "eventId": "evt001",
          "betType": "WIN",
          "description": "Team A has a strong advantage...",
          "createdAt": "2025-03-20T03:00:00Z"
        },
        ...
      ]
    }
    """
    user_id = request.query_params.get("userId")
    if not user_id:
        return Response({"error": "userId query parameter is required"}, status=status.HTTP_400_BAD_REQUEST)
    filterParams = {}
    if 'sport' in request.query_params:
        filterParams['sport'] = request.query_params['sport']
    recommendations = listRecommendedBets(user_id, filterParams)
    return Response({"recommendedBets": recommendations}, status=status.HTTP_200_OK)
