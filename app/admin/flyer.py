"""
Property Flyer Generator
Generates 4 branded 1080x1080px JPEG slides in memory (no disk writes).
Returns a list of 4 BytesIO objects.
"""

import os
import textwrap
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont


CANVAS = 1080
STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')


def _hex_to_rgb(hex_color):
    h = hex_color.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def _load_font(relative_path, size):
    """Load a TTF font from app/static/. Fall back to Pillow default if missing."""
    full = os.path.join(STATIC_DIR, relative_path)
    try:
        return ImageFont.truetype(full, size)
    except (IOError, OSError):
        return ImageFont.load_default()


def _fetch_image(filename):
    """Fetch a property image and return a Pillow Image (RGB, 1080x1080)."""
    try:
        if filename.startswith('http'):
            import urllib.request
            with urllib.request.urlopen(filename, timeout=10) as resp:
                data = resp.read()
            img = Image.open(BytesIO(data)).convert('RGB')
        else:
            local_path = os.path.join(STATIC_DIR, 'uploads', 'properties', filename)
            img = Image.open(local_path).convert('RGB')

        # Center-crop to square then resize to 1080x1080
        w, h = img.size
        min_dim = min(w, h)
        left = (w - min_dim) // 2
        top = (h - min_dim) // 2
        img = img.crop((left, top, left + min_dim, top + min_dim))
        return img.resize((CANVAS, CANVAS), Image.LANCZOS)
    except Exception:
        # Fallback: dark grey canvas
        img = Image.new('RGB', (CANVAS, CANVAS), (30, 28, 25))
        return img


def _dark_gradient_overlay():
    """Bottom-heavy dark gradient overlay, RGBA."""
    overlay = Image.new('RGBA', (CANVAS, CANVAS), (14, 13, 11, 0))
    draw = ImageDraw.Draw(overlay)
    start_y = 432
    for y in range(start_y, CANVAS):
        alpha = int(235 * ((y - start_y) / (CANVAS - start_y)))
        draw.line([(0, y), (CANVAS, y)], fill=(14, 13, 11, alpha))
    return overlay


def _heavy_overlay(opacity=224):
    """Solid dark overlay for bottom portion of amenities/CTA slides."""
    return Image.new('RGBA', (CANVAS, CANVAS), (14, 13, 11, opacity))


def _draw_rounded_rect(draw, xy, radius, fill):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill)


def _draw_logo(canvas_rgba, brand, height=80, x=40, y=40):
    logo_path = os.path.join(STATIC_DIR, brand['logo_file'])
    try:
        logo = Image.open(logo_path).convert('RGBA')
        ratio = height / logo.height
        new_w = int(logo.width * ratio)
        logo = logo.resize((new_w, height), Image.LANCZOS)
        canvas_rgba.paste(logo, (x, y), logo)
    except Exception:
        pass  # No logo file — skip silently


def _centered_x(draw, text, font, canvas_width=CANVAS):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return (canvas_width - text_width) // 2


def _draw_centered_text(draw, y, text, font, fill):
    x = _centered_x(draw, text, font)
    draw.text((x, y), text, font=font, fill=fill)


def _listing_label(listing_type):
    mapping = {'sale': 'FOR SALE', 'rent': 'FOR RENT', 'shortlet': 'SHORT LET'}
    return mapping.get(listing_type, 'FOR SALE')


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 1 — HERO
# ─────────────────────────────────────────────────────────────────────────────

def _slide1(prop, listing_type, brand, fonts):
    images = prop.images
    img = _fetch_image(images[0].filename if images else '')

    canvas = img.convert('RGBA')
    gradient = _dark_gradient_overlay()
    canvas = Image.alpha_composite(canvas, gradient)

    draw = ImageDraw.Draw(canvas)
    gold = _hex_to_rgb(brand['color_gold'])
    white = _hex_to_rgb(brand['color_text_light'])
    black = _hex_to_rgb(brand['color_black'])

    # Logo
    _draw_logo(canvas, brand, height=80, x=40, y=40)

    # Badge top-right
    label = _listing_label(listing_type)
    badge_font = fonts['body_sm']
    bbox = draw.textbbox((0, 0), label, font=badge_font)
    bw = bbox[2] - bbox[0] + 32
    bh = bbox[3] - bbox[1] + 18
    bx = CANVAS - bw - 40
    _draw_rounded_rect(draw, (bx, 40, bx + bw, 40 + bh), radius=6, fill=gold)
    draw.text((bx + 16, 40 + 9), label, font=badge_font, fill=black)

    # Property title (wrapped, bottom area)
    title = prop.title or ''
    lines = textwrap.wrap(title, width=30)[:2]
    y_title = 780 if len(lines) > 1 else 820
    for i, line in enumerate(lines):
        draw.text((60, y_title + i * 78), line, font=fonts['heading_lg'], fill=gold)

    # Price
    price_str = '₦ {:,}'.format(prop.price)
    if listing_type in ('rent', 'shortlet') and prop.price_period:
        price_str += ' / ' + prop.price_period
    draw.text((60, 920), price_str, font=fonts['body_md'], fill=white)

    # Gold divider
    draw.rectangle([(60, 970), (CANVAS - 60, 971)], fill=gold)

    out = BytesIO()
    canvas.convert('RGB').save(out, 'JPEG', quality=90)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 2 — PROPERTY DETAILS
