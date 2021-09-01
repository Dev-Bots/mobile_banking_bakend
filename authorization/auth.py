from flask_restful import Resource
from flask import request, make_response, jsonify
from models import Account
import jwt
import bcrypt
from helpers import *
import datetime as dt
from setting import SECERET_KEY
from decorators import *

from request_args import *

class Login(Resource):

    def get(self):
        auth = request.authorization

        if not auth or not auth.username or not auth.password:
            return make_response('Could not verify', 401, {'WWWAuthenticate': 'Basic realm="Login required"'})

        account = Account.query.filter(Account.email == auth.username).first()

        try:
            if account:
                if bcrypt.checkpw(auth.password.encode('utf-8'), account.password):
                    switch = {
                    "admin": admin(account.id),
                    "agent": agent(account.id),
                    "client": client(account.id)
                }
                # problem with the client
                data = switch[account.get_role()]
                
                #add the token to the data
                token = jwt.encode({'account_number': account.account_number, 'exp': dt.datetime.utcnow() + dt.timedelta(hours=5)}, SECERET_KEY)
                data["token"] = token

                return jsonify(data)
            else:
                return make_response('Could not verify', 401, {'WWWAuthenticate': 'Basic realm="Login required"'})
        except e:
            print(e)

            return make_response('Could not verify', 401, {'WWWAuthenticate': 'Basic realm="Login required"'})


