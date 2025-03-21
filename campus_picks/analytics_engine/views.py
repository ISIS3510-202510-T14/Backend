# analytics_engine.py
import datetime
import logging
import random

from acid_db.views import query_records
from realtime.views import read_data, write_data

logger = logging.getLogger(__name__)

def runDailyAnalytics():
    """
    Main entry point for daily analytics tasks.
    Ingests data from the ACID DB (bets) and from the Real-Time DB (incidents),
    then calculates recommended bets and metrics (conversion rate and total attendance),
    and writes the results back into MongoDB.
    """
    logger.info("Starting daily analytics...")
    
    # --- Ingest data from ACID DB (e.g., bets) ---
    bet_query = {"filters": []}  # Aquí podrías aplicar filtros específicos
    bets = query_records("bet", bet_query)
    
    # --- Generate recommended bets per user (dummy logic) ---
    recommendations_by_user = {}
    for bet in bets:
        user_id = bet.get("user_id")
        if user_id not in recommendations_by_user:
            recommendations_by_user[user_id] = []
        # Dummy: 50% chance to add a recommendation per bet
        if random.random() < 0.5:
            recommendation = {
                "recommendationId": f"reco-{random.randint(1000, 9999)}",
                "eventId": bet.get("event_id"),
                "betType": random.choice(["WIN", "OVER_UNDER"]),
                "description": "Recommended based on your betting history.",
                "createdAt": datetime.datetime.utcnow().isoformat()
            }
            recommendations_by_user[user_id].append(recommendation)
    
    # Store recommendations in the Real-Time DB
    for user_id, recommendations in recommendations_by_user.items():
        storeRecommendations(user_id, recommendations)
    
    # --- Ingest incidents from Real-Time DB ---
    incidents = read_data("incidents")
    if not incidents:
        incidents = []
    
    proximity_count = 0
    attendance_count = 0
    # Se asume que cada incidente tiene el campo "type" (string)
    for inc in incidents:
        # Si inc es un dict; si es un documento MongoEngine, se puede usar getattr(inc, "type")
        inc_type = inc.get("type") if isinstance(inc, dict) else getattr(inc, "type", None)
        if inc_type == "proximity":
            proximity_count += 1
        elif inc_type == "attendance":
            attendance_count += 1
    
    conversion_rate = (attendance_count / proximity_count) if proximity_count > 0 else 0.0
    
    # --- Build and store metrics ---
    metrics = {
        "conversionRate": round(conversion_rate, 2),
        "totalAttendance": attendance_count,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
    storeMetrics(metrics)
    
    logger.info("Daily analytics completed.")

def storeRecommendations(userId: str, recommendations: list) -> None:
    """
    Writes recommended bets for a user into the Real-Time DB.
    The recommendations are stored under the path "recommendedBets/{userId}".
    """
    path = f"recommendedBets/{userId}"
    data = {"recommendations": recommendations}
    write_data(path, data)
    logger.info(f"Stored recommendations for user {userId}.")

def storeMetrics(metrics: dict) -> None:
    """
    Writes metrics (e.g., conversion rate, total attendance) into the Real-Time DB.
    The metrics are stored under the path "analytics/metrics".
    """
    path = "analytics/metrics"
    write_data(path, metrics)
    logger.info("Stored metrics in Real-Time DB.")
