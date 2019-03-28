import pytest
from shoedog.tokenizer import Toks
from shoedog.ast import RootNode, RelationshipNode, \
    AttributeNode, FilterNode, BinaryLogicNode
from shoedog.parser import tokens_to_ast
from shoedog.registry import build_registry
from tests.mock_app import db, Sample, Tube

mock_registry = build_registry(db)

"""
query Sample {
    id
    tube {
        name
        type [any in ['a', 'b'] or all != 'c']
    }
    date [((* < '3/9/2017') or * == '3/3/2017') and ((* > '3/10/2017'))]
}
"""
test_token_gen_1 = (x for x in (
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
))

test_token_ast_1 = RootNode(mock_registry, 'Sample', children=[
    AttributeNode(mock_registry, Sample, 'id'),
    RelationshipNode(mock_registry, Sample, 'tube', children=[
        AttributeNode(mock_registry, Tube, 'name'),
        AttributeNode(mock_registry, Tube, 'type', children=[
            BinaryLogicNode('or', FilterNode('any', 'in', ['a', 'b']), FilterNode('all', '!=', 'c'))
        ]),
    ]),
    AttributeNode(mock_registry, Sample, 'date', children=[
        BinaryLogicNode(
            'and',
            BinaryLogicNode('or', FilterNode('*', '<', '3/9/2017'), FilterNode('*', '==', '3/3/2017')),
            FilterNode('*', '>', '3/10/2017')
        )
    ])
])


def test_tokens_to_ast_1():
    root, stream = tokens_to_ast(test_token_gen_1, mock_registry)
    with pytest.raises(StopIteration):
        next(stream)
    assert root == test_token_ast_1

"""
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
"""
test_token_gen_2 = (x for x in (
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
))

test_token_ast_2 = RootNode(mock_registry, 'Sample', children=[
    AttributeNode(mock_registry, Sample, 'id'),
    RelationshipNode(mock_registry, Sample, 'tube', children=[
        AttributeNode(mock_registry, Tube, 'name', children=[
            FilterNode('*', '==', 'only-this-tube')
        ]),
        RelationshipNode(mock_registry, Tube, 'self_tube', children=[
            AttributeNode(mock_registry, Tube, 'name', children=[
                FilterNode('*', '==', 'only-this-tube-self-tube')
            ]),
        ]),
    ]),
    RelationshipNode(mock_registry, Sample, 'self_sample', children=[
        AttributeNode(mock_registry, Sample, 'name', children=[
            FilterNode('*', '==', 'only-this-self-sample')
        ]),
        RelationshipNode(mock_registry, Sample, 'tube', children=[
            RelationshipNode(mock_registry, Tube, 'self_tube', children=[
                AttributeNode(mock_registry, Tube, 'name', children=[
                    FilterNode('*', '==', 'only-this-self-sample-tube-self-tube')
                ]),
            ]),
        ]),
    ]),
])


def test_tokens_to_ast_2():
    root, stream = tokens_to_ast(test_token_gen_2, mock_registry)
    with pytest.raises(StopIteration):
        next(stream)
    assert root == test_token_ast_2
