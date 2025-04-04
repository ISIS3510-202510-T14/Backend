# analytics_engine.py
import datetime
import logging
import random
from acid_db.views import query_records  # For reading bets from PostgreSQL
from realtime.views import read_data, write_data  # For reading/writing to MongoDB
from django.conf import settings
from django.shortcuts import render
from pymongo import MongoClient
from rest_framework.decorators import api_view
from rest_framework.response import Response
from realtime.models import Metric




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
    incidents = read_data("incidents")

    print(f"Found {len(incidents)} incidents in MongoDB.")
    if not incidents:
        incidents = []
    
    # Filtrar incidentes del día inmediatamente anterior
    # Se asume que la tarea se ejecuta a las 00:00 UTC (o se ajusta según la zona horaria)
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    start_of_yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_yesterday = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    filtered_incidents = []
    for inc in incidents:
        # Manejar tanto dicts como objetos de MongoEngine
        ts = inc.get("timestamp") if isinstance(inc, dict) else getattr(inc, "timestamp", None)
        if ts and isinstance(ts, str):
            ts = datetime.datetime.fromisoformat(ts)
        if ts and start_of_yesterday <= ts <= end_of_yesterday:
            filtered_incidents.append(inc)
    
    # Agrupar incidentes por evento y contar los tipos
    event_metrics = {}
    for inc in filtered_incidents:
        if isinstance(inc, dict):
            event_id = inc.get("eventId")
            inc_type = inc.get("incidentType")
        else:
            event_id = getattr(inc, "eventId", None)
            inc_type = getattr(inc, "incidentType", None)
        if event_id is None:
            continue
        if event_id not in event_metrics:
            event_metrics[event_id] = {"attendance": 0, "proximity": 0}
        if inc_type == "attendance":
            event_metrics[event_id]["attendance"] += 1
        elif inc_type == "proximity":
            event_metrics[event_id]["proximity"] += 1

        # ----------------------------------
    # 5) Update Metrics per event in MongoDB
    # ----------------------------------
    now_utc = datetime.datetime.utcnow()
    analytics_collection = Metric._get_collection()

    for event_id, counts in event_metrics.items():
        new_attendance = counts["attendance"]
        new_proximity = counts["proximity"]

        # Usamos $inc para sumar los nuevos contadores a los ya existentes
        analytics_collection.update_one(
            {"eventId": event_id},
            {
                "$inc": {"attendance": new_attendance, "proximity": new_proximity},
                "$set": {"timestamp": now_utc}
            },
            upsert=True
        )
        
        # Ahora obtenemos los valores acumulados para recalcular conversion_rate
        doc = analytics_collection.find_one({"eventId": event_id})
        if doc:
            total_attendance = doc.get("attendance", 0)
            total_proximity = doc.get("proximity", 0)
            new_conversion_rate = (total_attendance / total_proximity) if total_proximity > 0 else 0.0
            new_conversion_rate = round(new_conversion_rate, 2)
            
            # Actualizamos la tasa de conversión en el mismo documento
            analytics_collection.update_one(
                {"eventId": event_id},
                {"$set": {"conversion_rate": new_conversion_rate, "timestamp": now_utc}}
            )
            print(f"Updated event {event_id}: attendance={total_attendance}, proximity={total_proximity}, conversion_rate={new_conversion_rate}")

    print("Daily analytics completed successfully.")


@api_view(['POST'])
def triggerDailyAnalytics(request):
    """
    API endpoint to trigger the daily analytics process.
    """
    try:
        runDailyAnalytics()
        return Response({"status": "success", "message": "Daily analytics triggered."}, status=200)
    except Exception as e:
        logger.error(f"Error running daily analytics: {e}")
        return Response({"status": "error", "message": str(e)}, status=500)
    



# def storeRecommendations(userId: str, recommendations: list) -> None:
#     """
#     Writes each recommendation as its own doc in MongoDB's 'recommendedBets' collection.
#     """
#     if not recommendations:
#         return
    
