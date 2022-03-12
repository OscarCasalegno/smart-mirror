from FacesClass import Faces
from flask import Flask, render_template, redirect, url_for
app = Flask(__name__)
face = Faces()

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
    template = name + ".html"
    return render_template(template)



if __name__ == '__main__':
    app.run()
