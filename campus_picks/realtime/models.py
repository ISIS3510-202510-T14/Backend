# realtime/models.py
import datetime
from mongoengine import Document, StringField, DateTimeField, DictField, FloatField

class EventRT(Document):
    
    acidEventId = StringField(required=True)  # Referencia al event.event_id en la base ACID
    name = StringField(required=True)
    sport = StringField()  # Ej: 'soccer', 'basketball'
    location = DictField()  # Ej: {"lat": 40.7128, "lng": -74.0060}
    startTime = DateTimeField()  # Fecha y hora de inicio del evento
    endTime = DateTimeField()    # Fecha y hora de finalización del evento
    status = StringField()       # Ej: 'upcoming', 'live', 'ended'
    providerId = StringField()   # Debe coincidir con event.provider_id


    # New fields for the team names
    homeTeam = StringField()     # Name of the home team
    awayTeam = StringField()     # Name of the away team
    endTime = DateTimeField()    # End date and time

    meta = {
        'collection': 'events'
    }

class RecommendedBet(Document):
    userId = StringField(required=True)  # Identificador del usuario (Firebase Auth uid)
    recommendationId = StringField(required=True)  # ID única para la recomendación (única por usuario)
    eventId = StringField(required=True)  # Referencia al eventId en /events
    betType = StringField(required=True)  # Ej: 'win', 'over/under', etc.
    description = StringField()            # Breve descripción o razón
    createdAt = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'recommendedBets'
    }

class Incident(Document):
    incidentType = StringField(required=True, choices=['proximity', 'attendance'])
    userId = StringField(required=True)   # Coincide con user_id de ACID o Firebase Auth
    eventId = StringField(required=True)    # Referencia a /events/<eventId>
    timestamp = DateTimeField(default=datetime.datetime.utcnow)
    # Opcional: agregar datos de ubicación u otros campos extra
    location = DictField()

    meta = {
        'collection': 'incidents'
    }

class Metric(Document):
    metricId = StringField(required=True)  # ID único para la métrica
    type = StringField(required=True)        # Ej: "conversionRate", "attendanceCount", etc.
    eventId = StringField()                  # Puede ser específico de un evento, un usuario o global
    value = FloatField(required=True)        # Valor numérico de la métrica
    timestamp = DateTimeField(default=datetime.datetime.utcnow)

    meta = {
        'collection': 'analytics'
    }
