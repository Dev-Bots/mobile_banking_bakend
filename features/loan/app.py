from flask import make_response, jsonify, sessions
from flask_restful import Resource
from decorators import *
from request_args import *
import datetime
from constants import *
class LoanSchema(Resource):

    method_decorators = [token_required]
    def post(self, current_user):
        
        if current_user.get_role() == 'client':
            
            active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).all()

            if not active_loan:
                args = loan_args.parse_args()
                current_user = Client.query.get(current_user.id)
                if current_user.get_account_type() == 'gold':
                    days = GOLD_DAYS
                    amount_limit = GOLD_LOAN_AMOUNT
                    interest_rate = GOLD_RATE
                elif current_user.get_account_type() == 'silver':
                    days = SILVER_DAYS
                    amount_limit = SILVER_LOAN_AMOUNT
                    interest_rate = SILVER_RATE
                else:
                    days = BRONZE_DAYS
                    amount_limit = BRONZE_LOAN_AMOUNT
                    interest_rate = BRONZE_RATE

                print(amount_limit, args['amount'])
                if args['amount'] <= amount_limit:

                    new_loan = Loan(current_user.account_number, args["amount"], datetime.datetime.utcnow() + datetime.timedelta(days=days), interest_rate)
                    central_account = Admin.query.filter(Admin.account_number == CENTRAL_ACCOUNT_NUMBER).first()