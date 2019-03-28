from datetime import date
from tests.mock_app import db, Sample, Tube
from shoedog.registry import build_registry
from shoedog.eval import eval_ast
from shoedog.ast import RootNode, AttributeNode, RelationshipNode, BinaryLogicNode, \
    FilterNode


mock_registry = build_registry(db)

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
            BinaryLogicNode(
                'or',
                FilterNode('*', '<', '2017-1-31'),
                FilterNode('*', '==', '2017-12-31'),
            ),
            FilterNode('*', '>', '2017-1-1'),
        )
    ])
])


def test_eval(session):
    sample_1 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_1_1', type='a'),
            Tube(name='tube_1_2', type='c'),
        ]
    )
    session.add(sample_1)
    sample_2 = Sample(
        date=date(year=2016, month=12, day=31),
        tubes=[
            Tube(name='tube_2_1', type='a'),
            Tube(name='tube_2_2', type='c'),
        ]
    )
    session.add(sample_2)
    sample_3 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_3_1', type='c'),
            Tube(name='tube_3_2', type='c'),
        ]
    )
    session.add(sample_3)
    sample_4 = Sample(
        date=date(year=2017, month=1, day=2),
        tubes=[
            Tube(name='tube_4_1', type='d'),
        ]
    )
    session.add(sample_4)
    session.flush()
    e = eval_ast(test_ast_1, session)

    assert len(e) == 2
    assert {s.id for s in e} == {sample_1.id, sample_3.id}


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
test_ast_2 = RootNode(mock_registry, 'Sample', children=[
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


def test_eval_2(session):
    # The only sample that fits the criteria
    sample_1 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_1)
    sample_2 = Sample(
        tube=Tube(name='bad', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_2)
    sample_3 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='bad')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_3)
    sample_4 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='bad', tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_4)
    sample_5 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube(name='bad')))
    )
    session.add(sample_5)
    sample_6 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube()))
    )
    session.add(sample_6)
    sample_7 = Sample(
        tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')))
    )
    session.add(sample_7)
    sample_8 = Sample(
        tube=Tube(name='only-this-self-sample-tube-self-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(name='only-this-self-sample', tube=Tube(self_tube=Tube(name='only-this-tube')))
    )
    session.add(sample_8)
    session.flush()
    e = eval_ast(test_ast_2, session)
    assert len(e) == 1
    assert {s.id for s in e} == {sample_1.id}
