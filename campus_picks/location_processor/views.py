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

def process_location_update(user_id, location_data, timestamp_str):
    """
    Processes a location update:
    - Reads events from the real-time database (Mongo).
    - Filters events that have already started and haven't ended.
    - Calculates the distance between the user's location and each ongoing event.
    - If the user is within 1 km, records a proximity incident.
    - If the user is within 0.1 km, records an attendance incident.
    - Sends a notification with the information.
    """
    # Convert the ISO8601 timestamp string to a datetime object
    user_timestamp = datetime.datetime.fromisoformat(timestamp_str)
    
    # User location
    user_lat = location_data.get('lat')
    user_lng = location_data.get('lng')
    
    # Retrieve events from the real-time database (Mongo)
    # Each event is expected to have:
    #   - location: a dict with 'lat' and 'lng'
    #   - acidEventId: a unique identifier
    #   - startTime: event start time (ISO8601 string or datetime)
    #   - endTime: event end time (ISO8601 string or datetime)
    events = read_data('events')  # You can add filters if needed
    
    # Iterate through events to calculate the distance only if the event is currently ongoing
    for event in events:
        # Ensure event times are datetime objects; if stored as strings, convert them.
        if isinstance(event.startTime, str):
            event_start = datetime.datetime.fromisoformat(event.startTime)
        else:
            event_start = event.startTime

        if isinstance(event.endTime, str):
            event_end = datetime.datetime.fromisoformat(event.endTime)
        else:
            event_end = event.endTime

        # Check if the event is currently in progress
        if event_start <= user_timestamp < event_end:
            event_location = event.location  # Expecting a dict with 'lat' and 'lng'
            event_lat = event_location.get('lat')
            event_lng = event_location.get('lng')
            distance = haversine(user_lat, user_lng, event_lat, event_lng)
            
            if distance <= 1:  # Proximity threshold: 1 km
                record_proximity_incident(user_id, event.acidEventId)
                
                if distance <= 0.1:  # Attendance threshold: 0.1 km
                    record_attendance_incident(user_id, event.acidEventId)
                
                # # Send notification with the calculated distance
                # send_notification(user_id, {
                #     "title": "Proximity Alert",
                #     "body": f"You are {distance:.2f} km away from an event.",
                #     "eventId": event.acidEventId
                # })

def record_proximity_incident(user_id, event_id):
    """
    Records a proximity incident in the real-time database (e.g., under 'incidents').
    """
    incident = {
        "userId": user_id,
        "eventId": event_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    write_data('incidents', incident)
    print(f"Proximity incident recorded for user {user_id} at event {event_id}")

def record_attendance_incident(user_id, event_id):
    """
    Records an attendance incident in the real-time database.
    """
    incident = {
        "userId": user_id,
        "eventId": event_id,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    write_data('incidents', incident)
    print(f"Attendance incident recorded for user {user_id} at event {event_id}")
