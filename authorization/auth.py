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


# /api/admin/register_agent
class RegisterAgent(Resource):

    method_decorators = [admin_required]

    def post(self, current_user):
        args = account_args.parse_args()

        #encrypting password
        password_form_request = args["password"].encode("utf-8")
        password = bcrypt.hashpw(password_form_request, bcrypt.gensalt())

        try:
            agent = Agent(args["email"], password, args["phone_number"], args["first_name"], args["last_name"], args["DOB"], args["address"], args['budget'])
            current_user.bank_budget -= args['budget']
            
            db.session.add(current_user)
            db.session.add(agent)
            db.session.commit()

            #making the account number start from a base number
            agent.account_number = 1000000000 + agent.id
    
            db.session.add(agent)
            db.session.commit()


            return make_response({"Success": f"Agent({agent.account_number}) Created Successfully"}, 201)
        except:
            
            return make_response({"Error": "Failed to open an account."}, 401)
        

# /api/agent/register_client
class RegisterClient(Resource):

    method_decorators = [agent_required]

    def post(self, current_user):
        args = account_args.parse_args()

        #encrypting password
        password_form_request = args["password"].encode("utf-8")
        password = bcrypt.hashpw(password_form_request, bcrypt.gensalt())

        try:
            if current_user.budget < args['balance']:
                return make_response({'message': 'Insufficient balance to create the account.'}, 401)
            client = Client(args["email"], password, args["phone_number"], args["first_name"], args["last_name"], args['DOB'], args["address"], args["balance"], current_user.account_number)
            current_user.new_user_registered += 1
            current_user.budget -= args['balance']
            
            db.session.add(client)
            db.session.add(current_user)
            db.session.commit()

            #making the account number start from a base number
            client.account_number = 1000000000 + client.id
            db.session.add(client)
            db.session.commit()
            
            return make_response({"Success": f"Client({client.account_number}) Created Successfully"}, 201) 

        except e:
            print(e)
            return make_response({"Error": "Failed to open an account."}, 401)

    # view registered users
    def get(self, current_user):

        users = Client.query.filter(Client.agent_account_number == current_user.account_number).all()
        return jsonify([user.account_number for user in users])

class BlockAccount(Resource):

    method_decorators = [admin_required]

    def put(self, current_user, account_number):

        if account_number != current_user.account_number:
            account = Account.query.filter(Account.account_number==account_number).first()
            try:
                account.is_blocked = not account.is_blocked
                message = "blocked" if account.is_blocked else "unblocked"

                db.session.add(account)
                db.session.commit()

                return make_response({"message": f"{account.account_number} is {message}"})
            except:
                return make_response({"message": "Account does not exist."}, 404)
