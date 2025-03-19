# realtime/api.py
from realtime.models import EventRT, RecommendedBet, Incident, Metric

def parse_path(path: str):
    """Converts the given path into a list of segments."""
    return path.strip('/').split('/')

def read_data(path: str):
    """
    Reads data from a specified path.
    
    Example:
      - "events/event123" returns the EventRT document with acidEventId "event123".
      - "recommendedBets/userABC" returns all recommendations for the user.
    """
    segments = parse_path(path)
    collection = segments[0] if segments else None

    if collection == 'events':
        if len(segments) == 2:
            return EventRT.objects(acidEventId=segments[1]).first()
        return list(EventRT.objects())
    elif collection == 'recommendedBets':
        if len(segments) == 2:
            return list(RecommendedBet.objects(userId=segments[1]))
        elif len(segments) == 3:
            return RecommendedBet.objects(userId=segments[1], recommendationId=segments[2]).first()
        return list(RecommendedBet.objects())
    elif collection == 'incidents':
        return list(Incident.objects())
    elif collection == 'analytics':
        return list(Metric.objects())
    else:
        return None

def write_data(path: str, data: dict):
    """
    Writes or overwrites data at the specified path.
    
    Example:
      - "events/event123": Creates or updates an EventRT with acidEventId "event123".
      - "recommendedBets/userABC/reco001": Creates/updates a recommendation.
    """
    segments = parse_path(path)
    collection = segments[0] if segments else None

    if collection == 'events':
        if len(segments) == 2:
            doc = EventRT.objects(acidEventId=segments[1]).first()
            if doc:
                # Update existing document
                for key, value in data.items():
                    setattr(doc, key, value)
                doc.save()
            else:
                data['acidEventId'] = segments[1]
                doc = EventRT(**data)
                doc.save()
            return doc
        else:
            doc = EventRT(**data)
            doc.save()
            return doc
    elif collection == 'recommendedBets':
        if len(segments) == 3:
            doc = RecommendedBet.objects(userId=segments[1], recommendationId=segments[2]).first()
            if doc:
                # Update existing document
                for key, value in data.items():
                    setattr(doc, key, value)
                doc.save()
            else:
                data['userId'] = segments[1]
                data['recommendationId'] = segments[2]
                doc = RecommendedBet(**data)
                doc.save()
            return doc
        else:
            doc = RecommendedBet(**data)
            doc.save()
            return doc
    elif collection == 'incidents':
        doc = Incident(**data)
        doc.save()
        return doc
    elif collection == 'analytics':
        doc = Metric(**data)
        doc.save()
        return doc
    else:
        raise ValueError("Unknown collection in write_data.")

def update_data(path: str, partial_data: dict):
    """
    Performs a partial update/merge on the document at the specified path.
    
    Example:
      - "events/event123" updates only the provided fields for that event.
    """
    segments = parse_path(path)
    collection = segments[0] if segments else None

    if collection == 'events' and len(segments) == 2:
        doc = EventRT.objects(acidEventId=segments[1]).first()
        if doc:
            doc.update(**partial_data)
            return
    elif collection == 'recommendedBets' and len(segments) == 3:
        doc = RecommendedBet.objects(userId=segments[1], recommendationId=segments[2]).first()
        if doc:
            doc.update(**partial_data)
            return
    elif collection == 'incidents':
        # Note: This is a generic update; a more specific filter might be needed
        Incident.objects(**partial_data).update(**partial_data)
        return
    elif collection == 'analytics':
        Metric.objects(**partial_data).update(**partial_data)
        return
    else:
        raise ValueError("Path not supported in update_data.")

def delete_data(path: str):
    """
    Deletes data at the specified path.
    
    Example:
      - "events/event123" deletes the event document.
      - "recommendedBets/userABC/reco001" deletes the specific recommendation.
    """
    segments = parse_path(path)
    collection = segments[0] if segments else None

    if collection == 'events' and len(segments) == 2:
        EventRT.objects(acidEventId=segments[1]).delete()
    elif collection == 'recommendedBets' and len(segments) == 3:
        RecommendedBet.objects(userId=segments[1], recommendationId=segments[2]).delete()
    elif collection == 'incidents':
        Incident.objects.delete()  # Or apply a more specific filter
    elif collection == 'analytics':
        Metric.objects.delete()
    else:
        raise ValueError("Path not supported in delete_data.")