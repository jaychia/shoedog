import json
from flask import request
from shoedog.query_factory import QueryFactory


def shoedoggify(app, db):
    qf = QueryFactory(db)

    @app.route('/shoedog', methods=['POST'])
    def shoedog():
        res = qf.parse_query(request.data)
        return json.dumps(res), 200