# ─────────────────────────────────────────────────────────────────────────────

def _slide2(prop, listing_type, brand, fonts):
    images = prop.images
    src = images[1].filename if len(images) > 1 else (images[0].filename if images else '')
    img = _fetch_image(src)

    canvas = img.convert('RGBA')
    gradient = _dark_gradient_overlay()
    canvas = Image.alpha_composite(canvas, gradient)

    draw = ImageDraw.Draw(canvas)
    gold = _hex_to_rgb(brand['color_gold'])
    white = _hex_to_rgb(brand['color_text_light'])
    muted_gold = tuple(int(c * 0.7) for c in gold)

    _draw_logo(canvas, brand, height=80, x=40, y=40)

    # Ref code top-right
    draw.text((CANVAS - 200, 50), prop.ref_code or '', font=fonts['small'], fill=muted_gold)

    # City + State
    location = f"{prop.city or ''}, {prop.state or ''}"
    draw.text((60, 800), location, font=fonts['body_sm'], fill=gold)

    # Stats row
    stats = [
        (str(prop.bedrooms or 0), 'BEDROOMS', 60),
        (str(prop.bathrooms or 0), 'BATHROOMS', 300),
        (f"{prop.area_sqm or 0}sqm", 'TOTAL AREA', 540),
        (prop.city or '', 'LOCATION', 780),
    ]
    for val, label, x in stats:
        draw.text((x, 860), val, font=fonts['heading_md'], fill=white)
        draw.text((x, 920), label, font=fonts['small'], fill=muted_gold)

    draw.rectangle([(60, 970), (CANVAS - 60, 971)], fill=gold)
    name_x = _centered_x(draw, brand['name'], fonts['small'])
    draw.text((name_x, 1040), brand['name'], font=fonts['small'], fill=muted_gold)

    out = BytesIO()
    canvas.convert('RGB').save(out, 'JPEG', quality=90)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 3 — AMENITIES
# ─────────────────────────────────────────────────────────────────────────────

def _slide3(prop, listing_type, brand, fonts):
    images = prop.images
    src = images[2].filename if len(images) > 2 else (images[0].filename if images else '')
    img = _fetch_image(src)

    canvas = img.convert('RGBA')
    # Light gradient on top, heavy dark on bottom
    gradient = _dark_gradient_overlay()
    canvas = Image.alpha_composite(canvas, gradient)
    bottom = Image.new('RGBA', (CANVAS, CANVAS), (14, 13, 11, 0))
    bd = ImageDraw.Draw(bottom)
    bd.rectangle([(0, 400), (CANVAS, CANVAS)], fill=(14, 13, 11, 225))
    canvas = Image.alpha_composite(canvas, bottom)

    draw = ImageDraw.Draw(canvas)
    gold = _hex_to_rgb(brand['color_gold'])
    white = _hex_to_rgb(brand['color_text_light'])
    muted_gold = tuple(int(c * 0.7) for c in gold)

    _draw_logo(canvas, brand, height=80, x=40, y=40)

    draw.text((60, 430), "WHAT'S INCLUDED", font=fonts['body_sm'], fill=gold)
    draw.rectangle([(60, 470), (400, 471)], fill=gold)

    amenities = [a.name for a in prop.amenities[:8]]
    if amenities:
        row_ys = [500, 570, 640, 710]
        for i, name in enumerate(amenities):
            col = 60 if i < 4 else 560
            row_y = row_ys[i % 4]
            draw.text((col, row_y), f'✓  {name}', font=fonts['body_sm'], fill=white)
    else:
        draw.text((60, 520), 'Contact us for full amenity list', font=fonts['body_sm'], fill=white)

    name_x = _centered_x(draw, brand['name'], fonts['small'])
    draw.text((name_x, 1040), brand['name'], font=fonts['small'], fill=muted_gold)

    out = BytesIO()
    canvas.convert('RGB').save(out, 'JPEG', quality=90)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# SLIDE 4 — CTA / CONTACT
