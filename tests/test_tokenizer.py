import pytest
from shoedog.tokenizer import Toks, tokenize


def test_basic_tokenizer_no_fields():
    query = '''
       Sample {
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_one_field():
    query = '''
       Sample {
         field1
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_one_field_filtered():
    query = '''
       Sample {
         field1 [* == 'hi']
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val="'hi'"),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_line1_syntax_error():
    query = '''
       Sample{
    '''
    with pytest.raises(SyntaxError):
        tokenize(query)
