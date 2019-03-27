from sqlalchemy.orm import contains_eager, lazyload, aliased, load_only
from sqlalchemy import and_, or_
from shoedog.ast import RootNode, RelationshipNode, AttributeNode, BinaryLogicNode, FilterNode


def _eval_filters(ast, attr, rel):
    if isinstance(ast, BinaryLogicNode):
        if ast.op == 'and':
            return and_(_eval_filters(ast.left, attr, rel), _eval_filters(ast.right, attr, rel))
        elif ast.op == 'or':
            return or_(_eval_filters(ast.left, attr, rel), _eval_filters(ast.right, attr, rel))
        else:
            raise NotImplementedError(f'Binary op {ast.op} not implemented')
    elif isinstance(ast, FilterNode):
        f = {
            '==': '__eq__',
            '!=': '__ne__',
            '>': '__gt__',
            '<': '__lt__',
            '>=': '__gte__',
            '<=': '__lte__',
            'in': 'in_'
        }

        if ast.subject == 'any':
            if rel is None or not rel.property.uselist:
                e = 'root query class' if rel is None else rel
                raise SyntaxError(f'Cannot specify any filter on {e}')
            return rel.any(getattr(attr, f[ast.op])(ast.obj))

        elif ast.subject == 'all':
            if rel is None or not rel.property.uselist:
                e = 'root query class' if rel is None else rel
                raise SyntaxError(f'Cannot specify all filter on {e}')
            return ~rel.any(getattr(attr, f[ast.op])(ast.obj))

        elif ast.subject == '*':
            if rel is not None and rel.uselist:
                raise SyntaxError(f'Cannot specify * filter on singular relationship {rel}')
            return getattr(attr, f[ast.op])(ast.obj)

        else:
            raise SyntaxError(f'Invalid subject for _eval_filters {ast.subject}')


def _eval_ast(ast, query, current_model, current_rel):
    if isinstance(ast, RelationshipNode):
        new_rel = getattr(current_model, ast.rel.key)
        query = query.options(contains_eager(new_rel)) \
                     .join(new_rel)
        for c in ast.children:
            query = _eval_ast(c, query, ast.model, new_rel)
        return query
    elif isinstance(ast, AttributeNode):
        attr = getattr(current_model, ast.attr.key)
        # TODO: Pass in the entire rel path so we can do load_only
        # query = query.options(load_only(attr))
        if ast.children:
            filters = _eval_filters(ast.children[0], attr, current_rel)
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
        query = _eval_ast(c, query, root_alias, None)
    return query.all()
