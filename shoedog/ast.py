from sqlalchemy import inspect
from shoedog.tokenizer import Toks
from shoedog.utils import peek
from shoedog.consts import binary_logical_ops


class AstNode:
    """ A node in the AST tree """
    def __init__(self, children):
        self.children = tuple((x for x in children))

    def add_child(self, child):
        self.children += (child,)

    def eval(self, query):
        raise NotImplementedError(f'Node {self.__name__} has not implemented eval')

    def __repr__(self):
        return self.as_string() + '\n' + '\n'.join(['\n'.join([f'\t{l}' for l in c.__repr__().split('\n')]) for c in self.children])


class RootNode(AstNode):
    """ The root node of the AST representing the model at the root of the query """
    def __init__(self, registry, root_model_name, children=[]):
        super().__init__(children)
        self.model = registry.get_model_with_name(root_model_name)

    def __eq__(self, other):
        return type(other) == type(self) and \
            self.model == other.model and \
            len(self.children) == len(other.children) and \
            all([x == y for x, y in zip(self.children, other.children)])

    def as_string(self):
        return f'<RootNode {self.model.__name__}>'


class RelationshipNode(AstNode):
    """ The root node of the AST representing a relationship """
    def __init__(self, registry, root_model, rel, children=[]):
        super().__init__(children)
        self.rel = getattr(root_model, rel)
        self.model = registry.get_model_with_rel(self.rel)

    def __eq__(self, other):
        return type(other) == type(self) and \
            self.model == other.model and \
            inspect(self.rel).mapper.class_ == inspect(other.rel).mapper.class_ and \
            self.rel.key == other.rel.key and \
            len(self.children) == len(other.children) and \
            all([x == y for x, y in zip(self.children, other.children)])

    def as_string(self):
        return f'<RelationshipNode {self.model.__name__}.{self.rel.key}>'


class AttributeNode(AstNode):
    """ The root node of the AST representing an attribute """
    def __init__(self, registry, root_model, attr_name, children=[]):
        super().__init__(children)
        self.attr = getattr(root_model, attr_name)

    def __eq__(self, other):
        return type(other) == type(self) and \
            inspect(self.attr).class_ == inspect(other.attr).class_ and \
            self.attr.key == other.attr.key and \
            len(self.children) == len(other.children) and \
            all([x == y for x, y in zip(self.children, other.children)])

    def as_string(self):
        return f'<AttributeNode {self.attr.key}>'


class FilterNode(AstNode):
    """ The AST node representing a single filter """
    def __init__(self, subject, op, obj):
        # TODO: Type validations here
        super().__init__([])
        self.subject = subject
        self.op = op
        self.obj = obj

    def __eq__(self, other):
        return type(other) == type(self) and \
            self.subject == other.subject and \
            self.op == other.op and \
            self.obj == other.obj

    def add_child(self, child):
        raise NotImplementedError('Cannot add child to FilterNode')

    def as_string(self):
        return f'<FilterNode {self.subject} {self.op} {self.obj}>'


class BinaryLogicNode(AstNode):
    """ The AST node representing a binary logical operator on filters """
    def __init__(self, op, left, right):
        super().__init__([])
        self.op = op
        self.left = left
        self.right = right

    def __eq__(self, other):
        return type(other) == type(self) and \
            self.op == other.op and \
            self.left == other.left and \
            self.right == other.right

    def as_string(self):
        return f'<BinaryLogicNode {self.op}>'

    def __repr__(self):
        return self.as_string() + '\n' + '\n'.join(['\n'.join([f'\t{l}' for l in c.__repr__().split('\n')]) for c in [self.left, self.right]])


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
