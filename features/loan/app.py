from flask import make_response, jsonify, sessions
from flask_restful import Resource
from decorators import *
from request_args import *
import datetime
from constants import *

class LoanSchema(Resource):

    method_decorators = [token_required]
    # made loan post endpoint
    def post(self, current_user):
        # loan is only allowed for clients
        if current_user.get_role() == 'client':
            # check if the client doesn't already got an unpaid loan
            active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).all()

            if not active_loan:
                args = loan_args.parse_args()

                #converting account type to client model
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
                    
                    # tranfer from central to the client
                    central_account.bank_budget -= args['amount']
                    current_user.balance += args['amount']
                    
                    db.session.add(new_loan)
                    db.session.add(central_account)
                    db.session.add(current_user)
                    db.session.commit()

                

                    return make_response({"message": f"Loan taken successfully, amount to be paied is {new_loan.remaining_amount}"}, 201)
                return make_response({"message": "Can not take this ammount."}, 401)
            return make_response({"message": "Please pay your current debt first."}, 401)
        return make_response({"message": "Loan feature is only allowed for client accounts."}, 401)

    # made the function that retrieve active loans of a user
    def get(self, current_user):
        active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).first()

        if active_loan:
            return jsonify(active_loan.serialize())
        return make_response({"message": "No active loans."}, 400)

    # an update function for loan topup
    def put(self, current_user):
        active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).first()
        #converting account type to client model
        current_user = Client.query.get(current_user.id)
        #central account
        central_account = Admin.query.filter(Admin.account_number == CENTRAL_ACCOUNT_NUMBER).first()

        if active_loan:
            args = loan_args.parse_args()
            topup = args['topup']

            if current_user.balance >= topup:
                if topup <= active_loan.remaining_amount:
                    
                    active_loan.remaining_amount -= topup
                    current_user.balance -= topup
                    central_account.bank_budget += topup

                    #check if the user has finished the debt
                    if active_loan.remaining_amount == 0:
                        active_loan.is_active = False
                        db.session.add(current_user)
                        db.session.add(central_account)
                        db.session.add(active_loan)
                        db.session.commit()

                        return make_response({'message': 'Congragulations you have finished your debt.'}, 201)
                    
                    db.session.add(current_user)
                    db.session.add(central_account)
                    db.session.add(active_loan)
                    db.session.commit()
                    return make_response({'message': f'Topup successful, you now have {active_loan.remaining_amount} debt left'}, 201)
                
                current_user.balance -= active_loan.remaining_amount
                central_account.bank_budget += active_loan.remaining_amount
                # returning amount from the extra topup provided
                returning_amount = topup - active_loan.remaining_amount
                active_loan.remaining_amount = 0
                active_loan.is_active = False

                db.session.add(current_user)
                db.session.add(central_account)
                db.session.add(active_loan)
                db.session.commit()


                return make_response({"message": f"You have paid all the remaining amount, {returning_amount} has been returned to your account."}, 201)

            return make_response({'message': 'Insufficient balance'}, 401)  

        return make_response({'message': "Loan is not active."}, 401)

    # delete function for the loan
    def delete(self, current_user):
        active_loan = Loan.query.filter(Loan.account_number == current_user.account_number, Loan.is_active == True).first()
        #converting account type to client model
        current_user = Client.query.get(current_user.id)


        if active_loan:
            if current_user.balance >= active_loan.remaining_amount:
                current_user.balance -= active_loan.remaining_amount
                central_account = Admin.query.filter(Admin.account_number == CENTRAL_ACCOUNT_NUMBER).first()
                central_account.bank_budget += active_loan.remaining_amount
                active_loan.remaining_amount = 0
                active_loan.is_active = False

                db.session.add(current_user)
                db.session.add(central_account)
                db.session.add(active_loan)
                db.session.commit()

                return make_response({'message': 'Loan paid in full'}, 202)
            return make_response({'message': 'Insufficient balance'}, 401) 
        return make_response({"message": "loan deleted"})

