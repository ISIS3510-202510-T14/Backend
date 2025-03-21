# bet_management.py
import datetime
import logging
from dateutil.parser import parse as parse_date
from bson import ObjectId



from acid_db.views import (
    create_record, 
    read_record, 
    update_record, 
    query_records
)
from realtime.views import read_data, write_data, update_data

logger = logging.getLogger(__name__)

def listEvents(filterParams: dict) -> list:
    """
    Returns upcoming events, optionally filtered by parameters such as sport, startDate, endDate.
    Reads detailed event data from the Real-Time DB (Mongo).
    """
    # Here we simply retrieve all events; you can add filtering logic if needed.
    events = read_data("events")
    filtered = []
    for event in events:


        # Convert document to dict if necessary (depends on your Mongo driver usage)

        event_data = event.to_mongo().to_dict()
        event_data["eventId"] = str(event_data.pop("_id", None))




        # Apply simple filtering
        if "sport" in filterParams and event_data.get("sport") != filterParams["sport"]:
            continue
        if "startDate" in filterParams and event_data.get("startTime") < filterParams["startDate"]:
            continue
        if "endDate" in filterParams and event_data.get("startTime") > filterParams["endDate"]:
            continue
        filtered.append(event_data)
    return filtered

def listRecommendedBets(userId: str, filterParams: dict) -> list:
    """
    Retrieves recommended bets for the given user from the Real-Time DB.
    """
    path = f"recommendedBets/{userId}"
    recommendations = read_data(path)
    # Here you can apply additional filtering based on filterParams if needed.
    if recommendations and isinstance(recommendations, list):
        return [rec.to_mongo().to_dict() if hasattr(rec, "to_mongo") else rec for rec in recommendations]
    return []

def placeBet(userId: str, betInfo: dict) -> dict:
    """
    Creates a new bet transaction in the ACID DB.
    betInfo should include at least: eventId, stake, odds.
    Returns a confirmation with betId, status and timestamp.
    """
    payload = {
        "user_id": userId,
        "event_id": betInfo.get("eventId"),
        "stake": betInfo.get("stake"),
        "odds": betInfo.get("odds"),
        "status": "placed",
    }
    bet_id = create_record("bet", payload)
    return {
        "betId": bet_id,
        "status": "placed",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }

def getBetHistory(userId: str) -> list:
    """
    Returns a list of bets placed by the user from the ACID DB.
    """
    queryParams = {
        "filters": [{"field": "user_id", "operator": "=", "value": userId}],
        "sort": {"field": "created_at", "direction": "DESC"}
    }
    return query_records("bet", queryParams)

def getBetDetails(betId: str) -> dict:
    """
    Retrieves detailed information for a single bet from the ACID DB and
    returns it formatted as:
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
    bet = read_record("bet", betId)
    formatted_bet = {
        "betId": bet.get("bet_id", betId),
        "userId": str(bet.get("user")),
        "eventId": str(bet.get("event")),
        "stake": bet.get("stake"),
        "odds": bet.get("odds"),
        "status": bet.get("status"),
        "created_at": bet.get("created_at"),
        "updated_at": bet.get("updated_at")
    }
    return {"bet": formatted_bet}

def createOrUpdateEvent(eventInfo: dict) -> str:
    """
    Creates or updates an event in both the ACID (SQL) and Real-Time (Mongo) DBs.
    Expects eventInfo to include at least:
      - "eventId": external event id from the sports API
      - "name", "sport", "location", "startTime", "status", "providerId", "team1", "team2"
    Returns the identifier of the event in the Real-Time DB (or an equivalent string).
    """
    external_id = eventInfo.get("eventId")
    if not external_id:
        raise ValueError("eventInfo must include 'eventId'")
    
    # Build payload for ACID DB (we use external_id as a field; the DB will generate its own primary key)
    acid_payload = {
        "external_id": external_id,
        "name": eventInfo.get("name"),
        "provider_id": eventInfo.get("providerId"),
        "start_time": eventInfo.get("startTime"),
    }
    try:
        existing_rel = read_record("event", external_id)
        # Assume the existing record has a field "event_id" that is the primary key
        update_record("event", existing_rel.get("event_id"), acid_payload)
        acid_event_id = existing_rel.get("event_id")
    except Exception:
        acid_event_id = create_record("event", acid_payload)
    
    # Build payload for Real-Time DB
    rt_event_data = {
        "acidEventId": acid_event_id,
        "name": eventInfo.get("name"),
        "sport": eventInfo.get("sport"),
        "location": eventInfo.get("location"),
        "startTime": parse_date(eventInfo.get("startTime")),
        "status": eventInfo.get("status"),
        "providerId": eventInfo.get("providerId"),
        "homeTeam": eventInfo.get("team1"),
        "awayTeam": eventInfo.get("team2"),
    }
    rt_path = "events/" + acid_event_id
    existing_rt = read_data(rt_path)
    if existing_rt:
        update_data(rt_path, rt_event_data)
        rt_id = getattr(existing_rt, "id", None)
    else:
        new_rt = write_data("events", rt_event_data)
        rt_id = getattr(new_rt, "id", None)
    
    # Update the ACID DB record with the reference to the Real-Time document
    update_record("event", acid_event_id, {"rt_event_id": rt_id})
    return rt_id

def getEventDetails(eventId: str) -> dict:
    """
    Retrieves event details from the ACID DB.
    """
    return read_record("event", eventId)



