
from flask_restful import reqparse
from datetime import datetime


#register
account_args = reqparse.RequestParser()

account_args.add_argument("first_name", type=str)
account_args.add_argument("last_name", type=str)
account_args.add_argument("password", type=str)
account_args.add_argument("phone_number", type=str)
account_args.add_argument("email", type=str)
account_args.add_argument("address", type=str)
account_args.add_argument("DOB", type=str)
account_args.add_argument("balance", type=float)
account_args.add_argument("budget", type=float)
account_args.add_argument("account_type", type=int) #validator - must be 1,2 or 3 only



transaction_agrs  = reqparse.RequestParser()

transaction_agrs.add_argument('amount', type=float)
transaction_agrs.add_argument('reciever_account_number', type=str)
transaction_agrs.add_argument('tranction_id', type=int)




loan_args = reqparse.RequestParser()

loan_args.add_argument('amount', type=float)
loan_args.add_argument('topup', type=float)