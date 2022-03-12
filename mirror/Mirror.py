from FacesClass import Faces
from flask import Flask, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base

app = Flask(__name__)
face = Faces()

def path_getter(end_path):
    path = __file__ + ""
    temp = path.split("\\")
    uri_file = ""
    for direct in temp:
        uri_file = uri_file + direct + "\\"
        if direct == "smart-mirror":
            break
    return uri_file + end_path


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


@app.route('/person', methods= ['GET',  'POST'])
def get_person():
    prsn = face.recognize()
    print prsn
    return prsn



@app.route('/user/<name>')
def show_template(name):

    return render_template("registered_user.html", user=name)



if __name__ == '__main__':
    app.run()