#     for rec in recommendations:
#         recommendation_id = rec.get("recommendationId", f"reco-{random.randint(100000,999999)}")
#         path = f"recommendedBets/{userId}/{recommendation_id}"
#         write_data(path, rec)
    
#     print(f"Stored {len(recommendations)} recommendation(s) for user {userId}.")


# def storeMetrics(metrics: list) -> None:
#     """
#     Writes aggregated analytics to the 'analytics' collection in MongoDB, 
#     one document per metric (matching the contract's example of an array).
#     """
#     if not metrics:
#         print("No metrics to store.")
#         return

#     for metric in metrics:
#         metric_id = metric.get("metricId") or f"metric-{random.randint(1000,9999)}"
#         path = f"analytics/{metric_id}"
#         write_data(path, metric)
#         print(f"Stored metric '{metric.get('type')}' with ID {metric_id} in analytics.")




# # app/views.py
# from django.shortcuts import render
# from realtime.models import Incident  # Assuming you have a model for incidents



# def dashboard_view(request):
#     collection = Incident._get_collection()

#     # Obtener todos los eventos disponibles para el dropdown
#     all_events = list(collection.distinct("eventId"))

#     # Leer el filtro enviado por GET; si no se envía, se usa "all"
#     selected_event = request.GET.get("event_id", "all")

#     # --- Gráficos de Barras: Attendance y Proximity ---
#     # Filtrar para 'attendance'
#     match_filter_attendance = {"incidentType": "attendance"}
#     if selected_event != "all":
#         match_filter_attendance["eventId"] = selected_event

#     pipeline_attendance = [
#         {"$match": match_filter_attendance},
#         {"$group": {"_id": "$eventId", "unique_users": {"$addToSet": "$userId"}}},
#         {"$project": {"eventId": "$_id", "total_attendance": {"$size": "$unique_users"}}}
#     ]
#     attendance_results = list(collection.aggregate(pipeline_attendance))

#     # Filtrar para 'proximity'
#     match_filter_proximity = {"incidentType": "proximity"}
#     if selected_event != "all":
#         match_filter_proximity["eventId"] = selected_event

#     pipeline_proximity = [
#         {"$match": match_filter_proximity},
#         {"$group": {"_id": "$eventId", "unique_users": {"$addToSet": "$userId"}}},
#         {"$project": {"eventId": "$_id", "total_proximity": {"$size": "$unique_users"}}}
#     ]
#     proximity_results = list(collection.aggregate(pipeline_proximity))

#     # Combinar resultados en un diccionario
#     data = {}
#     for res in attendance_results:
#         data[res["eventId"]] = {"attendance": res["total_attendance"]}
#     for res in proximity_results:
#         if res["eventId"] in data:
#             data[res["eventId"]]["proximity"] = res["total_proximity"]
#         else:
#             data[res["eventId"]] = {"proximity": res["total_proximity"]}

#     # Preparar listas para los gráficos de barras
#     events = []
#     attendance = []
#     proximity = []
#     for eventId, metrics in data.items():
#         events.append(eventId)
#         attendance.append(metrics.get("attendance", 0))
#         proximity.append(metrics.get("proximity", 0))

