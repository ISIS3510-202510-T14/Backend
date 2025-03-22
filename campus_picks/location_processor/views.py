import datetime
import math
from realtime.views import read_data, write_data  # Functions to interact with MongoDB
#from integration.push_service import send_notification

def haversine(lat1, lon1, lat2, lon2):
    """
    Calculates the distance between two points (lat1, lon1) and (lat2, lon2) in km using the Haversine formula.
    """
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

import datetime
import json
import logging
import random
import uuid
import http.client
from dateutil.parser import parse as parse_date



logger = logging.getLogger(__name__)

def record_proximity_incident(user_id: str, event_id: str) -> None:
    """
    Records a proximity incident for a user and event,
    only if no existing incident of type "proximity" exists for that combination.
    """
    # Read all incidents from the "incidents" collection
    incidents = read_data("incidents")
    print(incidents)
    if incidents:
        for inc in incidents:
            # Assuming inc is a dict; adjust if using a MongoEngine document
            if inc.incidentType == "proximity" and inc.userId == user_id and inc.eventId == event_id:
                # Incident already exists, so exit
                return
    # If no duplicate found, create the incident
    incident_data = {
        "incidentType": "proximity",
        "userId": user_id,
        "eventId": event_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    write_data("incidents", incident_data)

def record_attendance_incident(user_id: str, event_id: str) -> None:
    """
    Records an attendance incident for a user and event,
    only if no existing incident of type "attendance" exists for that combination.
    """
    incidents = read_data("incidents")
    if incidents:
        for inc in incidents:
            if inc.incidentType == "attendance" and inc.userId == user_id and inc.eventId == event_id:
                return
    incident_data = {
        "incidentType": "attendance",
        "userId": user_id,
        "eventId": event_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    write_data("incidents", incident_data)

def process_location_update(user_id: str, location_data: dict, timestamp_str: str) -> None:
    """
    Processes a location update:
    - Converts the provided timestamp.
    - Reads events from the real-time database (Mongo).
    - Filters events with status "upcoming" or "live".
    - Calculates the distance between the user's location and each event.
    - If within 1 km, records a proximity incident.
    - If the event is live and within 0.1 km, records an attendance incident.
    """
    # Convert the ISO8601 timestamp string to a datetime object
    user_timestamp = datetime.datetime.fromisoformat(timestamp_str)
    
    # Get user's coordinates
    user_lat = location_data.get('lat')
    user_lng = location_data.get('lng')
    
    # Retrieve events from the real-time DB (Mongo)
    events = read_data('events')
    
    for event in events:
        # Process only events with status "upcoming" or "live"
        event_status = getattr(event, "status", "").lower() if hasattr(event, "status") else ""
        if event_status not in ("upcoming", "live"):
            continue
        
        # Ensure event startTime is a datetime object
        if isinstance(event.startTime, str):
            event_start = datetime.datetime.fromisoformat(event.startTime)
        else:
            event_start = event.startTime
        
        # Calculate the distance between user and event location
        event_location = event.location  # Expecting a dict with 'lat' and 'lng'
        event_lat = event_location.get('lat')
        event_lng = event_location.get('lng')
        distance = haversine(user_lat, user_lng, event_lat, event_lng)
        
        if distance <= 1:  # Proximity threshold: 1 km
            record_proximity_incident(user_id, event.acidEventId)
            
            # Record attendance only if the event is live and within 0.1 km
            if event_status == "live" and distance <= 0.1:
                record_attendance_incident(user_id, event.acidEventId)
            
            # Optionally, send a notification with the calculated distance
            # send_notification(user_id, {
            #     "title": "Proximity Alert",
            #     "body": f"You are {distance:.2f} km away from an event.",
            #     "eventId": event.acidEventId
            # })
