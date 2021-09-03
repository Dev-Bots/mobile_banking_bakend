from helpers import *
from flask import make_response, jsonify, sessions
from flask_restful import Resource
from decorators import *
from request_args import *
from sqlalchemy.sql import func


# account information
class AccountSchema(Resource):

    method_decorators = [token_required]

    def get(self, current_user, account_number, ):
        account = Account.query.filter(Account.account_number==account_number).first()
        if account:
            if current_user.id ==account.id or account.get_role() == "admin":
                switch = {
                    "admin": admin(account.id),
                    "agent": agent(account.id),
                    "client": client(account.id)
                }
                try:
                    return switch[account.get_role()]
                except:
                    
                    return make_response({"message": "something wrong"}, 400)

            elif current_user != account:
                return jsonify(account.serialize_general_info()) 
        return make_response({"message": "something wrong"}, 400)
#save customer(contacts) with get method and remove with delete method
class SaveAccount(Resource):

    method_decorators = [token_required]

    def put(self, current_user, account_number):

        account = Client.query.filter(Client.account_number == account_number).first()
        current_user = Client.query.get(current_user.id)
        if account and account is not current_user:
            current_user.beneficiaries.append(account)
            
            db.session.add(account)
            db.session.add(current_user)
            db.session.commit()
            
            return make_response({"message": f"Account({account.account_number}) saved."}, 201)
        return make_response({"message": "Account does not exist."}, 404)

    def delete(self, current_user, account_number):

        account = Client.query.filter(Client.account_number == account_number).first()
        current_user = Client.query.get(current_user.id)

        if account and account is not current_user:
  
            if account in list(current_user.beneficiaries):
                current_user.beneficiaries.remove(account)
                
                db.session.add(current_user)
                db.session.add(account)
                db.session.commit()
                return make_response({"message": f"Account({account.account_number}) removed."}, 202)
            return make_response({"message": "Account is not in saved list."}, 404)
        return make_response({"message": "Account does not exist."}, 404)

#transfer money to other clients
class ClientTransfer(Resource):

    method_decorators = [token_required]

    def post(self, current_user):
        args = transaction_agrs.parse_args()
        related_account = Client.query.filter(Account.account_number == args["reciever_account_number"]).first()
        current_user = Client.query.get(current_user.id)
        if related_account:

            amount = args["amount"]

            # clients can not deposit to thier own accounts
            if current_user.balance >= amount and current_user is not related_account:
                current_user.balance -= amount
                related_account.balance += amount
                transaction = Transaction(current_user.account_number, f"Transfer: Amount {amount} birr transfer has been made.", 0, related_account.account_number)
                related_account_transaction = Transaction(related_account.account_number, f"Deposit made: Amount {amount} birr has been deposited to your account.", 1, current_user.account_number)
                
                db.session.add(current_user)
                db.session.add(related_account)
                db.session.add(transaction)
                db.session.add(related_account_transaction)
                db.session.commit()

                return make_response({"message": "Transfer successful!"}, 201)
            
            return make_response({"message": "Failed: Balance is not sufficient."}, 401)
        
        return make_response({"message": "Account does not exist"}, 404)