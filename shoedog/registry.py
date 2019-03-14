from sqlalchemy import inspect


class ModelRegistry:
    def __init__(self, models):
        """Constructs a read-only registry of models given a list of models

        The registry provides convenience functions to work with the app's
        SQLAlchemy models
        """
        self._tablename_to_models = {
            model.__tablename__: model for model in models
        }
        self._tablename_to_cols = {
            model.__tablename__: set(inspect(model).columns.keys())
            for model in models
        }
        self._tablename_to_rels = {
            model.__tablename__: set(inspect(model).relationships.keys())
            for model in models
        }
        self._tablename_to_poly_child = {
            model.__tablename__:
            {polymodel.__tablename__ for polymodel in
             inspect(model).polymorphic_iterator
             if polymodel != model} for model in models
        }
        self._tablename_to_poly_parent = {
            child: model_tablename
            for model_tablename in self._tablename_to_poly_child
            for child in self._tablename_to_poly_child[model_tablename]
        }


def build_registry(db):
    """Builds a registry object representing a collection of
    all SQLAlchemy models in the application
    """
    models = [model for model in
              db.Model._decl_class_registry.values() if
              hasattr(model, '__tablename__')]
    return ModelRegistry(models)
