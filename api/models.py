from api import db
from datetime import datetime

class Customer(db.Model):
    """ORM class for holding customer records"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    def __repr__(self):
        return f"Customer: id={self.id}, name={self.name}"

class Account(db.Model):
    """ORM class for holding account details"""
    id = db.Column(db.Integer, primary_key=True)
    balance = db.Column(db.Integer, nullable=False)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    owner_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    owner = db.relationship('Customer',backref=db.backref('accounts', lazy=True))
    def __repr__(self):
        return f"Account: id={self.id}, owner_id={self.owner_id}, balance={self.balance}"

class Transfer(db.Model):
    """ORM class for holding transactions records"""
    id = db.Column(db.Integer, primary_key=True)
    create_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    reference = db.Column(db.String, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    from_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    to_id = db.Column(db.Integer, db.ForeignKey('account.id'), nullable=False)
    from_acc = db.relationship('Account', foreign_keys=[from_id], backref=db.backref('transfers_out'))
    to_acc = db.relationship('Account', foreign_keys=[to_id], backref=db.backref('transfers_in'))
    def __repr__(self):
        return f"Transfer: date={self.create_date},  ref={self.reference}, from={self.from_id}, to={self.to_id}, amount={self.amount}"

