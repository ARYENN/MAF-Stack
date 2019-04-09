from flask import Flask, render_template, request, make_response, url_for, redirect, session, flash
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from authomatic.adapters import WerkzeugAdapter
from flask_session import Session
from authomatic import Authomatic
import requests
import os
import sys
import json
import socket

API_IP = os.getenv('API_IP', 'api.arjen.io')
API_USER = os.getenv('API_USER', 'admin')
API_PASSWORD = os.getenv('API_PASSWORD', 'admin')
API_HTTP_SCHEME = os.getenv('API_HTTP_SCHEME', 'http')
WEBSITE_PORT = os.getenv('WEBSITE_PORT', '80')

from config import CONFIG

authomatic = Authomatic(CONFIG, 'test', report_errors=False)

app = Flask(__name__, template_folder='.')

app.config.from_object(__name__)

sess = Session()

class RegistrationForm(Form):
    straatnaam = StringField('Straatnaam', [validators.DataRequired()])
    huisnummer = StringField('Huisnummer', [validators.DataRequired()])
    postcode = StringField('Postcode', [validators.DataRequired()])
    woonplaats = StringField('Woonplaats', [validators.DataRequired()])
    land = StringField('Land', [validators.DataRequired()])
    accept_tos = BooleanField('Ik accepteer de voorwaarden.', [validators.DataRequired()])


@app.route('/')
def index():
    if session.get('name') is not None:
        if 'error' in requests.get('{}://{}/customers/username/{}'.format(API_HTTP_SCHEME, API_IP, session.get('email')), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD))).text:
            return redirect(url_for('register'))
        else:
            return redirect(url_for('dashboard'))

    public_ip = requests.get('https://ipinfo.io/ip').text
    lookup = requests.get('http://ip-api.com/json/{}'.format(str(public_ip).strip())).json()
    hostname = socket.gethostname()

    return render_template('index.html', ip=public_ip, lookup=lookup, hostname=hostname)

@app.route('/login/google/', methods=['GET', 'POST'])
def login():
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name='google')
    if result:
        
        if result.user:
            result.user.update()

        session['name'] = result.user.name
        session['email'] = result.user.email

        if 'error' in requests.get('{}://{}/customers/username/{}'.format(API_HTTP_SCHEME, API_IP, session.get('email')), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD))).text:
            return redirect(url_for('register'))
        
        return redirect(url_for('dashboard'))

    return response

@app.route('/logout')
def logout():
    session.clear()
    result = None
    naw_gegevens_json = None
    workouts_json = None

    public_ip = requests.get('https://ipinfo.io/ip').text
    lookup = requests.get('http://ip-api.com/json/{}'.format(str(public_ip).strip())).json()
    hostname = socket.gethostname()

    return render_template("index.html", ip=public_ip, lookup=lookup, hostname=hostname)



@app.route('/dashboard')
def dashboard():

    # Als er nog een sessie is
    if session.get('name') is not None:

        # Als er nog geen account is
        if 'error' in requests.get('{}://{}/customers/username/{}'.format(API_HTTP_SCHEME, API_IP, session.get('email')), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD))).text:
            return redirect(url_for('register'))

        # Als er wel een account is
        naw_gegevens = requests.get('{}://{}/customers/username/{}'.format(API_HTTP_SCHEME, API_IP, session.get('email')), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD))).json()
        workouts = requests.get('{}://{}/workouts/username/{}'.format(API_HTTP_SCHEME, API_IP, session.get('email')), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD))).json()

        naw_gegevens_cleaned = naw_gegevens['result'].replace("'",'"')
        naw_gegevens_json = json.loads(naw_gegevens_cleaned)

        workouts_json = None

        if workouts['result'] != 'Customer found, but has no workouts.':
            workouts_cleaned = workouts['result'].replace("'",'"')
            workouts_json = json.loads(workouts_cleaned)

            for workout in workouts_json:
                wrong_time = str(workout['timestamp'])
                wrong_time = wrong_time.split(' ')[0]
                pieces = wrong_time.split('-')
                correct_time = '{}-{}-{}'.format(pieces[2], pieces[1], pieces[0])
                workout['timestamp'] = correct_time

        return render_template("dashboard.html", result=session, naw_gegevens=naw_gegevens_json, workouts=workouts_json)

    # Als de sessie verlopen is
    else:
        return redirect(url_for('login'))

    

@app.route('/register', methods=['GET', 'POST'])
def register():

    # Als er nog een sessie is
    if session.get('name') is not None:
        form = RegistrationForm(request.form)

        # Als er gesubmit wordt
        if request.method == 'POST' and form.validate():

            # Als er nog een sessie is
            if session.get('name') is not None:
            
                USERNAME = session.get('email')
                FIRST_NAME = str(session.get('name')).split(' ')[0]
                LAST_NAME = str(session.get('name')).split(' ')[1]
                STREET = '{} {}'.format(form.straatnaam.data, form.huisnummer.data)
                ZIP = form.postcode.data
                CITY = form.woonplaats.data
                COUNTRY = form.land.data

                r = requests.post('{}://{}/customers/new'.format(API_HTTP_SCHEME, API_IP), auth=('{}'.format(API_USER), '{}'.format(API_PASSWORD)), data={'username': USERNAME, 'first_name': FIRST_NAME, 'last_name': LAST_NAME, 'street': STREET, 'zip': ZIP, 'city': CITY, 'country': COUNTRY })
            if session.get('name') is None:
                return redirect(url_for('login'))

            if 'error' in r.text:
                return render_template('register.html', form=form, result=session)
            else:
                return redirect(url_for('dashboard'))
        return render_template('register.html', form=form, result=session)

    else:
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    sess.init_app(app)
    
    app.run(debug=True, host='0.0.0.0', port=WEBSITE_PORT)