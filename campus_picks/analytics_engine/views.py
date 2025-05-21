# analytics_engine.py
import datetime
from mongoengine.queryset.visitor import Q
import logging
import random
from acid_db.views import query_records  # For reading bets from PostgreSQL
from realtime.views import read_data, write_data  # For reading/writing to MongoDB
from django.conf import settings
from django.shortcuts import render
from pymongo import MongoClient
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from realtime.models import Metric, EventRT, RecommendedBet
from uuid import UUID


from acid_db.models import Team, Bet, Product
from analytics_engine.serializers import ApiLogSerializer
from analytics_engine.models import ApiLog
from dateutil.parser import isoparse
from collections import Counter
from typing import Dict, List, Tuple





logger = logging.getLogger(__name__)

from mongoengine.queryset.visitor import Q
from django.conf import settings
from pymongo import MongoClient
from acid_db.models import Bet
from realtime.models import EventRT, RecommendedBet, Incident, Metric
import datetime
import random
import logging

logger = logging.getLogger(__name__)


from mongoengine.queryset.visitor import Q
from django.conf import settings
from pymongo import MongoClient
from acid_db.models import Bet
from realtime.models import EventRT, RecommendedBet, Incident, Metric
import datetime
import random
import logging

logger = logging.getLogger(__name__)


from mongoengine.queryset.visitor import Q
from django.conf import settings
from pymongo import MongoClient
from acid_db.models import Bet
from realtime.models import EventRT, RecommendedBet, Incident, Metric
import datetime
import random
import logging

logger = logging.getLogger(__name__)


def _collect_user_team_data():
    print("[DEBUG] Starting user-team aggregation...")
    user_team_bets = {}
    betted_teams = {}
    for bet in Bet.objects.select_related('team', 'user').all():
        uid = str(bet.user.pk)
        tid = str(bet.team.pk)
        team_name = bet.team.name
        print(f"[DEBUG] Processing bet: user={uid}, team={tid} ({team_name})")
        user_team_bets.setdefault(uid, {}).setdefault(tid, {'count': 0, 'team_name': team_name})['count'] += 1
        betted_teams.setdefault(tid, team_name)
    print(f"[DEBUG] Aggregated data for {len(user_team_bets)} users and {len(betted_teams)} teams.")
    return user_team_bets, betted_teams


def _fetch_team_data(betted_teams):
    print("[DEBUG] Fetching team data (upcoming events & performance)...")
    team_data = {}
    two_weeks_ago = datetime.datetime.utcnow() - datetime.timedelta(weeks=2)
    for tid, name in betted_teams.items():
        print(f"[DEBUG] Team {tid}: {name}")
        upcoming = list(
            EventRT.objects.filter(
                (Q(homeTeam=name) | Q(awayTeam=name)) & Q(status__in=['upcoming', 'live'])
            ).order_by('startTime')
        )
        print(f"[DEBUG]  Upcoming events count: {len(upcoming)}")
        recent = EventRT.objects.filter(
            (Q(homeTeam=name) | Q(awayTeam=name)) & Q(status='ended') & Q(endTime__gte=two_weeks_ago)
        )
        wins = sum(
            1 for e in recent if (e.homeTeam == name and e.home_score > e.away_score)
        )
        losses = sum(
            1 for e in recent if (e.homeTeam == name and e.home_score < e.away_score)
        )
        wins += sum(
            1 for e in recent if (e.awayTeam == name and e.away_score > e.home_score)
        )
        losses += sum(
            1 for e in recent if (e.awayTeam == name and e.away_score < e.home_score)
        )
        print(f"[DEBUG]  Recent performance: {wins} wins, {losses} losses")
        team_data[tid] = {
            'team_name': name,
            'upcoming': upcoming,
            'performance': {'wins': wins, 'losses': losses}
        }
    print("[DEBUG] Completed fetching team data.")
    return team_data


