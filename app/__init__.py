import os
import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from .models import db, User, Property, PropertyImage, PropertyAmenity, Agent, Inquiry, NewsletterSubscriber, ExchangeRate
from .config import config

login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')

    app = Flask(
        __name__,
        template_folder='../templates',
        static_folder='static'
    )
    app.config.from_object(config.get(config_name, config['default']))

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'properties'), exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access the admin panel.'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Inject current datetime into all templates
    @app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.utcnow()}

    # Custom Jinja2 filters
    @app.template_filter('naira')
    def naira_filter(value):
        return '₦ {:,}'.format(int(value))

    @app.template_filter('short_number')
    def short_number_filter(value):
        if value >= 1_000_000_000:
            return f'{value / 1_000_000_000:.1f}B'
        elif value >= 1_000_000:
            return f'{value / 1_000_000:.1f}M'
        elif value >= 1_000:
            return f'{value / 1_000:.0f}K'
        return str(value)

    # Register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Exempt AJAX-only public endpoints from CSRF
    from .main.routes import (
        valuation, api_rates, properties_batch, property_inquire,
        newsletter_subscribe
    )
    csrf.exempt(valuation)
    csrf.exempt(api_rates)
    csrf.exempt(properties_batch)
    csrf.exempt(property_inquire)
    csrf.exempt(newsletter_subscribe)

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    # Register CLI commands
    register_commands(app)

    return app


