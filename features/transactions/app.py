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
    
    
    
    # send money  to agents and recieve cash
class ClientWithdraw(Resource):
    
    method_decorators = [token_required]

    def post(self, current_user):
        args = transaction_agrs.parse_args()
        agent = Agent.query.filter(Agent.account_number == args["reciever_account_number"]).first()
        current_user = Client.query.get(current_user.id)
        if agent:

            amount = args["amount"]

            # clients can not deposit to thier own accounts
            if current_user.balance >= amount and current_user is not agent:
                # transfer amount from client to agent
                current_user.balance -= amount
                agent.budget += amount

                #account the accepted withdraw ammount for the agent
                agent.withdraw_accepted += amount

                transaction = Transaction(current_user.account_number, f"Withdraw: Amount {amount} birr has been withdrawn from account.", 2, agent.account_number)
                agent_transaction = Transaction(agent.account_number, f"Withdraw_accepted: Amount {amount}birr.", 1, current_user.account_number)

                db.session.add(current_user)
                db.session.add(agent)
                db.session.add(transaction)
                db.session.add(agent_transaction)
                db.session.commit()

                return make_response({"message": "Withdraw successful!"}, 201)
            
            return make_response({"message": "Failed: Balance is not sufficient."}, 401)
        
        return make_response({"message": "Account does not exist"}, 404)
    
    
    
    # deposit money to accounts recieving cash
class AcceptDeposit(Resource):
    
    method_decorators = [agent_required]
    
    def post(self, current_user):
        args = transaction_agrs.parse_args()
        related_account = Client.query.filter(Client.account_number == args["reciever_account_number"]).first()
        
        if related_account:

            amount = args["amount"]

            
            if current_user.budget >= amount and related_account.account_number != current_user.account_number:
                
                #transfer made from agent to client
                current_user.budget -= amount
                related_account.balance += amount

                # account the deposit amount accepted by the agent
                current_user.deposit_accepted += amount

                transaction = Transaction(current_user.account_number, f"Deposited: Amount {amount} birr transfer has been made.", 0, related_account.account_number)
                related_account_transaction = Transaction(related_account.account_number, f"Deposit made: Amount {amount} birr has been deposited to your account.", 1, current_user.account_number)
                
                db.session.add(related_account_transaction)
                db.session.add(related_account) 
                db.session.add(current_user)
                db.session.add(transaction)
                
                db.session.commit()

                return make_response({"message": "Deposit successful!"}, 201)
            
            return make_response({"message": "Failed: Insufficient budget."}, 401)
        
        return make_response({"message": "Account does not exist"}, 404)
    

class RequestPayment(Resource):
    
    method_decorators=[agent_required]

    def put(self, current_user):
        
        data = current_user.serialize()

    
        commission = data['pending_commisssion_payement']
        central_account = Admin.query.filter(Admin.account_number == CENTRAL_ACCOUNT_NUMBER).first()

        if commission > 0:
            
            # to check if the agent has deposited more or withdrawn more
            budget_effect = current_user.deposit_accepted - current_user.withdraw_accepted

            # positive or neutral effect
            if budget_effect >= 0:
                central_account.bank_budget += budget_effect
            # negative effect
            else:
                central_account.bank_budget -= abs(budget_effect) 
            
            # paying the agent his/her commission
            central_account.bank_budget -= commission
            current_user.budget += commission

            # reseting to zero
            current_user.deposit_accepted = 0
            current_user.withdraw_accepted = 0
            current_user.new_user_registered = 0

            db.session.add(current_user)
            db.session.add(central_account)

            db.session.commit()

            return make_response({"message": "Commission payment successful"}, 201)

        return make_response({"message": "No Commission to be paid."}, 401)

class AgentWithdraw(Resource):
    
    method_decorators = [agent_required]

    def post(self, current_user):
        args = transaction_agrs.parse_args()
        related_account = Admin.query.filter(Admin.account_number == args["reciever_account_number"]).first()
        
        if related_account:

            amount = args["amount"]

            
            if current_user.budget >= amount:
                current_user.budget -= amount
                related_account.bank_budget += amount
                transaction = Transaction(current_user.account_number, f"Withdraw: Amount {amount} birr has been withdrawn from account.", 2, related_account.account_number)
                related_account_transaction = Transaction(related_account.account_number, f"Deposit made: Amount {amount} birr has been deposited to your account.", 1, current_user.account_number)
                db.session.add(current_user)
                db.session.add(related_account)
                db.session.add(transaction)
                db.session.add(related_account_transaction)
                db.session.commit()

                return make_response({"message": "Withdraw successful!"}, 201)
            
            return make_response({"message": "Failed: Budget is not sufficient."}, 401)
        
        return make_response({"message": "Account does not exist"}, 404)

# deposit money to agents and add money to the central account
class AdminDeposit(Resource):
    
    method_decorators = [admin_required]
    
    def post(self, current_user):
        args = transaction_agrs.parse_args()
        related_account = Agent.query.filter(Agent.account_number == args["reciever_account_number"]).first()
        
        if related_account:

            amount = args["amount"]

            # admin can deposit to its own account
            if related_account.account_number == current_user.account_number:
                current_user.bank_budget += amount
            else:
                current_user.bank_budget -= amount
                related_account.budget += amount
                related_account_transaction = Transaction(related_account.account_number, f"Deposit made: Amount {amount} birr has been deposited to your account.", 1, current_user.account_number)
                db.session.add(related_account_transaction)
                db.session.add(related_account)
            transaction = Transaction(current_user.account_number, f"Deposited: Amount {amount} birr transfer has been made.", 0, related_account.account_number)
            
                
            db.session.add(current_user)
            db.session.add(transaction)
            
            db.session.commit()

            return make_response({"message": "Deposit successful!"}, 201)
        
        return make_response({"message": "Account does not exist"}, 404)

class TransactionHistory(Resource):
    
    method_decorators = [token_required]

    def get(self, current_user):
        transactions = Transaction.query.filter(Transaction.account_number == current_user.account_number, Transaction.deleted == False).all()
  
        if transactions:
            transaction = [transaction.serialize() for transaction in transactions]
            transaction.reverse()
            return jsonify(transaction)

        return make_response({"message": "Can't find transaction history"}, 404)