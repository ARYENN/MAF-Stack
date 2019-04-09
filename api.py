from pymongo import MongoClient
from flask import Flask, request
from flask_restful import Resource, Api, reqparse
from flask_httpauth import HTTPBasicAuth
import sys
import datetime
import os
import json
import socket

# Set Environment Vars
API_PORT = os.getenv('API_PORT', '8080')
API_IP = os.getenv('API_IP', '0.0.0.0')
API_USERNAME = os.getenv('API_USERNAME', 'admin')
API_PASSWORD = os.getenv('API_PASSWORD', 'admin')

hostname = socket.gethostname()

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    if username == str(API_USERNAME) and password == str(API_PASSWORD):
        return True
    else:
        return False


class ClearCustomers(Resource):
    @auth.login_required
    def get(self):
        db.customers.drop()
        return {'status': 'ok', 'server_hostname': hostname}


class ClearWorkouts(Resource):
    @auth.login_required
    def get(self):
        db.workouts.drop()
        return {'status': 'ok', 'server_hostname': hostname}


class Customer(Resource):
    @auth.login_required
    def get(self, username):
        result = db.customers.find_one({'username': username}, {'_id': False})
        if str(result) != 'None':


            return {'status': 'ok',
                    'result': str(result), 'server_hostname': hostname}
        else:
            return {'status': 'error',
                    'result': 'Customer not found.', 'server_hostname': hostname}

    @auth.login_required
    def delete(self, username):
        result = db.customers.delete_one({'username': username})
        if str(result) != 'None':
            return {'status': 'ok', 'server_hostname': hostname}
        else:
            return {'status': 'error',
                    'result': 'Customer not found.', 'server_hostname': hostname}

class AllCustomers(Resource):
    @auth.login_required
    def get(self):
        result = [i for i in db.customers.find()]
        if str(result) != 'None':
            return {'status': 'ok', 'result': str(result), 'server_hostname': hostname}
        else:
            return {'status': 'error',
                    'result': 'No customers found.', 'server_hostname': hostname}


class Workouts(Resource):
    @auth.login_required
    def get(self, username):
        customer_exists = db.customers.find_one({'username': username})
        if str(customer_exists) != 'None':

            has_workouts = db.workouts.find_one({'username': username})
            if str(has_workouts) != 'None':

                result = str([i for i in db.workouts.find({'username': username}, {'_id': False})])

                return {'status': 'ok',
                        'result': str(result), 'server_hostname': hostname}

            else:
                return {'status': 'error',
                        'result': 'Customer found, but has no workouts.', 'server_hostname': hostname}

        else:
            return {'status': 'error',
                    'result': 'Customer not found.', 'server_hostname': hostname}


class NewCustomer(Resource):
    @auth.login_required
    def post(self):
        args = parser.parse_args()

        db.customers.insert_one({'username': args['username'],
                                 'first_name': args['first_name'],
                                 'last_name': args['last_name'],
                                 'street': args['street'],
                                 'zip': args['zip'],
                                 'city': args['city'],
                                 'country': args['country']})

        return {'status': 'ok', 'server_hostname': hostname}


class NewWorkout(Resource):
    @auth.login_required
    def post(self):
        args = parser.parse_args()

        result = db.customers.find_one({'username': args['username']})
        if str(result) != 'None':

            db.workouts.insert_one({'username': args['username'],
                                     'timestamp': str(datetime.datetime.now()),
                                     'activity_name': args['activity_name'],
                                     'duration': args['duration'],
                                     'calories_burned': args['calories_burned']})

            return {'status': 'ok', 'server_hostname': hostname}
        else:


            return {'status': 'error',
                    'result': 'No workouts found for this customer.', 'server_hostname': hostname}


class UpdateCustomer(Resource):
    @auth.login_required
    def put(self, username):
        args = parser.parse_args()

        data = {'username': args['username'],
                'first_name': args['first_name'],
                'last_name': args['last_name'],
                'street': args['street'],
                'zip': args['zip'],
                'city': args['city'],
                'country': args['country']}

        db.customers.find_one_and_update({'username': username}, {'$set': data})

        return {'status': 'ok', 'server_hostname': hostname}


if __name__ == '__main__':

    client = MongoClient('mongodb://rep1:27017,rep2:27017,rep3:27017/?replicaSet=rs0')

    db = client.cloudproject

    app = Flask(__name__)
    api = Api(app)

    parser = reqparse.RequestParser()

    # Arguments for customer collection
    parser.add_argument('username')
    parser.add_argument('first_name')
    parser.add_argument('last_name')
    parser.add_argument('street')
    parser.add_argument('zip')
    parser.add_argument('city')
    parser.add_argument('country')

    # Arguments for workout
    parser.add_argument('activity_name')
    parser.add_argument('duration')
    parser.add_argument('calories_burned')

    # Add namespaces
    api.add_resource(ClearCustomers, '/customers/clear')
    api.add_resource(ClearWorkouts, '/workouts/clear')
    api.add_resource(Customer, '/customers/username/<username>')
    api.add_resource(AllCustomers, '/customers/all')
    api.add_resource(Workouts, '/workouts/username/<username>')
    api.add_resource(NewCustomer, '/customers/new')
    api.add_resource(NewWorkout, '/workouts/new')
    api.add_resource(UpdateCustomer, '/customers/update/<username>')

    app.run(host=API_IP, port=API_PORT)
