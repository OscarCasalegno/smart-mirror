import json
import os

import flask
import googleapiclient
from googleapiclient import sample_tools
import requests
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user

import website
from website import app, db, mail, get_google_provider_cfg, client, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
from website.forms import RegisterForm, LoginForm, UpdateForm, RegisterMirrorForm, LinkMirrorForm, EditMirrorForm, \
    LayoutForm
from website.models import User, Mirror, Relation
from website import api_manager, mail_manager
from pprint import pprint
from datetime import datetime

import google.oauth2.credentials
import google_auth_oauthlib.flow

CLIENT_SECRETS_FILE = website.uri_file
SCOPES = ["openid", "https://www.googleapis.com/auth/userinfo.profile",
          "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/calendar.readonly"]


@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')


@app.route('/register', methods=['GET', 'POST'])
def register_page():
    form = RegisterForm()
    if form.validate_on_submit():

        email = form.email_address.data
        if not User.query.filter_by(email_address=email).first() is None:
            flash("The email '{0}' is already registered in our systems, please login!".format(email),
                  category='warning')
            return redirect(url_for('login_page'))

        if not User.query.filter_by(g_email_address=email).first() is None:
            flash(
                "The Google email '{0}' is already registered in our systems, please login with Google!".format(email),
                category='warning')
            return redirect(url_for('login_page'))

        user_to_create = User(name="", surname="", username=form.username.data, email_address=email,
                              password=form.password1.data, credentials="")
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        mail_manager.send_registration_mail(email, "Welcome in Cleveror", user_to_create.username)
        flash("Account created successfully! You are now logged in as {0}".format(user_to_create.username),
              category='success')
        return redirect(url_for('personal_page'))

    if form.errors != {}:  # If there are errors from the validations
        for err_msg in form.errors.values():
            flash('There was an error with creating a user: {0}'.format(err_msg[0]), category='danger')

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()
    if form.validate_on_submit():
        attempted_user = User.query.filter_by(email_address=form.email_address.data).first()
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
    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('g_callback_page', _external=True)  # Complete URI

    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Enable to refresh an access token without re-prompting the user for permission
        include_granted_scopes='true')  # Enable incremental authorization.

    return flask.redirect(authorization_url)


@app.route("/g_login/callback")
def g_callback_page():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('g_callback_page', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    #  Send back the received code to get an access token
    flow.fetch_token(authorization_response=authorization_response)

    # Retrieve the credentials
    credentials = flow.credentials

    # calendar = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)
    # events = calendar.events().list(calendarId="primary", timeMin=datetime.utcnow().isoformat() + "Z", singleEvents=True, orderBy="startTime").execute()
    # print "Events: {}".format(events)

    info_service = googleapiclient.discovery.build("people", "v1", credentials=credentials)
    info = info_service.people().get(resourceName="people/me",
                                     personFields="names,emailAddresses,coverPhotos,photos").execute()
    print "info: {}".format(info)

    g_email = info["emailAddresses"][0]["value"]
    g_name = info["names"][0]["givenName"]
    g_surname = info["names"][0]["familyName"]
    g_username = g_email.split('@')[0].replace(".", "_")
    g_picture = info["photos"][0]["url"]
    g_credential = json.dumps(credentials_to_dict(credentials))

    attempted_g_user = User.query.filter_by(g_email_address=g_email).first()
    attempted_user = User.query.filter_by(email_address=g_email).first()

    if attempted_g_user:  # If user has already logged in with Google
        attempted_g_user.credentials = g_credential  # Update Credentials in DB as a string
        db.session.commit()
        login_user(attempted_g_user)  # Login User
        flash('Success! You are logged in as: {0}'.format(attempted_g_user.username), category='success')

    elif attempted_user:  # If user has already logged in, but not with Google
        if attempted_user.g_email_address:
            flash(
                'An account using this email already exists, but it is linked to a different Google account. Login without Google!',
                category='danger')
            return redirect(url_for('login_page'))

        attempted_user.g_email_address = g_email
        attempted_user.credentials = g_credential  # Update Credentials in DB as a string
        db.session.commit()
        login_user(attempted_user)  # Login User
        flash(
            'Success! You are logged in as: {0}, this account is now linked to Google!'.format(attempted_user.username),
            category='success')

    else:
        user_to_create = None
        while user_to_create is None:
            try:
                user_to_create = User(name=g_name, surname=g_surname, username=g_username,
                                      email_address=g_email, g_email_address=g_email, password=os.urandom(15),
                                      credentials=g_credential)
            except:
                print "Retrying user creation"
        db.session.add(user_to_create)
        db.session.commit()
        login_user(user_to_create)
        flash("Account created successfully! You are now logged in as {0}".format(user_to_create.username),
              category='success')

    return redirect(url_for('personal_page'))


@app.route("/g_link")
def g_link_page():
    if current_user.has_g_account():
        flash('Your account is already linked to Google', category='warning')
        return redirect(url_for('info_page'))

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)

    flow.redirect_uri = flask.url_for('g_link_callback_page', _external=True)  # Complete URI

    authorization_url, state = flow.authorization_url(
        access_type='offline',  # Enable to refresh an access token without re-prompting the user for permission
        include_granted_scopes='true')  # Enable incremental authorization.

    return flask.redirect(authorization_url)


