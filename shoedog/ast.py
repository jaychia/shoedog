from sqlalchemy import inspect

class AstNode:
    """ A node in the AST tree """
    def __init__(self, children):
        self.children = tuple((x for x in children))

    def add_child(self, child):
        self.children += (child,)

    def eval(self, query):
        raise NotImplementedError(f'Node {self.__name__} has not implemented eval')

    def __repr__(self):
        return self.as_string() + '\n' + \
            '\n'.join(['\n'.join([f'\t{l}' for l in c.__repr__().split('\n')])
                       for c in self.children])


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
        return self.as_string() + '\n' + \
            '\n'.join(['\n'.join([f'\t{l}' for l in c.__repr__().split('\n')])
                       for c in [self.left, self.right]])
