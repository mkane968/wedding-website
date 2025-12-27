# Deployment Guide

## Overview
Your wedding website needs to be deployed to a hosting service. GitHub only stores your code - it doesn't run Django applications.

## Quick Deployment Options

### Option 1: Railway (Recommended - Easiest)
1. Go to [railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your `wedding-website` repository
5. Railway will detect Django automatically
6. Add environment variables in the Railway dashboard:
   - `DJANGO_SECRET_KEY`: Generate one with: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `DEBUG`: Set to `False`
   - `ALLOWED_HOSTS`: Set to your Railway domain (e.g., `your-app.railway.app`)
7. Add a build command: `npm install && npm run build:chapel && uv sync`
8. Add a start command: `uv run python manage.py migrate && uv run python manage.py collectstatic --noinput && uv run gunicorn wedding_site.wsgi:application`
9. Your site will be live at a Railway URL!

### Option 2: Render
1. Go to [render.com](https://render.com)
2. Sign up/login with GitHub
3. Click "New" → "Web Service"
4. Connect your `wedding-website` repository
5. Settings:
   - Build Command: `npm install && npm run build:chapel && uv sync`
   - Start Command: `uv run python manage.py migrate && uv run python manage.py collectstatic --noinput && uv run gunicorn wedding_site.wsgi:application`
   - Environment: `Python 3`
6. Add environment variables:
   - `DJANGO_SECRET_KEY`: Generate a secret key
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: Your Render URL (e.g., `your-app.onrender.com`)

### Option 3: PythonAnywhere (Mentioned in README)
1. Sign up at [pythonanywhere.com](https://www.pythonanywhere.com)
2. Go to the Web tab
3. Click "Add a new web app"
4. Follow their Django setup wizard
5. Upload your code or clone from GitHub
6. Configure static files and environment variables
7. More detailed guide: https://help.pythonanywhere.com/pages/DeployExistingDjangoProject

## Required Steps Before Deploying

1. **Install Gunicorn** (for production server):
   Add to `pyproject.toml`:
   ```toml
   gunicorn = "*"
   ```

2. **Collect Static Files** (after deployment):
   ```bash
   uv run python manage.py collectstatic
   ```

3. **Run Migrations**:
   ```bash
   uv run python manage.py migrate
   ```

4. **Create Superuser** (for admin access):
   ```bash
   uv run python manage.py createsuperuser
   ```

## Environment Variables Needed

- `DJANGO_SECRET_KEY`: A secret key (generate a new one for production!)
- `DEBUG`: Set to `False` in production
- `ALLOWED_HOSTS`: Your domain (comma-separated, e.g., `yourdomain.com,www.yourdomain.com`)

## Testing Locally First

Before deploying, make sure it works locally:
```bash
uv sync
npm install
npm run build:chapel
uv run python manage.py migrate
uv run python manage.py runserver
```

Visit http://127.0.0.1:8000/ to test locally.

