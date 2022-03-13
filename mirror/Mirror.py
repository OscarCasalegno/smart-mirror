import time

from FacesClass import Faces, path_getter
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base

mirror_app = Flask(__name__)
face = Faces()


mirror_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+path_getter("\\website\\website.db")
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


def get_users():
    linked_users = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id).all()
    return linked_users


def set_recognisable(user_id, value):
    return 0
    #SULLA RELAZIONE!!!
    #linked_user = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == user_id).all()
    #if len(linked_user) == 1:
    #    linked_user[0].xxxxx = value
    #    return True
    #else:
    #    return False


@mirror_app.route('/test')
def test():
    #prova = db.session.query(User).join(Mirror).filter(Mirror.id == 2).count()
    #utenti = db.session.query(User).all()
    #for u in utenti:
    #    print u.id, " - ", u.username
    #for x in dir(utenti[2]):
    #    print "| ", x
    #print utenti[2].username
    #print utenti[2].relations_collection
    utenti = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == 3).all()
    for x in dir(utenti[0]):
        print "| ", x
    print utenti[0].username


@mirror_app.route('/')
def mirror():
    return render_template("no_face.html")


@mirror_app.route('/add_face/<user_id>')
def add_face(user_id):

    relation = db.session.query(Relation).filter(Relation.mirror_id == me.id, Relation.user_id == user_id).all()
    if len(relation) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return redirect(url_for('mirror'))

    if face.newface( str(user_id) ):
        print "Face of user {} added!".format(user_id)
        train()
    else:
        print "Face of user {} is already present!".format(user_id)

    relation[0].recognisable = True
    db.session.commit()

    return redirect(url_for('show_template', user_id=user_id))


@mirror_app.route('/remove_face/<user_id>')
def remove_face(user_id):
    user_id = str(user_id)
    if face.removeface(user_id):
        print "Face of user {} removed!".format(user_id)
        train()
    else:
        print "Face of user {} not in the system!".format(user_id)

    return redirect(url_for('mirror'))


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


@mirror_app.route('/person', methods=['GET',  'POST'])
def get_person():
    prsn = face.recognize()
    print prsn
    return prsn


@mirror_app.route('/user/<user_id>')
def show_template(user_id):
    if me is None:
        return redirect(url_for('register'))
    if user_id == "no_face":
        return render_template("no_face.html")
    if user_id == "unknown":
        return render_template("unknown.html")

    user = db.session.query(User).join(Relation).filter(Relation.mirror_id == me.id, User.id == user_id).all()

    if len(user) != 1:
        print "Error!\nUser {} not linked".format(user_id)
        return render_template("unknown.html")
    else:
        return render_template("registered_user.html", user=user[0])


if __name__ == '__main__':
    mirror_app.run(port=8080)
