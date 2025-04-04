# acid_db/api.py
from acid_db.models import User, Event, Bet, Team
from django.forms.models import model_to_dict
from django.db import transaction

# Mapping of entity names to Django models
ENTITY_MODEL_MAP = {
    'user': User,
    'event': Event,
    'bet': Bet,
    "team": Team,
}

def create_record(entityName: str, payload: dict) -> str:
    """
    Inserts a new row for the specified entity.
    Returns the primary key (record ID) of the new record.
    """
    Model = ENTITY_MODEL_MAP.get(entityName)
    if not Model:
        raise ValueError(f"Unknown entity: {entityName}")
    obj = Model.objects.create(**payload)
    return str(obj.pk)

def read_record(entityName: str, recordId: str) -> dict:
    """
    Retrieves a single record by its primary key.
    """
    Model = ENTITY_MODEL_MAP.get(entityName)
    if not Model:
        raise ValueError(f"Unknown entity: {entityName}")
    obj = Model.objects.get(pk=recordId)
    fields = [field.name for field in obj._meta.fields]
    data = model_to_dict(obj, fields=fields)
    
    if hasattr(obj, "created_at"):
        data["created_at"] = obj.created_at.isoformat()
    if hasattr(obj, "updated_at"):
        data["updated_at"] = obj.updated_at.isoformat()
    
    obj_pk_field = obj._meta.pk.name
    

    data[obj_pk_field ] = str(getattr(obj, obj_pk_field))

    
    return data

def update_record(entityName: str, recordId: str, payload: dict) -> None:
    """
    Updates an existing record by its primary key.
    """
    Model = ENTITY_MODEL_MAP.get(entityName)
    if not Model:
        raise ValueError(f"Unknown entity: {entityName}")
    Model.objects.filter(pk=recordId).update(**payload)

def delete_record(entityName: str, recordId: str) -> None:
    """
    Deletes a record by its primary key.
    """
    Model = ENTITY_MODEL_MAP.get(entityName)
    if not Model:
        raise ValueError(f"Unknown entity: {entityName}")
    Model.objects.filter(pk=recordId).delete()

def run_transactional_operation(operations: list) -> None:
    """
    Executes a sequence of inserts/updates/deletes atomically.
    Each operation is a dict with keys: 'type', 'entityName', 'recordId' (optional), and 'payload'.
    """
    with transaction.atomic():
        for op in operations:
            op_type = op.get('type')
            entityName = op.get('entityName')
            recordId = op.get('recordId', None)
            payload = op.get('payload', {})
            if op_type == 'insert':
                create_record(entityName, payload)
            elif op_type == 'update':
                if not recordId:
                    raise ValueError("recordId is required for update")
                update_record(entityName, recordId, payload)
            elif op_type == 'delete':
                if not recordId:
                    raise ValueError("recordId is required for delete")
                delete_record(entityName, recordId)
            else:
                raise ValueError(f"Unknown operation type: {op_type}")

from django.forms.models import model_to_dict

def query_records(entityName: str, queryParams: dict) -> list:
    """
    Retrieves multiple records based on provided query parameters.
    Returns a list of dictionaries representing each record, ensuring the primary key is included.
    """
    Model = ENTITY_MODEL_MAP.get(entityName)
    if not Model:
        raise ValueError(f"Unknown entity: {entityName}")
    
    qs = Model.objects.all()
    # Apply filters
    for filter_item in queryParams.get('filters', []):
        field = filter_item.get('field')
        operator = filter_item.get('operator')
        value = filter_item.get('value')
        if operator == '=':
            qs = qs.filter(**{field: value})
    
    # Apply sorting if provided
    sort = queryParams.get('sort')
    if sort:
        field = sort.get('field')
        direction = sort.get('direction', 'ASC')
        if direction.upper() == 'DESC':
            field = '-' + field
        qs = qs.order_by(field)
    
    # Apply limit if provided
    limit = queryParams.get('limit')
    if limit:
        qs = qs[:limit]
    
    results = []
    for obj in qs:
        # Convert model to dict
        data = model_to_dict(obj)
        # Ensure the primary key is included as a string
        pk_field = obj._meta.pk.name
        pk_field_key = pk_field.replace('_id', 'Id')

        data[pk_field_key] = str(getattr(obj, pk_field))
        results.append(data)
    
    return results
