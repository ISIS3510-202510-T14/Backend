# acid_db/api.py
from acid_db.models import User, Event, Bet
from django.forms.models import model_to_dict
from django.db import transaction

# Mapping of entity names to Django models
ENTITY_MODEL_MAP = {
    'user': User,
    'event': Event,
    'bet': Bet,
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
    return model_to_dict(obj)

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

def query_records(entityName: str, queryParams: dict) -> list:
    """
    Retrieves multiple records based on provided query parameters.
    queryParams should be a dictionary with optional keys:
      - filters: a list of dicts { "field": "string", "operator": "=", "value": any }
      - sort: a dict { "field": "string", "direction": "ASC" or "DESC" }
      - limit: an integer to limit the number of records returned.
    Returns a list of dictionaries representing each record.
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
        # Here we handle only the '=' operator; extend as needed.
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
    # Return list of dicts
    return [model_to_dict(obj) for obj in qs]
