from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, RadioField, IntegerField
from wtforms.validators import DataRequired, Email, Optional, Length


CITIES = [
    ('', 'Select City'),
    ('Lagos', 'Lagos'),
    ('Abuja', 'Abuja'),
    ('Port Harcourt', 'Port Harcourt'),
    ('Ibadan', 'Ibadan'),
    ('Kano', 'Kano'),
    ('Benin City', 'Benin City'),
    ('Enugu', 'Enugu'),
    ('Warri', 'Warri'),
    ('Asaba', 'Asaba'),
    ('Owerri', 'Owerri'),
    ('Uyo', 'Uyo'),
    ('Others', 'Others'),
]

PROPERTY_TYPES = [
    ('', 'Property Type'),
    ('Apartment', 'Apartment'),
    ('Duplex', 'Duplex'),
    ('Terrace', 'Terrace'),
    ('Detached', 'Detached'),
    ('Semi-Detached', 'Semi-Detached'),
    ('Land', 'Land'),
    ('Commercial', 'Commercial'),
    ('Penthouse', 'Penthouse'),
]


class InquiryForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    message = TextAreaField('Message', validators=[DataRequired()])


class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[Optional(), Length(max=30)])
    subject = StringField('Subject', validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', validators=[DataRequired()])


class NewsletterForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired(), Email()])


class ValuationForm(FlaskForm):
    city = SelectField('City', choices=CITIES, validators=[DataRequired()])
    property_type = SelectField('Property Type', choices=PROPERTY_TYPES, validators=[DataRequired()])
    bedrooms = SelectField('Bedrooms', choices=[
        ('', 'Select Bedrooms'),
        ('1', '1 Bedroom'),
        ('2', '2 Bedrooms'),
        ('3', '3 Bedrooms'),
        ('4', '4 Bedrooms'),
        ('5', '5+ Bedrooms'),
    ], validators=[Optional()])
    area_sqm = IntegerField('Approximate Area (sqm)', validators=[Optional()])
    listing_purpose = RadioField('I want to', choices=[
        ('For Sale', 'Sell this property'),
        ('For Rent', 'Rent it out'),
    ], validators=[DataRequired()])
    your_name = StringField('Your Name', validators=[DataRequired(), Length(max=120)])
    your_phone = StringField('Your Phone Number', validators=[DataRequired(), Length(max=30)])