def register_commands(app):
    @app.cli.command('seed-db')
    def seed_db():
        """Seed the database with initial data."""
        with app.app_context():
            db.create_all()

            # Admin user
            if not User.query.filter_by(username='admin').first():
                admin = User(username='admin', email='admin@kingmac.com')
                admin.set_password('Kingmac@2024')
                db.session.add(admin)
                click.echo('Created admin user.')

            # Agents
            agents_data = [
                {
                    'name': 'Emeka Okonkwo',
                    'title': 'Senior Property Consultant',
                    'bio': 'With over 10 years in Nigerian real estate, Emeka specializes in luxury residential properties across Lagos and Abuja.',
                    'phone': '+234 801 234 5678',
                    'whatsapp': '2348012345678',
                    'email': 'emeka@kingmac.com',
                    'photo': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80',
                },
                {
                    'name': 'Chidinma Eze',
                    'title': 'Property Investment Advisor',
                    'bio': 'Chidinma is our diaspora specialist, helping UK and US-based Nigerians invest confidently in the Nigerian property market.',
                    'phone': '+234 802 345 6789',
                    'whatsapp': '2348023456789',
                    'email': 'chidinma@kingmac.com',
                    'photo': 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=400&q=80',
                },
                {
                    'name': 'Tunde Adeyemi',
                    'title': 'Commercial Real Estate Lead',
                    'bio': 'Tunde heads our commercial division, advising corporate clients on office spaces, warehouses, and high-yield commercial investments.',
                    'phone': '+234 803 456 7890',
                    'whatsapp': '2348034567890',
                    'email': 'tunde@kingmac.com',
                    'photo': 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=400&q=80',
                },
            ]

            created_agents = []
            for a in agents_data:
                if not Agent.query.filter_by(email=a['email']).first():
                    agent = Agent(**a)
                    db.session.add(agent)
                    created_agents.append(agent)
                else:
                    created_agents.append(Agent.query.filter_by(email=a['email']).first())

            db.session.flush()
            click.echo('Created agents.')

            # Properties
            unsplash_images = [
                'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800&q=80',
                'https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=800&q=80',
                'https://images.unsplash.com/photo-1568605114967-8130f3a36994?w=800&q=80',
                'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=800&q=80',
                'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=800&q=80',
                'https://images.unsplash.com/photo-1583608205776-bfd35f0d9f83?w=800&q=80',
                'https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=800&q=80',
                'https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?w=800&q=80',
                'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=800&q=80',
                'https://images.unsplash.com/photo-1570129477492-45c003edd2be?w=800&q=80',
                'https://images.unsplash.com/photo-1484154218962-a197022b5858?w=800&q=80',
                'https://images.unsplash.com/photo-1556020685-ae41abfc9365?w=800&q=80',
            ]

            properties_data = [
                {
                    'title': 'Luxury 4-Bedroom Penthouse in Ikoyi',
                    'slug': 'luxury-4-bedroom-penthouse-ikoyi',
                    'description': 'A stunning penthouse apartment nestled in the heart of Ikoyi, offering panoramic views of Lagos lagoon. This exceptional property features floor-to-ceiling windows, a private rooftop terrace, and world-class finishes throughout. Perfect for discerning buyers who demand the very best.',
                    'property_type': 'Penthouse',
                    'listing_type': 'For Sale',
                    'price': 450000000,
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': '14 Bourdillon Road, Ikoyi, Lagos',
                    'latitude': 6.4550,
                    'longitude': 3.4318,
                    'bedrooms': 4,
                    'bathrooms': 4,
                    'toilets': 5,
                    'parking_spaces': 3,
                    'area_sqm': 580,
                    'is_featured': True,
                    'amenities': ['Swimming Pool', 'Generator', 'CCTV', '24/7 Security', 'Gym', 'Rooftop Terrace', 'Air Conditioning', 'Smart Home', 'Waterfront', 'Serviced', 'Gated Estate', 'Fitted Kitchen'],
                    'img_index': 0,
                    'agent_index': 0,
                },
                {
                    'title': 'Elegant 3-Bedroom Terrace in Lekki Phase 1',
                    'slug': 'elegant-3-bedroom-terrace-lekki-phase-1',
                    'description': 'A beautifully designed terrace house in one of Lekki\'s most sought-after estates. The property boasts a spacious open-plan living area, modern kitchen with island, and a private courtyard garden.',
                    'property_type': 'Terrace',
                    'listing_type': 'For Sale',
                    'price': 180000000,
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Paradise Estate, Lekki Phase 1, Lagos',
                    'latitude': 6.4360,
                    'longitude': 3.4742,
                    'bedrooms': 3,
                    'bathrooms': 3,
                    'toilets': 4,
                    'parking_spaces': 2,
                    'area_sqm': 280,
                    'is_featured': True,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Gated Estate', 'Fitted Kitchen', 'Backup Water'],
                    'img_index': 1,
                    'agent_index': 0,
                },
                {
                    'title': 'Modern 5-Bedroom Detached Duplex in Maitama',
                    'slug': 'modern-5-bedroom-detached-duplex-maitama',
                    'description': 'An architectural masterpiece in Abuja\'s premium Maitama district. This expansive duplex sits on a 1,200sqm plot with manicured gardens, a private swimming pool, and a fully equipped boys\' quarters.',
                    'property_type': 'Duplex',
                    'listing_type': 'For Sale',
                    'price': 620000000,
                    'city': 'Abuja',
                    'state': 'FCT',
                    'address': '7 Suleiman Barau Street, Maitama, Abuja',
                    'latitude': 9.0833,
                    'longitude': 7.4833,
                    'bedrooms': 5,
                    'bathrooms': 5,
                    'toilets': 6,
                    'parking_spaces': 4,
                    'area_sqm': 700,
                    'is_featured': True,
                    'amenities': ['Swimming Pool', 'Generator', 'CCTV', '24/7 Security', 'Boys Quarters', 'Air Conditioning', 'Smart Home', 'Gated Estate', 'Fitted Kitchen', 'Backup Water', 'Intercom'],
                    'img_index': 2,
                    'agent_index': 1,
                },
                {
                    'title': 'Contemporary 2-Bedroom Apartment in Wuse II',
                    'slug': 'contemporary-2-bedroom-apartment-wuse-ii',
                    'description': 'A sleek, move-in ready apartment in the vibrant Wuse II neighbourhood of Abuja. Featuring high-end finishes, ample natural light, and access to premium estate facilities.',
                    'property_type': 'Apartment',
                    'listing_type': 'For Rent',
                    'price': 3500000,
                    'price_period': 'per month',
                    'city': 'Abuja',
                    'state': 'FCT',
                    'address': 'Emerald Court, Wuse II, Abuja',
                    'latitude': 9.0711,
                    'longitude': 7.4891,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'toilets': 3,
                    'parking_spaces': 1,
                    'area_sqm': 145,
                    'is_featured': False,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Air Conditioning', 'Fitted Kitchen', 'Backup Water'],
                    'img_index': 3,
                    'agent_index': 1,
                },
                {
                    'title': 'Grand 6-Bedroom Mansion in GRA, Port Harcourt',
                    'slug': 'grand-6-bedroom-mansion-gra-port-harcourt',
                    'description': 'A palatial residence in Port Harcourt\'s prestigious Government Reserved Area. This grand mansion features a home theatre, indoor gym, wine cellar, and a sprawling outdoor entertainment space with a resort-style pool.',
                    'property_type': 'Detached',
                    'listing_type': 'For Sale',
                    'price': 800000000,
                    'city': 'Port Harcourt',
                    'state': 'Rivers',
                    'address': 'Old GRA, Port Harcourt, Rivers State',
                    'latitude': 4.8156,
                    'longitude': 7.0498,
                    'bedrooms': 6,
                    'bathrooms': 6,
                    'toilets': 8,
                    'parking_spaces': 6,
                    'area_sqm': 1200,
                    'is_featured': True,
                    'amenities': ['Swimming Pool', 'Generator', 'CCTV', '24/7 Security', 'Gym', 'Boys Quarters', 'Air Conditioning', 'Smart Home', 'Gated Estate', 'Fitted Kitchen', 'Backup Water', 'Intercom'],
                    'img_index': 4,
                    'agent_index': 2,
                },
                {
                    'title': 'Prime Commercial Space in Victoria Island',
                    'slug': 'prime-commercial-space-victoria-island',
                    'description': 'A prestigious Grade-A office space in Lagos\' financial district. This fully serviced commercial property is ideal for corporate headquarters, banking institutions, or premium retail operations.',
                    'property_type': 'Commercial',
                    'listing_type': 'For Rent',
                    'price': 25000000,
                    'price_period': 'per month',
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Adeola Odeku Street, Victoria Island, Lagos',
                    'latitude': 6.4281,
                    'longitude': 3.4219,
                    'bedrooms': 0,
                    'bathrooms': 4,
                    'toilets': 6,
                    'parking_spaces': 20,
                    'area_sqm': 1500,
                    'is_featured': False,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Air Conditioning', 'Smart Home', 'Serviced', 'Backup Water', 'Intercom'],
                    'img_index': 5,
                    'agent_index': 2,
                },
                {
                    'title': 'Stylish 3-Bedroom Semi-Detached in Asokoro',
                    'slug': 'stylish-3-bedroom-semi-detached-asokoro',
                    'description': 'Located in the exclusive Asokoro district of Abuja, this beautifully finished semi-detached home offers a perfect blend of luxury and practicality for the modern family.',
                    'property_type': 'Semi-Detached',
                    'listing_type': 'For Sale',
                    'price': 145000000,
                    'city': 'Abuja',
                    'state': 'FCT',
                    'address': 'Diamond Estate, Asokoro, Abuja',
                    'latitude': 9.0579,
                    'longitude': 7.5264,
                    'bedrooms': 3,
                    'bathrooms': 3,
                    'toilets': 4,
                    'parking_spaces': 2,
                    'area_sqm': 320,
                    'is_featured': False,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Gated Estate', 'Fitted Kitchen', 'Backup Water'],
                    'img_index': 6,
                    'agent_index': 1,
                },
                {
                    'title': 'Luxury Short-Let Apartment in Oniru, Lekki',
                    'slug': 'luxury-short-let-apartment-oniru-lekki',
                    'description': 'A premium short-let apartment perfectly designed for executives and high-value guests. Fully furnished with hotel-grade amenities, smart TV, high-speed WiFi, and dedicated concierge service.',
                    'property_type': 'Apartment',
                    'listing_type': 'Short Let',
                    'price': 150000,
                    'price_period': 'per night',
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Oniru Estate, Lekki, Lagos',
                    'latitude': 6.4269,
                    'longitude': 3.4692,
                    'bedrooms': 2,
                    'bathrooms': 2,
                    'toilets': 2,
                    'parking_spaces': 1,
                    'area_sqm': 120,
                    'is_featured': True,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Gym', 'Air Conditioning', 'Smart Home', 'Waterfront', 'Serviced', 'Fitted Kitchen', 'Backup Water'],
                    'img_index': 7,
                    'agent_index': 0,
                },
                {
                    'title': 'Expansive Land Plot in Ajah, Lagos',
                    'slug': 'expansive-land-plot-ajah-lagos',
                    'description': 'A rare opportunity to acquire a prime 2,000sqm land plot in the rapidly developing Ajah corridor. Situated within a gated estate with all documents intact — C of O, survey plan, and governor\'s consent.',
                    'property_type': 'Land',
                    'listing_type': 'For Sale',
                    'price': 85000000,
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Pinnacle Estate, Ajah, Lagos',
                    'latitude': 6.4655,
                    'longitude': 3.5822,
                    'bedrooms': 0,
                    'bathrooms': 0,
                    'toilets': 0,
                    'parking_spaces': 0,
                    'area_sqm': 2000,
                    'is_featured': False,
                    'amenities': ['Gated Estate', '24/7 Security', 'CCTV'],
                    'img_index': 8,
                    'agent_index': 0,
                },
                {
                    'title': '4-Bedroom Terrace in Omole Phase II, Ikeja',
                    'slug': '4-bedroom-terrace-omole-phase-ii-ikeja',
                    'description': 'A beautifully maintained terrace house in the serene and family-friendly Omole Phase II estate. This property is ideal for families seeking quality living in a secure, well-managed community close to major expressways.',
                    'property_type': 'Terrace',
                    'listing_type': 'For Sale',
                    'price': 120000000,
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Omole Phase II Estate, Ikeja, Lagos',
                    'latitude': 6.6074,
                    'longitude': 3.3580,
                    'bedrooms': 4,
                    'bathrooms': 4,
                    'toilets': 5,
                    'parking_spaces': 2,
                    'area_sqm': 340,
                    'is_featured': False,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Boys Quarters', 'Gated Estate', 'Fitted Kitchen', 'Backup Water'],
                    'img_index': 9,
                    'agent_index': 0,
                },
                {
                    'title': 'Premium 3-Bedroom Apartment in GRA, Port Harcourt',
                    'slug': 'premium-3-bedroom-apartment-gra-port-harcourt',
                    'description': 'A sophisticated apartment in Port Harcourt\'s prestigious GRA, designed for executives and professionals. Features imported marble finishes, a private balcony, and access to estate facilities.',
                    'property_type': 'Apartment',
                    'listing_type': 'For Rent',
                    'price': 4500000,
                    'price_period': 'per month',
                    'city': 'Port Harcourt',
                    'state': 'Rivers',
                    'address': 'New GRA, Port Harcourt, Rivers State',
                    'latitude': 4.8242,
                    'longitude': 7.0414,
                    'bedrooms': 3,
                    'bathrooms': 3,
                    'toilets': 4,
                    'parking_spaces': 2,
                    'area_sqm': 210,
                    'is_featured': False,
                    'amenities': ['Generator', 'CCTV', '24/7 Security', 'Air Conditioning', 'Gated Estate', 'Fitted Kitchen', 'Backup Water', 'Intercom'],
                    'img_index': 10,
                    'agent_index': 2,
                },
                {
                    'title': 'Waterfront 5-Bedroom Detached in Banana Island',
                    'slug': 'waterfront-5-bedroom-detached-banana-island',
                    'description': 'The crown jewel of Lagos real estate — a breathtaking waterfront estate on Banana Island. This ultra-luxury property offers unobstructed views of Lagos harbour, a private jetty, infinity pool, and the finest international finishes.',
                    'property_type': 'Detached',
                    'listing_type': 'For Sale',
                    'price': 2500000000,
                    'city': 'Lagos',
                    'state': 'Lagos',
                    'address': 'Banana Island, Ikoyi, Lagos',
                    'latitude': 6.4725,
                    'longitude': 3.4386,
                    'bedrooms': 5,
                    'bathrooms': 5,
                    'toilets': 7,
                    'parking_spaces': 6,
                    'area_sqm': 1800,
                    'is_featured': True,
                    'amenities': ['Swimming Pool', 'Generator', 'CCTV', '24/7 Security', 'Gym', 'Boys Quarters', 'Rooftop Terrace', 'Air Conditioning', 'Smart Home', 'Waterfront', 'Serviced', 'Gated Estate', 'Fitted Kitchen', 'Backup Water', 'Intercom'],
                    'img_index': 11,
                    'agent_index': 0,
                },
            ]

            for i, p_data in enumerate(properties_data):
                if not Property.query.filter_by(slug=p_data['slug']).first():
                    amenities = p_data.pop('amenities')
                    img_index = p_data.pop('img_index')
                    agent_index = p_data.pop('agent_index')

                    # Assign a temporary ref_code so NOT NULL constraint passes on flush
                    p_data['ref_code'] = 'KMP-TEMP'
                    prop = Property(**p_data)
                    if agent_index < len(created_agents):
                        prop.agent = created_agents[agent_index]
                    db.session.add(prop)
                    db.session.flush()

                    # Now ID is known — assign the real ref_code
                    prop.ref_code = prop.generate_ref_code()

                    # Add cover image (using Unsplash URL stored as filename for seed)
                    img = PropertyImage(
                        property_id=prop.id,
                        filename=unsplash_images[img_index],
                        is_cover=True,
                        sort_order=0
                    )
                    db.session.add(img)

                    for amenity_name in amenities:
                        amenity = PropertyAmenity(property_id=prop.id, name=amenity_name)
                        db.session.add(amenity)

            db.session.commit()
            click.echo('Seeded 12 properties with images and amenities.')

            # Seed initial exchange rates
            for currency, rate in [('USD', 0.00063), ('GBP', 0.00050)]:
                if not ExchangeRate.query.filter_by(currency=currency).first():
                    db.session.add(ExchangeRate(currency=currency, rate=rate))
            db.session.commit()
            click.echo('Seeded exchange rates (USD, GBP).')
            click.echo('Done! Admin login: admin / Kingmac@2024')
