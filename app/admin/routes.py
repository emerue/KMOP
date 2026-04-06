import os
import io
import csv
import uuid
from flask import (
    render_template, redirect, url_for, flash, request,
    jsonify, current_app, send_file, make_response
)
from flask_login import login_required, current_user
from PIL import Image
from . import admin
from ..models import db, Property, PropertyImage, PropertyAmenity, Agent, Inquiry, NewsletterSubscriber, ExchangeRate
from .forms import PropertyForm, AgentForm, AMENITIES_LIST


def save_image(file_obj, folder, size=(1200, 900), square=False):
    """Process an uploaded image. Returns Cloudinary URL (production) or local filename (dev)."""
    import io as _io
    img = Image.open(file_obj)
    img = img.convert('RGB')

    if square:
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        img = img.resize(size, Image.LANCZOS)
    else:
        img.thumbnail(size, Image.LANCZOS)

    if os.environ.get('CLOUDINARY_URL'):
        # Upload directly to Cloudinary — no local disk write needed
        import cloudinary.uploader
        buf = _io.BytesIO()
        img.save(buf, 'JPEG', quality=85, optimize=True)
        buf.seek(0)
        result = cloudinary.uploader.upload(
            buf,
            resource_type='image',
            format='jpg',
            quality=85,
            folder='kingmac'
        )
        return result['secure_url']
    else:
        os.makedirs(folder, exist_ok=True)
        filename = uuid.uuid4().hex[:12] + '.jpg'
        filepath = os.path.join(folder, filename)
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        return filename


@admin.route('/dashboard')
@login_required
def dashboard():
    total_props = Property.query.count()
    published_props = Property.query.filter_by(is_published=True).count()
    unread_inquiries = Inquiry.query.filter_by(is_read=False).count()
    total_subscribers = NewsletterSubscriber.query.count()
    recent_inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
        total_props=total_props,
        published_props=published_props,
        unread_inquiries=unread_inquiries,
        total_subscribers=total_subscribers,
        recent_inquiries=recent_inquiries
    )


# ─── PROPERTIES ───────────────────────────────────────────────────────────────

@admin.route('/properties')
@login_required
def properties():
    all_props = Property.query.order_by(Property.created_at.desc()).all()
    return render_template('admin/properties.html', properties=all_props)


@admin.route('/properties/new', methods=['GET', 'POST'])
@login_required
def property_new():
    form = PropertyForm()
    agents = Agent.query.filter_by(is_active=True).all()
    form.agent_id.choices = [(0, '— No Agent —')] + [(a.id, a.name) for a in agents]

    if form.validate_on_submit():
        prop = Property(
            title=form.title.data,
            slug=form.slug.data,
            description=form.description.data,
            property_type=form.property_type.data,
            listing_type=form.listing_type.data,
            price=form.price.data,
            price_period=form.price_period.data or None,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            latitude=form.latitude.data,
            longitude=form.longitude.data,
            bedrooms=form.bedrooms.data,
            bathrooms=form.bathrooms.data,
            toilets=form.toilets.data,
            parking_spaces=form.parking_spaces.data,
            area_sqm=form.area_sqm.data,
            is_featured=form.is_featured.data,
            is_published=form.is_published.data,
        )
        if form.agent_id.data and form.agent_id.data != 0:
            prop.agent_id = form.agent_id.data

        db.session.add(prop)
        db.session.flush()
        prop.ref_code = prop.generate_ref_code()

        # Amenities
        amenities_selected = request.form.getlist('amenities')
        for name in amenities_selected:
            db.session.add(PropertyAmenity(property_id=prop.id, name=name))

        db.session.commit()
        flash('Property created. Now add images.', 'success')
        return redirect(url_for('admin.property_media', property_id=prop.id))

    return render_template('admin/property_form.html',
        form=form, prop=None, amenities_list=AMENITIES_LIST, selected_amenities=[])


