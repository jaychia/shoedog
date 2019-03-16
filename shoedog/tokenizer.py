import re
from collections import namedtuple


class Toks:
    OpenObjectToken = namedtuple('OpenObjectToken', ['query_model'])
    AttributeToken = namedtuple('AttributeToken', ['attribute_name'])
    FilterToken = namedtuple('FilterToken', ['left', 'op', 'right'])
    CloseObjectToken = namedtuple('ClosedObjectToken', [])
    CastToken = namedtuple('CastToken', ['cast_class'])


regexes = {
    Toks.OpenObjectToken: re.compile(r'(?P<query_model>[A-Z]\w*) {'),
    Toks.CloseObjectToken: re.compile(r'\s*}\s*'),
}


def _validate_line(i, match, match_tok, line):
    """ Helper to throw errors based on state of tokenizer """
    if i == 0 and match_tok.__name__ != Toks.OpenObjectToken.__name__:
        raise SyntaxError(f'line {i+1}: Expected a query model on the first line'
                          f' but received `{line}` instead')


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

        tokens += (match_tok(**match.groupdict()),)

    return tokens