# ─────────────────────────────────────────────────────────────────────────────

def _slide4(prop, listing_type, brand, fonts):
    images = prop.images
    src = images[3].filename if len(images) > 3 else (images[0].filename if images else '')
    img = _fetch_image(src)

    canvas = img.convert('RGBA')
    heavy = _heavy_overlay(opacity=230)
    canvas = Image.alpha_composite(canvas, heavy)

    draw = ImageDraw.Draw(canvas)
    gold = _hex_to_rgb(brand['color_gold'])
    white = _hex_to_rgb(brand['color_text_light'])
    muted_white = (200, 195, 185)
    muted_gold = tuple(int(c * 0.65) for c in gold)

    # Gold border frame
    draw.rectangle([(30, 30), (CANVAS - 30, CANVAS - 30)], outline=gold, width=2)

    # Logo centered
    logo_path = os.path.join(STATIC_DIR, brand['logo_file'])
    try:
        logo = Image.open(logo_path).convert('RGBA')
        lh = 100
        lw = int(logo.width * (lh / logo.height))
        logo = logo.resize((lw, lh), Image.LANCZOS)
        lx = (CANVAS - lw) // 2
        canvas.paste(logo, (lx, 120), logo)
    except Exception:
        pass

    # Divider below logo
    div_w = 200
    draw.rectangle([((CANVAS - div_w) // 2, 250), ((CANVAS + div_w) // 2, 251)], fill=gold)

    # Headline
    headline = "Interested in this property?"
    _draw_centered_text(draw, 300, headline, fonts['heading_md'], white)

    # Property title
    title = (prop.title or '')[:40]
    _draw_centered_text(draw, 380, title, fonts['body_sm'], gold)

    # Short divider
    short_w = 120
    draw.rectangle([((CANVAS - short_w) // 2, 430), ((CANVAS + short_w) // 2, 431)], fill=gold)

    # WhatsApp / Phone
    _draw_centered_text(draw, 480, brand['phone'], fonts['heading_sm'], gold)

    # Site URL
    _draw_centered_text(draw, 545, brand['site_url'], fonts['small'], muted_white)

    # Ref code bottom-right
    ref = prop.ref_code or ''
    draw.text((CANVAS - 160, CANVAS - 70), ref, font=fonts['small'], fill=muted_gold)

    out = BytesIO()
    canvas.convert('RGB').save(out, 'JPEG', quality=90)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────────────────────

def generate_property_flyer(prop, listing_type, brand):
    """Generate 4 JPEG slides. Returns list of 4 BytesIO objects."""
    fonts = {
        'heading_lg': _load_font(brand['flyer_font_heading'], 64),
        'heading_md': _load_font(brand['flyer_font_heading'], 48),
        'heading_sm': _load_font(brand['flyer_font_heading'], 36),
        'body_md':    _load_font(brand['flyer_font_body'], 32),
        'body_sm':    _load_font(brand['flyer_font_body'], 24),
        'small':      _load_font(brand['flyer_font_small'], 20),
    }
    return [
        _slide1(prop, listing_type, brand, fonts),
        _slide2(prop, listing_type, brand, fonts),
        _slide3(prop, listing_type, brand, fonts),
        _slide4(prop, listing_type, brand, fonts),
    ]


def generate_caption(prop, listing_type, brand):
    amenity_names = [a.name for a in prop.amenities[:5]]
    amenities_str = ' | '.join(amenity_names) if amenity_names else ''

    type_label = 'FOR SALE' if listing_type == 'sale' else ('SHORT LET' if listing_type == 'shortlet' else 'FOR RENT')
    price_str = '₦ {:,}'.format(prop.price)
    if prop.price_period:
        price_str += f' {prop.price_period}'

    caption = f"""🏡 {prop.title} | {type_label}

💰 {price_str}
🛏 {prop.bedrooms} Beds  🚿 {prop.bathrooms} Baths  📐 {prop.area_sqm} sqm
📍 {prop.city}, {prop.state}
🔖 Ref: {prop.ref_code}
"""
    if amenities_str:
        caption += f'\n✅ {amenities_str}\n'

    city_tag = (prop.city or '').replace(' ', '')
    short_name_tag = brand['short_name'].replace(' ', '')

    caption += f"""
View full details & photos 👇
{brand['site_url']}/properties/{prop.slug}

📞 Call/WhatsApp: {brand['phone']}

─────────────────────────────
💬 DM us to schedule a viewing
🔔 Follow for more premium listings

#{city_tag}RealEstate #NigeriaRealEstate #PropertyForSale #LuxuryHomes #{short_name_tag}"""

    return caption.strip()
