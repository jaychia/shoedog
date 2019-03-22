from shoedog.tokenizer import Toks
from shoedog.ast import RootNode, RelationshipNode, AttributeNode, \
    FilterNode, BinaryLogicNode
from shoedog.utils import peek


def _tokens_to_ast(root_token, current_model, token_stream, registry):
    """ Helper to convert the next tokens in the token_stream to some AST

    Precondition: users of this helper need to peek to ensure that the next token
        is non-null. This helper works by calling the appropriate ast node specific
        helper function after introspecting the next token
    """
    if isinstance(root_token, Toks.RootQueryToken):
        return _root_query_to_ast(root_token, token_stream, registry)
    elif isinstance(root_token, Toks.OpenObjectToken):
        return _open_object_to_ast(root_token, current_model, token_stream, registry)
    elif isinstance(root_token, Toks.AttributeToken):
        return _attribute_to_ast(root_token, current_model, token_stream, registry)
    else:
        assert False, f'Should never be calling _tokens_to_ast on {root_token}'


def _filter_open_paran_to_ast(token_stream):
    next_token = next(token_stream)
    if isinstance(next_token, Toks.FilterOpenParanToken):
        ast, token_stream = _filter_open_paran_to_ast(token_stream)
    elif isinstance(next_token, Toks.FilterBoolToken):
        ast, token_stream = _filter_bool_to_ast(next_token, token_stream)
    else:
        assert False, f'Should not have {next_token} after OpenParan'

    # At this point, we have the ast from inside the open paran and token_stream
    # just passed a close paranthesis
    next_token = next(token_stream)
    if isinstance(next_token, Toks.FilterEndToken) or isinstance(next_token, Toks.FilterCloseParanToken):
        return ast, token_stream
    elif isinstance(next_token, Toks.FilterBinaryLogicToken):
        return _filter_binary_logic_to_ast(ast, next_token, token_stream)
    else:
        assert False, f'Should not have {next_token} after CloseParan'


def _filter_bool_to_ast(tok, token_stream):
    filter_node = FilterNode(tok.sel, tok.op, tok.val)
    next_token = next(token_stream)
    if isinstance(next_token, Toks.FilterBinaryLogicToken):
        return _filter_binary_logic_to_ast(filter_node, next_token, token_stream)
    elif isinstance(next_token, Toks.FilterCloseParanToken) or isinstance(next_token, Toks.FilterEndToken):
        return filter_node, token_stream
    else:
        assert False, f'Should not have {next_token} after FilterBoolToken'


def _filter_binary_logic_to_ast(left_bool, tok, token_stream):
    next_token = next(token_stream)
    if isinstance(next_token, Toks.FilterOpenParanToken):
        right_bool, token_stream = _filter_open_paran_to_ast(token_stream)
    elif isinstance(next_token, Toks.FilterBoolToken):
        right_bool, token_stream = _filter_bool_to_ast(next_token, token_stream)
    else:
        assert False, f'Should not have {next_token} after FilterBinaryLogicToken'

    root = BinaryLogicNode(tok.logic_op, left_bool, right_bool)
    return root, token_stream


def _filters_to_ast(token_stream):
    tok = next(token_stream)
    assert isinstance(tok, Toks.FilterStartToken)

    tok = next(token_stream)
    if isinstance(tok, Toks.FilterBoolToken):
        return _filter_bool_to_ast(tok, token_stream)
    elif isinstance(tok, Toks.FilterOpenParanToken):
        return _filter_open_paran_to_ast(token_stream)
    else:
        assert False, \
            f'Should not be receiving {tok} after FilterStartToken'


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

    child, token_stream = _filters_to_ast(token_stream)
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
