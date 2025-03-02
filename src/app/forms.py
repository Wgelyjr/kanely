from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

class RegistrationForm(FlaskForm):
    username = StringField('Username', 
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')

class LoginForm(FlaskForm):
    email = StringField('Email', 
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                             validators=[DataRequired()])
    submit = SubmitField('Login')

class BoardForm(FlaskForm):
    title = StringField('Board Title', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Create Board')

class ColumnForm(FlaskForm):
    title = StringField('Column Title', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Column')

class CardForm(FlaskForm):
    title = StringField('Card Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description')
    submit = SubmitField('Add Card')

class SettingsForm(FlaskForm):
    dark_mode = BooleanField('Dark Mode')
    submit = SubmitField('Save Settings')

class ShareBoardForm(FlaskForm):
    user_email = StringField('User Email', validators=[DataRequired(), Email()])
    permission = SelectField('Permission', choices=[
        ('view', 'View Only'), 
        ('edit', 'Can Edit')
    ], validators=[DataRequired()])
    submit = SubmitField('Share Board')
    
    def validate_user_email(self, user_email):
        user = User.query.filter_by(email=user_email.data).first()
        if not user:
            raise ValidationError('No user found with this email address.')
