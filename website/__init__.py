from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

from oauthlib.oauth2 import WebApplicationClient
import requests
import os

from website import google_configuration

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///website.db'
app.config['SECRET_KEY'] = os.urandom(24)  # 'ec9439cfc6c496ae2029594d'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
#Talisman(app)
login_manager = LoginManager(app)
login_manager.login_view = "login_page"
login_manager.login_message_category = "info"


def path_getter(end_path):
    path = __file__ + ""
    temp = path.split("\\")
    uri_file = ""
    for direct in temp:
        uri_file = uri_file + direct + "\\"
        if direct == "website":
            break
    return uri_file + end_path


uri_mail = path_getter("static\\secret\\mail_id.txt")
f = open(uri_mail, "r")
mail_add = f.readline().strip()
mail_pw = f.readline().strip()
f.close()

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = mail_add
app.config['MAIL_PASSWORD'] = mail_pw
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)


#google_configuration.get_id_client_secret()
#google_configuration.get_maps_key()

# Configuration
#GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
#GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)

(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET) = google_configuration.get_id_client_secret()
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

client = WebApplicationClient(GOOGLE_CLIENT_ID)

uri_file = path_getter("static\\secret\\client_secrets.json")


def get_google_provider_cfg():
    answer = requests.get(GOOGLE_DISCOVERY_URL)
    if answer.status_code == requests.codes.ok:
        return answer.json()
    else:
        return False


from website import routes
