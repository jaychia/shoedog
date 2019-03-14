from tokenizer import tokenize
from ast import tokens_to_ast, ast_to_query
from registry import build_registry
from serializer import serialize_to_json


class QueryFactory():
    """Factory class for building queries"""
    def __init__(self, db):
        self.model_registry = build_registry(db)

    def parse_query(self, query_string):
        """Parses a string and returns a SQLAlchemy query"""
        token_list = tokenize(query_string)
        ast = tokens_to_ast(token_list, self.model_registry)
        query = ast_to_query(ast)
        json_response = serialize_to_json(query)
        return json_response