def _fetch_popular_events(user_team_bets):
    print("[DEBUG] Checking for fallback popular events...")
    total_bets = sum(sum(t['count'] for t in teams.values()) for teams in user_team_bets.values())
    print(f"[DEBUG] Total bets = {total_bets}, total users = {len(user_team_bets)}")
    if len(user_team_bets) <= 1 or total_bets < 5:
        print("[DEBUG] Using popular events fallback.")
        coll = Metric._get_collection()
        top = list(coll.find().sort('attendance', -1).limit(5))
        popular_ids = [d['eventId'] for d in top]
        print(f"[DEBUG] Popular event IDs: {popular_ids}")
        events = list(EventRT.objects.filter(
            acidEventId__in=popular_ids,
            status__in=['upcoming', 'live']
        ))
        print(f"[DEBUG] Fetched {len(events)} popular events.")
        return events
    print("[DEBUG] No popular fallback needed.")
    return []


def _generate_recommendations(user_team_bets, team_data, popular_events):
    print("[DEBUG] Generating recommendations...")
    recs = {}
    for uid, teams in user_team_bets.items():
        print(f"[DEBUG] User {uid} has {len(teams)} teams.")
        # Fallback for users with very few team interactions
        if len(teams) < 2 and popular_events:
            print(f"[DEBUG] User {uid} receives popular event recommendations.")
            for evt in popular_events:
                rec = {
                    'recommendationId': f"reco-{random.randint(100000, 999999)}",
                    'userId': uid,
                    'eventId': str(evt.id),
                    'betType': 'popular',
                    'description': f"Check out this popular match: {evt.homeTeam} vs {evt.awayTeam} at {evt.startTime}.",
                    'createdAt': datetime.datetime.utcnow().isoformat()
                }
                print(f"[DEBUG] Popular rec for {uid}: {rec}")
                recs.setdefault(uid, []).append(rec)
            continue
        # Personalized for every team regardless of bet count
        for tid, info in teams.items():
            data = team_data.get(tid)
            if not data:
                print(f"[DEBUG] No team data for team {tid}, skipping.")
                continue
            wins = data['performance']['wins']
            losses = data['performance']['losses']
            for evt in data['upcoming']:
                rec = {
                    'recommendationId': f"reco-{random.randint(100000, 999999)}",
                    'userId': uid,
                    'eventId': str(evt.id),
                    'betType': 'caution' if losses > wins else 'win',
                    'description': (
                        f"{data['team_name']} recent record: {wins}W-{losses}L. "
                        f"Next: {evt.homeTeam} vs {evt.awayTeam} at {evt.startTime}."
                    ),
                    'createdAt': datetime.datetime.utcnow().isoformat()
                }
                print(f"[DEBUG] Personalized rec for {uid}: {rec}")
                recs.setdefault(uid, []).append(rec)
    print("[DEBUG] Completed recommendation generation.")
    return recs


def _persist_recommendations(recommendations_by_user):
    print("[DEBUG] Persisting recommendations to MongoDB...")
    for uid, rec_list in recommendations_by_user.items():
        for rec in rec_list:
            print(f"[DEBUG] Saving rec: {rec}")
            rec_time = datetime.datetime.fromisoformat(rec['createdAt'])
            RecommendedBet(
                recommendationId=rec['recommendationId'],
                userId=uid,
                eventId=rec['eventId'],
                betType=rec['betType'],
                description=rec['description'],
                createdAt=rec_time
            ).save()
    print("[DEBUG] All recommendations persisted.")


def _process_incidents():
    print("[DEBUG] Processing incidents and updating metrics...")
    yesterday = datetime.datetime.utcnow() - datetime.timedelta(days=1)
    start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
    print(f"[DEBUG] Incident window: {start} to {end}")
    incidents = Incident.objects.filter(timestamp__gte=start, timestamp__lte=end)
    metrics = {}
    for inc in incidents:
        eid = inc.eventId
        metrics.setdefault(eid, {'attendance': 0, 'proximity': 0})
        metrics[eid][inc.incidentType] += 1
        print(f"[DEBUG] Incident {inc.incidentType} for event {eid}")
    coll = Metric._get_collection()
    now = datetime.datetime.utcnow()
    for eid, counts in metrics.items():
        print(f"[DEBUG] Updating metrics for {eid}: {counts}")
        coll.update_one(
            {'eventId': eid},
            {'$inc': {'attendance': counts['attendance'], 'proximity': counts['proximity']},
             '$set': {'timestamp': now}},
            upsert=True
        )
        doc = coll.find_one({'eventId': eid})
        total_att = doc.get('attendance', 0)
        total_prox = doc.get('proximity', 0)
        conv_rate = round((total_att / total_prox) if total_prox else 0, 2)
        coll.update_one(
            {'eventId': eid},
            {'$set': {'conversion_rate': conv_rate, 'timestamp': now}}
        )
        print(f"[DEBUG] Metrics for {eid} saved: attendance={total_att}, proximity={total_prox}, conversion_rate={conv_rate}")
    print("[DEBUG] Incident processing complete.")


