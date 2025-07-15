from flask import url_for
from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms.fields import (
    RadioField,
    BooleanField,
    PasswordField,
    StringField,
    SubmitField,
)
# from wtforms.fields.html5 import EmailField
from wtforms.fields import DateField, EmailField, TelField
from wtforms.validators import Email, EqualTo, InputRequired, Length, Optional
from wtforms import ValidationError
import phonenumbers
from phonenumbers import NumberParseException, PhoneNumberFormat

from app.models import User

'''
def email_or_phone_required(form, field):
    if not form.email.data and not form.phone_number.data:
        raise ValidationError('Either email or phone number is required.')
'''
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

def validate_domain(form, field):
    allowed_domain = 'ntplc.co.th'
    if not field.data.endswith(f"@{allowed_domain}"):
        raise ValidationError(f"Email domain must be {allowed_domain}")
    
class LoginForm(FlaskForm):
    login_method = RadioField('Login with:', choices=[('email', 'Email'), ('phone', 'Phone Number')], default='email')
    email = EmailField(
        'Email', validators=[Optional(),
                             Length(1, 64),
                             Email()])
    phone_number = StringField('Phone Number', validators=[Optional(), Length(min=10, max=15), validate_and_format_phone_number])
    password = PasswordField('Password', validators=[InputRequired()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log in')
    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self, extra_validators)
        if not rv:
            return False
        if not self.email.data and not self.phone_number.data:
            self.email.errors.append('Either email or phone number is required.')
            self.phone_number.errors.append('Either email or phone number is required.')
            return False
        return True

class RegistrationFormSelect(FlaskForm):
    registration_type = RadioField('Register with:', 
                                   choices=[('email', 'Email'), ('phone', 'Phone Number')], # , ('phone', 'Phone Number')
                                   default='email',  # กำหนดค่าเริ่มต้น
                                   validators=[InputRequired()])
    submit = SubmitField('Continue')

class PhoneNumberForm(FlaskForm):
    first_name = StringField(
        'First name', validators=[InputRequired(),
                                  Length(1, 64)])
    last_name = StringField(
        'Last name', validators=[InputRequired(),
                                 Length(1, 64)])
    phone_number = StringField('Phone Number', validators=[InputRequired(), Length(min=10, max=15), validate_and_format_phone_number])
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Send OTP')
    def validate_phone_number(self, field):
        if User.query.filter_by(phone_number=field.data).first():
            raise ValidationError('Phone number already registered. (Did you mean to '
                                  '<a href="{}">log in</a> instead?)'.format(
                                    url_for('account.login')))

class OTPForm(FlaskForm):
    otp = StringField('OTP', validators=[InputRequired(), Length(min=4, max=4)])
    submit = SubmitField('Verify OTP')

class RegistrationForm(FlaskForm):
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
    # validate_domain
    
    # phone_number = TelField('Phone')
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match')
        ])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered. (Did you mean to '
                                  '<a href="{}">log in</a> instead?)'.format(
                                    url_for('account.login')))


class RequestResetPasswordForm(FlaskForm):
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    submit = SubmitField('Reset password')

    # We don't validate the email address so we don't confirm to attackers
    # that an account with the given email exists.


class ResetPasswordForm(FlaskForm):
    email = EmailField(
        'Email', validators=[InputRequired(),
                             Length(1, 64),
                             Email()])
    new_password = PasswordField(
        'New password',
        validators=[
            InputRequired(),
            EqualTo('new_password2', 'Passwords must match.')
        ])
    new_password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Reset password')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first() is None:
            raise ValidationError('Unknown email address.')


class CreatePasswordForm(FlaskForm):
    password = PasswordField(
        'Password',
        validators=[
            InputRequired(),
            EqualTo('password2', 'Passwords must match.')
        ])
    password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Set password')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old password', validators=[InputRequired()])
    new_password = PasswordField(
        'New password',
        validators=[
            InputRequired(),
            EqualTo('new_password2', 'Passwords must match.')
        ])
    new_password2 = PasswordField(
        'Confirm new password', validators=[InputRequired()])
    submit = SubmitField('Update password')


class ChangeEmailForm(FlaskForm):
    email = EmailField(
        'New email', validators=[InputRequired(),
                                 Length(1, 64),
                                 Email()])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Update email')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')
        
class ChangePhoneForm(FlaskForm):
    phone_number = StringField('New phone number', validators=[InputRequired(), 
                                                           Length(min=10, max=15), 
                                                           validate_and_format_phone_number])
    password = PasswordField('Password', validators=[InputRequired()])
    submit = SubmitField('Update phone number')

    def validate_phone_number(self, field):
        if User.query.filter_by(phone_number=field.data).first():
            raise ValidationError('Phone number already registered.')
