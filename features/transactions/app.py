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
