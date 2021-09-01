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