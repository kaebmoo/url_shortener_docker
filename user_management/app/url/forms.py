from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, URL, Optional

class URLShortenForm(FlaskForm):
    original_url = StringField('Enter URL', validators=[DataRequired(), URL()])
    custom_key = StringField('Custom Key', validators=[Optional()]) 
    submit = SubmitField('Shorten URL')
