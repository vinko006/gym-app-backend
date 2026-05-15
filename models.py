from email.policy import default
from xmlrpc.client import DateTime

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Clan(db.Model):
    __tablename__ = 'clanovi'
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50))
    trener_id = db.Column(db.Integer, db.ForeignKey('treneri.id'), nullable=True)
    paket_id = db.Column(db.Integer, db.ForeignKey('paketi.id'), nullable=True)

    trener = db.relationship('Trener', backref='clanovi')
    paket = db.relationship('Paket', backref='clanovi')

class Trener(db.Model):
    __tablename__ = 'treneri'
    id = db.Column(db.Integer, primary_key=True)
    ime = db.Column(db.String(50), nullable=False)
    prezime = db.Column(db.String(50), nullable=False)
    specijalnost = db.Column(db.String(50))


class Paket(db.Model):
    __tablename__ = 'paketi'
    id = db.Column(db.Integer, primary_key=True)
    naziv = db.Column(db.String(50), nullable=False)
    cijena = db.Column(db.Integer)
    trajanje_dana = db.Column(db.Integer)


class Uplata(db.Model):
    __tablename__ = 'uplate'
    id = db.Column(db.Integer, primary_key=True)
    clan_id = db.Column(db.Integer, db.ForeignKey('clanovi.id'), nullable=False)
    paket_id = db.Column(db.Integer, db.ForeignKey('paketi.id'), nullable=False)
    datum_uplate = db.Column(db.Date, default=datetime.utcnow)

    paket = db.relationship('Paket', backref='sve_uplate')

class Dolazak(db.Model):
    __tablename__ = 'dolasci'
    id = db.Column(db.Integer, primary_key=True)
    datum_vrijeme = db.Column(db.DateTime, default=datetime.utcnow)
    napomena = db.Column(db.String(200))
    clan_id = db.Column(db.Integer, db.ForeignKey('clanovi.id'), nullable=False)

    clan = db.relationship('Clan', backref=db.backref('dolasci', lazy=True))