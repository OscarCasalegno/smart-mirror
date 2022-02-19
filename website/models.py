from website import db, login_manager
from website import bcrypt
from flask_login import UserMixin
import pickle

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

ac_mirrors = db.Table('ac_mirrors',
            db.Column('mirror_id', db.Integer, db.ForeignKey('mirror.id'), primary_key=True),
            db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
            db.Column('ownership', db.Boolean(), default=False)
        )
# current_user.mirrors.append(new_mirror)
# db.session.commit()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    name = db.Column(db.String(length=30), nullable=False)      #TBD
    surname = db.Column(db.String(length=30), nullable=False)   #TBD
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    g_email_address = db.Column(db.String(length=50), unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    credentials = db.Column(db.Text())
    face_details = db.Column(db.LargeBinary)
    mirrors = db.relationship('Mirror', secondary=ac_mirrors, backref=db.backref('users'))

    def __repr__(self):
        return "{username}".format(username=self.username)

    def __str__(self):
        return "User: {name} {surname}".format(name=self.name, surname=self.surname)

    @property
    def password(self):
        return self.password

    @password.setter
    def password(self, plain_text_password):
        self.password_hash = bcrypt.generate_password_hash(plain_text_password).decode('utf-8')

    def check_password_correction(self, attempted_password):
        return bcrypt.check_password_hash(self.password_hash, attempted_password)


class Mirror(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    product_code = db.Column(db.String(length=40), nullable=False)
    secret_code = db.Column(db.String(length=10), nullable=False)
    model = db.Column(db.String(length=40))
    preferences = db.Column(db.Text())
    location = db.Column(db.Text())
    name = db.Column(db.String(length=40))

    def __repr__(self):
        return self.name if self.name != "" else self.product_code

    def __str__(self):
        return "Mirror: {name}".format(name=self.__repr__())

"""
from website import db
db.drop_all()
db.create_all()
"""
