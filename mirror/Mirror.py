import datetime
import json
import time

from FacesClass import Faces, path_getter
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
import api
from widget import widget_html_handler
from dateutil.parser import parse

mirror_app = Flask(__name__)
face = Faces()

mirror_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + path_getter("\\website\\website.db")
db = SQLAlchemy(mirror_app)

Base = automap_base()
Base.prepare(db.engine, reflect=True)
User = Base.classes.user
Mirror = Base.classes.mirror
Relation = Base.classes.relations

product_code = 11
me = db.session.query(Mirror).filter(Mirror.product_code == product_code).first()
if me is not None:
    print "I am", me.id
else:
    print "Mirror not registered"


def get_mirror():
    return me


@mirror_app.route('/get_users')
def get_users():
    linked_users = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id).all()
    return linked_users

@mirror_app.route('/get_recognisable_users')
def get_not_recognisable_users():
    recognisable_users = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id,
                                                                          Relation.recognisable == True).all()
    users_dict = {}
    for person in recognisable_users:
        users_dict[person.id] = person.name

    return users_dict

@mirror_app.route('/get_not_recognisable_users')
def get_not_recognisable_users():
    not_recognisable_users = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id,
                                                                          Relation.recognisable == False).all()

    users_dict = {}
    for person in not_recognisable_users:
        users_dict[person.id] = person.name

    return users_dict


@mirror_app.route('/test')
def test():
    # prova = db.session.query(User).join(Mirror).filter(Mirror.id == 2).count()
    # utenti = db.session.query(User).all()
    # for u in utenti:
    #    print u.id, " - ", u.username
    # for x in dir(utenti[2]):
    #    print "| ", x
    # print utenti[2].username
    # print utenti[2].relations_collection
    # utenti = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == 3).all()
    # for x in dir(utenti[0]):
    #    print "| ", x
    # print utenti[0].username
    # for user in get_users():
    #    print "User {username} ({id}) is linked".format(id=user.id, username=user.username)

    # for user in get_not_recognisable_users():
    #    print "User {username} ({id}) is not recognisable, add his face".format(id=user.id, username=user.username)

    # for person in face.get_registered_faces():
    #    print "Face of the user {id}".format(id=person)
    # for user in get_users():
    #    print api.get_google_events(user)

    events = api.get_google_events(get_users()[0])
    for event in events["items"]:
        name = event["summary"]
        location = event["location"]
        start = parse(event["start"]["dateTime"])
        # print start.date()
        # print start.time()
        # print start.tzinfo
        end = parse(event["end"]["dateTime"])

        by = "driving"
        path = api.get_distance(me.location, location, by)
        duration = path["rows"][0]["elements"][0]["duration"]["text"]
        distance = path["rows"][0]["elements"][0]["distance"]["text"]

        print "{summary} in {location} starting at {start} for {duration}".format(summary=name, location=location,
                                                                                  start=start.time(),
                                                                                  duration=api.format_duration(
                                                                                      end - start))
        print "It will took {duration} {by} to travel the {distance} of distance\n".format(duration=duration,
                                                                                           distance=distance, by=by)

    return jsonify(**events)


@mirror_app.route('/initialize')
def initiation():
    print "hello"


@mirror_app.route('/')
def mirror():
    return redirect(url_for('show_template', user_id='no_face'))


@mirror_app.route('/add_face/<user_id>')
def add_face(user_id):
    relation = db.session.query(Relation).filter(Relation.mirror_id == me.id, Relation.user_id == user_id).all()
    if len(relation) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return redirect(url_for('mirror'))

    if face.newface(str(user_id)):
        print "Face of user {} added!".format(user_id)
        train()
    else:
        print "Face of user {} is already present!".format(user_id)

    relation[0].recognisable = True
    db.session.commit()

    return redirect(url_for('show_template', user_id=user_id))


@mirror_app.route('/remove_face/<user_id>')
def remove_face(user_id):
    relation = db.session.query(Relation).filter(Relation.mirror_id == me.id, Relation.user_id == user_id).all()
    if len(relation) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return redirect(url_for('mirror'))

    if face.removeface(str(user_id)):
        print "Face of user {} removed!".format(user_id)
        train()
    else:
        print "Face of user {} not in the system!".format(user_id)

    relation[0].recognisable = False
    db.session.commit()

    return redirect(url_for('mirror'))


@mirror_app.route('/selector')
def selector_page():
    return render_template("selector.html")


@mirror_app.route('/train')
def train_page():
    train()
    return redirect(url_for('mirror'))


@mirror_app.route('/register')
def register():
    return render_template("register.html")


def train():
    print "Train started"
    start = time.time()
    face.train()
    end = time.time()
    print "Train over in {:.1f} seconds".format(end - start)


@mirror_app.route('/person', methods=['GET', 'POST'])
def get_person():
    prsn = face.recognize()

    print prsn

    user = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == prsn).all()

    if len(user) != 1:
        print "Error!\nUser {} not linked".format(prsn)
        return "unknown"
    else:
        return prsn


@mirror_app.route('/user/<user_id>')
def show_template(user_id):
    if me is None:
        return redirect(url_for('register'))
    if user_id == "no_face":
        return render_template("no_face.html")
    if user_id == "unknown":
        return render_template("registered_user.html", user=None, layout=mirror_unknown_html_handler())

    user = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == user_id).all()

    layout = mirror_html_handler(user_id)

    if len(user) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return render_template("unknown.html")
    else:
        return render_template("registered_user.html", user=user[0], layout=layout)


@mirror_app.route('/armageddon')
def armageddon():
    print "Procedure starting:"
    for person in face.get_registered_faces():
        if face.removeface(str(person)):
            print "  Face of the user {id} has been deleted".format(id=person)
        else:
            "  Error deleting the face of the user {id}".format(id=person)
    print "Procedure finished!"


def mirror_html_handler(user_id):
    relation = db.session.query(Relation).filter(Relation.mirror_id == me.id, Relation.user_id == user_id).all()
    if len(relation) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return redirect(url_for('mirror'))
    relation = relation[0]
    user = db.session.query(User).filter(User.id == user_id).first()

    layout = json.loads(relation.layout)
    payload = {}

    for k, v in layout.items():
        payload[k] = widget_html_handler(v, user, me)

    payload["text"] = layout["text"]

    print json.dumps(payload)
    return payload


def mirror_unknown_html_handler():
    layout = json.loads(me.standard_layout)
    payload = {}

    for k, v in layout.items():
        payload[k] = widget_html_handler(v, None, me)

    payload["text"] = layout["text"]

    print json.dumps(payload)
    return payload


if __name__ == '__main__':
    mirror_app.run(port=8080)
