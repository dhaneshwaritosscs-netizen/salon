from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, DateTimeField, BooleanField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, NumberRange
from wtforms.widgets import CheckboxInput, ListWidget
from wtforms.fields import SelectMultipleField

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')

class CustomerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    mobile = StringField('Mobile Number', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[Optional()])

class AppointmentForm(FlaskForm):
    customer_id = SelectField('Customer', coerce=int, validators=[DataRequired()])
    staff_id = SelectField('Staff', coerce=int, validators=[DataRequired()])
    appointment_date = DateTimeField('Appointment Date & Time', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    service_ids = SelectMultipleField('Services', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])

class StaffForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional(), Email()])
    mobile = StringField('Mobile Number', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[Optional()])

class ServiceForm(FlaskForm):
    name = StringField('Service Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Optional()])
    price = FloatField('Price (₹)', validators=[DataRequired(), NumberRange(min=0)])
    duration = IntegerField('Duration (minutes)', validators=[DataRequired(), NumberRange(min=1)])

class PromotionForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    discount_type = SelectField('Discount Type', choices=[('percentage', 'Percentage'), ('fixed', 'Fixed Amount')], validators=[DataRequired()])
    discount_value = FloatField('Discount Value', validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateTimeField('Start Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    end_date = DateTimeField('End Date', validators=[DataRequired()], format='%Y-%m-%dT%H:%M')
    target_audience = SelectField('Target Audience', 
                                 choices=[('all', 'All Customers'), 
                                         ('new_customers', 'New Customers'), 
                                         ('loyal_customers', 'Loyal Customers')],
                                 validators=[DataRequired()])

