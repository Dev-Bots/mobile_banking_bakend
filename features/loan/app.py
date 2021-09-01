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
                    central_account.bank_budget -= args['amount']
                    current_user.balance += args['amount']
                    
                    db.session.add(new_loan)
                    db.session.add(central_account)
                    db.session.add(current_user)
                    db.session.commit()

                

                    return make_response({"message": f"Loan taken successfully, amount to be paied is {new_loan.remaining_amount}"})
                return make_response({"message": "Can not take this ammount."}, 401)
            return make_response({"message": "Please pay your current debt first."}, 401)
        return make_response({"message": "Loan feature is only allowed for client accounts."}, 401)

    def get(self, current_user):
        active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).first()

        if active_loan:
            return jsonify(active_loan.serialize())
        return make_response({"message": "No active loans."}, 400)