
from os import error
from re import DEBUG
from flask import Flask
from flask_restful import Api

from setting import *
from models import db
from authorization.auth import BlockAccount, ChangeAccountType, Login, RegisterAgent, RegisterClient
from features.transactions.app import *
from features.loan.app import *

from decorators import *
from helpers import *


app = Flask(__name__)
app.config['SECRET_KEY'] = SECERET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = SQLALCHEMY_TRACK_MODIFICATIONS


db.init_app(app)
api = Api(app)



# Endpoints

# # authorization and authentication features
# api.add_resource(Login, "/api/login")
# api.add_resource(RegisterAgent, "/api/admin/register_agent")
# api.add_resource(RegisterClient, "/api/agent/register_client")
# api.add_resource(AccountSchema, "/api/account/<account_number>")
# api.add_resource(BlockAccount, "/api/admin/block/<account_number>")
# api.add_resource(ChangeAccountType, "/api/admin/change_type/<account_number>")


# # basic bank transaction features
# api.add_resource(SaveAccount, "/api/client/save_account/<account_number>") #put and delete request
# api.add_resource(ClientTransfer, "/api/client/transfer")
# api.add_resource(ClientWithdraw, "/api/client/withdraw")
# api.add_resource(AgentWithdraw, "/api/agent/get_cash")  ######## untested ##############
# api.add_resource(AcceptDeposit, "/api/agent/deposit") ######## untested ##############
# api.add_resource(RequestPayment, "/api/agent/request_payment")
# api.add_resource(AdminDeposit, "/api/admin/deposit/") ######## untested ##############

# api.add_resource(TransactionHistory, "/api/account/transactions")
# api.add_resource(TransactionDelete, "/api/account/transaction/<transaction_id>") #delete request

# api.add_resource(AdminReport, '/api/admin/reports')
# api.add_resource(TransactionHistoryAdmin, "/api/admin/transactions/<account_number>")


# # Loan features
# api.add_resource(LoanSchema, "/api/loan")


if __name__ == "__main__":
    app.run(debug=DEBUG)




# saving aint working
