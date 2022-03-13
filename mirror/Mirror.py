import time

from FacesClass import Faces, path_getter
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base

app = Flask(__name__)
face = Faces()


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+path_getter("\\website\\website.db")
db = SQLAlchemy(app)

Base = automap_base()
Base.prepare(db.engine, reflect=True)
User = Base.classes.user
Mirror = Base.classes.mirror
Relation = Base.classes.relations

product_code = 11
me = db.session.query(Mirror).filter(Mirror.product_code == product_code).first()
print "I am", me.id



@app.route('/test')
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


@app.route('/')
def mirror():
    return render_template("no_face.html")


@app.route('/add_face')
def add_face():
    user_id = str(3)
    if face.newface(user_id):
        print "Face of user {} added!".format(user_id)
        train()
    else:
        print "Face of user {} is already present!".format(user_id)

    return redirect(url_for('show_template', user_id=user_id))


@app.route('/remove_face/<user_id>')
def remove_face(user_id):
    user_id = str("luca")
    if face.removeface(user_id):
        print "Face of user {} removed!".format(user_id)
        train()
    else:
        print "Face of user {} not in the system!".format(user_id)

    return redirect(url_for('mirror'))


@app.route('/train')
def train_page():
    train()
    return redirect(url_for('mirror'))


def train():
    print "Train started"
    start = time.time()
    face.train()
    end = time.time()
    print "Train over in {:.1f} seconds".format(end - start)


@app.route('/person', methods=['GET',  'POST'])
def get_person():
    prsn = face.recognize()
    print prsn
    return prsn


@app.route('/user/<user_id>')
def show_template(user_id):
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
    app.run()
