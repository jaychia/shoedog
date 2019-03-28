from shoedog.tokenizer import tokenize
from shoedog.eval import eval_ast
from shoedog.parser import tokens_to_ast
from shoedog.registry import build_registry
from shoedog.serializer import serialize_to_json


class QueryFactory():
    """Factory class for building queries"""
    def __init__(self, db):
        self.model_registry = build_registry(db)
        self.db = db

    def parse_query(self, query_string):
        """Parses a string and returns a SQLAlchemy query"""
        token_list = tokenize(query_string)
        ast = tokens_to_ast(token_list, self.model_registry)
        query_response = eval_ast(ast, self.db)
        json_response = serialize_to_json(query_response)
        return json_response
