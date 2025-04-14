# integration/sports_data.py
import datetime
import requests  # You can use requests for API calls, or any other HTTP client
import logging
import http.client
import json
import django
from rest_framework.decorators import api_view
from rest_framework.response import Response
import random
import uuid

from acid_db.models import Team, Event

from realtime.views import read_data, write_data, update_data
from acid_db.views import read_record, create_record, update_record



logger = logging.getLogger(__name__)


def get_random_location():
    locations = [
        {'lat': 40.7128, 'lng': -74.0060},  # New York
        {'lat': 34.0522, 'lng': -118.2437}, # Los Angeles
        {'lat': 41.8781, 'lng': -87.6298},  # Chicago
        {'lat': 29.7604, 'lng': -95.3698},  # Houston
        {'lat': 33.4484, 'lng': -112.0740}  # Phoenix
    ]
    return random.choice(locations)



def calculate_end_time(start_time):
    # Lista de duraciones posibles en horas
    possible_durations = [1, 1.5, 2, 2.5, 3]
    # Selecciona una duración aleatoria
    duration = random.choice(possible_durations)
    return start_time + datetime.timedelta(hours=duration)


@api_view(['POST'])
def trigger_polling(request):
    """
    Endpoint to trigger the polling of events from the sports API.
    Expects an optional JSON payload:
    {
      "provider": "api-sports"  // Default if not provided.
    }
    """
    provider = request.data.get('provider', 'api-sports')
    print ("Starting polling for provider: {provider}")
    try:
        poll_events(provider)
        return Response({"message": "Polling triggered successfully"}, status=200)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
    

def start_polling(provider_id: str) -> None:
    """
    Initiates periodic polling for a given provider.
    In a production system, you might schedule this with Celery or another task scheduler.
    For now, this simply calls poll_events() once as a placeholder.
    
    Input:
        {
            "providerId": "string"  # e.g., "extProvider001"
        }
    """
    logger.info(f"Starting polling for provider: {provider_id}")
    # TODO: Schedule poll_events to run periodically (e.g., every minute)
    poll_events(provider_id)

def stop_polling(provider_id: str) -> None:
    """
    Stops periodic polling for a given provider.
    In a production system, this would cancel the scheduled polling task.
    
    Input:
        {
            "providerId": "string"
        }
    """
    logger.info(f"Stopping polling for provider: {provider_id}")
    # TODO: Implement task cancellation logic
    pass

def register_event_webhook(event_id: str, callback_url: str) -> None:
    """
    Registers a webhook on the external sports API for a specific live event.
    Since the sports API is not defined yet, this function is a placeholder.
    
    Input:
        {
            "eventId": "string",
            "callbackUrl": "string"  # e.g., "https://api.myapp.com/webhook/externalProvider"
        }
    """
    logger.info(f"Registering webhook for event {event_id} with callback URL: {callback_url}")
    # TODO: Call the external sports API to register the webhook.
    # Example placeholder:
    # response = requests.post("https://api.sportsprovider.com/register_webhook", json={
    #     "eventId": event_id,
    #     "callbackUrl": callback_url
    # })
    # Handle the response accordingly.
    pass

from dateutil.parser import parse as parse_date
import datetime
import http.client
import json
import logging

logger = logging.getLogger(__name__)

from dateutil.parser import parse as parse_date
import datetime
import http.client
import json
import logging

from realtime.views import read_data, write_data, update_data

logger = logging.getLogger(__name__)

# Options for random sport, team names, and status
SPORTS = ["basketball", "soccer", "baseball", "tennis", "hockey"]
TEAM_NAMES = ["Team A", "Team B", "Los Andes", "La Javeriana", "Team Gamma", "Team Betta", "Team Pepe"]


class BaseSportsAPIAdapter:
    def __init__(self, provider_id: str, api_key: str):
        self.provider_id = provider_id
        self.api_key = api_key
    
    def get_events(self, date_str: str) -> list:
        raise NotImplementedError("Subclasses must implement this method")
    
class BaseSportsAPIAdapter:
    """
    Base adapter class for sports APIs.
    Subclasses must implement the get_events() method.
    """
    def __init__(self, provider_id: str, api_key: str):
        self.provider_id = provider_id
        self.api_key = api_key
    
    def get_events(self, date_str: str) -> list:
        raise NotImplementedError("Subclasses must implement get_events()")

