from shoedog.tokenizer import Toks
from shoedog.utils import peek


class AstNode:
    """ A node in the AST tree """
    def __init__(self):
        self._children = tuple()

    def add_child(self, child):
        self._children += (child,)

    def eval(self, query):
        raise NotImplementedError(f'Node {self.__name__} has not implemented eval')


class RootNode(AstNode):
    """ The root node of the AST representing the model at the root of the query """
    def __init__(self, registry, root_model_name):
        super().__init__()
        self.model = registry.get_model_with_name(root_model_name)


class RelationshipNode(AstNode):
    """ The root node of the AST representing a relationship """
    def __init__(self, registry, root_model, rel):
        super().__init__()
        self.rel = getattr(root_model, rel)
        self.model = registry.get_model_with_rel(self.rel)


class AttributeNode(AstNode):
    """ The root node of the AST representing an attribute """
    def __init__(self, registry, root_model, attr_name):
        super().__init__()
        self.attr = getattr(root_model, attr_name)


class FilterNode(AstNode):
    """ The root node of the AST representing a set of filters """
    def __init__(self):
        # TODO: Fill out data structure
        super().__init__()


def _tokens_to_ast(root_token, current_model, token_stream, registry):
    """ Helper to convert the next tokens in the token_stream to some AST

    Precondition: users of this helper need to peek to ensure that the next token
        is non-null. This helper works by calling the appropriate ast node specific
        helper function after introspecting the next token
    """
    print('_tokens_to_ast', root_token)
    if isinstance(root_token, Toks.RootQueryToken):
        return _root_query_to_ast(root_token, token_stream, registry)
    elif isinstance(root_token, Toks.OpenObjectToken):
        return _open_object_to_ast(root_token, current_model, token_stream, registry)
    elif isinstance(root_token, Toks.AttributeToken):
        return _attribute_to_ast(root_token, current_model, token_stream, registry)
    else:
        assert False, f'Should never be calling _tokens_to_ast on {root_token}'


def _filters_to_ast(current_model, attr_name, token_stream, registry):
    """ Helper to be called when building an ast representing a set of filters

    Requires:
        current_model: The current SQLAlchemy model being filtered on
        attr_name: The name of the attribute of the SQLAlchemy model being filtered
        token_stream: Remaining tokens after parsing attribute (Should start on a
            FilterStartToken)
        registry: ModelRegistry

    Returns:
        root: FilterNode
        token_stream: generator(Toks) - remaining tokens after parsing filters
    """
    # TODO: Logic
    tok = None
    while not isinstance(tok, Toks.FilterEndToken):
        tok = next(token_stream)
    return FilterNode(), token_stream


def _attribute_to_ast(root_token, current_model, token_stream, registry):
    """ Helper to be called when building on a AttributeToken

    Requires:
        root_token: Toks.AttributeToken - the root token for the attribute
        current_model: The current SQLAlchemy model being parsed
        registry: ModelRegistry

    Returns:
        token_stream: generator(Toks) - remaining tokens after parsing attribute
        root: RootModel - the AstNode that is at the root of the object
    """
    assert isinstance(root_token, Toks.AttributeToken), \
        '_attribute_to_ast needs to have AttributeToken as its first token'

    root = AttributeNode(registry, current_model, root_token.attribute_name)
    next_token, token_stream = peek(token_stream)
    if not isinstance(next_token, Toks.FilterStartToken):
        return root, token_stream

    child = _filters_to_ast(current_model, root_token.attribute_name, token_stream, registry)
    root.add_child(child)

    return root, token_stream


def _open_object_to_ast(root_token, current_model, token_stream, registry):
    """ Helper to be called when building on a OpenObjectToken

    Requires:
        root_token: Toks.OpenObjectToken - the root token for the object
        current_model: The current SQLAlchemy model being parsed
        token_stream: generator(Toks) - stream of remaining tokens
        registry: ModelRegistry

    Returns:
        token_stream: generator(Toks) - remaining tokens after parsing object, after
            the CloseObjectToken that terminates the root query
        root: RootModel - the AstNode that is at the root of the object
    """
    assert isinstance(root_token, Toks.OpenObjectToken), \
        '_open_object_to_ast needs to have OpenObjectToken as its first token'

    root = RelationshipNode(registry, current_model, root_token.rel)

    token_ptr = next(token_stream)
    while not isinstance(token_ptr, Toks.CloseObjectToken):
        child_ast, token_stream = _tokens_to_ast(token_ptr, root.model, token_stream, registry)
        root.add_child(child_ast)
        try:
            token_ptr = next(token_stream)
        except StopIteration:
            raise SyntaxError(f'Closing }} not found while parsing {root.model}')

    return root, token_stream


def _root_query_to_ast(root_token, token_stream, registry):
    """ Helper to be called when building on a RootQueryToken

    Requires:
        root_token: Toks.RootQueryToken - the root token for the query
        token_stream: generator(Toks) - stream of remaining tokens
        registry: ModelRegistry

    Returns:
        token_stream: generator(Toks) - remaining tokens after parsing object, after
            the CloseObjectToken that terminates the root query
        root: RootModel - the AstNode that is at the root of the object
    """
    assert isinstance(root_token, Toks.RootQueryToken), \
        '_root_query_to_ast needs to have RootQueryToken as its first token'

    root = RootNode(registry, root_token.query_model)

    token_ptr = next(token_stream)
    while not isinstance(token_ptr, Toks.CloseObjectToken):
        child_ast, token_stream = _tokens_to_ast(token_ptr, root.model, token_stream, registry)
        root.add_child(child_ast)
        try:
            token_ptr = next(token_stream)
        except StopIteration:
            raise SyntaxError(f'Closing }} not found while parsing {root_token.query_model}')

    return root, token_stream


def tokens_to_ast(token_stream, registry):
    """ Returns the AST given a list of tokens and the model registry """
    root_token = next(token_stream)
    return _tokens_to_ast(root_token, None, token_stream, registry)
