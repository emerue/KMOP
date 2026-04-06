from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    title = db.Column(db.String(80))
    bio = db.Column(db.Text)
    phone = db.Column(db.String(30))
    whatsapp = db.Column(db.String(30))
    email = db.Column(db.String(120))
    photo = db.Column(db.String(300))
    is_active = db.Column(db.Boolean, default=True)
    properties = db.relationship('Property', back_populates='agent', lazy='dynamic')


class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ref_code = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    property_type = db.Column(db.String(50))
    listing_type = db.Column(db.String(20))
    price = db.Column(db.BigInteger, nullable=False)
    price_period = db.Column(db.String(20))
    city = db.Column(db.String(80))
    state = db.Column(db.String(80))
    address = db.Column(db.String(300))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    toilets = db.Column(db.Integer)
    parking_spaces = db.Column(db.Integer)
    area_sqm = db.Column(db.Integer)
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    views = db.Column(db.Integer, default=0)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    agent = db.relationship('Agent', back_populates='properties')
    images = db.relationship(
        'PropertyImage',
        back_populates='property',
        cascade='all, delete-orphan',
        order_by='PropertyImage.sort_order'
    )
    amenities = db.relationship(
        'PropertyAmenity',
        back_populates='property',
        cascade='all, delete-orphan'
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def cover_image(self):
        cover = next((img for img in self.images if img.is_cover), None)
        return cover or (self.images[0] if self.images else None)

    @property
    def cover_image_url(self):
        img = self.cover_image
        if img:
            return '/static/uploads/properties/' + img.filename
        return None

    def generate_ref_code(self):
        return 'KMP-' + str(self.id).zfill(4)


class PropertyImage(db.Model):
    __tablename__ = 'property_images'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    property = db.relationship('Property', back_populates='images')
    filename = db.Column(db.String(300), nullable=False)
    is_cover = db.Column(db.Boolean, default=False)
    sort_order = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)


class PropertyAmenity(db.Model):
    __tablename__ = 'property_amenities'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id', ondelete='CASCADE'), nullable=False)
    property = db.relationship('Property', back_populates='amenities')
    name = db.Column(db.String(100))


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30))
    message = db.Column(db.Text, nullable=False)
    inquiry_type = db.Column(db.String(30), default='general')
    property_id = db.Column(db.Integer, db.ForeignKey('properties.id'), nullable=True)
    property = db.relationship('Property', backref='inquiries')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExchangeRate(db.Model):
    """Stores NGN exchange rates. Rate = how much 1 NGN is worth in that currency."""
    __tablename__ = 'exchange_rates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    currency = db.Column(db.String(10), unique=True, nullable=False)  # 'USD', 'GBP'
    rate = db.Column(db.Float, nullable=False)   # e.g. 0.00063 means 1 NGN = $0.00063
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
