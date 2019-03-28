from datetime import datetime
from sqlalchemy.types import Date

from sqlalchemy.orm import contains_eager, lazyload, aliased, load_only
from sqlalchemy import and_, or_
from shoedog.ast import RootNode, RelationshipNode, AttributeNode, BinaryLogicNode, FilterNode
from sqlalchemy import inspect

FMAP = {
    '==': '__eq__',
    '!=': '__ne__',
    '>': '__gt__',
    '<': '__lt__',
    '>=': '__gte__',
    '<=': '__lte__',
    'in': 'in_'
}


def _cast_obj(raw_obj, attr):
    # TODO: Add more custom parsing for SQLAlchemy types
    # Possibly allow for custom type parsing here too
    if isinstance(attr.type, Date):
        return datetime.strptime(raw_obj, '%Y-%m-%d')
    else:
        return raw_obj


def _eval_filters(ast, attr, rel, alias):
    if isinstance(ast, BinaryLogicNode):
        if ast.op == 'and':
            return and_(
                _eval_filters(ast.left, attr, rel, alias),
                _eval_filters(ast.right, attr, rel, alias),
            )
        elif ast.op == 'or':
            return or_(
                _eval_filters(ast.left, attr, rel, alias),
                _eval_filters(ast.right, attr, rel, alias),
            )
        else:
            raise NotImplementedError(f'Binary op {ast.op} not implemented')
    elif isinstance(ast, FilterNode):
        obj = _cast_obj(ast.obj, attr)

        if ast.subject == 'any':
            if rel is None or not rel.property.uselist:
                e = 'root query class' if rel is None else rel
                raise SyntaxError(f'Cannot specify any filter on {e}')
            return rel.any(getattr(attr, FMAP[ast.op])(obj))

        elif ast.subject == 'all':
            if rel is None or not rel.property.uselist:
                e = 'root query class' if rel is None else rel
                raise SyntaxError(f'Cannot specify all filter on {e}')
            return ~rel.any(getattr(attr, FMAP[ast.op])(obj))

        elif ast.subject == '*':
            if rel is not None and rel.property.uselist:
                raise SyntaxError(f'Cannot specify * filter on singular relationship {rel}')
            return getattr(attr, FMAP[ast.op])(obj)

        else:
            raise SyntaxError(f'Invalid subject for _eval_filters {ast.subject}')


def _eval_ast(ast, query, aliased_current_model, current_rel_path):
    """
    Requires:
        aliased_current_model - is the current model aliased
        current_rel_path - a tuple of (relationship, aliased_class) where the first
            relationship (relationship on the root model) is aliased but the rest
            are not. This ends up looking something like:

            ((root_alias.field1, Field1Alias),
             (Field1.field2, Field2Alias),
             (Field2.field3, Field3Alias))
    """
    # Handle RelationshipNode
    if isinstance(ast, RelationshipNode):
        # Get the relationship and alias it to avoid conflicts
        current_model = inspect(aliased_current_model).class_
        aliased_new_rel = getattr(aliased_current_model, ast.rel.key)
        new_rel = getattr(current_model, ast.rel.key)  # Unaliased rel

        aliased_rel_model = aliased(new_rel)  # Create an alias of the new relationship we are diving into

        # Build a chain of contains_eagers to get to the new relationship we are diving into
        #
        # The chain has to look like:
        # contains_eager(root_alias.field1, alias=Field1Alias). \
        #   contains_eager(Field1.field2, alias=Field2Alias). \
        #   contains_eager(Field2.field3, alias=Field3Alias). \
        #
        # Notice the root contains_eager starts with the root_alias.field1 aliased relationship
        # but every consequent contains_eager does not use an alias. The alias kwarg tells
        # contains_eager where to find the corresponding .join - for e.g. alias=Field2Alias
        # looks for .join(Field2Alias, Field1Alias.field2) and uses the loaded data there
        # as the data to populate for root_alias.field1.field2
        #
        # Therefore, when we store the new_rel_path, we store the first root rel as an aliased
        # relationship, but every other relationship is an unaliased relationship
        new_rel_path = ((aliased_new_rel, aliased_rel_model),) \
            if not current_rel_path else \
            current_rel_path + ((new_rel, aliased_rel_model),)

        contains_eager_chain = None
        for rel, rel_alias in new_rel_path:
            contains_eager_chain = contains_eager(rel, alias=rel_alias) \
                if contains_eager_chain is None \
                else contains_eager_chain.contains_eager(rel, alias=rel_alias)

        # Add the appropriate join, and annotate it with the correct alias
        query = query.options(contains_eager_chain) \
                     .join(aliased_rel_model, aliased_new_rel)

        # Run recursively on the children
        for c in ast.children:
            query = _eval_ast(c, query, aliased_rel_model, new_rel_path)
        return query

    # Handle AttributeNode
    elif isinstance(ast, AttributeNode):
        attr = getattr(aliased_current_model, ast.attr.key)
        # TODO: Pass in the entire rel path so we can do load_only
        # query = query.options(load_only(attr))
        if ast.children:
            rel, alias = current_rel_path[-1] if current_rel_path else (None, None)
            filters = _eval_filters(ast.children[0], attr, rel, alias)
            query = query.filter(filters)
        return query
    else:
        assert False, f'Should not vall _eval_ast on {ast}'


def eval_ast(ast, session):
    assert isinstance(ast, RootNode), \
            'Must start evaluation on RootNode!'
    root_alias = aliased(ast.model)
    query = session.query(root_alias).options(lazyload('*'))
    for c in ast.children:
        query = _eval_ast(c, query, root_alias, tuple())
    return query.all()