def runDailyAnalytics():
    print("[INFO] === Starting runDailyAnalytics ===")
    user_team_bets, betted_teams = _collect_user_team_data()
    team_data = _fetch_team_data(betted_teams)
    popular_events = _fetch_popular_events(user_team_bets)
    recommendations = _generate_recommendations(user_team_bets, team_data, popular_events)
    _persist_recommendations(recommendations)
    print(f"[INFO] Built recommendations for {len(recommendations)} users.")

    _process_incidents()
    print("[INFO] Completed incidents & metrics update.")

    print("[INFO] === runDailyAnalytics finished ===")


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


def get_sports_attention():

    bets = Bet.objects.all()  # Puedes aplicar filtros si es necesario
    events_id = set([bet.event.pk for bet in bets])
    events = EventRT.objects.filter(id__in=events_id)  # Filtrar eventos por los IDs de las apuestas




def get_bet_count_by_sport() -> Dict[str, int]:
    """
    Returns a dict  {sport_name: bet_count}.
    It joins:
      • Bet  ->  Event (relational FK)
      • Event.event_id  ->  EventRT.acidEventId   (Mongo)
    """
    # 1) Build an in‑memory map from ACID Event‑ID   ➜   sport
    event_to_sport = {
        evt.acidEventId: (evt.sport or "unknown")
        for evt in EventRT.objects.only("acidEventId", "sport")
    }

    for acid_id, sport in event_to_sport.items():
        print (f"Event ID: {acid_id}  ➜  Sport: {sport}")
        

    #print (event_to_sport, "event_to_sport")

    # 2) Count bets per sport
    counter = Counter()
    for bet in (
        Bet.objects             # SELECT * FROM bet …
        .select_related("event")  # join to Event once, avoids n+1 queries
    ):

        acid_id = str(bet.event.event_id)
        acid_id_formatted = acid_id.replace("-", "").strip() # Remove dashes for matching
        print (f"Bet event_id: {acid_id_formatted}")

        sport   = event_to_sport.get(acid_id, "unknown")
        counter[sport] += 1

    print (f"Bet count by sport: {counter}")

    return dict(counter)


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
        sport_bet_counts = get_bet_count_by_sport()

        category_views = views_by_category()
        print (f"Category views: {category_views}")

        product_views = views_by_product()
    
    context = {
        "events": events,
        "attendance": attendance,
        "proximity": proximity,
        "all_events": list(Metric.objects.distinct("eventId")),  # Para el dropdown
        "selected_event": selected_event,
        "conversion_data": conversion_data,
        "sport_bet_counts": sport_bet_counts,  # Para el gráfico de deportes
        "category_views": category_views,  # Para el gráfico de categorías
        "product_views": product_views,  # Para el gráfico de productos
    }
    
    return render(request, "dashboard.html", context)

@api_view(['POST'])
def log_api_metrics(request):
    data = request.data

    # Verifica si es una lista
    if isinstance(data, list):
        for item in data:
            timestamp_str = item.get('timestamp')
            try:
                timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            except (TypeError, ValueError):
                return Response({"error": "Invalid timestamp format."}, status=400)

            ApiLog.objects.create(
                endpoint=item.get('endpoint', ''),
                duration=item.get('duration', 0),
                status_code=item.get('statusCode'),
                success=bool(item.get('success', 0)),
                error=item.get('error', ''),
                timestamp=timestamp,
            )
        return Response({"message": "Metrics logged successfully."}, status=201)

    # Si no es lista, devuelva error
    return Response({"error": "Expected a list of metrics."}, status=400)

