import json
import os

import flask
import googleapiclient
import requests
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user

import website
from website import app, db, get_google_provider_cfg, client, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from website.forms import RegisterForm, LoginForm, UpdateForm
from website.models import User
from website import google_calendar_api
from pprint import pprint
from datetime import datetime

import google.oauth2.credentials
import google_auth_oauthlib.flow

CLIENT_SECRETS_FILE = website.uri_file
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/calendar.readonly"]
API_SERVICE_NAME = "calendar"
API_VERSION = "v3"


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():
        user_to_create = User(name="Name", surname="Surname", username=form.username.data,
                              email_address=form.email_address.data,
                              password=form.password1.data, credentials="")
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash("Account created successfully! You are now logged in as {0}".format(user_to_create.username), category='success')
        return redirect(url_for('personal_page'))

    if form.errors != {}: #If there are errors from the validations
        for err_msg in form.errors.values():
            flash('There was an error with creating a user: {0}'.format(err_msg[0]), category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(username=form.username.data).first()
        if attempted_user and attempted_user.check_password_correction(
                attempted_password=form.password.data
        ):
            login_user(attempted_user)
            flash('Success! You are logged in as: {0}'.format(attempted_user.username), category='success')
            return redirect(url_for('personal_page'))
        else:
            flash('Username and password are not match! Please try again', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout')
def logout_page():
    logout_user()
    flash("You have been logged out!", category='info')
    return redirect(url_for("home_page"))


@app.route("/g_login")
def g_login_page():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    if google_provider_cfg:
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]  # https://accounts.google.com/o/oauth2/v2/auth

        # Request for Google login, providing scopes to retrieve user's profile from Google
        # print client.client_id
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=SCOPES,       # https://developers.google.com/identity/protocols/oauth2/scopes   ["openid", "email", "profile", "https://www.googleapis.com/auth/calendar.readonly"]    , "https://www.googleapis.com/auth/calendar.events.readonly"
        )
        # print "URL 1: {}".format(request_uri)  #  https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=252222429193-m7i9qf1jmprqquf7skbjejutubodgrpa.apps.googleusercontent.com&redirect_uri=https%3A%2F%2F127.0.0.1%3A5000%2Fg_login%2Fcallback&scope=openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly
        return redirect(request_uri)
    else:
        flash("Temporary impossible to connect to Google's servers, try again later!", category='danger')
        return redirect(url_for("login_page"))


@app.route("/g_login/callback")
def g_callback_page():  #Google send us a request on this page
    # Get authorization code Google sent back to you
    code = request.args.get("code")
    # print "This is the code: {}".format(code)
    # Find out what URL to hit to get tokens that allow you to ask for things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    if google_provider_cfg:
        token_endpoint = google_provider_cfg["token_endpoint"]  # "https://oauth2.googleapis.com/token"
        # print "1: {}\n2: {}".format(request.url, request.base_url)
        # print "URL 2: {}".format(request.url)  # URL 2: https://127.0.0.1:5000/g_login/callback?code=4%2F0AX4XfWhjPjamTwsZuRNGwowgGJ6c8LoL1dN7q3pKPk56px6WcRIL0MfflWxsK8C5MGW0GA&scope=email+profile+openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fcalendar.readonly&authuser=0&prompt=consent
        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,                     # https://oauth2.googleapis.com/token
            authorization_response=request.url, # Full URI: (base + parameters)  https://127.0.0.1:5000/g_login/callback?code=4%2F0AX4XfWiCknLCuiB6U_0-U0aP2T2VFDasj297j-RS8B0Yn61deFfSWzJ0FtCQfaJX3aDShQ&scope=email+profile+openid+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.email+https%3A%2F%2Fwww.googleapis.com%2Fauth%2Fuserinfo.profile&authuser=0&prompt=consent
            redirect_url=request.base_url,      # Base URI: https://127.0.0.1:5000/g_login/callback
            code=code
        )
        token_response = requests.post(         # Nuova Richiesta
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        print token_response.json()
        # print "URL 3:  -  \n  {}\n  {}\n  {}".format(token_response.url, token_response.headers, token_response.json())

        # At this point I received an Access Token! Let's parse it!
        client.parse_request_body_response(json.dumps(token_response.json()))
        # print "Token: {}".format(json.dumps(token_response.json()))

        # We have the tokens!!
        # -> Follow URL from Google which gives us the user's profile information in scope
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]  # https://openidconnect.googleapis.com/v1/userinfo
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        # print userinfo_response.json()  # Dati
        # print userinfo_response         # Risposta 200 (o altri codici brutti)

        if userinfo_response.json().get("email_verified"):   # If the email is verified.
            # unique_id = userinfo_response.json()["sub"]
            email = userinfo_response.json()["email"]
            username = email.split('@')[0].replace(".", "_")
            name = userinfo_response.json()["given_name"]
            surname = userinfo_response.json()["family_name"]
            # picture = userinfo_response.json()["picture"]
            # users_name = userinfo_response.json()["given_name"]

            attempted_user = User.query.filter_by(email_address=email).first()
            if attempted_user:  # If user has already logged in
                login_user(attempted_user)
                flash('Success! You are logged in as: {0}'.format(attempted_user.username), category='success')

            else:
                user_to_create = User(name=name, surname=surname, username=username,
                                      email_address=email,
                                      password=os.urandom(15), credentials="")
                db.session.add(user_to_create)
                db.session.commit()
                login_user(user_to_create)
                flash("Account created successfully! You are now logged in as {0}".format(user_to_create.username), category='success')

            return redirect(url_for('personal_page'))

        else:
            flash("User email not available or not verified by Google!", category='danger')
            return redirect(url_for("login_page"))

    else:
        flash("Temporary impossible to connect to Google's servers, try again later!", category='danger')
        return redirect(url_for("login_page"))


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/personal')
def personal_page():
    if current_user.is_authenticated:
        return render_template('personal.html')
    else:
        flash("To access personal pages please authenticate yourself!", category='warning')
        return redirect(url_for('login_page'))


