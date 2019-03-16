import pytest
from shoedog.tokenizer import Toks, tokenize


def test_basic_tokenizer():
    query = '''
       Sample {
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.CloseObjectToken(),
    )


def test_line1_syntax_error():
    query = '''
       Sample{
    '''
    with pytest.raises(SyntaxError):
        tokenize(query)
