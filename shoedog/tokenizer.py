import re
from collections import namedtuple
from shoedog.consts import integer_only_ops, valid_ops, valid_selectors


class Toks:
    CastToken = namedtuple('CastToken', ['cast_class'])
    OpenObjectToken = namedtuple('OpenObjectToken', ['query_model'])
    CloseObjectToken = namedtuple('CloseObjectToken', [])
    AttributeToken = namedtuple('AttributeToken', ['attribute_name'])
    FilterBoolToken = namedtuple('FilterBoolToken', ['sel', 'op', 'val'])
    FilterBinaryLogicToken = namedtuple('FilterBinaryLogicToken', ['logic_op'])
    FilterOpenParanToken = namedtuple('FilterOpenParanToken', [])
    FilterCloseParanToken = namedtuple('FilterCloseParanToken', [])
    FilterStartToken = namedtuple('FilterStartToken', [])
    FilterEndToken = namedtuple('FilterEndToken', [])


class LineToks:
    OpenObjectLine = namedtuple('OpenObjectLine', ['query_model', 'cast_class'])
    AttributeLine = namedtuple('AttributeLine', ['attribute_name', 'filters'])
    CloseObjectLine = namedtuple('CloseObjectLine', [])


regexes = {
    LineToks.OpenObjectLine: re.compile(r'^(?P<query_model>[A-Z]\w*)(?P<cast_class> \([A-Z]\w*\))? {$'),
    LineToks.CloseObjectLine: re.compile(r'^}$'),
    LineToks.AttributeLine: re.compile(r"^(?P<attribute_name>\w*)[\s]?(?P<filters>\[.+\])?$")
}


def _validate_line(i, match, match_tok, line):
    """ Helper to throw errors based on state of tokenizer """
    if i == 0 and match_tok.__name__ != LineToks.OpenObjectLine.__name__:
        raise SyntaxError(f'line {i+1}: Expected a query model on the first line'
                          f' but received `{line}` instead')


def _validate_filter(match_obj, filter_string, lexer_ptr):
    """ Helper to throw errors based on matched filter """
    if not match_obj:
        raise SyntaxError(
            f'Could not parse filter {filter_string}\n{" " * len("SyntaxError: Could not parse filter ")}'
            f'{" " * lexer_ptr}^ SyntaxError starting here\n'
        )
    s = match_obj.group('subject')
    op = match_obj.group('op')
    obj = match_obj.group('object')
    if not s or not op or not obj:
        raise SyntaxError(f'Unable to parse filter {s} {op} {obj}')
    if s not in valid_selectors:
        raise SyntaxError(f'Unable to parse selector {s}')
    if op not in valid_ops:
        raise SyntaxError(f'Invalid filter op {op}')


filter_regex = re.compile(r"^(?P<subject>\*|all|any) (?P<op>[^\s]+) (?P<object>'?\w+'?)")


def _get_filter_tokens_from_string(s):
    filter_toks = tuple()
    filters = s[1:-1]

    lexer_ptr = 0
    while lexer_ptr < len(filters):
        c = filters[lexer_ptr]
        if c == ' ':
            lexer_ptr += 1
            continue
        elif c == '(':
            filter_toks += (Toks.FilterOpenParanToken(),)
            lexer_ptr += 1
            continue
        elif c == ')':
            filter_toks += (Toks.FilterCloseParanToken(),)
            lexer_ptr += 1
            continue
        elif filters[lexer_ptr:lexer_ptr+4] == 'and ':
            filter_toks += (Toks.FilterBinaryLogicToken(logic_op='and'),)
            lexer_ptr += len('and ')
            continue
        elif filters[lexer_ptr:lexer_ptr+4] == 'or ':
            filter_toks += (Toks.FilterBinaryLogicToken(logic_op='or'),)
            lexer_ptr += len('or ')
            continue
        else:
            print(filter_regex.match(filters[lexer_ptr:]))
            m = filter_regex.match(filters[lexer_ptr:])
            _validate_filter(m, s, lexer_ptr)
            filter_toks += (Toks.FilterBoolToken(sel=m.group('subject'), op=m.group('op'), val=m.group('object')),)
            lexer_ptr += m.end() - m.start()
    return filter_toks


def tokenize(querystring):
    """Takes a query string and returns a list of tokens"""
    tokens = tuple()
    lines = (s.strip() for s in querystring.split('\n') if s.strip())

    for i, line in enumerate(lines):
        match, match_tok = None, None
        for tok in regexes:
            m = regexes[tok].match(line)
            if m:
                match, match_tok = m, tok
        if (match, match_tok) == (None, None):
            raise SyntaxError(f'line {i+1}: {line}')

        _validate_line(i, match, match_tok, line)

        ast_tokens = tuple()
        line_token = match_tok(**match.groupdict())

        if isinstance(line_token, LineToks.OpenObjectLine):
            ast_tokens += (Toks.OpenObjectToken(query_model=line_token.query_model),)
            if line_token.cast_class:
                ast_tokens += (Toks.CastToken(cast_class=line_token.cast_class),)
        elif isinstance(line_token, LineToks.AttributeLine):
            ast_tokens += (Toks.AttributeToken(attribute_name=line_token.attribute_name),)
            if line_token.filters:
                ast_tokens += (Toks.FilterStartToken(),)
                ast_tokens += _get_filter_tokens_from_string(line_token.filters)
                ast_tokens += (Toks.FilterEndToken(),)
        elif isinstance(line_token, LineToks.CloseObjectLine):
            ast_tokens += (Toks.CloseObjectToken(),)
        else:
            raise NotImplementedError(f'Internal Error: Token parsing for'
                                      f'{match_tok} not implemented')
        tokens += ast_tokens

    return tokens
