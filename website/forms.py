from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from wtforms.validators import Length, EqualTo, Email, DataRequired, ValidationError
from website.models import User
import re

"""
validators=[Length(min=2, max=30), DataRequired(message="messaggio di errore personalizzato")]
"""

class RegisterForm(FlaskForm):
    def validate_username(self, username_to_check):     #Validate_field is a custom validator automatically checked with the others related to the field!
        user = User.query.filter_by(username=username_to_check.data).first()
        if user:
            raise ValidationError('Username already exists! Please try a different username')

    def validate_email_address(self, email_address_to_check):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(regex, email_address_to_check.data, 0):
            raise ValidationError('{} is not a valid Email Address!'.format(email_address_to_check.data))
        email_address = User.query.filter_by(email_address=email_address_to_check.data).first()
        if email_address:
            raise ValidationError('Email Address already exists! Please try a different email address')

    username = StringField(label='User Name:', validators=[Length(min=2, max=30), DataRequired()])
    email_address = StringField(label='Email Address:', validators=[DataRequired()]) #Email() ,
    password1 = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    password2 = PasswordField(label='Confirm Password:', validators=[EqualTo('password1'), DataRequired()])
    submit = SubmitField(label='Create Account')


class LoginForm(FlaskForm):
    email_address = StringField(label='Email Address:', validators=[DataRequired()])
    password = PasswordField(label='Password:', validators=[DataRequired()])
    submit = SubmitField(label='Sign in')


class UpdateForm(FlaskForm):
    #password = PasswordField(label='Password:', validators=[Length(min=6), DataRequired()])
    name = StringField(label='Name:', validators=[Length(max=30)])
    surname = StringField(label='Surname:', validators=[Length(max=30)])
    submit = SubmitField(label='Update Values')


class LayoutForm(FlaskForm):
    top_left_choice = StringField(id='top-left-choice')
    center_left_choice = StringField(id='center-left-choice')
    bottom_left_choice = StringField(id='bottom-left-choice')

    top_right_choice = StringField(id='top-right-choice')
    center_right_choice = StringField(id='center-right-choice')
    bottom_right_choice = StringField(id='bottom-right-choice')

    text_choice = StringField(id='text-choice')

    layout_submit = SubmitField(label='Save Layout')


class RegisterMirrorForm(FlaskForm):
    product_code = StringField(label='Product Code:', validators=[DataRequired(), Length(min=2, max=30)])
    secret_code = StringField(label='Secret Code:', validators=[DataRequired(), Length(min=10, max=10)])
    name = StringField(label='Name:', validators=[Length(max=40)])

    country = StringField(label='Country:', validators=[Length(max=30)])
    region = StringField(label='Region:', validators=[Length(max=30)])
    city = StringField(label='City:', validators=[Length(max=30)])
    address = StringField(label='Address:', validators=[Length(max=50)])
    number = StringField(label='Number:', validators=[Length(max=6)])
    postal_code = StringField(label='Postal Code:', validators=[Length(max=10)])

    register_submit = SubmitField(label='Register Mirror')


class LinkMirrorForm(FlaskForm):
    product_code = StringField(label='Product Code:', validators=[DataRequired(), Length(min=2, max=30)])
    owner_email_address = StringField(label='Owner\'s Email Address:', validators=[DataRequired()])

    link_submit = SubmitField(label='Link Mirror')


class EditMirrorForm(FlaskForm):
    #product_code = StringField(label='Product Code:', validators=[Length(min=2, max=30)])
    #secret_code = StringField(label='Secret Code:', validators=[Length(min=10, max=10)])

    name = StringField(label='Name:', validators=[Length(max=40)])
    location = StringField(label='Location:', validators=[Length(max=200)])

    submit = SubmitField(label='Save Changes')
