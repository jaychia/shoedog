from datetime import datetime, date, time
import decimal
import uuid
from enum import Enum

from sqlalchemy import inspect
from flask_sqlalchemy.model import Model


def _get_primary_keys(model_obj):
    """Gets the value of the primary key(s) as a concatted string
    Returns None if the object has no identity.
    """
    # inspect(obj).identity returns a tuple of all primary key values of obj
    ident = inspect(model_obj).identity
    return '.'.join([str(key) for key in ident]) if ident else None


def serialize_to_json(query_result):
    def m_to_d(obj, objects_in_load_path):
        """Converts a SQLAlchemy model to a python dict recursively

            Args:
                obj (Model): A SQLAlchemy instance of class Model
                objects_in_load_path: Set of (tablename, id) tuples previously loaded to get to this object
        """
        assert isinstance(obj, Model), f'Invariant failed: Object {obj} must be a model object'
        obj_inspection = inspect(obj)
        relationship_fields = set(obj_inspection.mapper.relationships.keys())
        non_relationship_fields = {x for x in obj_inspection.attrs.keys() if x not in relationship_fields}
        fields = {}
        new_path = objects_in_load_path.union({(obj.__tablename__, _get_primary_keys(obj))})

        # Serialize all non-relationship (scalar) attributes in object if non-empty
        for field in non_relationship_fields:
            val = obj.__getattribute__(field)
            if isinstance(val, (datetime, date, time)):
                field_value = val.isoformat()
            elif isinstance(val, uuid.UUID):
                field_value = str(val)
            elif isinstance(val, decimal.Decimal):
                field_value = float(val)
            elif isinstance(val, Enum):
                field_value = val.value
            else:
                field_value = val

            fields[field] = field_value

        # Serialize relationships in object by expanding the fields
        for field in relationship_fields:

            # Skip field if it is not loaded
            # The field is either lazy or
            if (field in obj_inspection.unloaded and
                    not obj_inspection.transient and
                    not obj_inspection.pending):
                continue

            val = obj.__getattribute__(field)

            # If value is empty, assign and move on to next field
            if val in [{}, [], None]:
                fields[field] = val
                continue

            # Skip field if it is an object already on path (avoid infinite recursion)
            if isinstance(val, Model) and \
                    (val.__tablename__, _get_primary_keys(val)) in objects_in_load_path:
                continue

            # Serialize the field and record it
            if isinstance(val, list):
                fields[field] = [m_to_d(x, new_path) for x in val if
                                 not (x.__tablename__, _get_primary_keys(x)) in objects_in_load_path]
            else:
                fields[field] = m_to_d(val, new_path)

        return fields

    return [m_to_d(obj, set()) for obj in query_result]
