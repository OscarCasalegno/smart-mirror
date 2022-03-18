import google
import googleapiclient
import json
from datetime import datetime
import google.oauth2.credentials
import googleapiclient.discovery
import googlemaps

from Mirror import db, path_getter


def get_google_events(user):
    cred = user.credentials
    if cred == "":
        print "No Credentials! {}".format(cred)     # .format(flask.session.items())
        return None

    json_cred = json.loads(cred)
    credentials = google.oauth2.credentials.Credentials(**json_cred)          # (**flask.session['credentials'])
    print "Credentials db: {}".format(credentials.to_json())

    calendar = googleapiclient.discovery.build("calendar", "v3", credentials=credentials)

    all_calendars = calendar.calendarList().list().execute()
    calendar_id = "primary"  # all_calendars["items"][1]["id"]

    events = calendar.events().list(calendarId=calendar_id, timeMin=datetime.utcnow().isoformat()+"Z", singleEvents=True, orderBy="startTime").execute()
    print "Events: {}".format(events)

    user.credentials = json.dumps(credentials_to_dict(credentials))
    db.session.commit()

    return events


def get_distance(start_point, end_point, mode):
    f = open(path_getter("/website/static/secret/google_key.txt"), "r")
    my_key = f.read()
    f.close()

    gmaps = googlemaps.Client(key=my_key)
    response = gmaps.distance_matrix(origins=start_point, destinations=end_point, mode=mode, language="en")  # mode="driving"
    print json.dumps(response)
    return response


def get_geocode(address):
    f = open(path_getter("/website/static/secret/google_key.txt"), "r")
    my_key = f.read()
    f.close()

    gmaps = googlemaps.Client(key=my_key)
    response = gmaps.geocode(address=address)  # mode="driving"
    print json.dumps(response)
    return response


def credentials_to_dict(credentials):
    return {'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes}


def format_duration(duration=None, seconds=None):
    if seconds is None and duration is None:
        return "-"

    if seconds is None:
        seconds = duration.total_seconds()

    if seconds > 60*60*24:
        return str(duration)
    minutes = seconds/60
    result = divmod(minutes, 60)
    hours = result[0]
    minutes = result[1]

    formatted = ""
    if hours > 1:
        formatted += "{h:.0f}h".format(h=hours)
    if hours == 1:
        formatted += "{h:.0f}h".format(h=hours)
    if hours > 0 and minutes > 0:
        formatted += "-"
    if minutes > 1:
        formatted += "{m:.0f}min".format(m=minutes)
    if minutes == 1:
        formatted += "{m:.0f}min".format(m=minutes)

    return formatted

