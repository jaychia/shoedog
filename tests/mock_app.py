from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import Date
from shoedog.api import shoedoggify


def create_app(name, extra_config):
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
    for k in extra_config:
        app.config[k] = extra_config[k]
    return app

app = create_app(__name__, {})
app.app_context().push()
db = SQLAlchemy()
db.init_app(app)


class Tube(db.Model):
    __tablename__ = 'tubes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date = db.Column(Date)
    type = db.Column(db.String)
    sample_id = db.Column(db.Integer, db.ForeignKey('samples.id'))
    self_tube_id = db.Column(db.Integer, db.ForeignKey('tubes.id'))
    self_tube = db.relationship('Tube', uselist=False)


class Sample(db.Model):
    __tablename__ = 'samples'
    id = db.Column(db.Integer, primary_key=True)
    tube_id = db.Column(db.Integer, db.ForeignKey('tubes.id'))
    self_sample_id = db.Column(db.Integer, db.ForeignKey('samples.id'))
    tube = db.relationship('Tube', uselist=False, foreign_keys=[tube_id])
    tubes = db.relationship('Tube', uselist=True, foreign_keys=[Tube.sample_id])
    date = db.Column(Date)
    name = db.Column(db.String)
    self_sample = db.relationship('Sample', uselist=False)


db.create_all()

shoedoggify(app, db)
