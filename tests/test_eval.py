import pytest

from datetime import date
from tests.mock_app import db, Sample, Tube
from shoedog.parser import tokens_to_ast
from shoedog.registry import build_registry
from shoedog.eval import eval_ast
from shoedog.ast import RootNode, AttributeNode, RelationshipNode, BinaryLogicNode, \
    FilterNode


mock_registry = build_registry(db)


# Insert mock data
@pytest.fixture
def samples():
    sample_1 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_1_1', type='a'),
            Tube(name='tube_1_2', type='c'),
        ]
    )
    db.session.add(sample_1)
    sample_2 = Sample(
        date=date(year=2016, month=12, day=31),
        tubes=[
            Tube(name='tube_2_1', type='a'),
            Tube(name='tube_2_2', type='c'),
        ]
    )
    db.session.add(sample_2)
    sample_3 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_3_1', type='c'),
            Tube(name='tube_3_2', type='c'),
        ]
    )
    db.session.add(sample_3)
    sample_4 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_4_1', type='d'),
        ]
    )
    db.session.add(sample_4)
    db.session.flush()


"""
query Sample {
    id
    tubes {
        name
        type [any in ['a', 'b'] or all != 'c']
    }
    date [((* < '2017-01-31') or * == '2017-12-31') and ((* > '2017-1-1'))]
}
"""
test_ast_1 = RootNode(mock_registry, 'Sample', children=[
    AttributeNode(mock_registry, Sample, 'id'),
    RelationshipNode(mock_registry, Sample, 'tubes', children=[
        AttributeNode(mock_registry, Tube, 'name'),
        AttributeNode(mock_registry, Tube, 'type', children=[
            BinaryLogicNode('or', FilterNode('any', 'in', ['a', 'b']), FilterNode('all', '!=', 'c'))
        ]),
    ]),
    AttributeNode(mock_registry, Sample, 'date', children=[
        BinaryLogicNode(
            'and',
            BinaryLogicNode('or', FilterNode('*', '<', date(year=2017, month=1, day=31)), FilterNode('*', '==', date(year=2017, month=12, day=31))),
            FilterNode('*', '>', date(year=2017, month=1, day=1))
        )
    ])
])


def test_eval(session, samples):
    e = eval_ast(test_ast_1, session)
    print(e)
