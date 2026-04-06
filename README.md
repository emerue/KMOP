# KingMac of Property — Corporate Website

> "Your Crown. Your Property."

Premium real estate website built with Flask. Covers Lagos, Abuja, Port Harcourt and beyond.

## Quick Start

```bash
# 1. Activate the virtual environment
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the database (creates admin user + 12 sample properties)
flask seed-db

# 4. Run the development server
flask run
```

Open http://127.0.0.1:5000

## Admin Panel

URL: http://127.0.0.1:5000/admin/login

| Field    | Value          |
|----------|----------------|
| Username | admin          |
| Password | Kingmac@2024   |

## Features

- **Currency Toggle** — Switch between ₦ / $ / £ instantly (stored in localStorage)
- **Shortlist** — Heart-save properties, send bulk WhatsApp to agent
- **Instant Valuation Tool** — Price estimate from live DB data
- **Property Media Manager** — Drag-to-reorder, set cover, AJAX upload/delete
- **AJAX Admin Toggles** — Publish/Feature properties without page reload
- **Leaflet Maps** — Per-property and contact page maps
- **WhatsApp Integration** — Agent cards, shortlist send, valuation results
- **Newsletter** — AJAX subscribe with CSV export in admin
- **SEO** — sitemap.xml, robots.txt, OG meta on every page

## Project Structure

```
KMOP2/
├── app/                  # Flask application package
│   ├── __init__.py       # App factory + seed-db CLI command
│   ├── models.py         # SQLAlchemy models
│   ├── config.py         # Dev/prod configuration
│   ├── main/             # Public blueprint (routes, forms)
│   ├── admin/            # Admin blueprint (CRUD, media manager)
│   ├── auth/             # Login / logout
│   └── static/           # CSS, JS, images, uploads
├── templates/            # Jinja2 templates
│   └── admin/            # Admin dashboard templates
├── instance/             # SQLite database (auto-created)
├── .env                  # Environment variables
├── requirements.txt
└── run.py
```

## Environment Variables (.env)

| Variable            | Description                        |
|---------------------|------------------------------------|
| SECRET_KEY          | Flask session secret               |
| WHATSAPP_NUMBER     | WhatsApp number (no + or spaces)   |
| UPLOAD_FOLDER       | Path for uploaded property images  |
| MAX_CONTENT_LENGTH  | Max upload size in bytes (16MB)    |
# KMOP
