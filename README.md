## Academic Freedom LK – Judgement Search

A Django web app to browse and search Sri Lankan apex court judgements related to academic freedom (2009–2023). It provides a BM25-based keyword search, filters by year/month, and direct links to case documents.

## Features

- Keyword search powered by a simple BM25 implementation over a positional inverted index (`pos_inv_ind.json`).
- List view of judgements with filters for year and month, plus exact link lookup.
- Clean UI with `base.html` navigation: Search, Academic Freedom Decisions, About.
- Admin registration for the `Judgement` model (quick data inspection).
- Static asset handling via WhiteNoise for simple deployments.

## Tech stack

- Python 3.9 (per Pipfile)
- Django 3.1.x
- Gunicorn (for production serving)
- WhiteNoise (static files)
- NLTK (stopwords, tokenization) with extra legal stopwords from `legalstopwords.txt`
- Pandas (for one-off CSV → SQLite ingestion)

## App architecture

- App: `pages`
	- Model: `Judgement` with fields: `date`, `link`, `standard_casenumber`, `standard_nameofparties`, `in_the_matter_of`, `primary_key`, `judgement_text`.
	- Views:
		- Home (`/`): BM25 search over `pos_inv_ind.json` and displays top ranked matches (up to 30).
		- Academic Freedom Decisions (`/academic_freedom_judgements/`): list with year/month filter and link search.
		- About (`/about/`).
	- Forms: `JudgementsSearchForm`, `JudgementsFilterForm`, `JudgementsPDFForm`.
	- Template filter: `relevant_text` to extract a sentence around a matched term in a judgement.
	- BM25: implemented in `pages/bm25.py` using NLTK stopwords and custom legal stop words.
- Templates: `templates/base.html`, `home.html`, `judgements_list.html`, `about.html`
- Routing: `config/urls.py` includes `pages.urls`
- Static: `static/` (dev), collected into `staticfiles/` (prod) via WhiteNoise

## Requirements

- Python 3.9
- Pipenv (recommended) or pip/venv
- NLTK data: `stopwords`, `punkt`
- Local files expected in repo root:
	- `pos_inv_ind.json` – positional inverted index used for search
	- `legalstopwords.txt` – one term per line
	- Optional: data CSV for ingestion script described below

## Quick start (local)

1) Create and activate environment, install deps

```bash
pipenv install --dev
pipenv shell
```

2) Set Django settings (defaults are development-friendly)

No env vars are strictly required for local dev. `DEBUG=True` and SQLite are already configured in `config/settings.py`.

3) Prepare NLTK data

The app uses NLTK stopwords and tokenization. Install the data once:

```bash
python - << 'PY'
import nltk
for pkg in ["stopwords", "punkt"]:
		nltk.download(pkg)
print("Downloaded: stopwords, punkt")
PY
```

Alternatively, install per the provided `nltk.txt` list.

4) Initialize database

If you have `db.sqlite3` already committed/populated, you can skip. Otherwise run migrations to create an empty schema:

```bash
python manage.py migrate
```

5) Optional: ingest dataset into SQLite

There is a helper script `inject_to_db.py` that reads a CSV and writes to `pages_judgement` in `db.sqlite3` using pandas. Notes:

- It deletes `db.sqlite3` if present, then writes a fresh DB.
- It expects the CSV at `../academic_freedom/ed_cases_df.csv` relative to this repo root. Adjust the path inside the script for your data.
- It assumes columns compatible with the `Judgement` model; add/rename columns in the script if your CSV differs.

Run at your own discretion:

```bash
python inject_to_db.py
```

6) Run the dev server

```bash
python manage.py runserver
```

Navigate to:

- Search: http://127.0.0.1:8000/
- Academic Freedom Decisions: http://127.0.0.1:8000/academic_freedom_judgements/
- About: http://127.0.0.1:8000/about/
- Admin: http://127.0.0.1:8000/admin/ (create a superuser first if needed)

## Running tests

Tests are minimal and cover basic route status/template usage. Run:

```bash
python manage.py test
```

Note: Two tests reference legacy paths (`/supreme_court_judgements/`) which don’t exist in current URLs. You may update tests to `academic_freedom_judgements` or add a URL alias.

## Search pipeline details

- Index source: `pos_inv_ind.json` – maps tokens to document postings with positions; loaded at app start in `HomePageView`.
- Doc length table is computed from the index for BM25 normalization.
- Query processing uses NLTK stopwords, Porter stemming, and custom legal stop words.
- Results are a list of `primary_key` values; the queryset is ordered to match ranking and truncated to top 30.
- The template filter `relevant_text` can extract a matching sentence from `judgement_text` if that field is loaded.

## Deployment

This repo includes a `Procfile` for platforms like Heroku:

```
web: gunicorn config.wsgi --log-file -
```

Static files are served via WhiteNoise. Before deploying, collect static files:

```bash
python manage.py collectstatic --noinput
```

Recommended environment variables in production:

- `DEBUG=False`
- `SECRET_KEY` – override the dev key in `config/settings.py`
- `ALLOWED_HOSTS` – add deployment host(s)

## Troubleshooting

- ImportError: NLTK stopwords not found – make sure you ran the NLTK download step above, or set `nltk.data.path` appropriately.
- Missing `pos_inv_ind.json` – search will return empty; ensure the file exists at the project root and matches expected structure.
- UnicodeDecodeError / CSV ingestion – ensure your CSV is UTF-8 or pass `encoding=` when loading via pandas in `inject_to_db.py`.
- Static files not updating – if using WhiteNoise’s manifest storage, run `collectstatic` after CSS changes.

## Repository structure (high level)

```
config/              # Django project settings, URLs, WSGI/ASGI
pages/               # App with models, views, forms, BM25, templates filter
templates/           # Base, home, judgements_list, about templates
static/              # CSS during development
staticfiles/         # Collected static (generated)
db.sqlite3           # SQLite database (dev/demo). Can be regenerated
pos_inv_ind.json     # Positional inverted index for search
legalstopwords.txt   # Domain-specific stop words
inject_to_db.py      # Helper script to load CSV → SQLite
Procfile             # Gunicorn entry for deployment
Pipfile              # Dependencies (Python 3.9)
```

## License

Add your preferred license here. If data carries separate terms, include attribution and usage notes.