class BasketballAPIAdapter(BaseSportsAPIAdapter):
    """
    Adapter for the external Basketball API.
    Encapsulates connection details and transforms the API response
    into a standardized list of event dictionaries.
    """
    def __init__(self, provider_id: str, api_key: str):
        super().__init__(provider_id, api_key)
        self.host = "v1.basketball.api-sports.io"
        # Mapping from API status codes to simplified statuses
        self.status_mapping = {
            "NS": "upcoming",   # Not Started → upcoming
            "Q1": "live",       # Quarter 1 (In Play) → live
            "Q2": "live",       # Quarter 2 (In Play) → live
            "Q3": "live",       # Quarter 3 (In Play) → live
            "Q4": "live",       # Quarter 4 (In Play) → live
            "OT": "live",       # Over Time (In Play) → live
            "BT": "live",       # Break Time (In Play) → live
            "HT": "live",       # Halftime (In Play) → live
            "FT": "finished",   # Game Finished → finished
            "AOT": "finished",  # After Over Time → finished
            "POST": "upcoming", # Game Postponed → upcoming
            "CANC": "finished", # Game Cancelled → finished
            "SUSP": "finished", # Game Suspended → finished
            "AWD": "finished",  # Game Awarded → finished
            "ABD": "finished"   # Game Abandoned → finished
        }

    def get_events(self, date_str: str) -> list:
        """
        Retrieves and transforms basketball events for a given date.
        Returns a standardized list of event dictionaries.
        """
        conn = http.client.HTTPSConnection(self.host)
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }
        # Request games for the given date
        conn.request("GET", f"/games?date={date_str}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        try:
            result = json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error("Error decoding JSON in BasketballAPIAdapter: %s", e)
            return []
        
        events = []
        for event in result.get("response", []):
            # Extract the external event ID
            event_id = event.get("id")
            if not event_id:
                continue
            external_id = str(event_id)
            # Generate a deterministic UUID using UUIDv5 from the external ID
            acid_event_id = uuid.uuid5(uuid.NAMESPACE_DNS, external_id)
            
            # Retrieve date and time
            date_event = event.get("date")  # e.g., "2025-03-19T00:00:00+00:00"
            time_event = event.get("time")  # e.g., "23:30"
            
            # Parse startTime; if unavailable, use current UTC time
            start_time = None
            if date_event and time_event:
                if len(time_event.split(":")) == 2:
                    time_event += ":00"
                start_time_str = f"{date_event[:10]}T{time_event}+00:00"
                try:
                    start_time = parse_date(start_time_str)
                except Exception as e:
                    logger.error("Error parsing startTime: %s", e)
                    continue
            if not start_time:
                start_time = datetime.datetime.utcnow()
            
            # Calculate a random endTime based on startTime
            end_time = calculate_end_time(start_time)
            
            # Map API status code to our simplified status
            api_status = event.get("status", {}).get("short", "NS")
            mapped_status = self.status_mapping.get(api_status, "upcoming")
            
            # Build event name from teams data
            teams = event.get("teams", {})
            home_team = teams.get("home", {}).get("name")
            away_team = teams.get("away", {}).get("name")
            event_name = f"{home_team} vs {away_team}" if home_team and away_team else "Unnamed Event"
            scores = event.get("scores", {})
            home_score = scores.get("home", 0).get("total", 0) or 0
            away_score = scores.get("away", 0).get("total", 0) or 0
            
            # Fix sport as "basketball"
            sport = "basketball"
            
            # Get a random location since the API does not provide one
            event_location = get_random_location()
            
            # Build the standardized event dictionary
            event_data = {
                "acidEventId": acid_event_id.hex,  # Store as string
                "name": event_name,
                "sport": sport,
                "location": event_location,
                "startTime": start_time,
                "endTime": end_time,
                "status": mapped_status,
                "providerId": self.provider_id,
                "homeTeam": home_team,
                "awayTeam": away_team,
                "home_score": home_score,
                "away_score": away_score

            }
            events.append(event_data)
        return events

class FootballAPIAdapter:
    """
    Adapter for the external Football API.
    It retrieves fixtures for a given date and transforms the API response
    into a standardized list of event dictionaries.
    """
    def __init__(self, provider_id: str, api_key: str):
        self.provider_id = provider_id
        self.api_key = api_key
        self.host = "v3.football.api-sports.io"
        # Mapping from API fixture status codes to simplified statuses
        self.status_mapping = {
            "TBD": "upcoming",      # Time To Be Defined → upcoming
            "NS": "upcoming",       # Not Started → upcoming
            "1H": "live",           # First Half, Kick Off → live
            "HT": "live",           # Halftime → live
            "2H": "live",           # Second Half → live
            "ET": "live",           # Extra Time → live
            "P": "live",            # Penalty In Progress → live
            "SUSP": "live",         # Match Suspended → live
            "INT": "live",          # Match Interrupted → live
            "FT": "finished",       # Match Finished → finished
            "AET": "finished",      # Finished after extra time → finished
            "PEN": "finished",      # Finished after penalty shootout → finished
            "PST": "upcoming",      # Postponed → upcoming
            "CANC": "finished",     # Cancelled → finished
            "ABD": "finished",      # Abandoned → finished
            "AWD": "finished",      # Technical Loss → finished
            "WO": "finished",       # WalkOver → finished
            "LIVE": "live"          # In Progress → live
        }
    
    def get_events(self, date_str: str) -> list:
        """
        Retrieves and transforms football fixtures for the given date.
        
        Input:
            date_str: Date in ISO format (e.g., "2025-03-20")
        
        Returns:
            A list of standardized event dictionaries.
        """
        conn = http.client.HTTPSConnection(self.host)
        headers = {
            'x-rapidapi-host': self.host,
            'x-rapidapi-key': self.api_key
        }
        # Send GET request to the fixtures endpoint
        conn.request("GET", f"/fixtures?date={date_str}", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        try:
            result = json.loads(data.decode("utf-8"))
        except Exception as e:
            logger.error("Error decoding JSON in FootballAPIAdapter: %s", e)
            return []
        
        events = []
        # Process each fixture from the API response
        for item in result.get("response", []):
            fixture = item.get("fixture", {})
            teams = item.get("teams", {})
            goals = item.get("goals", {})
            home_score = goals.get("home", 0) or 0
            away_score = goals.get("away", 0) or 0

            
            
            # Extract the external fixture ID from the API response
            external_id = fixture.get("id")
            if not external_id:
                continue
            external_id = str(external_id)
            
            # Use the external ID directly as acidEventId for simplicity
            acid_event_id = uuid.uuid5(uuid.NAMESPACE_DNS, external_id)
            
            # Parse the start time from fixture.date; if not available, use current UTC time
            start_time = None
            date_fixture = fixture.get("date")  # e.g., "2025-03-20T00:00:00+00:00"
            if date_fixture:
                try:
                    start_time = parse_date(date_fixture)
                except Exception as e:
                    logger.error("Error parsing fixture date: %s", e)
                    start_time = datetime.datetime.utcnow()
            else:
                start_time = datetime.datetime.utcnow()
            
            # Calculate a random end time based on start time
            end_time = calculate_end_time(start_time)
            
            # Map the API fixture status to a simplified status
            api_status = fixture.get("status", {}).get("short", "NS")
            mapped_status = self.status_mapping.get(api_status, "upcoming")
            
            # Build event name from teams data
            home_team = teams.get("home", {}).get("name")
            away_team = teams.get("away", {}).get("name")
            event_name = f"{home_team} vs {away_team}" if home_team and away_team else "Unnamed Fixture"
            
            # Set sport as football
            sport = "football"
            
            # Get a random location since the API doesn't provide one in the desired format
            event_location = get_random_location()
            
            # Build the standardized event dictionary
            event_data = {
                "acidEventId": str(acid_event_id),
                "name": event_name,
                "sport": sport,
                "location": event_location,
                "startTime": start_time,
                "endTime": end_time,
                "status": mapped_status,
                "providerId": self.provider_id,
                "homeTeam": home_team,
                "awayTeam": away_team,
                "home_score": home_score,
                "away_score": away_score
            }
            events.append(event_data)
        return events
    
def poll_events(provider_id: str) -> None:
    """
    Polls the external sports API for games on a given date,
    processes the returned data, updates the Real-Time DB (MongoDB)
    and the ACID (relational) DB, and relates both by storing the Real-Time DB id
    in the ACID record.
    """
    date_str = datetime.date.today().isoformat()
    # Create the adapter instance for basketball
    adapter_basket = BasketballAPIAdapter(provider_id, "3d554a0f6cde30dcb24c6c262a047429")
    adapter_football = FootballAPIAdapter(provider_id, "3d554a0f6cde30dcb24c6c262a047429")
    events_data_basket = adapter_basket.get_events(date_str)
    events_data_football = adapter_football.get_events(date_str)
    events_data = events_data_basket + events_data_football
    
    for event_data in events_data:
        acid_event_id = event_data["acidEventId"]
        
        # --- Update or create in the Real-Time DB (MongoDB) ---
        rt_path = "events/" + acid_event_id
        existing_rt = read_data(rt_path)
        if existing_rt:
            update_data(rt_path, event_data)
            rt_id = getattr(existing_rt, "id", None)
        else:
            new_rt = write_data("events", event_data)
            rt_id = getattr(new_rt, "id", None)
        
        # --- Update or create in the ACID DB (SQL) ---
        acid_payload = {
            "event_id": acid_event_id,
            "rt_event_id": rt_id,
            "home_score": event_data.get("home_score"),
            "away_score": event_data.get("away_score"),
     
        }
        # try:
        #     event_instance = Event.objects.get(event_id=acid_event_id)
        #     update_record("event", acid_event_id, acid_payload)
        # except Exception:
        #     create_record("event", acid_payload)
        #     event_instance = Event.objects.create(**acid_payload)

                # Actualiza o crea el evento de forma atómica usando get_or_create.
        event_instance, created = Event.objects.get_or_create(
            event_id=acid_event_id,
            defaults=acid_payload
        )
        if not created:
            # Si el evento ya existe, actualizamos los campos necesarios.
            for key, value in acid_payload.items():
                setattr(event_instance, key, value)
            event_instance.save()



        home_team_name = event_data["homeTeam"]
        away_team_name = event_data["awayTeam"]
        
        # Verificar si existe el equipo por nombre; si no, crearlo.
        home_team_obj, _ = Team.objects.get_or_create(name=home_team_name)
        away_team_obj, _ = Team.objects.get_or_create(name=away_team_name)
        
        # Asociar los equipos al evento (ManyToMany)
        if home_team_obj not in event_instance.home_team.all():
            event_instance.home_team.add(home_team_obj)
        if away_team_obj not in event_instance.away_team.all():
            event_instance.away_team.add(away_team_obj)
        
        logger.info(f"Processed event: {event_data['name']} (ACID ID: {acid_event_id}, RT ID: {rt_id})")

def process_events_data(data: dict) -> None:
    """
    Processes the events data obtained from the sports API.
    This function should update your Real-Time DB and/or ACID DB accordingly.
    
    Input:
        data: A dictionary containing event information.
    """
    logger.info("Processing events data: %s", data)
    # TODO: Implement the logic to update your databases with the new event data.
    pass

def on_webhook_received(payload: dict) -> None:
    """
    Processes an incoming webhook payload from a sports provider.
    Although the design now has this module actively polling the sports API,
    this function is kept for compatibility or for future use.
    
    Input (example):
        {
          "eventId": "string",
          "timestamp": "ISO8601 string",
          "type": "scoreUpdate" | "oddsUpdate" | "eventEnd" | ...,
          "details": {
              "score": "2-1",
              "odds": 1.75,
              "status": "live"
          }
        }
    
    Behavior:
        - Updates the Real-Time DB and/or ACID DB with the new event data.
    """
    logger.info("Webhook received with payload: %s", payload)
    # TODO: Process the webhook payload and update your databases accordingly.
    pass



logger = logging.getLogger(__name__)

def poll_events_task():
    
    provider_id = "api-sports"  # O lo que necesites
    print("Executing poll_events_task")
    poll_events(provider_id)
    print("poll_events_task executed")
    #logger.info("poll_events_task ejecutada")
