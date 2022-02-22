from sqlalchemy.orm import relationship, backref
from website import db, login_manager
from website import bcrypt
from flask_login import UserMixin
import pickle

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# current_user.mirrors.append(new_mirror)
# db.session.commit()

#user = User.query.first()
#user.products  # List all products, eg [<productA>, <productB> ]
#user.orders    # List all orders, eg [<order1>, <order2>]
#user.orders[0].products  # List products from the first order
#p1 = Product.query.first()
#p1.users  # List all users who have bought this product, eg [<user1>, <user2>]

class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    username = db.Column(db.String(length=30), nullable=False, unique=True)
    name = db.Column(db.String(length=30))      #TBD
    surname = db.Column(db.String(length=30))   #TBD
    email_address = db.Column(db.String(length=50), nullable=False, unique=True)
    g_email_address = db.Column(db.String(length=50), unique=True)
    password_hash = db.Column(db.String(length=60), nullable=False)
    credentials = db.Column(db.Text())
    face_details = db.Column(db.LargeBinary)
    mirrors = relationship("Mirror", secondary="relations", backref=db.backref('users'))

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
    #users = relationship("User", secondary="relations", back_populates="mirrors") #Already in User

    def get_owner(self):
        relations = self.related
        owner_iterator = filter(lambda rel: rel.ownership, relations)
        return list(owner_iterator)

    def get_users_number(self):
        n = len(self.users)
        return "{} users".format(n) if n != 1 else "{} user".format(n)

    def get_location_lim(self, n):
        return (self.location[:n:].strip()+"..." if len(self.location) > n+3 else self.location).strip()

    def __repr__(self):
        return self.name if self.name != "" else self.product_code

    def __str__(self):
        return "Mirror: {name}".format(name=self.__repr__())


class Relation(db.Model):
    __tablename__ = 'relations'
    mirror_id = db.Column(db.Integer, db.ForeignKey('mirror.id'), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    ownership = db.Column(db.Boolean(), default=False)

    user = relationship(User, backref=backref("related", cascade="all, delete-orphan"))
    mirror = relationship(Mirror, backref=backref("related", cascade="all, delete-orphan"))

    def __repr__(self):
        return "[ {user} - {mirror} ]".format(user=self.user.__repr__(), mirror=self.mirror.__repr__())

    def __str__(self):
        return "R( U: {user} M: {mirror} )".format(user=self.user.__repr__(), mirror=self.mirror.__repr__())



"""
from website import db
db.drop_all()
db.create_all()
"""
