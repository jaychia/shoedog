import json
from flask import request, Response
from shoedog.query_factory import QueryFactory


def shoedoggify(app, db):
    qf = QueryFactory(db)

    @app.route('/shoedog', methods=['POST'])
    def shoedog():
        data = request.data.decode('utf-8')
        res = qf.parse_query(data)
        return Response(json.dumps(res), mimetype='application/json'), 200
