from website import db, login_manager
from website import bcrypt
from flask_login import UserMixin
import pickle

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

""" Note on db:

1 to 1 relationship
    mirrors = db.relationship('Mirror', backref='owned_user', lazy=True)    #backref creates the new property "owned_user" in the table Mirror
    # mirrors is a list of mirrors related to the specific user (thanks to laze you have them already loaded) 
    
    In the mirror table i still have to declare the foreign key:
    owner = db.Column(db.Integer(), db.ForeignKey('user.id'))       #user.id is table.lower() . key property of table

n to n relationship
        tags = db.Table('tags',
            db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True),
            db.Column('page_id', db.Integer, db.ForeignKey('page.id'), primary_key=True)
        )           # name of the field                     reference           also key for this table
        
        class Page(db.Model):
            id = db.Column(db.Integer, primary_key=True)
            tags = db.relationship('Tag', secondary=tags, lazy='subquery', backref=db.backref('pages', lazy=True))
        
        class Tag(db.Model):
            id = db.Column(db.Integer, primary_key=True)


"For only {price}".format(price = 49)

"Mirror {name}".format(name = self.name)
"Mirror {0}".format(self.name)
"""

ac_mirrors = db.Table('ac_mirrors',
            db.Column('mirror_id', db.Integer, db.ForeignKey('mirror.id'), primary_key=True),
            db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
            db.Column('ownership', db.Boolean())
        )


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    name = db.Column(db.String(length=30), nullable=False)      #TBD
    surname = db.Column(db.String(length=30), nullable=False)   #TBD
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    mirrors = db.relationship('Mirror', secondary=ac_mirrors, lazy='subquery', backref=db.backref('users', lazy='subquery'))
    credentials = db.Column(db.Text())

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
    model = db.Column(db.String(length=40), nullable=False, unique=True)
    location = db.Column(db.Integer(), nullable=False)  #TBD

    def __repr__(self):
        return "Mirror #{name}".format(name=self.name)
