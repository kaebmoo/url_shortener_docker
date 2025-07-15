from flask_wtf import FlaskForm
from wtforms import ValidationError
# from wtforms.ext.sqlalchemy.fields import QuerySelectField
# from wtforms.fields import QuerySelectField
from wtforms_sqlalchemy.fields import QuerySelectField

from wtforms.fields import (
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.fields import DateField, EmailField, TelField
# from wtforms.fields.html5 import EmailField
from wtforms.validators import (
    Email,
    EqualTo,
    InputRequired,
    Length,
    DataRequired,
    URL as URLValidator,
)

from wtforms import FileField
from flask_wtf.file import FileAllowed, FileRequired

from app import db
from app.models import Role, User

import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

def validate_and_format_phone_number(form, field):
    try:
        # Parse the phone number with TH (Thailand) as the default region
        parsed_number = phonenumbers.parse(field.data, "TH")
        
        # Validate the parsed number
        if phonenumbers.is_valid_number(parsed_number):
            # Format the number in E164 format (e.g., +66813520625)
            formatted_number = phonenumbers.format_number(parsed_number, PhoneNumberFormat.E164)
            field.data = formatted_number.replace('+', '')  # Update field data with the formatted number without '+'
        else:
            raise ValidationError('Invalid phone number.')
    except NumberParseException:
        raise ValidationError('Invalid phone number format.')
    
class ChangeUserEmailForm(FlaskForm):
    email = EmailField(
        'New email', validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

class ChangeUserPhoneForm(FlaskForm):
    phone_number = StringField('New phone number', validators=[InputRequired(), 
                                                           Length(min=10, max=15), 
                                                           validate_and_format_phone_number])
    # password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Update phone number')

    def validate_phone_number(self, field):
        if User.query.filter_by(phone_number=field.data).first():
            raise ValidationError('Phone number already registered.')

class ChangeAccountTypeForm(FlaskForm):
    role = QuerySelectField(
        'New account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    submit = SubmitField('Update role')


class InviteUserForm(FlaskForm):
    role = QuerySelectField(
        'Account type',
        validators=[InputRequired()],
        get_label='name',
        query_factory=lambda: db.session.query(Role).order_by('permissions'))
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField('Invite')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')


class NewUserForm(InviteUserForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    submit = SubmitField('Create')

class AddURLForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URLValidator()])
    category = StringField('Category', validators=[DataRequired()])
    reason = StringField('Reason', validators=[DataRequired()])
    source = StringField('Source', validators=[DataRequired()])
    submit = SubmitField('Add URL')

class ImportForm(FlaskForm):
    file = FileField('File', validators=[FileRequired(), FileAllowed(['csv', 'json'], 'CSV and JSON files only!')])
    submit = SubmitField('Import')