#     # --- Gráfico Circular de Conversión ---
#     # Queremos mostrar, para el evento filtrado (o globalmente), 
#     # dos valores:
#     #   - "Converted": número de usuarios que tienen tanto proximity como attendance.
#     #   - "Only Proximity": usuarios con proximity pero sin attendance.
#     conversion_data = {}
#     if selected_event != "all":
#         # Filtrar por el evento seleccionado
#         pipeline_conversion = [
#             {"$match": {"eventId": selected_event}},
#             {"$group": {
#                 "_id": "$eventId",
#                 "attendance_users": {"$addToSet": {
#                     "$cond": [{"$eq": ["$incidentType", "attendance"]}, "$userId", "$$REMOVE"]
#                 }},
#                 "proximity_users": {"$addToSet": {
#                     "$cond": [{"$eq": ["$incidentType", "proximity"]}, "$userId", "$$REMOVE"]
#                 }}
#             }},
#             {"$project": {
#                 "attendance_count": {"$size": "$attendance_users"},
#                 "proximity_count": {"$size": "$proximity_users"},
#                 "conversion_count": {"$size": {"$setIntersection": ["$attendance_users", "$proximity_users"]}}
#             }}
#         ]
#     else:
#         # Global: agrupar sin filtrar por evento
#         pipeline_conversion = [
#             {"$group": {
#                 "_id": None,
#                 "attendance_users": {"$addToSet": {
#                     "$cond": [{"$eq": ["$incidentType", "attendance"]}, "$userId", "$$REMOVE"]
#                 }},
#                 "proximity_users": {"$addToSet": {
#                     "$cond": [{"$eq": ["$incidentType", "proximity"]}, "$userId", "$$REMOVE"]
#                 }}
#             }},
#             {"$project": {
#                 "attendance_count": {"$size": "$attendance_users"},
#                 "proximity_count": {"$size": "$proximity_users"},
#                 "conversion_count": {"$size": {"$setIntersection": ["$attendance_users", "$proximity_users"]}}
#             }}
#         ]
#     conversion_results = list(collection.aggregate(pipeline_conversion))
#     if conversion_results:
#         result = conversion_results[0]
#         conversion_count = result.get("conversion_count", 0)
#         proximity_count = result.get("proximity_count", 0)
#         # Usuarios que solo tienen proximity son el total proximity menos los convertidos
#         only_proximity = proximity_count - conversion_count
#         conversion_data = {
#             "converted": conversion_count,
#             "only_proximity": only_proximity
#         }
#     else:
#         conversion_data = {"converted": 0, "only_proximity": 0}

#     context = {
#         "events": events,
#         "attendance": attendance,
#         "proximity": proximity,
#         "all_events": all_events,         # Para el dropdown
#         "selected_event": selected_event,   # Evento actualmente seleccionado
#         "conversion_data": conversion_data, # Datos para la gráfica circular
#     }
#     return render(request, "dashboard.html", context)


def dashboard_view(request):
    # Leer el filtro enviado por GET; si no se envía, se usa "all"
    selected_event = request.GET.get("event_id", "all")
    
    # Si se selecciona un evento específico, filtramos; de lo contrario, consultamos todos
    if selected_event != "all":
        metrics = Metric.objects(eventId=selected_event)
    else:
        metrics = Metric.objects()
    
    # Preparar listas para los gráficos
    events = []
    attendance = []
    proximity = []
    
    # Si es por evento específico, suponemos que habrá un solo documento (o unos pocos)
    if selected_event != "all":
        doc = metrics.first()
        if doc:
            events = [doc.eventId]
            attendance = [doc.attendance]
            proximity = [doc.proximity]
            converted = doc.attendance  # Suponiendo que "attendance" ya representa a los convertidos
            only_proximity = doc.proximity - doc.attendance
            conversion_data = {"converted": converted, "only_proximity": only_proximity}
        else:
            conversion_data = {"converted": 0, "only_proximity": 0}
    else:
        # Global: por cada documento (cada evento) creamos una entrada
        events = [doc.eventId for doc in metrics]
        attendance = [doc.attendance for doc in metrics]
        print (f"Attendance: {attendance}")
        proximity = [doc.proximity for doc in metrics]
        
        # Agregamos totales globales para el gráfico circular
        total_attendance = sum(attendance)
        total_proximity = sum(proximity)
        converted = total_attendance
        only_proximity = total_proximity - total_attendance
        conversion_data = {"converted": converted, "only_proximity": only_proximity}
    
    context = {
        "events": events,
        "attendance": attendance,
        "proximity": proximity,
        "all_events": list(Metric.objects.distinct("eventId")),  # Para el dropdown
        "selected_event": selected_event,
        "conversion_data": conversion_data,
    }
    
    return render(request, "dashboard.html", context)

