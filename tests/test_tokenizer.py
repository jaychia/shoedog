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


def test_tokenizer_filters1():
    query = '''
       Sample {
         field1 [* == 'hi']
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters2():
    query = '''
       Sample {
         field1 [* == 'hi' and * <= 3]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters3():
    query = '''
       Sample {
         field1 [(* == 'hi') and (* <= 3)]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters4():
    query = '''
       Sample {
         field1 [((* == 'hi') and (* <= 3))]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterCloseParanToken(),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters4():
    query = '''
       Sample {
         field1 [((* == 'hi') and (* <= 3)) or (* != 9)]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterCloseParanToken(),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='or'),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='!=', val=9),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_line1_syntax_error():
    query = '''
       Sample{
    '''
    with pytest.raises(SyntaxError):
        tokenize(query)
