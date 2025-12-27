## Wedding Website (Django + UV)

A bespoke wedding portal inspired by muted lavender stationery for Megan & Stephen. Built with Django, UV-managed
dependencies, and ready for deployment on PythonAnywhere or any static-friendly host.

### Features
- RSVP flow that validates invited guests, captures three.js avatar selections with live previews, and routes attendees to the chapel
  visualization or livestream lounge.
- Admin dashboard to pre-load guest lists, review RSVPs, and approve QR/NFC photo uploads.
- Chapel experience now powered by a three.js scene that seats confirmed guests in an interactive 3D view.
- Livestream placeholder page with Subsplash embed snippet ready for the final link.
- Photo upload portal suitable for QR/NFC handouts and a curated gallery.
- Travel, lodging, registry, and wedding party sections using the provided invitation for visual direction.

### Prerequisites
- [UV](https://github.com/astral-sh/uv) (already used for dependency management).
- Python 3.12+ (UV will bootstrap a compatible interpreter).

### Setup
```bash
cd ~/Documents/wedding-website
uv sync
# install JS dependencies for DiceBear-powered avatar previews (optional if using CDN, recommended for type checking)
npm install
```

### Front-end assets
Three.js powers both the RSVP avatar studio (`frontend/avatar.js`) and the chapel scene (`frontend/chapel/`). The modular
structure keeps each element (environment, organ, stained glass, pews, petals, etc.) isolated for easier iteration.
Bundle commands are captured as npm scripts:

```bash
npm run build:avatars   # bundles frontend/avatar.js
npm run build:chapel    # bundles frontend/chapel/main.js
```

Update the module files and rerun the appropriate build command whenever you tweak the visuals.

### Running locally
```bash
uv run python manage.py migrate
uv run python manage.py createsuperuser  # optional for admin access
uv run python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the home page, `/chapel/` for live seating, `/livestream/` for the virtual viewing
room, and `/admin/` to manage guests, RSVPs, and photo approvals.

### Visual regression testing
Automated screenshot comparisons help keep the three.js chapel consistent with the provided reference photo
(`assets/IMG_8663.jpg`, resized to `tests/reference/chapel-reference.png` and
`cypress/snapshots/base/chapel-reference.png`).

1. Ensure the Django dev server is running locally (`uv run python manage.py runserver`).
2. In another terminal run either suite:

Playwright (Chromium):
```bash
npm run test:playwright
```

Cypress (headless):
```bash
npm run test:cypress
```

Cypress (interactive runner):
```bash
npm run test:cypress:open
```

Both suites capture `/chapel/`, normalize the viewport to 1280×720, and compare the render against the purple/rose-stained
glass reference using `pixelmatch`/`cypress-image-snapshot`. Adjust thresholds in `tests/playwright/chapel.spec.js` or
`cypress/support/commands.js` if you intentionally change the scene lighting. Playwright automatically stores its latest
capture and diff under `assets/playwright-captures/chapel-latest.png` and `.../chapel-diff.png` so you can git-track
visual changes alongside code.

Need a single command that bundles assets, runs Django checks, spins up a temporary dev server, and executes the Playwright
and Cypress suites sequentially? Use:

```bash
npm run test:full
```
(`scripts/verify.sh` handles startup/shutdown automatically.)

### Testing checklist
- Desktop/tablet/mobile breakpoints (≥1200px, 768px, 480px).
- RSVP “yes” populates the chapel with avatar preview and reroutes there.
- RSVP “no” reroutes to the livestream page.
- Avatar controls update the preview instantly.
- Photo uploads succeed from the homepage and QR portal.
- Livestream placeholder renders without browser security warnings.

### Deployment notes
- Configure `ALLOWED_HOSTS` and Django `SECRET_KEY` via environment variables before deploying.
- For PythonAnywhere, collect static assets (`uv run python manage.py collectstatic`) and point media storage to a durable
  location for uploads.
- If using a CDN for QR/NFC uploads, update `MEDIA_URL` accordingly.
