import statistics
from flask import (
    render_template, request, jsonify, redirect, url_for,
    flash, current_app, make_response
)
from . import main
from ..models import db, Property, Agent, Inquiry, NewsletterSubscriber, PropertyImage, ExchangeRate
from .forms import InquiryForm, ContactForm, NewsletterForm, ValuationForm


@main.route('/')
def index():
    featured = Property.query.filter_by(is_featured=True, is_published=True)\
        .order_by(Property.created_at.desc()).limit(6).all()
    return render_template('index.html', featured=featured)


@main.route('/properties')
def listings():
    city = request.args.get('city', '')
    prop_type = request.args.get('type', '')
    listing_type = request.args.get('listing', '')
    budget = request.args.get('budget', '')
    bedrooms = request.args.get('bedrooms', '')
    sort = request.args.get('sort', 'latest')
    page = request.args.get('page', 1, type=int)

    query = Property.query.filter_by(is_published=True)

    if city:
        query = query.filter(Property.city == city)
    if prop_type:
        query = query.filter(Property.property_type == prop_type)
    if listing_type:
        query = query.filter(Property.listing_type == listing_type)
    if bedrooms:
        if bedrooms == '5':
            query = query.filter(Property.bedrooms >= 5)
        else:
            try:
                query = query.filter(Property.bedrooms == int(bedrooms))
            except ValueError:
                pass
    if budget:
        try:
            max_price = int(budget)
            query = query.filter(Property.price <= max_price)
        except ValueError:
            pass

    if sort == 'price_asc':
        query = query.order_by(Property.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Property.price.desc())
    elif sort == 'most_viewed':
        query = query.order_by(Property.views.desc())
    else:
        query = query.order_by(Property.created_at.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)
    properties = pagination.items

    # Get distinct cities for filter
    cities = db.session.query(Property.city).filter(Property.is_published == True)\
        .distinct().order_by(Property.city).all()
    cities = [c[0] for c in cities if c[0]]

    return render_template('listings.html',
        properties=properties,
        pagination=pagination,
        cities=cities,
        current_city=city,
        current_type=prop_type,
        current_listing=listing_type,
        current_budget=budget,
        current_bedrooms=bedrooms,
        current_sort=sort
    )


@main.route('/properties/<slug>')
def property_detail(slug):
    prop = Property.query.filter_by(slug=slug, is_published=True).first_or_404()
    prop.views = (prop.views or 0) + 1
    db.session.commit()

    similar = Property.query.filter(
        Property.is_published == True,
        Property.id != prop.id,
        db.or_(Property.city == prop.city, Property.property_type == prop.property_type)
    ).limit(3).all()

    form = InquiryForm()
    return render_template('property_detail.html', prop=prop, similar=similar, form=form)


@main.route('/properties/<slug>/inquire', methods=['POST'])
def property_inquire(slug):
    prop = Property.query.filter_by(slug=slug, is_published=True).first_or_404()
    form = InquiryForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=form.message.data,
            inquiry_type='property',
            property_id=prop.id
        )
        db.session.add(inquiry)
        db.session.commit()
        return jsonify({'success': True, 'message': "Thank you! We'll be in touch shortly."})
    return jsonify({'success': False, 'errors': form.errors}), 400


@main.route('/about')
def about():
    agents = Agent.query.filter_by(is_active=True).all()
    return render_template('about.html', agents=agents)


@main.route('/contact')
def contact():
    form = ContactForm()
    return render_template('contact.html', form=form)


@main.route('/contact/submit', methods=['POST'])
def contact_submit():
    form = ContactForm()
    if form.validate_on_submit():
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            message=f"Subject: {form.subject.data}\n\n{form.message.data}",
            inquiry_type='general'
        )
        db.session.add(inquiry)
        db.session.commit()
        flash("Thank you for reaching out. We'll be in touch within 24 hours.", 'success')
        return redirect(url_for('main.contact'))
    for field, errors in form.errors.items():
        for error in errors:
            flash(f'{error}', 'error')
    return redirect(url_for('main.contact'))


@main.route('/agents')
def agents():
    all_agents = Agent.query.filter_by(is_active=True).all()
    return render_template('agents.html', agents=all_agents)


@main.route('/shortlist')
def shortlist():
    whatsapp_number = current_app.config.get('WHATSAPP_NUMBER', '2348000000000')
    return render_template('shortlist.html', whatsapp_number=whatsapp_number)


@main.route('/api/properties/batch')
def properties_batch():
    ids_param = request.args.get('ids', '')
    if not ids_param:
        return jsonify([])
    try:
        ids = [int(i) for i in ids_param.split(',') if i.strip().isdigit()]
    except ValueError:
        return jsonify([])

    properties = Property.query.filter(
        Property.id.in_(ids),
        Property.is_published == True
    ).all()

    result = []
    for p in properties:
        cover = p.cover_image
        if cover:
            fn = cover.filename
            if fn.startswith('http'):
                img_url = fn
            else:
                img_url = '/static/uploads/properties/' + fn
        else:
            img_url = None

        result.append({
            'id': p.id,
            'title': p.title,
            'ref_code': p.ref_code,
            'slug': p.slug,
            'price': p.price,
            'price_formatted': '₦ {:,}'.format(p.price),
            'price_period': p.price_period or '',
            'city': p.city,
            'state': p.state,
            'bedrooms': p.bedrooms,
            'bathrooms': p.bathrooms,
            'area_sqm': p.area_sqm,
            'listing_type': p.listing_type,
            'property_type': p.property_type,
            'cover_image_url': img_url,
        })

    return jsonify(result)


