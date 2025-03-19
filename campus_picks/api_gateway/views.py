# api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from location_processor.views import process_location_update
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

# api/views.py
from rest_framework.decorators import api_view
from rest_framework.response import Response
from location_processor.views import process_location_update

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