@app.route('/info', methods=['GET', 'POST'])
def info_page():
    if current_user.is_authenticated:
        form = UpdateForm()
        if form.validate_on_submit():
            name = form.name.data
            surname = form.surname.data
            current_user.name = name
            current_user.surname = surname

            db.session.commit()

            flash('Success! Your personal information have been updated!'.format(), category='success')
            return redirect(url_for('personal_page'))

        return render_template('user_info.html', form=form)

    else:
        flash("To access personal pages please authenticate yourself!", category='warning')
        return redirect(url_for('login_page'))


@app.route('/aaa')
def index():
    return print_index_table()


@app.route('/test')
def test_api_request():
    if not current_user.is_authenticated:
        return flask.redirect(url_for("login_page"))

    cred = current_user.credentials
    if cred == "":
        print "No Credentials! {}".format(cred)     # .format(flask.session.items())
        return flask.redirect('authorize')
    # Load credentials from the session.
    #print "Credenziali stringa: {}".format(cred)
    json_cred = json.loads(cred)
    #print "Credenziali nuove {}: ".format(json_cred)
    credentials = google.oauth2.credentials.Credentials(**json_cred)          # (**flask.session['credentials'])
    #credentials = google.oauth2.credentials.Credentials(credentials_to_dict(credentials))
    #credentials = google.oauth2.credentials.Credentials(flask.session['credentials'])

    #credentials_sess = google.oauth2.credentials.Credentials(flask.session['credentials'])
    print "Credentials db: {}".format(credentials.to_json())
    #print "Credentials ss: {}".format(credentials_sess.to_json())

    calendar = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    all_calendars = calendar.calendarList().list().execute()
    calendar_id = "primary"  # all_calendars["items"][1]["id"]

    events = calendar.events().list(calendarId=calendar_id, timeMin=datetime.utcnow().isoformat()+"Z", singleEvents=True, orderBy="startTime").execute()
    print "Events: {}".format(events)

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)
    current_user.credentials = json.dumps(credentials_to_dict(credentials))
    db.session.commit()

    return flask.jsonify(**events)  # all_calendars)


@app.route('/authorize')
def authorize():
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES)

    # The URI created here must exactly match one of the authorized redirect URIs
    # for the OAuth 2.0 client, which you configured in the API Console. If this
    # value doesn't match an authorized URI, you will get a 'redirect_uri_mismatch'
    # error.
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')

    # Store the state so the callback can verify the auth server response.
    # flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    # state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES) #, state=state
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    print "Flow: {}".format(flow.__dict__)

    flask.session['credentials'] = credentials_to_dict(credentials)
    current_user.credentials = json.dumps(credentials_to_dict(credentials))
    db.session.commit()

    print "Database: {}".format(json.loads(current_user.credentials))
    print "Session: {}".format(flask.session['credentials'])


    return flask.redirect(flask.url_for('test_api_request'))


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return('Credentials successfully revoked.' + print_index_table())
    else:
        return('An error occurred.' + print_index_table())


@app.route('/clear')
def clear_credentials():
    current_user.credentials = ""
    db.session.commit()

    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared.<br><br>' +
            print_index_table())


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}

def print_index_table():
    return ('<table>' +
            '<tr><td><a href="/test">Test an API request</a></td>' +
            '<td>Submit an API request and see a formatted JSON response. ' +
            '    Go through the authorization flow if there are no stored ' +
            '    credentials for the user.</td></tr>' +
            '<tr><td><a href="/authorize">Test the auth flow directly</a></td>' +
            '<td>Go directly to the authorization flow. If there are stored ' +
            '    credentials, you still might not be prompted to reauthorize ' +
            '    the application.</td></tr>' +
            '<tr><td><a href="/revoke">Revoke current credentials</a></td>' +
            '<td>Revoke the access token associated with the current user ' +
            '    session. After revoking credentials, if you go to the test ' +
            '    page, you should see an <code>invalid_grant</code> error.' +
            '</td></tr>' +
            '<tr><td><a href="/clear">Clear Flask session credentials</a></td>' +
            '<td>Clear the access token currently stored in the user session. ' +
            '    After clearing the token, if you <a href="/test">test the ' +
            '    API request</a> again, you should go back to the auth flow.' +
            '</td></tr></table>')







