import re
from collections import namedtuple


class Toks:
    OpenObjectToken = namedtuple('OpenObjectToken', ['query_model'])
    AttributeToken = namedtuple('AttributeToken', ['attribute_name'])
    FilterToken = namedtuple('FilterToken', ['left', 'op', 'right'])
    CloseObjectToken = namedtuple('CloseObjectToken', [])
    CastToken = namedtuple('CastToken', ['cast_class'])


class LineToks:
    OpenObjectLine = namedtuple('OpenObjectLine', ['query_model', 'cast_class'])
    AttributeLine = namedtuple('AttributeLine', ['attribute_name', 'filters'])
    CloseObjectLine = namedtuple('CloseObjectLine', [])


regexes = {
    LineToks.OpenObjectLine: re.compile(r'(?P<query_model>[A-Z]\w*)(?P<cast_class> \([A-Z]\w*\))? {'),
    LineToks.CloseObjectLine: re.compile(r'\s*}\s*'),
    LineToks.AttributeLine: re.compile(r"(?P<attribute_name>\w*)(?P<filters>\[[\w|\s|<|>|<=|>=|==|']+\])?$")
}


def _validate_line(i, match, match_tok, line):
    """ Helper to throw errors based on state of tokenizer """
    if i == 0 and match_tok.__name__ != LineToks.OpenObjectLine.__name__:
        raise SyntaxError(f'line {i+1}: Expected a query model on the first line'
                          f' but received `{line}` instead')


def _get_filters_from_string(s):
    print(f'Trying to get filter from {s}')
    return tuple()


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
                ast_tokens += (Toks.CastToken(cast_class=line_token.cast_class))
        elif isinstance(line_token, LineToks.AttributeLine):
            ast_tokens += (Toks.AttributeToken(attribute_name=line_token.attribute_name))
            if line_token.filters:
                ast_tokens += _get_filters_from_string(line_token.filters)
        elif isinstance(line_token, LineToks.CloseObjectLine):
            ast_tokens += (Toks.CloseObjectToken(),)
        else:
            raise NotImplementedError(f'Internal Error: Token parsing for'
                                      f'{match_tok} not implemented')
        tokens += ast_tokens
    return tokens
