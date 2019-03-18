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
         field1 [* == 4 and * <= 3]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=4),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters3():
    query = '''
       Sample {
         field1 [(* == 'hi') and (* != 'bye')]
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
        Toks.FilterBoolToken(sel='*', op='!=', val='bye'),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters4():
    query = '''
       Sample {
         field1 [((* == 4) and (* <= 3))]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=4),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='<=', val=3),
        Toks.FilterCloseParanToken(),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters5():
    query = '''
       Sample {
         field1 [((* == 4) and (* <= 3)) or (* != 9)]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=4),
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


def test_tokenizer_filters6():
    query = '''
       Sample {
         field1 [* in ['foo', 'bar']]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=['foo', 'bar']),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters7():
    query = '''
       Sample {
         field1 [* in [true, false]]
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=[True, False]),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_subobject_filters():
    query = '''
       Sample {
         field1 [* in ['foo', 'bar']]
         tube (CastTube) {
           field2 [* == 3]
         }
       }
    '''
    assert tokenize(query) == (
        Toks.OpenObjectToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=['foo', 'bar']),
        Toks.FilterEndToken(),
        Toks.OpenObjectToken(query_model='tube'),
        Toks.CastToken(cast_class='CastTube'),
        Toks.AttributeToken(attribute_name='field2'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=3),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
    )


def test_line_syntax_error():
    query = '''
       Sample{
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'line 1: Sample{'

    query = '''
       Sample {
        field 1 [* == 9]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'line 2: field 1 [* == 9]'

    query = '''
       Sample {
        field1 [* in [1, 'hi']]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Multiple types detected for obj [1, \'hi\']'

    query = '''
       Sample {
        field1 [* == [1, 2]]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op == used on list obj [1, 2]'

    query = '''
       Sample {
        field1 [* in 'hey']
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op in used on non-list obj hey'

    query = '''
       Sample {
        field1 [* >= 'hey']
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op >= used on non-int obj hey'

    query = '''
       Sample {
        field1 [asdf]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == f'Could not parse filter [asdf]\n{" "* 37}^ SyntaxError starting here\n'

    query = '''
       Sample {
        field1 [* >= 'hey]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid filter object \'hey - is this a string?'

    query = '''
       Sample {
        field1 [* != true]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op != used on bool obj True: only == can be used on bools'

    query = '''
       Sample {
        field1 [* == true and any == false]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'A mix of selectors was provided for filter [* == true and any == false]'
