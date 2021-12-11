
# -*- coding: utf-8 -*-

import os
import flask
import requests

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import website

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = website.uri_file

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]  # ['https://www.googleapis.com/auth/drive.metadata.readonly']
API_SERVICE_NAME = "calendar"  # 'drive'
API_VERSION = "v3"  # 'v2'

app = flask.Flask(__name__)
# Note: A secret key is included in the sample so that it works.
# If you use this code in your application, replace this with a truly secret
# key. See https://flask.palletsprojects.com/quickstart/#sessions.
app.secret_key = '547467465463'


@app.route('/')
def index():
    return print_index_table()


@app.route('/test')
def test_api_request():
    if 'credentials' not in flask.session:
        return flask.redirect('authorize')

    # Load credentials from the session.
    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    drive = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    files = drive.files().list().execute()

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)

    return flask.jsonify(**files)


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
    flask.session['state'] = state

    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verified in the authorization server response.
    state = flask.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store credentials in the session.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    credentials = flow.credentials
    flask.session['credentials'] = credentials_to_dict(credentials)

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


if __name__ == '__main__':
    # When running locally, disable OAuthlib's HTTPs verification.
    # ACTION ITEM for developers:
    #     When running in production *do not* leave this option enabled.
    # os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

    # Specify a hostname and port that are set as a valid redirect URI
    # for your API project in the Google API Console.
    #app.run('localhost', 8080, debug=True)
    app.run(ssl_context='adhoc', debug=True)



# Resti di codice
"""

@app.route('/g_calendar')
def g_calendar_page():
    uri_file = website.uri_file
    scopes = ["https://www.googleapis.com/auth/calendar.readonly"]
    
    client_file = uri_file
    api_name = "calendar"
    api_version = "v3"
    service = Create_Service(client_file, api_name, api_version, scopes)
    response = service.CalendarList().list().execute()
    pprint(response)
    
    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(uri_file, scopes=scopes)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = request.base_url + "/callback"

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    return redirect(authorization_url)

    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    if google_provider_cfg:
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]

        # Use library to construct the request for Google login and provide
        # scopes that let you retrieve user's profile from Google
        print client.client_id
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["https://www.googleapis.com/auth/calendar.readonly"],
            # https://developers.google.com/identity/protocols/oauth2/scopes
        )
        return redirect(request_uri)
    else:
        flash("Temporary impossible to connect to Google's servers, try again later!", category='danger')
        return redirect(url_for("personal_page"))


@app.route("/g_calendar/callback")
def g_cal_back_page():
    ""state = flask.session['state']""
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        website.uri_file,
        scopes=["https://www.googleapis.com/auth/calendar.readonly"])
    ""state=state""
    flow.redirect_uri = flask.url_for(request.base_url, _external=True)

    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    # ACTION ITEM for developers:
    #     Store user's access and refresh tokens in your data store if
    #     incorporating this code into your real app.
    credentials = flow.credentials
    flask.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}

    calendar = googleapiclient.discovery.build('calendar', 'v3', credentials=credentials)
    response = calendar.CalendarList().list().execute()
    print response

    # Get authorization code Google sent back to you
    code = request.args.get("code")
    print request.args   # ImmutableMultiDict([('scope', u'https://www.googleapis.com/auth/calendar.readonly'), ('code', u'4/0AX4XfWiB8eBIo-JrcPy9yvzqsxBnD2TjTgdtOOjTVdFvaZLmaZtlrSTIMAROt0dg91aJTg')])
    # print "This is the code: {}".format(code)
    # Find out what URL to hit to get tokens that allow you to ask for things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    print google_provider_cfg
    if google_provider_cfg:
        token_endpoint = google_provider_cfg["token_endpoint"]      #  u'token_endpoint': u'https://oauth2.googleapis.com/token'
        #print "1: {}\n2: {}".format(request.url, request.base_url)
        # Prepare and send a request to get tokens! Yay tokens!
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,                     # https://oauth2.googleapis.com/token
            authorization_response=request.url, # Full URI: (base + parameters)
            redirect_url=request.base_url,      # Base URI: https://127.0.0.1:5000/g_calendar/callback
            code=code
        )
        token_response = requests.post(         # Nuova Richiesta
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )

        # Parse the tokens!
        client.parse_request_body_response(json.dumps(token_response.json()))
        # print "Token: {}".format(json.dumps(token_response.json()))     # Token: {"access_token": "ya29.a0ARrdaM8MhiecStfw71nEI_zOmjVz81-igebi1lghhVjKhBiqwapgrNtp-QedxSKIZbWrUXQbNyoOvaEbkSoL4TpjLu4BaVj_P8sOAxyMAQaueXkZXxH1KDVSERG9Gmu08m7jLb12rA14w1-vF8H30dOHSFte", "scope": "https://www.googleapis.com/auth/calendar.readonly", "expires_in": 3599, "token_type": "Bearer"}


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
                                      password=os.urandom(15))
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
        
@app.before_request
def before_request():
    if request.is_secure:
        return

    url = request.url.replace("http://", "https://", 1)
    code = 301
    return redirect(url, code=code)
"""

"""
@app.route('/website', methods=['GET', 'POST'])
@login_required
def market_page():
    purchase_form = PurchaseItemForm()
    selling_form = SellItemForm()
    if request.method == "POST":
        #Purchase Item Logic
        purchased_item = request.form.get('purchased_item')
        p_item_object = Item.query.filter_by(name=purchased_item).first()
        if p_item_object:
            if current_user.can_purchase(p_item_object):
                p_item_object.buy(current_user)
                flash("Congratulations! You purchased {p_item_object.name} for {p_item_object.price}$", category='success')
            else:
                flash("Unfortunately, you don't have enough money to purchase {p_item_object.name}!", category='danger')
        #Sell Item Logic
        sold_item = request.form.get('sold_item')
        s_item_object = Item.query.filter_by(name=sold_item).first()
        if s_item_object:
            if current_user.can_sell(s_item_object):
                s_item_object.sell(current_user)
                flash("Congratulations! You sold {s_item_object.name} back to website!", category='success')
            else:
                flash("Something went wrong with selling {s_item_object.name}", category='danger')


        return redirect(url_for('market_page'))

    if request.method == "GET":
        items = Item.query.filter_by(owner=None)
        owned_items = Item.query.filter_by(owner=current_user.id)
        return render_template('website.html', items=items, purchase_form=purchase_form, owned_items=owned_items, selling_form=selling_form)

"""
