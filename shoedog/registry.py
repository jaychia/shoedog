from sqlalchemy import inspect
from shoedog.errors import ModelNotFoundException


class ModelRegistry:
    def __init__(self, models):
        """Constructs a read-only registry of models given a list of models

        The registry provides convenience functions to work with the app's
        SQLAlchemy models
        """
        self._name_to_models = {
            model.__name__: model for model in models
        }
        self._relationships_to_class = {
            (rel.mapper.class_.__name__, rel.key):
            rel.mapper.class_ for model in models for rel in inspect(model).relationships
        }

    def get_model_with_name(self, root_model_name):
        model = self._name_to_models.get(root_model_name)
        if not model:
            raise ModelNotFoundException(f'Could not find model with name {root_model_name}')
        return model

    def get_model_with_rel(self, rel):
        model = self._relationships_to_class.get((rel.mapper.class_.__name__, rel.key))
        if not model:
            raise ModelNotFoundException(f'Could not find relationship {rel}')
        return model


def build_registry(db):
    """Builds a registry object representing a collection of
    all SQLAlchemy models in the application
    """
    models = [model for model in
              db.Model._decl_class_registry.values() if
              hasattr(model, '__tablename__')]
    return ModelRegistry(models)
