from datetime import date
from shoedog.registry import build_registry
from shoedog.query_factory import QueryFactory
from tests.mock_app import db, Sample, Tube

mock_registry = build_registry(db)

qf = QueryFactory(db)


def test_end_to_end_1(session):
    q = '''
        query Sample {
        id
        tubes {
            name
            type [any in ['a', 'b'] or all != 'c']
        }
        date [((* < '2017-01-31') or * == '2017-12-31') and ((* > '2017-1-1'))]
    }
    '''
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

    json_response = qf.parse_query(q)

    # TODO: Change test after implementing returning only
    # specified fields
    assert json_response == \
        [{'date': '2017-01-02',
          'id': 1,
          'name': None,
          'self_sample_id': None,
          'tube_id': None,
          'tubes': [{'date': None,
                     'id': 1,
                     'name': 'tube_1_1',
                     'sample_id': 1,
                     'self_tube_id': None,
                     'type': 'a'},
                    {'date': None,
                     'id': 2,
                     'name': 'tube_1_2',
                     'sample_id': 1,
                     'self_tube_id': None,
                     'type': 'c'}]},
         {'date': '2017-01-02',
          'id': 3,
          'name': None,
          'self_sample_id': None,
          'tube_id': None,
          'tubes': [{'date': None,
                     'id': 5,
                     'name': 'tube_3_1',
                     'sample_id': 3,
                     'self_tube_id': None,
                     'type': 'c'},
                    {'date': None,
                     'id': 6,
                     'name': 'tube_3_2',
                     'sample_id': 3,
                     'self_tube_id': None,
                     'type': 'c'}]}]


def test_end_to_end_2(session):
    q = '''
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
    # The only sample that fits the criteria
    sample_1 = Sample(
        name='I should be the only one being returned',
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_1)
    sample_2 = Sample(
        tube=Tube(name='bad', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_2)
    sample_3 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='bad')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_3)
    sample_4 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='bad',
            tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')))
    )
    session.add(sample_4)
    sample_5 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube(name='bad')))
    )
    session.add(sample_5)
    sample_6 = Sample(
        tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube()))
    )
    session.add(sample_6)
    sample_7 = Sample(
        tube=Tube(self_tube=Tube(name='only-this-self-sample-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(name='only-this-tube', self_tube=Tube(name='only-this-tube-self-tube')))
    )
    session.add(sample_7)
    sample_8 = Sample(
        tube=Tube(name='only-this-self-sample-tube-self-tube', self_tube=Tube(name='only-this-tube-self-tube')),
        self_sample=Sample(
            name='only-this-self-sample',
            tube=Tube(self_tube=Tube(name='only-this-tube')))
    )
    session.add(sample_8)
    session.flush()

    json_response = qf.parse_query(q)

    # TODO: Change test after implementing returning only
    # specified fields
    assert json_response == \
        [{'date': None,
          'id': 1,
          'name': 'I should be the only one being returned',
          'self_sample': {'date': None,
                          'id': 9,
                          'name': 'only-this-self-sample',
                          'self_sample_id': 1,
                          'tube': {'date': None,
                                   'id': 2,
                                   'name': None,
                                   'sample_id': None,
                                   'self_tube': {'date': None,
                                                 'id': 18,
                                                 'name': 'only-this-self-sample-tube-self-tube',
                                                 'sample_id': None,
                                                 'self_tube_id': 2,
                                                 'type': None},
                                   'self_tube_id': None,
                                   'type': None},
                          'tube_id': 2},
          'self_sample_id': None,
          'tube': {'date': None,
                   'id': 1,
                   'name': 'only-this-tube',
                   'sample_id': None,
                   'self_tube': {'date': None,
                                 'id': 17,
                                 'name': 'only-this-tube-self-tube',
                                 'sample_id': None,
                                 'self_tube_id': 1,
                                 'type': None},
                   'self_tube_id': None,
                   'type': None},
          'tube_id': 1}]
