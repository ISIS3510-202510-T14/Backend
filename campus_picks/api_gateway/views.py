# api/views.py
from decimal import Decimal
import uuid
from rest_framework.decorators import api_view
from rest_framework.response import Response
from location_processor.views import process_location_update
from rest_framework.views import APIView
from rest_framework import status
from bet_management.views import (
    placeBet,
    getBetHistory,
    getBetDetails,
    listEvents,
    listRecommendedBets
)
from user_management.views import (
    createUser,
    getUser,
    updateUser,
    deleteUser
)

from acid_db.models import User, Product, Purchase
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.response import Response

# (Any other imports you need can remain here)


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

@api_view(['GET'])
def login_probe(request):
    """
    GET /api/auth/login?uid=<firebase_uid>

    • 200  – row exists, so the mobile app continues
    • 404  – row missing -> the app treats Firebase login as a failure
    """
    uid = request.query_params.get("uid")
    if not uid:
        return Response({"error": "Missing uid"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(pk=uid).exists():
        return Response({"ok": True}, status=status.HTTP_200_OK)

    return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

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
    
    print(request.data, "request.data")
    bet_info = {
        "eventId": request.data.get("eventId"),
        "stake": request.data.get("stake"),
        "odds": request.data.get("odds"),
        "team": request.data.get("team")  # Assuming team is part of the request
    }
    
    result = placeBet(user_id, bet_info)
    return Response(result, status=status.HTTP_201_CREATED)

@api_view(['GET'])
def list_bets(request):
    """
    GET /bets/history
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
    if not events:
      return Response(
          {"events": [], "message": "No events match the given criteria."},
          status=status.HTTP_200_OK
      )
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

# Import the poll_events function from sports_data_integration
# (Adjust if you want to import trigger_polling or something else.)
from sports_data_integration.views import poll_events
from marketplace.views import (
    listProducts,
    getProduct,
    createProduct,
    updateProduct,
    deleteProduct,
)

@api_view(['POST'])
def trigger_sports_polling(request):
    """
    POST /polling
    Triggers the poll_events function from the sports_data_integration module.
    Optional JSON payload:
    {
      "provider": "api-sports"
    }
    """
    # Obtain the provider from the request body if present
    provider_id = request.data.get('provider', 'api-sports')
    try:
        poll_events(provider_id)
        return Response({"message": f"Polling triggered for provider: {provider_id}"},
                        status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'POST'])
def products_endpoint(request):
    """GET or create products."""
    if request.method == 'GET':
        products = listProducts()
        return Response({'products': products}, status=status.HTTP_200_OK)

    # POST
    try:
        product_id = createProduct(request.data)
        return Response({'productId': product_id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def product_detail_endpoint(request, productId):
    if request.method == 'GET':
        try:
            product = getProduct(productId)
            return Response({'product': product}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PUT':
        try:
            updateProduct(productId, request.data)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        try:
            deleteProduct(productId)
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

@api_view(["POST"])
def create_purchase(request):
    try:
        user_id = request.data["user_id"]
        product_id = request.data["product_id"]
        quantity = int(request.data["quantity"])

        user = User.objects.get(user_id=user_id)
        product = Product.objects.get(product_id=product_id)
        total_price = product.price * Decimal(quantity)


        purchase = Purchase.objects.create(
            purchase_id=uuid.uuid4(),
            user=user,
            product=product,
            quantity=quantity,
            total_price=total_price
        )

        print(f"Purchase created: {purchase}")

        return Response({
            "message": "Purchase successful.",
            "purchase_id": str(purchase.purchase_id),
            "total_price": str(total_price)
        }, status=status.HTTP_201_CREATED)

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
    except Product.DoesNotExist:
        return Response({"error": "Product not found."}, status=status.HTTP_404_NOT_FOUND)
    except (KeyError, ValueError):
        return Response({"error": "Invalid request."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_purchase(request, purchase_id):
    try:
        purchase = Purchase.objects.select_related('user', 'product').get(purchase_id=purchase_id)
        return Response({
            "purchase_id": str(purchase.purchase_id),
            "user_id": purchase.user.user_id,
            "product_id": str(purchase.product.product_id),
            "product_name": purchase.product.name,
            "quantity": purchase.quantity,
            "total_price": str(purchase.total_price),
            "created_at": purchase.created_at.isoformat(),
        })
    except Purchase.DoesNotExist:
        return Response({"error": "Purchase not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(["GET"])
def get_user_purchases(request, user_id):
    try:
        user = User.objects.get(user_id=user_id)
        purchases = user.purchases.select_related('product').all().order_by('-created_at')

        result = [{
            "purchase_id": str(p.purchase_id),
            "product_id": str(p.product.product_id),
            "product_name": p.product.name,
            "quantity": p.quantity,
            "total_price": str(p.total_price),
            "created_at": p.created_at.isoformat()
        } for p in purchases]

        return Response({"purchases": result})

    except User.DoesNotExist:
        return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