@api_view(['GET'])
def check_metrics(request):
    """
    Lista con promedio de duración por endpoint.
    Filtros: start_date, end_date (formato YYYY-MM-DD)
    """
    logs = ApiLog.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            logs = logs.filter(timestamp__gte=start)
        except ValueError:
            return Response({'error': 'start_date inválido. Formato esperado: YYYY-MM-DD'}, status=400)

    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            logs = logs.filter(timestamp__lte=end)
        except ValueError:
            return Response({'error': 'end_date inválido. Formato esperado: YYYY-MM-DD'}, status=400)

    data = logs.values('endpoint').annotate(average_response=Avg('duration')).order_by('endpoint')

    return Response(data)


from .models import ProductViewMetric

@api_view(['POST'])
def ingest_product_views(request):
    """
    Recibe un array de {productId, userId, viewedAt} en ISO8601 (incluye 'Z').
    Guarda cada doc en Mongo y devuelve {'stored': N}.
    """
    data = request.data
    if not isinstance(data, list):
        return Response({'error': 'expected a list'}, status=status.HTTP_400_BAD_REQUEST)

    stored = 0
    for item in data:
        try:
            # parseo estricto ISO8601 (Z, +00:00, etc.)
            dt = isoparse(item['viewedAt'])
            ProductViewMetric(
                productId=item['productId'],
                userId   =item['userId'],
                viewedAt =dt
            ).save()
            stored += 1
        except Exception:
            
            continue

    return Response({'stored': stored}, status=status.HTTP_201_CREATED)


def views_by_category():
    """
    Devuelve [{'category': 'Ropa', 'views': 98}, …] sin pelear con UUID ⇄ str.
    """
    # 1) totales en Mongo
    pipeline = [{'$group': {'_id': '$productId', 'views': {'$sum': 1}}}]
    product_counts = list(ProductViewMetric._get_collection().aggregate(pipeline))

    # 2) build map completo id → category desde SQL
    prod_map = {
        str(p.product_id): (p.category or 'Uncategorized')
        for p in Product.objects.all().only('product_id', 'category')
    }

    # 3) acumula vistas por categoría
    cat_counts = {}
    for rec in product_counts:
        cat = prod_map.get(str(rec['_id']), 'Uncategorized')
        cat_counts[cat] = cat_counts.get(cat, 0) + rec['views']

    # 4) ordena
    result = [{'category': c, 'views': v} for c, v in cat_counts.items()]
    result.sort(key=lambda x: x['views'], reverse=True)
    return result

def views_by_product(limit=100):
    """
    Top-N productos más vistos – matching manual id → nombre.
    """
    pipeline = [
        {'$group': {'_id': '$productId', 'views': {'$sum': 1}}},
        {'$sort':  {'views': -1}},
        {'$limit': limit},
    ]
    raw = list(ProductViewMetric._get_collection().aggregate(pipeline))

    # mapa id→nombre
    name_map = {
        str(p.product_id): p.name
        for p in Product.objects.all().only('product_id', 'name')
    }

    return [
        {'product': name_map.get(str(r['_id']), 'Unknown'), 'views': r['views']}
        for r in raw
    ]



def metrics_dashboard_view(request):
    # Captura los parámetros GET
    from django.db.models import Avg
    from datetime import datetime

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    min_duration_str = request.GET.get('min_duration')
    max_duration_str = request.GET.get('max_duration')

    metrics = ApiLog.objects.all()

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        metrics = metrics.filter(timestamp__gte=start_date)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        metrics = metrics.filter(timestamp__lte=end_date)

    if min_duration_str:
        metrics = metrics.filter(duration__gte=int(min_duration_str))

    if max_duration_str:
        metrics = metrics.filter(duration__lte=int(max_duration_str))

    aggregated_data = metrics.values('endpoint').annotate(
        avg_duration=Avg('duration')
    ).order_by('-avg_duration')
    

    return render(request, 'metrics_dashboard.html', {
        'aggregated_data': aggregated_data,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'min_duration': min_duration_str,
        'max_duration': max_duration_str,
    })