@admin.route('/properties/<int:property_id>/edit', methods=['GET', 'POST'])
@login_required
def property_edit(property_id):
    prop = Property.query.get_or_404(property_id)
    form = PropertyForm(obj=prop)
    agents = Agent.query.filter_by(is_active=True).all()
    form.agent_id.choices = [(0, '— No Agent —')] + [(a.id, a.name) for a in agents]
    selected_amenities = [a.name for a in prop.amenities]

    if form.validate_on_submit():
        prop.title = form.title.data
        prop.slug = form.slug.data
        prop.description = form.description.data
        prop.property_type = form.property_type.data
        prop.listing_type = form.listing_type.data
        prop.price = form.price.data
        prop.price_period = form.price_period.data or None
        prop.city = form.city.data
        prop.state = form.state.data
        prop.address = form.address.data
        prop.latitude = form.latitude.data
        prop.longitude = form.longitude.data
        prop.bedrooms = form.bedrooms.data
        prop.bathrooms = form.bathrooms.data
        prop.toilets = form.toilets.data
        prop.parking_spaces = form.parking_spaces.data
        prop.area_sqm = form.area_sqm.data
        prop.is_featured = form.is_featured.data
        prop.is_published = form.is_published.data
        prop.agent_id = form.agent_id.data if form.agent_id.data != 0 else None

        # Update amenities
        PropertyAmenity.query.filter_by(property_id=prop.id).delete()
        for name in request.form.getlist('amenities'):
            db.session.add(PropertyAmenity(property_id=prop.id, name=name))

        db.session.commit()
        flash('Property updated successfully.', 'success')
        return redirect(url_for('admin.properties'))

    return render_template('admin/property_form.html',
        form=form, prop=prop, amenities_list=AMENITIES_LIST,
        selected_amenities=selected_amenities)


@admin.route('/properties/<int:property_id>/delete', methods=['POST'])
@login_required
def property_delete(property_id):
    prop = Property.query.get_or_404(property_id)
    upload_folder = current_app.config['UPLOAD_FOLDER']
    for img in prop.images:
        if not img.filename.startswith('http'):
            try:
                os.remove(os.path.join(upload_folder, img.filename))
            except FileNotFoundError:
                pass
    db.session.delete(prop)
    db.session.commit()
    flash('Property deleted.', 'success')
    return redirect(url_for('admin.properties'))


@admin.route('/properties/<int:property_id>/toggle-publish', methods=['POST'])
@login_required
def property_toggle_publish(property_id):
    prop = Property.query.get_or_404(property_id)
    prop.is_published = not prop.is_published
    db.session.commit()
    return jsonify({'published': prop.is_published})


@admin.route('/properties/<int:property_id>/toggle-featured', methods=['POST'])
@login_required
def property_toggle_featured(property_id):
    prop = Property.query.get_or_404(property_id)
    prop.is_featured = not prop.is_featured
    db.session.commit()
    return jsonify({'featured': prop.is_featured})


# ─── MEDIA MANAGER ────────────────────────────────────────────────────────────

@admin.route('/properties/<int:property_id>/media')
@login_required
def property_media(property_id):
    prop = Property.query.get_or_404(property_id)
    return render_template('admin/property_media.html', prop=prop)


