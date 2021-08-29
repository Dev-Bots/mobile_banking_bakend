from enum import unique
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import backref
from setting import *
from constants import *
import datetime
from sqlalchemy import event
from sqlalchemy import DDL

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI

db = SQLAlchemy(app)

###########################################################################################

# Base account class
class Account(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String, nullable=False, unique=True)
    phone_number = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)
    account_number = db.Column(db.Integer, unique=True)
    first_name = db.Column(db.String(20), nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    DOB = db.Column(db.String, nullable=False)
    account_role = db.Column(db.Integer)
    address = db.Column(db.String(30), nullable=False)
    is_blocked = db.Column(db.Boolean)

    def __init__(self, email, password, phone_number, first_name, last_name, DOB, address):
        self.email = email
        self.phone_number = phone_number
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.DOB = DOB
        self.address = address
        self.is_blocked = False


    def get_role(self):
        roles = {
            "0": "admin",
            "1": "agent",
            "2": "client"
        }
        return roles[f"{self.account_role}"]

    def fullname(self):
        return self.first_name + " " + self.last_name
    
    def serialize_general_info(self):
        return {
            "id":self.id,
            "account_number": self.account_number,
            "email": self.email,
            "first_name":self.first_name,
            "last_name":self.last_name,
            "fullname":self.fullname(),
            "role":self.get_role(),
            "address":self.address,
            "DOB":self.DOB,
            "is_blocked": self.is_blocked
        }


    def __repr__(self):
        return f'<{self.get_role()}: {self.id} {self.fullname()}>'

###########################################################################################

#Admin specific Account
class Admin(Account):

    __tablename__ = 'admin'

    bank_budget = db.Column(db.Float)
    

    def __init__(self, email, password, phone_number, first_name, last_name, DOB, address):
        super().__init__(email, password, phone_number, first_name, last_name, DOB, address)
        self.account_role = 0
        self.bank_budget = 100

    def serialize(self):
        general = self.serialize_general_info()
        general['bank_budget'] = self.bank_budget
        

        return general


###########################################################