@main.route('/valuation', methods=['GET', 'POST'])
def valuation():
    form = ValuationForm()
    if request.method == 'POST':
        # Read directly from request.form to avoid CSRF/coercion issues with AJAX
        city          = request.form.get('city', '').strip()
        prop_type     = request.form.get('property_type', '').strip()
        bedrooms_str  = request.form.get('bedrooms', '').strip()
        listing_purpose = request.form.get('listing_purpose', '').strip()
        your_name     = request.form.get('your_name', '').strip()
        your_phone    = request.form.get('your_phone', '').strip()

        # Basic server-side validation
        missing = []
        if not city:          missing.append('City')
        if not prop_type:     missing.append('Property Type')
        if not listing_purpose: missing.append('Listing Purpose')
        if not your_name:     missing.append('Your Name')
        if not your_phone:    missing.append('Your Phone')

        if missing:
            return jsonify({
                'success': False,
                'message': f"Please fill in: {', '.join(missing)}"
            }), 400

        query = Property.query.filter(
            Property.city == city,
            Property.property_type == prop_type,
            Property.listing_type == listing_purpose,
            Property.is_published == True
        )

        if bedrooms_str and bedrooms_str.isdigit():
            beds = int(bedrooms_str)
            if beds >= 5:
                query = query.filter(Property.bedrooms >= 5)
            else:
                query = query.filter(Property.bedrooms == beds)

        matches = query.all()
        prices  = [p.price for p in matches]

        if len(prices) >= 3:
            low   = (min(prices) // 1_000_000) * 1_000_000
            high  = ((max(prices) + 999_999) // 1_000_000) * 1_000_000
            avg   = round(statistics.mean(prices) / 500_000) * 500_000
            match_count = len(prices)
        elif 1 <= len(prices) < 3:
            # Widen: remove bedroom filter, keep city + type
            wider = Property.query.filter(
                Property.city == city,
                Property.property_type == prop_type,
                Property.listing_type == listing_purpose,
                Property.is_published == True
            ).all()
            all_prices = [p.price for p in wider] or prices
            avg_raw    = statistics.mean(all_prices)
            low        = round(avg_raw * 0.80 / 1_000_000) * 1_000_000
            high       = round(avg_raw * 1.20 / 1_000_000) * 1_000_000
            avg        = round(avg_raw / 500_000) * 500_000
            match_count = len(all_prices)
        else:
            # No data — save inquiry and return no_data
            db.session.add(Inquiry(
                name=your_name, email='valuation@request.com',
                phone=your_phone,
                message=f"Valuation request: {city}, {prop_type}, {bedrooms_str} beds",
                inquiry_type='valuation'
            ))
            db.session.commit()
            return jsonify({
                'success': False, 'no_data': True,
                'city': city, 'property_type': prop_type
            })

        db.session.add(Inquiry(
            name=your_name, email='valuation@request.com',
            phone=your_phone,
            message=f"Valuation request: {city}, {prop_type}, {bedrooms_str} beds",
            inquiry_type='valuation'
        ))
        db.session.commit()

        return jsonify({
            'success': True,
            'low': low, 'high': high, 'avg': avg,
            'currency': 'NGN',
            'matches': match_count,
            'city': city,
            'property_type': prop_type,
            'bedrooms': bedrooms_str,
            'disclaimer': f'Based on {match_count} comparable listing{"s" if match_count != 1 else ""}.'
        })

    return render_template('valuation.html', form=form)


@main.route('/api/rates')
def api_rates():
    """Return current exchange rates from DB. Used by JS for live currency toggle."""
    rates = {r.currency: r.rate for r in ExchangeRate.query.all()}
    # Fallback defaults if DB is empty
    if 'USD' not in rates: rates['USD'] = 0.00063
    if 'GBP' not in rates: rates['GBP'] = 0.00050
    rates['NGN'] = 1.0
    # Include last updated timestamp
    latest = ExchangeRate.query.order_by(ExchangeRate.updated_at.desc()).first()
    return jsonify({
        'rates': rates,
        'updated_at': latest.updated_at.isoformat() if latest else None
    })


@main.route('/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    email = request.form.get('email', '').strip()
    if not email or '@' not in email:
        return jsonify({'success': False, 'message': 'Please enter a valid email.'})
    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({'success': True, 'message': "You're already subscribed. Thank you!"})
    subscriber = NewsletterSubscriber(email=email)
    db.session.add(subscriber)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Thank you for subscribing!'})


@main.route('/sitemap.xml')
def sitemap():
    properties = Property.query.filter_by(is_published=True).all()
    urls = [
        {'loc': url_for('main.index', _external=True)},
        {'loc': url_for('main.listings', _external=True)},
        {'loc': url_for('main.about', _external=True)},
        {'loc': url_for('main.contact', _external=True)},
        {'loc': url_for('main.agents', _external=True)},
        {'loc': url_for('main.valuation', _external=True)},
    ]
    for p in properties:
        urls.append({'loc': url_for('main.property_detail', slug=p.slug, _external=True)})

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        xml.append(f'  <url><loc>{u["loc"]}</loc></url>')
    xml.append('</urlset>')

    response = make_response('\n'.join(xml))
    response.headers['Content-Type'] = 'application/xml'
    return response


@main.route('/robots.txt')
def robots():
    content = "User-agent: *\nDisallow: /admin\n"
    response = make_response(content)
    response.headers['Content-Type'] = 'text/plain'
    return response


@main.app_errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404
