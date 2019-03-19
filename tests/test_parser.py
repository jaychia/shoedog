from shoedog.tokenizer import Toks
from shoedog.ast import tokens_to_ast
from shoedog.registry import build_registry
from tests.mock_app import db

mock_registry = build_registry(db)

"""
query Sample {
    id
    tube {
        name
        type [any in ['a', 'b'] or all in ['c']]
    }
    date [* < '3/9/2017' and * > '3/10/2017']
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
    Toks.FilterBoolToken(sel='all', op='in', val=['c']),
    Toks.FilterEndToken(),
    Toks.CloseObjectToken(),
    Toks.AttributeToken(attribute_name='date'),
    Toks.FilterStartToken(),
    Toks.FilterBoolToken(sel='*', op='<', val='3/9/2017'),
    Toks.FilterBinaryLogicToken(logic_op='and'),
    Toks.FilterBoolToken(sel='*', op='>', val='3/10/2017'),
    Toks.FilterEndToken(),
    Toks.CloseObjectToken(),
))


def test_tokens_to_ast():
    tokens_to_ast(test_token_gen_1, mock_registry)
