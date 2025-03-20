# user_management.py
from acid_db.views import create_record, read_record, update_record, delete_record

def createUser(userData: dict) -> str:
    """
    Inserts a new user into PostgreSQL.
    
    Input:
      {
        "email": "test@example.com",
        "phone": "555-1234",
        "name": "John Doe",
        "balance": 100.0
      }
      
    Returns:
      The newly created user's ID (as a string).
    """
    user_id = create_record("user", userData)
    return user_id

def getUser(userId: str) -> dict:
    """
    Retrieves a user record from PostgreSQL by ID.
    
    Input:
      userId: The user's ID.
    
    Returns:
      A dictionary with the user data.
    """
    user = read_record("user", userId)
    return {"user": user}

def updateUser(userId: str, userData: dict) -> None:
    """
    Updates an existing user in PostgreSQL.
    
    Input:
      userId: The user's ID.
      userData: Dictionary with the fields to update (e.g., phone, name).
    
    No direct output; raises an exception if an error occurs.
    """
    update_record("user", userId, userData)

def deleteUser(userId: str) -> None:
    """
    Deletes a user record from PostgreSQL.
    
    Input:
      userId: The user's ID.
    
    No direct output; raises an exception if an error occurs.
    """
    delete_record("user", userId)

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
##from user_management import createUser, getUser, updateUser, deleteUser

@api_view(['POST'])
def create_user_view(request):
    """
    POST /users
    Request Body Example:
    {
      "email": "test@example.com",
      "phone": "555-1234",
      "name": "John Doe",
      "balance": 100.0
    }
    Response Example:
    {
      "userId": "userABC"
    }
    """
    userData = request.data
    try:
        user_id = createUser(userData)
        return Response({"userId": user_id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_view(request, user_id):
    """
    GET /users/{user_id}
    Response Example:
    {
      "user": {
        "user_id": "userABC",
        "email": "test@example.com",
        "phone": "555-1234",
        "name": "John Doe",
        "balance": 100.0,
        "created_at": "2025-03-19T18:55:00Z",
        "updated_at": "2025-03-19T18:55:00Z"
      }
    }
    """
    try:
        user = getUser(user_id)
        return Response(user, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
def update_user_view(request, user_id):
    """
    PUT /users/{user_id}
    Request Body Example:
    {
      "phone": "555-9999",
      "name": "Johnny D"
    }
    No response body (just HTTP success/failure).
    """
    userData = request.data
    try:
        updateUser(user_id, userData)
        return Response(status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
def delete_user_view(request, user_id):
    """
    DELETE /users/{user_id}
    No request body.
    No response body (just HTTP success/failure).
    """
    try:
        deleteUser(user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
