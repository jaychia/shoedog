from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.types import Date

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class Tube(db.Model):
    __tablename__ = 'tubes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    date = db.Column(Date)
    type = db.Column(db.String)


class Sample(db.Model):
    __tablename__ = 'samples'
    id = db.Column(db.Integer, primary_key=True)
    tube_id = db.Column(db.Integer, db.ForeignKey("tubes.id"))
    tube = db.relationship('Tube', uselist=False)
    date = db.Column(Date)
    name = db.Column(db.String)
