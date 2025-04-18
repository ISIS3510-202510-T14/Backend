# bet_management.py
import datetime
import logging
from sqlite3 import IntegrityError
from typing import Dict, List
from dateutil.parser import parse as parse_date
from bson import ObjectId
from acid_db.models import Event, Team, Bet, User
from realtime.models import EventRT, RecommendedBet
from acid_db.models import User, Event, Team, Bet
from django.core.exceptions import ObjectDoesNotExist



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

# def listRecommendedBets(userId: str, filterParams: dict) -> list:
#     """
#     Retrieves recommended bets for the given user from the Real-Time DB.
#     """
#     path = f"recommendedBets/{userId}"
#     recommendations = read_data(path)
#     # Here you can apply additional filtering based on filterParams if needed.
#     if recommendations and isinstance(recommendations, list):
#         return [rec.to_mongo().to_dict() if hasattr(rec, "to_mongo") else rec for rec in recommendations]
#     return []

def listRecommendedBets(userId: str, filterParams: dict) -> list:
    """
    Retrieves recommended bets for the given user using the MongoEngine ORM.
    """
    userId = userId.strip() 
    
    print(userId)
    # Consulta básica por userId
    qs = RecommendedBet.objects(userId=userId)

    print (f"qs: {qs}")
    
    # Aplicar filtros adicionales si se especifican
    # Ejemplo: filtrar por betType si se incluye en filterParams
    if 'betType' in filterParams:
        qs = qs.filter(betType=filterParams['betType'])
    
    # Convertir los documentos a diccionarios
    recommendations = [rec.to_mongo().to_dict() for rec in qs]
    return recommendations

def placeBet(userId: str, betInfo: dict) -> dict:
    # --- 0) Sanity‑check the payload you already build ---
    team_name = betInfo.get("team")
    if not team_name:
        raise ValueError("Bet information must include 'team'")

    # --- 1) Verify *all* foreign keys really exist --------------------------
    try:
        user   = User.objects.get(pk=userId)
    except ObjectDoesNotExist:
        raise ValueError(f"User '{userId}' not registered")

    try:
        event  = Event.objects.get(event_id=betInfo["eventId"].replace("-", ""))
    except ObjectDoesNotExist:
        raise ValueError(f"Event '{betInfo['eventId']}' not found")

    team = Team.objects.filter(name=team_name).first()
    if not team:
        raise ValueError(f"Team '{team_name}' not found")

    # --- 2) Create the bet (now safe) ---------------------------------------
    bet = Bet.objects.create(
        user   = user,
        event  = event,
        team   = team,
        stake  = betInfo["stake"],
        odds   = betInfo["odds"],
        status = "placed",
    )

    return {
        "betId"    : str(bet.bet_id),
        "status"   : bet.status,
        "timestamp": bet.created_at.isoformat(),
    }
def getBetHistory(userId: str) -> List[Dict]:
    """
    Returns *both* the identifiers the app still needs (betId, eventId, teamId)
    **and** the human‑readable fields required for display.

    Each element:
    {
      "betId"     : "0039b9b3‑d1b1‑47c6‑8e90‑4f95b146dc83",
      "eventId"   : "65680a73‑25b1‑55e4‑97e4‑33e50ce5155e",
      "teamId"    : "163d78a7‑2bd8‑43ee‑acc0‑a10e53f023e1",
      "match"     : "Osos de Manatí vs Gigantes de Carolina",
      "sport"     : "basketball",
      "yourTeam"  : "Osos de Manatí",
      "stake"     : 1000.0,
      "odds"      : 2.71,
      "status"    : "placed",
      "placedAt"  : "2025‑04‑18T19:25:00Z",
      "updatedAt" : "2025‑04‑18T19:25:00Z"
    }
    """
    # 1) pull the user’s bets (newest first) with FK objects pre‑fetched
    bets = (
        Bet.objects
        .filter(user__pk=userId)
        .select_related("event", "team")
        .order_by("-created_at")
    )

    history: List[Dict] = []
    for bet in bets:
        event = bet.event

        # -------------------------
        # Build “Home vs Away” name
        # -------------------------
        home_name = (
            event.home_team.first().name
            if event.home_team.exists() else "Home"
        )
        away_name = (
            event.away_team.first().name
            if event.away_team.exists() else "Away"
        )
        match_title = f"{home_name} vs {away_name}"

        # sport label (from the RT document, if any)
        rt_doc = EventRT.objects(acidEventId=str(event.event_id).replace("-", "")).first()
        sport   = getattr(rt_doc, "sport", None) or "unknown"

        # ------------- assemble friendly record -------------
        history.append({
            # identifiers the client may still cache
            "betId"   : str(bet.bet_id),
            "eventId" : str(event.event_id),
            "teamId"  : str(bet.team.team_id),

            # user‑facing data
            "match"     : match_title,
            "sport"     : sport,
            "yourTeam"  : bet.team.name,
            "stake"     : float(bet.stake),
            "odds"      : float(bet.odds),
            "status"    : bet.status,
            "placedAt"  : bet.created_at.isoformat(),
            "updatedAt" : bet.updated_at.isoformat(),
        })

    return history

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