@admin.route('/properties/<int:property_id>/media/upload', methods=['POST'])
@login_required
def media_upload(property_id):
    prop = Property.query.get_or_404(property_id)
    files = request.files.getlist('images')
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)

    uploaded = []
    for file in files:
        if not file or not file.filename:
            continue
        allowed = {'jpg', 'jpeg', 'png', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower()
        if ext not in allowed:
            continue
        try:
            filename = save_image(file, upload_folder, size=(1200, 900))
            is_cover = len(prop.images) == 0
            max_order = db.session.query(db.func.max(PropertyImage.sort_order))\
                .filter_by(property_id=prop.id).scalar() or 0
            img = PropertyImage(
                property_id=prop.id,
                filename=filename,
                is_cover=is_cover,
                sort_order=max_order + 1
            )
            db.session.add(img)
            db.session.flush()
            uploaded.append({
                'id': img.id,
                'filename': filename,
                'url': filename if filename.startswith('http') else '/static/uploads/properties/' + filename,
                'is_cover': is_cover,
                'sort_order': img.sort_order,
            })
        except Exception as e:
            continue

    db.session.commit()
    return jsonify({'success': True, 'images': uploaded})


@admin.route('/properties/<int:property_id>/media/reorder', methods=['POST'])
@login_required
def media_reorder(property_id):
    data = request.get_json()
    order = data.get('order', [])
    for i, img_id in enumerate(order):
        img = PropertyImage.query.get(img_id)
        if img and img.property_id == property_id:
            img.sort_order = i
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/properties/<int:property_id>/media/<int:img_id>/set-cover', methods=['POST'])
@login_required
def media_set_cover(property_id, img_id):
    PropertyImage.query.filter_by(property_id=property_id).update({'is_cover': False})
    img = PropertyImage.query.get_or_404(img_id)
    if img.property_id != property_id:
        return jsonify({'success': False}), 403
    img.is_cover = True
    db.session.commit()
    return jsonify({'success': True, 'img_id': img_id})


@admin.route('/properties/<int:property_id>/media/<int:img_id>/delete', methods=['POST'])
@login_required
def media_delete(property_id, img_id):
    img = PropertyImage.query.get_or_404(img_id)
    if img.property_id != property_id:
        return jsonify({'success': False}), 403

    upload_folder = current_app.config['UPLOAD_FOLDER']
    if not img.filename.startswith('http'):
        try:
            os.remove(os.path.join(upload_folder, img.filename))
        except FileNotFoundError:
            pass

    was_cover = img.is_cover
    db.session.delete(img)
    db.session.flush()

    # If deleted was cover, set first remaining as cover
    if was_cover:
        remaining = PropertyImage.query.filter_by(property_id=property_id)\
            .order_by(PropertyImage.sort_order).first()
        if remaining:
            remaining.is_cover = True

    db.session.commit()
    return jsonify({'success': True})


# ─── INQUIRIES ────────────────────────────────────────────────────────────────

@admin.route('/inquiries')
@login_required
def inquiries():
    filter_type = request.args.get('filter', 'all')
    query = Inquiry.query

    if filter_type == 'unread':
        query = query.filter_by(is_read=False)
    elif filter_type == 'property':
        query = query.filter(Inquiry.property_id != None)
    elif filter_type == 'general':
        query = query.filter_by(inquiry_type='general')

    all_inquiries = query.order_by(Inquiry.created_at.desc()).all()
    unread_count = Inquiry.query.filter_by(is_read=False).count()
    return render_template('admin/inquiries.html',
        inquiries=all_inquiries, unread_count=unread_count, current_filter=filter_type)


@admin.route('/inquiries/<int:inquiry_id>/mark-read', methods=['POST'])
@login_required
def inquiry_mark_read(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    inquiry.is_read = True
    db.session.commit()
    return jsonify({'success': True})


@admin.route('/inquiries/<int:inquiry_id>/delete', methods=['POST'])
@login_required
def inquiry_delete(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    flash('Inquiry deleted.', 'success')
    return redirect(url_for('admin.inquiries'))


# ─── AGENTS ───────────────────────────────────────────────────────────────────

@admin.route('/agents')
@login_required
def agents():
    all_agents = Agent.query.order_by(Agent.name).all()
    return render_template('admin/agents.html', agents=all_agents)


@admin.route('/agents/new', methods=['GET', 'POST'])
@login_required
def agent_new():
    form = AgentForm()
    if form.validate_on_submit():
        agent = Agent(
            name=form.name.data,
            title=form.title.data,
            bio=form.bio.data,
            phone=form.phone.data,
            whatsapp=form.whatsapp.data,
            email=form.email.data,
            is_active=form.is_active.data,
        )
        if form.photo.data:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            agent.photo = save_image(form.photo.data, upload_folder,
                                     size=(400, 400), square=True)
        db.session.add(agent)
        db.session.commit()
        flash('Agent created.', 'success')
        return redirect(url_for('admin.agents'))
    return render_template('admin/agent_form.html', form=form, agent=None)


@admin.route('/agents/<int:agent_id>/edit', methods=['GET', 'POST'])
@login_required
def agent_edit(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    form = AgentForm(obj=agent)
    if form.validate_on_submit():
        agent.name = form.name.data
        agent.title = form.title.data
        agent.bio = form.bio.data
        agent.phone = form.phone.data
        agent.whatsapp = form.whatsapp.data
        agent.email = form.email.data
        agent.is_active = form.is_active.data
        if form.photo.data and form.photo.data.filename:
            upload_folder = current_app.config['UPLOAD_FOLDER']
            agent.photo = save_image(form.photo.data, upload_folder,
                                     size=(400, 400), square=True)
        db.session.commit()
        flash('Agent updated.', 'success')
        return redirect(url_for('admin.agents'))
    return render_template('admin/agent_form.html', form=form, agent=agent)


@admin.route('/agents/<int:agent_id>/delete', methods=['POST'])
@login_required
def agent_delete(agent_id):
    agent = Agent.query.get_or_404(agent_id)
    if agent.photo and not agent.photo.startswith('http'):
        upload_folder = current_app.config['UPLOAD_FOLDER']
        try:
            os.remove(os.path.join(upload_folder, agent.photo))
        except FileNotFoundError:
            pass
    db.session.delete(agent)
    db.session.commit()
    flash('Agent deleted.', 'success')
    return redirect(url_for('admin.agents'))


# ─── SUBSCRIBERS ──────────────────────────────────────────────────────────────

@admin.route('/subscribers')
@login_required
def subscribers():
    all_subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    return render_template('admin/subscribers.html', subscribers=all_subs)


@admin.route('/subscribers/export')
@login_required
def subscribers_export():
    all_subs = NewsletterSubscriber.query.order_by(NewsletterSubscriber.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Email', 'Signup Date'])
    for sub in all_subs:
        writer.writerow([sub.email, sub.created_at.strftime('%Y-%m-%d %H:%M')])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=subscribers.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response


# ─── EXCHANGE RATES ───────────────────────────────────────────────────────────

@admin.route('/rates', methods=['GET', 'POST'])
@login_required
def rates():
    usd = ExchangeRate.query.filter_by(currency='USD').first()
    gbp = ExchangeRate.query.filter_by(currency='GBP').first()

    if request.method == 'POST':
        action = request.form.get('action', 'save')

        if action == 'refresh':
            # Fetch live rates from open.er-api.com (free, no key needed)
            try:
                import urllib.request, json as _json
                with urllib.request.urlopen(
                    'https://open.er-api.com/v6/latest/NGN', timeout=8
                ) as resp:
                    data = _json.loads(resp.read().decode())
                if data.get('result') == 'success':
                    live_usd = data['rates'].get('USD')
                    live_gbp = data['rates'].get('GBP')
                    if live_usd:
                        if not usd:
                            usd = ExchangeRate(currency='USD', rate=live_usd)
                            db.session.add(usd)
                        else:
                            usd.rate = live_usd
                    if live_gbp:
                        if not gbp:
                            gbp = ExchangeRate(currency='GBP', rate=live_gbp)
                            db.session.add(gbp)
                        else:
                            gbp.rate = live_gbp
                    db.session.commit()
                    flash('Exchange rates refreshed from live data.', 'success')
                else:
                    flash('Live rate fetch returned an unexpected response.', 'error')
            except Exception as e:
                flash(f'Could not fetch live rates: {e}', 'error')
        else:
            # Manual save
            try:
                usd_val = float(request.form.get('usd_rate', '').replace(',', '.'))
                gbp_val = float(request.form.get('gbp_rate', '').replace(',', '.'))
                if not usd:
                    usd = ExchangeRate(currency='USD', rate=usd_val)
                    db.session.add(usd)
                else:
                    usd.rate = usd_val
                if not gbp:
                    gbp = ExchangeRate(currency='GBP', rate=gbp_val)
                    db.session.add(gbp)
                else:
                    gbp.rate = gbp_val
                db.session.commit()
                flash('Exchange rates updated successfully.', 'success')
            except (ValueError, TypeError):
                flash('Invalid rate values. Enter decimals like 0.00063', 'error')

        return redirect(url_for('admin.rates'))

    return render_template('admin/rates.html', usd=usd, gbp=gbp)