@app.route("/g_link/callback")
def g_link_callback_page():
    if current_user.has_g_account():
        flash('Your account is already linked to Google', category='warning')
        return redirect(url_for('info_page'))

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes=SCOPES)
    flow.redirect_uri = flask.url_for('g_link_callback_page', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    #  Send back the received code to get an access token
    flow.fetch_token(authorization_response=authorization_response)

    # Retrieve the credentials
    credentials = flow.credentials

    info_service = googleapiclient.discovery.build("people", "v1", credentials=credentials)
    info = info_service.people().get(resourceName="people/me",
                                     personFields="names,emailAddresses,coverPhotos,photos").execute()
    print "info: {}".format(info)

    g_email = info["emailAddresses"][0]["value"]
    g_name = info["names"][0]["givenName"]
    g_surname = info["names"][0]["familyName"]
    g_credential = json.dumps(credentials_to_dict(credentials))

    attempted_g_user = User.query.filter_by(g_email_address=g_email).first()

    if attempted_g_user:  # If user has already logged in with Google
        attempted_g_user.credentials = g_credential  # Update Credentials in DB as a string
        db.session.commit()
        flash('This Google account is already linked to the user: {0}'.format(attempted_g_user.username),
              category='danger')
        return redirect(url_for('info_page'))

    else:
        current_user.g_email_address = g_email
        current_user.credentials = g_credential
        if not current_user.name:
            current_user.name = g_name
        if not current_user.surname:
            current_user.surname = g_surname

        db.session.commit()
        flash("Account linked successfully!", category='success')

    return redirect(url_for('info_page'))


@app.route('/about')
def about_page():
    return render_template('about.html')


@app.route('/personal')
def personal_page():
    if current_user.is_authenticated:
        # return render_template('personal.html')
        return redirect(url_for('mirrors_page'))
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


@app.route('/layout/<mirror_id>', methods=['GET', 'POST'])
def layout_page(mirror_id):  # DA GESTIRE CENTROLLO SPECCHIO
    if current_user.is_authenticated:
        # Retrieve the mirror (handling errors)
        mirror = Mirror.query.filter_by(id=mirror_id).first()
        if mirror is None:
            flash("No such mirror in our BD, try to register the mirror first!", category='warning')
            return flask.redirect(url_for("mirrors_page"))

        relation = Relation.query.filter_by(mirror=mirror, user=current_user).first()
        if relation is None:
            flash("You are not authorized to view this mirror, please register it first!", category='warning')
            return flask.redirect(url_for("mirrors_page"))

        form = LayoutForm()
        if form.validate_on_submit():
            layout_new = {"top-left": form.top_left_choice.data, "center-left": form.center_left_choice.data,
                          "bottom-left": form.bottom_left_choice.data,
                          "top-right": form.top_right_choice.data, "center-right": form.center_right_choice.data,
                          "bottom-right": form.bottom_right_choice.data,
                          "text": form.text_choice.data}

            relation.layout = json.dumps(layout_new)
            print json.dumps(layout_new)
            db.session.commit()

            flash('Success! Your Layout for {mirror} has been updated!'.format(mirror=mirror.__repr__()),
                  category='success')
            return redirect(url_for('mirrors_page'))

        # layout_base = {"top-left": "", "center-left": "", "bottom-left": "",
        #     "top-right": "", "center-right": "", "bottom-right": "",
        #     "text": "Hello!"}
        # print json.dumps(layout_base)
        layout_base = json.loads(relation.layout)

        return render_template('choice.html', form=form, layout=layout_base)

    else:
        flash("To access personal pages please authenticate yourself!", category='warning')
        return redirect(url_for('login_page'))


@app.route('/standard_layout/<mirror_id>', methods=['GET', 'POST'])
def standard_layout_page(mirror_id):
    if current_user.is_authenticated:
        # Retrieve the mirror (handling errors)
        mirror = Mirror.query.filter_by(id=mirror_id).first()
        if mirror is None:
            flash("No such mirror in our BD, try to register the mirror first!", category='warning')
            return flask.redirect(url_for("mirrors_page"))

        relation = Relation.query.filter_by(mirror=mirror, user=current_user, ownership=True).first()
        if relation is None:
            flash("You are not the owner of this mirror.", category='warning')
            return flask.redirect(url_for("mirrors_page"))

        form = LayoutForm()
        if form.validate_on_submit():
            layout_new = {"top-left": form.top_left_choice.data, "center-left": form.center_left_choice.data,
                          "bottom-left": form.bottom_left_choice.data,
                          "top-right": form.top_right_choice.data, "center-right": form.center_right_choice.data,
                          "bottom-right": form.bottom_right_choice.data,
                          "text": form.text_choice.data}

            mirror.standard_layout = json.dumps(layout_new)
            print json.dumps(layout_new)
            db.session.commit()

            flash('Success! Your Standard Layout for {mirror} has been updated!'.format(mirror=mirror.__repr__()),
                  category='success')
            return redirect(url_for('mirrors_page'))

        layout_base = json.loads(mirror.standard_layout)

        return render_template('choice_standard.html', form=form, layout=layout_base)

    else:
        flash("To access personal pages please authenticate yourself!", category='warning')
        return redirect(url_for('login_page'))


@app.route('/mirrors')
def mirrors_page():
    if not current_user.is_authenticated:
        flash("To see linked mirrors please authenticate yourself!", category='warning')
        return flask.redirect(url_for("login_page"))

    # owned_items = Item.query.filter_by(owner=current_user.id)
    related_mirrors = current_user.related

    def ordinator(relation):
        return 1 if relation.ownership else 0

    related_mirrors.sort(reverse=True, key=ordinator)

    return render_template('mirrors.html', mirrors=related_mirrors)


@app.route('/mirrors/add', methods=['GET', 'POST'])
def add_mirror_page():
    if not current_user.is_authenticated:
        flash("To link a new mirror please authenticate yourself!", category='warning')
        return flask.redirect(url_for("login_page"))

    register_form = RegisterMirrorForm()
    link_form = LinkMirrorForm()

    # REGISTER MIRROR FORM
    if register_form.register_submit.data and register_form.validate():

        raw_location = register_form.address.data + " " + register_form.number.data + ", " + register_form.city.data + ", " + register_form.region.data + ", " + register_form.country.data + ", " + register_form.postal_code.data
        # print "Raw: "+raw_location
        location = api_manager.get_address(raw_address=raw_location)
        # print "New: "+location

        # Add check if already inserted---- OWNER!!!
        check_mirror = Mirror.query.filter_by(product_code=register_form.product_code.data,
                                              secret_code=register_form.secret_code.data).first()
        if check_mirror is not None:
            flash('The mirror {} has already been inserted!'.format(register_form.product_code.data),
                  category='warning')
            return redirect(url_for('mirrors_page'))

        mirror_to_create = Mirror(product_code=register_form.product_code.data,
                                  secret_code=register_form.secret_code.data, location=location,
                                  name=register_form.name.data)
        mirror_to_create.users.append(current_user)
        db.session.add(mirror_to_create)
        db.session.commit()
        relation = Relation.query.filter_by(user=current_user, mirror=mirror_to_create).first()  # Get the relation
        if relation:  # Assign the ownership of the mirror to the current user
            relation.ownership = True
            db.session.commit()

        flash('Success! You have successfully registered the mirror {}!'.format(register_form.product_code.data),
              category='success')
        return redirect(url_for('mirrors_page'))

    if register_form.register_submit.data and register_form.errors != {}:  # If there are errors from the validations
        for err_msg in register_form.errors.values():
            flash('Error during the process: {0}'.format(err_msg[0]), category='danger')

    # LINK MIRROR FORM
    if link_form.link_submit.data and link_form.validate():

        check_mirror = Mirror.query.filter_by(product_code=link_form.product_code.data).first()
        if check_mirror is None:
            flash('No mirror found having code {}. Try to register it!'.format(link_form.product_code.data),
                  category='warning')
            return redirect(url_for('mirrors_page'))

        check_user = User.query.filter_by(email_address=link_form.owner_email_address.data).first()
        if check_user is None:
            flash('No user found having primary email {}!'.format(link_form.owner_email_address.data),
                  category='warning')
            return redirect(url_for('mirrors_page'))

        check_relation = Relation.query.filter_by(user=check_user, mirror=check_mirror).first()
        if check_relation is None:
            flash('The user {user} is not linked to the mirror {mirror}!'.format(user=check_user.email_address,
                                                                                 mirror=check_mirror.product_code),
                  category='warning')
            return redirect(url_for('mirrors_page'))
        elif not check_relation.ownership:
            flash('The user {user} is not the owner of the mirror {mirror}!'.format(user=check_user.email_address,
                                                                                    mirror=check_mirror.product_code),
                  category='warning')
            return redirect(url_for('mirrors_page'))
        else:
            check_mirror.users.append(current_user)
            db.session.commit()
            flash('Success! Your account is now linked to the mirror {}!'.format(register_form.product_code.data),
                  category='success')
            return redirect(url_for('mirrors_page'))

    if link_form.link_submit.data and link_form.errors != {}:  # If there are errors from the validations
        for err_msg in link_form.errors.values():
            flash('Error during the process: {0}'.format(err_msg[0]), category='danger')

    return render_template("add_mirror.html", register_form=register_form, link_form=link_form)


@app.route('/mirrors/edit/<mirror_id>', methods=['GET', 'POST'])
def edit_mirror_page(mirror_id):
    if not current_user.is_authenticated:
        flash("To edit a mirror please authenticate yourself!", category='warning')
        return flask.redirect(url_for("login_page"))

    # Retrieve the mirror (handling errors)
    mirror = Mirror.query.filter_by(id=mirror_id).first()
    if mirror is None:
        flash("No such mirror in our BD, try to register the mirror first!", category='warning')
        return flask.redirect(url_for("mirrors_page"))

    relation = Relation.query.filter_by(mirror=mirror, user=current_user).first()
    if relation is None:
        flash("You are not authorized to view this mirror, please register it first!", category='warning')
        return flask.redirect(url_for("mirrors_page"))

    form = EditMirrorForm()

    if form.validate_on_submit():
        if form.location.data and form.location.data != mirror.location:
            mirror.location = api_manager.get_address(raw_address=form.location.data)
        mirror.name = form.name.data
        db.session.commit()

        flash('Success! Your changes on {} have been saved!'.format(mirror.product_code), category='success')
        return redirect(url_for('mirrors_page'))

    if form.errors != {}:  # If there are errors from the validations
        for err_msg in form.errors.values():
            flash('Error during the process: {0}'.format(err_msg[0]), category='danger')

    return render_template("edit_mirror.html", form=form, relation=relation)


@app.errorhandler(404)
def error_404(error):
    return render_template("ERROR_404.html"), 404


@app.route('/test')
def test_api_request():
    if not current_user.is_authenticated:
        return flask.redirect(url_for("login_page"))

    cred = current_user.credentials
    if cred == "":
        print "No Credentials! {}".format(cred)  # .format(flask.session.items())
        return flask.redirect('authorize')
    # Load credentials from the session.
    # print "Credenziali stringa: {}".format(cred)
    json_cred = json.loads(cred)
    # print "Credenziali nuove {}: ".format(json_cred)
    credentials = google.oauth2.credentials.Credentials(**json_cred)  # (**flask.session['credentials'])
    # credentials = google.oauth2.credentials.Credentials(credentials_to_dict(credentials))
    # credentials = google.oauth2.credentials.Credentials(flask.session['credentials'])

    # credentials_sess = google.oauth2.credentials.Credentials(flask.session['credentials'])
    print "Credentials db: {}".format(credentials.to_json())
    # print "Credentials ss: {}".format(credentials_sess.to_json())

    calendar = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)

    all_calendars = calendar.calendarList().list().execute()
    calendar_id = "primary"  # all_calendars["items"][1]["id"]

    events = calendar.events().list(calendarId=calendar_id, timeMin=datetime.utcnow().isoformat() + "Z",
                                    singleEvents=True, orderBy="startTime").execute()
    print "Events: {}".format(events)

    info_service = googleapiclient.discovery.build("people", "v1", credentials=credentials)
    info = info_service.people().get(resourceName="people/me",
                                     personFields="names,emailAddresses,coverPhotos,photos").execute()
    print "info: {}".format(info)
    # print type(info)

    print info["emailAddresses"][0]["value"]
    print info["names"][0]["familyName"]
    print info["names"][0]["givenName"]

    # Save credentials back to session in case access token was refreshed.
    # ACTION ITEM: In a production app, you likely want to save these
    #              credentials in a persistent database instead.
    flask.session['credentials'] = credentials_to_dict(credentials)
    current_user.credentials = json.dumps(credentials_to_dict(credentials))
    db.session.commit()

    return flask.jsonify(**info)  # flask.jsonify(**events)  # all_calendars)


@app.route('/revoke')
def revoke():
    if 'credentials' not in flask.session:
        return ('You need to <a href="/authorize">authorize</a> before ' +
                'testing the code to revoke credentials.')

    credentials = google.oauth2.credentials.Credentials(
        **flask.session['credentials'])

    revoke = requests.post('https://oauth2.googleapis.com/revoke',
                           params={'token': credentials.token},
                           headers={'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        return ('Credentials successfully revoked.')
    else:
        return ('An error occurred.')


@app.route('/clear')
def clear_credentials():
    current_user.credentials = ""
    db.session.commit()

    if 'credentials' in flask.session:
        del flask.session['credentials']
    return ('Credentials have been cleared')


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}
