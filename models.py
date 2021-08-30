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

#Agent specific Account
class Agent(Account):

    __tablename__ = 'agent'
    
    budget = db.Column(db.Float)
    withdraw_accepted = db.Column(db.Float)
    deposit_accepted = db.Column(db.Float)
    new_user_registered = db.Column(db.Integer)

    def __init__(self, email, password,  phone_number, first_name, last_name, DOB, address, budget=0):
        super().__init__(email, password, phone_number, first_name, last_name, DOB, address)
        self.budget = budget
        self.account_role = 1
        self.new_user_registered = 0
        self.deposit_accepted = 0
        self.withdraw_accepted = 0
   

    def serialize(self):
        general = self.serialize_general_info()
        general['budget'] = self.budget
        if self.withdraw_accepted:
            general['pending_commisssion_payement'] = (self.withdraw_accepted + self.deposit_accepted) * AGENT_TRANSACTION_COMMISSION + self.new_user_registered * COMMISSION_FOR_REGISTERING
        
        registered = Client.query.filter(Client.registered_by == self.account_number).all()
        if registered:
            general["registered_clients"] = [client.account_number for client in registered]

        return general

###############################################################################################
#Client specific Account
class Client(Account):

    __tablename__ = 'client'
    client_id = db.Column(db.String, db.ForeignKey('account.account_number'))
    balance = db.Column(db.Float)
    beneficiaries = db.relationship('Client', foreign_keys=client_id)    
    account_type = db.Column(db.Integer, nullable=True)
    registered_by = db.Column(db.String)

    def __init__(self, email, password, phone_number, first_name, last_name, DOB, address, balance, registered_by):
        super().__init__(email, password, phone_number, first_name, last_name, DOB, address)
        self.balance = balance
        self.account_role = 2
        self.client_id = self.account_number
        self.registered_by = registered_by
        
        if self.balance >= GOLD_AMOUNT:
            self.account_type = 1
        elif self.balance >= SILVER_AMOUNT:
            self.account_type = 2
        else:
            self.account_type = 3


    def get_account_type(self):
        types = {
            "3": "bronze",
            "2": "silver",
            "1": "gold"
        }

        if self.account_type:
            return types[str(self.account_type)]

        return None



    def serialize(self):
        general = self.serialize_general_info()
        general["balance"] = self.balance
        general["account_type"] = self.get_account_type()
        general["saved"] = [account.account_number for account in self.beneficiaries] # saved for ease of use
        general["registered_by"] = self.registered_by

        return general
    
###########################################################################################

#history table to keep any kind of transactions
class Transaction(db.Model):
    
    __tablename__ = 'transaction'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_number = db.Column(db.Integer, db.ForeignKey('account.account_number'))
    transaction_type = db.Column(db.Integer, nullable=False)
    related_account = db.Column(db.Integer, nullable=True)
    remark = db.Column(db.String(30), nullable=False)
    deleted = db.Column(db.Boolean)
    date = db.Column(db.DateTime)

    def __init__(self, account_number, remark, transaction_type, reciever_account_number=None):
        self.account_number = account_number
        self.related_account = reciever_account_number
        self.remark = remark
        self.deleted = False
        self.transaction_type = transaction_type
        self.date = datetime.datetime.now()

    def get_type(self):

        if self.transaction_type is None:
            return "Unspecified type"

        types = {
            "0": "transfer",
            "1": "deposit",
            "2": "withdraw"
        }

        return types[str(self.transaction_type)]

    def serialize(self):
        return {
            "id": self.id,
            "account_id": self.account_number,
            "related_account": self.related_account,
            "transaction_type": self.get_type(),
            "text": self.remark,
            "date": self.date
        }

###########################################################################################
class Loan(db.Model):
    
    __tablename__ = 'loan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    account_number = db.Column(db.Integer, db.ForeignKey('account.account_number'))
    amount_taken = db.Column(db.Float, nullable=False)
    remaining_amount = db.Column(db.Float)
    due_date = db.Column(db.DateTime, nullable=False)
    date_taken = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean)
    
    

    def __init__(self, account_number, amount_taken, due_date, interest_rate):
        self.account_number = account_number
        self.amount_taken = amount_taken
        self.remaining_amount = amount_taken + amount_taken * interest_rate
        self.due_date = due_date
        self.is_active = True
        self.date_taken = datetime.datetime.now()


    def serialize(self):
        return {
            "id":self.id,
            "account_number": self.account_number,
            "amount_taken": self.amount_taken,
            "remaining_amount": self.remaining_amount,
            "is_active": self.is_active,
            "date_taken": self.date_taken,
            "due_date":self.due_date
        }

#############################################################################################


# import bcrypt
# db.drop_all()
# db.create_all()
# password = bcrypt.hashpw(b"1234", bcrypt.gensalt())

# admin = Admin("@administrator", password, "1234", "admin", "admin_last", "yesturday", "jemo")
# # agent = Agent("agent", password, '123456', 'k', 's', 'now', 'here', 1000)
# # client = Client('new', password, '4321', 'kev', 'shi', 'now', 'here', 5000, '1000000002')
# admin.account_number = CENTRAL_ACCOUNT_NUMBER
# db.session.add(admin)
# db.session.commit()