from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, SelectField, BooleanField,
                     IntegerField, FloatField, SelectMultipleField, widgets)
from wtforms.validators import DataRequired, Optional, Length, Email


CITIES = [
    ('Lagos', 'Lagos'), ('Abuja', 'Abuja'), ('Port Harcourt', 'Port Harcourt'),
    ('Ibadan', 'Ibadan'), ('Kano', 'Kano'), ('Benin City', 'Benin City'),
    ('Enugu', 'Enugu'), ('Warri', 'Warri'), ('Asaba', 'Asaba'),
    ('Owerri', 'Owerri'), ('Uyo', 'Uyo'), ('Others', 'Others'),
]

PROPERTY_TYPES = [
    ('Apartment', 'Apartment'), ('Duplex', 'Duplex'), ('Terrace', 'Terrace'),
    ('Detached', 'Detached'), ('Semi-Detached', 'Semi-Detached'),
    ('Land', 'Land'), ('Commercial', 'Commercial'), ('Penthouse', 'Penthouse'),
]

LISTING_TYPES = [
    ('For Sale', 'For Sale'), ('For Rent', 'For Rent'), ('Short Let', 'Short Let'),
]

AMENITIES_LIST = [
    'Swimming Pool', 'Generator', 'CCTV', '24/7 Security', 'Gym',
    'Boys Quarters', 'Rooftop Terrace', 'Air Conditioning', 'Smart Home',
    'Waterfront', 'Serviced', 'Gated Estate', 'Fitted Kitchen',
    'Backup Water', 'Intercom',
]


class PropertyForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=220)])
    description = TextAreaField('Description', validators=[DataRequired()])
    property_type = SelectField('Property Type', choices=PROPERTY_TYPES, validators=[DataRequired()])
    listing_type = SelectField('Listing Type', choices=LISTING_TYPES, validators=[DataRequired()])
    price = IntegerField('Price (₦)', validators=[DataRequired()])
    price_period = StringField('Price Period', validators=[Optional(), Length(max=20)])
    city = SelectField('City', choices=CITIES, validators=[DataRequired()])
    state = StringField('State', validators=[Optional(), Length(max=80)])
    address = StringField('Full Address', validators=[Optional(), Length(max=300)])
    latitude = FloatField('Latitude', validators=[Optional()])
    longitude = FloatField('Longitude', validators=[Optional()])
    bedrooms = IntegerField('Bedrooms', validators=[Optional()])
    bathrooms = IntegerField('Bathrooms', validators=[Optional()])
    toilets = IntegerField('Toilets', validators=[Optional()])
    parking_spaces = IntegerField('Parking Spaces', validators=[Optional()])
    area_sqm = IntegerField('Area (sqm)', validators=[Optional()])
    agent_id = SelectField('Assign Agent', coerce=int, validators=[Optional()])
    is_featured = BooleanField('Featured Property')
    is_published = BooleanField('Published', default=True)


class AgentForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired(), Length(max=120)])
    title = StringField('Title / Role', validators=[Optional(), Length(max=80)])
    bio = TextAreaField('Bio', validators=[Optional()])
    phone = StringField('Phone', validators=[Optional(), Length(max=30)])
    whatsapp = StringField('WhatsApp Number', validators=[Optional(), Length(max=30)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=120)])
    photo = FileField('Profile Photo', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'webp'])])
    is_active = BooleanField('Active', default=True)
