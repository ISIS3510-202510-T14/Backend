# analytics_engine.py
import datetime
import logging
import random
from acid_db.views import query_records  # For reading bets from PostgreSQL
from realtime.views import read_data, write_data  # For reading/writing to MongoDB

logger = logging.getLogger(__name__)

def runDailyAnalytics():
    """
    Main entry point for the daily analytics tasks.
    Triggered by a scheduler (cron, APScheduler, etc.) ideally at 6 pm, Colombian time.

    Steps:
      1. Reads user bet data from PostgreSQL (ACID).
      2. Reads incident data (proximity, attendance) from MongoDB.
      3. Generates recommended bets per user (dummy logic).
      4. Stores recommended bets in the 'recommendedBets' collection.
      5. Calculates metrics (conversion rate, total attendance, etc.).
      6. Stores metrics in the 'analytics' collection.
    """
    print("Starting daily analytics ...")

    # (A) Ingest all events from 'events' collection in Mongo:
    all_events = read_data("events")  # returns a list of EventRT documents (or dicts)
    if not all_events:
        all_events = []
    print(f"Found {len(all_events)} events in MongoDB.")

    # (B) Ingest bets (ACID DB):
    bet_query = {"filters": []}
    bets = query_records("bet", bet_query)
    print(f"Found {len(bets)} bets in the SQL DB.")
    
    # (C) Generate user recommendations referencing random events:
    recommendations_by_user = {}
    
    for bet in bets:
        # Example bet dict:
        # {
        #   'user': UUID('...'),
        #   'event': UUID('...'),
        #   'stake': Decimal('50.00'),
        #   'odds': Decimal('1.85'),
        #   'status': 'placed',
        #   'betId': '...'
        # }
        user_id_str = str(bet["user"])  # Convert UUID to string
        if user_id_str not in recommendations_by_user:
            recommendations_by_user[user_id_str] = []
        
        # We'll generate 1 or 2 recommended bets for each user's bet:
        num_recs = random.randint(1, 2)
        for _ in range(num_recs):
            if not all_events:
                continue
            
            # Pick a random event from the existing events collection.
            # We'll store the MongoDB _id (converted to string) to be safe.
            random_event_doc = random.choice(all_events)
            event_id_str = str(random_event_doc.id)
            
            recommendation_id = f"reco-{random.randint(100000, 999999)}"
            recommendation = {
                "recommendationId": recommendation_id,
                "userId": user_id_str,
                "eventId": event_id_str,    # referencing an existing event in Mongo
                "betType": random.choice(["WIN", "OVER_UNDER"]),
                "description": "A recommended event chosen from the existing events",
                "createdAt": datetime.datetime.utcnow().isoformat()
            }
            recommendations_by_user[user_id_str].append(recommendation)

    print(f"Built recommendations for {len(recommendations_by_user)} distinct user(s).")
    
    # (D) Store recommendations in Mongo (one doc per recommendation):
    for user_id, recs in recommendations_by_user.items():
        storeRecommendations(user_id, recs)

    # -----------------------------------------
    # 4) Ingest Incidents (Real-Time DB)
    # -----------------------------------------
    # We read from path "incidents". This should return a list of all incident docs.
    incidents = read_data("incidents")
    if not incidents:
        incidents = []

    # We'll track two global counters for demonstration: total proximity vs attendance
    proximity_count = 0
    attendance_count = 0

    for inc in incidents:
        # Handle both dicts and MongoEngine objects:
        inc_type = inc.incidentType if isinstance(inc, dict) else getattr(inc, "incidentType", None)
        if inc_type == "proximity":
            proximity_count += 1
        elif inc_type == "attendance":
            attendance_count += 1
    
    # Compute a global conversion rate
    conversion_rate = (attendance_count / proximity_count) if proximity_count > 0 else 0.0
    conversion_rate = round(conversion_rate, 2)

    # ----------------------------------
    # 5) Build & Store Metrics
    # ----------------------------------
    # The API contract's example shows an array of metric documents. We'll store two:
    #   1) conversionRate
    #   2) attendanceCount
    # each as a separate doc in the 'analytics' collection.
    now_utc = datetime.datetime.utcnow().isoformat()

    metrics_list = [
        {
            "metricId": f"metric-{random.randint(1000,9999)}-convRate",
            "type": "conversionRate",
            "value": conversion_rate,
            "timestamp": now_utc
        },
        {
            "metricId": f"metric-{random.randint(1000,9999)}-attCount",
            "type": "attendanceCount",
            "value": attendance_count,
            "timestamp": now_utc
        }
    ]

    # Pass the entire array to storeMetrics, which will write each doc individually
    storeMetrics(metrics_list)

    print("Daily analytics completed successfully.")


def storeRecommendations(userId: str, recommendations: list) -> None:
    """
    Writes each recommendation as its own doc in MongoDB's 'recommendedBets' collection.
    """
    if not recommendations:
        return
    
    for rec in recommendations:
        recommendation_id = rec.get("recommendationId", f"reco-{random.randint(100000,999999)}")
        path = f"recommendedBets/{userId}/{recommendation_id}"
        write_data(path, rec)
    
    print(f"Stored {len(recommendations)} recommendation(s) for user {userId}.")


def storeMetrics(metrics: list) -> None:
    """
    Writes aggregated analytics to the 'analytics' collection in MongoDB, 
    one document per metric (matching the contract's example of an array).
    """
    if not metrics:
        print("No metrics to store.")
        return

    for metric in metrics:
        metric_id = metric.get("metricId") or f"metric-{random.randint(1000,9999)}"
        path = f"analytics/{metric_id}"
        write_data(path, metric)
        print(f"Stored metric '{metric.get('type')}' with ID {metric_id} in analytics.")
