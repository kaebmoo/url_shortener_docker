# user_management/app/main/forms.py

from flask_wtf import FlaskForm
from wtforms import HiddenField, SubmitField

class URLActionForm(FlaskForm):
    url_secret_key = HiddenField()
    target_url = HiddenField()
    submit = SubmitField('Delete')
    submit_info = SubmitField('Info')

