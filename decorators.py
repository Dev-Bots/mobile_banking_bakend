from flask import make_response, request
from models import *
from functools import wraps
import jwt
from setting import SECERET_KEY

# decorators
##################################################################################################################
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return make_response({"message": "Token is required!"}, 401)

        try:
            data = jwt.decode(token, SECERET_KEY, algorithms=["HS256"])
            current_user = Account.query.filter(Account.account_number == data['account_number']).first()
            if current_user.is_blocked == True:
                return make_response({"message": "Account is blocked!"}, 400)
        except:
           
            return make_response({"message": "Token is invalid!"}, 401)

        return f(current_user, *args, **kwargs)

    return decorated  


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return make_response({"message": "Token is invalid!"}, 401)

        try:
            data = jwt.decode(token, SECERET_KEY, algorithms=["HS256"])
            current_user = Admin.query.filter(Admin.account_number == data['account_number'], Admin.account_role== 0).first()
            if current_user.is_blocked == True:
                return make_response({"message": "Account is blocked!"}, 400)
        except:
            
            return make_response({"message": "Token is invalid!"}, 401)


        return f(current_user, *args, **kwargs)

    return decorated 


def agent_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'token' in request.headers:
            token = request.headers['token']

        if not token:
            return make_response({"message": "Token is invalid!"}, 401)

        try:
            data = jwt.decode(token, SECERET_KEY, algorithms=["HS256"])
            current_user = Agent.query.filter(Agent.account_number == data['account_number'], Agent.account_role == 1).first()            
            if current_user.is_blocked == True:
                return make_response({"message": "Account is blocked!"}, 400)
        except:
            
            return make_response({"message": "Token is invalid!"}, 401)

        return f(current_user, *args, **kwargs)

    return decorated 

############################################################################################################################