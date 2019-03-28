import pytest
from shoedog.tokenizer import Toks, tokenize


def test_basic_tokenizer_no_fields():
    query = '''
       query Sample {
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_one_field():
    query = '''
       query Sample {
         field1
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters1():
    query = '''
       query Sample {
         field1 [* == 'hi']
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='hi'),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters2():
    query = '''
       query Sample {
         field1 [* == 4 and * <= 3]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
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
       query Sample {
         field1 [(* == 'hi') and (* != 'bye')]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
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
       query Sample {
         field1 [((* == 4) and (* <= 3))]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
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
       query Sample {
         field1 [((* == 4) and (* <= 3)) or (* != 9)]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
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
       query Sample {
         field1 [* in ['foo', 'bar']]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=['foo', 'bar']),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_filters7():
    query = '''
       query Sample {
         field1 [* in [true, false]]
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=[True, False]),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_subobject_filters1():
    query = '''
       query Sample {
         field1 [* in ['foo', 'bar']]
         tube (CastTube) {
           field2 [* == 3]
         }
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=['foo', 'bar']),
        Toks.FilterEndToken(),
        Toks.OpenObjectToken(rel='tube'),
        Toks.CastToken(cast_class='CastTube'),
        Toks.AttributeToken(attribute_name='field2'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=3),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_subobject_filters2():
    query = '''
       query Sample {
         field1 [* in ['foo', 'bar']]
         tube {
           field2 [* == 3]
         }
       }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='field1'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='in', val=['foo', 'bar']),
        Toks.FilterEndToken(),
        Toks.OpenObjectToken(rel='tube'),
        Toks.AttributeToken(attribute_name='field2'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val=3),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_parser_test_1():
    query = '''
        query Sample {
            id
            tube {
                name
                type [any in ['a', 'b'] or all != 'c']
            }
            date [((* < '3/9/2017') or * == '3/3/2017') and ((* > '3/10/2017'))]
        }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='id'),
        Toks.OpenObjectToken(rel='tube'),
        Toks.AttributeToken(attribute_name='name'),
        Toks.AttributeToken(attribute_name='type'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='any', op='in', val=['a', 'b']),
        Toks.FilterBinaryLogicToken(logic_op='or'),
        Toks.FilterBoolToken(sel='all', op='!=', val='c'),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.AttributeToken(attribute_name='date'),
        Toks.FilterStartToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='<', val='3/9/2017'),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='or'),
        Toks.FilterBoolToken(sel='*', op='==', val='3/3/2017'),
        Toks.FilterCloseParanToken(),
        Toks.FilterBinaryLogicToken(logic_op='and'),
        Toks.FilterOpenParanToken(),
        Toks.FilterOpenParanToken(),
        Toks.FilterBoolToken(sel='*', op='>', val='3/10/2017'),
        Toks.FilterCloseParanToken(),
        Toks.FilterCloseParanToken(),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
    )


def test_tokenizer_parser_test_2():
    query = '''
        query Sample {
            id
            tube {
                name [* == 'only-this-tube']
                self_tube {
                    name [* == 'only-this-tube-self-tube']
                }
            }
            self_sample {
                name [* == 'only-this-self-sample']
                tube {
                    self_tube {
                        name [* == 'only-this-self-sample-tube-self-tube']
                    }
                }
            }
        }
    '''
    assert tuple(tokenize(query)) == (
        Toks.RootQueryToken(query_model='Sample'),
        Toks.AttributeToken(attribute_name='id'),
        Toks.OpenObjectToken(rel='tube'),
        Toks.AttributeToken(attribute_name='name'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='only-this-tube'),
        Toks.FilterEndToken(),
        Toks.OpenObjectToken(rel='self_tube'),
        Toks.AttributeToken(attribute_name='name'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='only-this-tube-self-tube'),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
        Toks.OpenObjectToken(rel='self_sample'),
        Toks.AttributeToken(attribute_name='name'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='only-this-self-sample'),
        Toks.FilterEndToken(),
        Toks.OpenObjectToken(rel='tube'),
        Toks.OpenObjectToken(rel='self_tube'),
        Toks.AttributeToken(attribute_name='name'),
        Toks.FilterStartToken(),
        Toks.FilterBoolToken(sel='*', op='==', val='only-this-self-sample-tube-self-tube'),
        Toks.FilterEndToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
        Toks.CloseObjectToken(),
    )


def test_line_syntax_error():
    query = '''
       query Sample{
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'line 1: query Sample{'

    query = '''
       query Sample {
        field 1 [* == 9]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'line 2: field 1 [* == 9]'

    # This is prevented by regex
    # query = '''
    #    query Sample {
    #     field1 [* in [1, 'hi']]
    #    }
    # '''
    # with pytest.raises(SyntaxError) as e:
    #     tokenize(query)
    # assert str(e.value) == 'Multiple types detected for obj [1, \'hi\']'

    query = '''
       query Sample {
        field1 [* == [1, 2]]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op == used on list obj [1, 2]'

    query = '''
       query Sample {
        field1 [* in 'hey']
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op in used on non-list obj hey'

    # Sometimes strings could be dates
    # query = '''
    #    query Sample {
    #     field1 [* >= 'hey']
    #    }
    # '''
    # with pytest.raises(SyntaxError) as e:
    #     tokenize(query)
    # assert str(e.value) == 'Invalid op >= used on non-int obj hey'

    query = '''
       query Sample {
        field1 [asdf]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == f'Could not parse filter [asdf]\n{" "* 38}^ SyntaxError starting here\n'

    # This is prevented by regex
    # query = '''
    #    query Sample {
    #     field1 [* >= 'hey]
    #    }
    # '''
    # with pytest.raises(SyntaxError) as e:
    #     tokenize(query)
    # assert str(e.value) == 'Invalid filter object \'hey - is this a string?'

    query = '''
       query Sample {
        field1 [* != true]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'Invalid op != used on bool obj True: only == can be used on bools'

    query = '''
       query Sample {
        field1 [* == true and any == false]
       }
    '''
    with pytest.raises(SyntaxError) as e:
        tokenize(query)
    assert str(e.value) == 'A mix of selectors was provided for filter [* == true and any == false]'
