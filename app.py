"""
Amruthadhara Infra - Production Flask Application (Render-ready)
"""
import json
import os
import secrets
import threading
import uuid
from functools import wraps

from flask import (
    Flask, render_template, request, jsonify, redirect,
    session, render_template_string, send_from_directory
)
from werkzeug.utils import secure_filename

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))
except ImportError:
    pass

# ---------------------------------------------------------------------------
# Paths & Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# On Render we set STORAGE_DIR to a persistent disk mount.
# Locally it falls back to the app folder.
STORAGE_DIR = os.environ.get('STORAGE_DIR', BASE_DIR)

DATA_FILE = os.path.join(STORAGE_DIR, 'data.json')
UPLOAD_FOLDER = os.path.join(STORAGE_DIR, 'uploads')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'svg'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
IS_PRODUCTION = os.environ.get('FLASK_ENV', 'production') == 'production'

ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'nagesh@1024')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Q2!f<?P')


def _load_or_create_secret_key():
    env_key = os.environ.get('SECRET_KEY')
    if env_key:
        return env_key
    key_file = os.path.join(STORAGE_DIR, '.secret_key')
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r', encoding='utf-8') as fh:
                key = fh.read().strip()
                if key:
                    return key
        except OSError:
            pass
    key = secrets.token_hex(32)
    try:
        with open(key_file, 'w', encoding='utf-8') as fh:
            fh.write(key)
        os.chmod(key_file, 0o600)
    except OSError:
        pass
    return key


app = Flask(__name__)
app.secret_key = _load_or_create_secret_key()

app.config.update(
    MAX_CONTENT_LENGTH=MAX_CONTENT_LENGTH,
    UPLOAD_FOLDER=UPLOAD_FOLDER,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_SECURE=IS_PRODUCTION,
    PERMANENT_SESSION_LIFETIME=60 * 60 * 24 * 7,
    JSON_SORT_KEYS=False,
)

# Create folders safely — on Vercel this fails, but on Render it works
try:
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
except OSError as exc:
    app.logger.warning("Could not create upload folder %s: %s", UPLOAD_FOLDER, exc)

_data_lock = threading.Lock()


def _default_data():
    return {
        "logo_url": "logo.png",
        "hero": [
            {"image": "hero1.jpg", "title": "Building Dreams",
             "subtitle": "Excellence in Civil Engineering & Construction"},
            {"image": "hero2.jpg", "title": "Sustainable Future",
             "subtitle": "Innovative Green Construction Solutions"},
            {"image": "hero3.jpg", "title": "Precision & Quality",
             "subtitle": "Delivering Excellence Every Time"},
        ],
        "what_we_do": [
            {"icon": "fa-building", "title": "Residential Building",
             "description": "Quality homes designed for comfort and longevity."},
            {"icon": "fa-house-chimney", "title": "Duplex House",
             "description": "Modern duplex designs with premium finishes."},
            {"icon": "fa-tree", "title": "Villa & Farmhouse",
             "description": "Luxury villas and farmhouses in serene locations."},
            {"icon": "fa-paint-roller", "title": "Interiors",
             "description": "Aesthetic interiors with sustainable materials."},
        ],
        "specialized_in": [
            {"icon": "fa-droplet", "title": "Rain Water Harvesting",
             "description": "Sustainable water management solutions."},
            {"icon": "fa-microchip", "title": "IOT Integration",
             "description": "Smart building automation and IOT solutions."},
            {"icon": "fa-leaf", "title": "Green Interiors",
             "description": "Eco-friendly materials and sustainable design."},
            {"icon": "fa-solar-panel", "title": "Solar Solutions",
             "description": "Renewable energy integration for buildings."},
        ],
        "testimonials": [
            {"name": "Ramesh Kumar",
             "feedback": "Amruthadhara Infra delivered our dream home with exceptional quality and on time. Highly recommended!",
             "project": "Residential Villa"},
            {"name": "Priya Reddy",
             "feedback": "Their attention to detail and sustainable approach made our farmhouse truly special. Amazing team!",
             "project": "Farmhouse Project"},
            {"name": "Suresh Patel",
             "feedback": "Professional, reliable, and innovative. They transformed our commercial space beyond expectations.",
             "project": "Commercial Building"},
        ],
        "vision": {
            "title": "Young minds big vision",
            "text": ("We are a team of passionate engineers and designers committed to building a "
                     "sustainable future through innovative construction practices. Our vision is to "
                     "create structures that stand the test of time while respecting the environment."),
        },
        "contact": {
            "phone": "9347051097",
            "whatsapp": "9347051097",
            "email": "info@amruthadharainfra.com",
            "address": "Hyderabad, Telangana, India",
        },
        "social": {
            "youtube": "https://youtube.com",
            "twitter": "https://x.com",
            "facebook": "#",
            "instagram": "#",
            "linkedin": "#",
        },
        "pricing": [
            {"label": "Basic", "price": "₹1,899", "note": "per sq.ft"},
            {"label": "Premium", "price": "₹2,399", "note": "per sq.ft"},
            {"label": "Luxury", "price": "₹3,299", "note": "per sq.ft"},
            {"label": "Ultra Luxury", "price": "₹4,999", "note": "per sq.ft"},
        ],
        "parallax_image": "parallax.jpg",
        "about": {
            "what_we_do_text": ("We are a civil-engineering-led Private Limited Company delivering "
                                "integrated solutions across construction, interiors, water "
                                "infrastructure and development."),
            "mission": ("To deliver integrated construction, interior, water, and real estate "
                        "solutions through site-first understanding, practical design, quality "
                        "execution, and a strong commitment to safety, sustainability, and client trust."),
            "vision": ("To create safe, sustainable, and high-performing built environments by "
                       "combining thoughtful planning, engineering discipline, and responsible execution."),
            "founders": [],
            "supporters": [],
            "achievements": [
                {"title": "Best Construction Company 2024", "image": "ach1.jpg"},
                {"title": "Green Building Award 2023", "image": "ach2.jpg"},
                {"title": "ISO 9001:2020 Certified", "image": "ach3.jpg"},
            ],
        },
        "careers": {
            "jobs": [
                {"title": "Senior Site Engineer", "experience": "5+ Years", "type": "Full Time"},
                {"title": "Architect", "experience": "3+ Years", "type": "Full Time"},
                {"title": "Project Manager", "experience": "7+ Years", "type": "Full Time"},
            ],
            "internships": [
                {"title": "Site Engineer Intern", "location": "Hyderabad", "duration": "6 Months"},
                {"title": "CAD/CAM Intern", "location": "Hyderabad", "duration": "3 Months"},
                {"title": "2D and 3D Designer Intern", "location": "Remote", "duration": "3 Months"},
                {"title": "Video Editing Intern", "location": "Remote", "duration": "3 Months"},
            ],
        },
        "gallery": [
            "https://images.unsplash.com/photo-1541888081622-c20536443c51?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?auto=format&fit=crop&w=800&q=80",
            "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=800&q=80",
        ],
        "projects": {
            "past": [
                {"title": "Sunrise Villas", "description": "Luxury villa project completed in 2023",
                 "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=600&q=80"},
                {"title": "Green Valley Township", "description": "Completed in 2022",
                 "image": "https://images.unsplash.com/photo-1541888081622-c20536443c51?auto=format&fit=crop&w=600&q=80"},
            ],
            "present": [
                {"title": "Downtown Commercial Tower", "description": "Expected completion 2026",
                 "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80"},
                {"title": "Riverside Residences", "description": "Ongoing project",
                 "image": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=600&q=80"},
            ],
            "upcoming": [
                {"title": "Eco-Friendly Tech Park", "description": "Starting Q3 2027",
                 "image": "https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&w=600&q=80"},
                {"title": "Smart City Housing", "description": "Planned for 2028",
                 "image": "https://images.unsplash.com/photo-1541888081622-c20536443c51?auto=format&fit=crop&w=600&q=80"},
            ],
        },
    }


def load_data():
    with _data_lock:
        if not os.path.exists(DATA_FILE):
            data = _default_data()
            try:
                with open(DATA_FILE, 'w', encoding='utf-8') as fh:
                    json.dump(data, fh, indent=2, ensure_ascii=False)
            except OSError:
                pass
            return data
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as fh:
                return json.load(fh)
        except (json.JSONDecodeError, OSError):
            return _default_data()


def save_data(data):
    with _data_lock:
        tmp_path = DATA_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False)
        os.replace(tmp_path, DATA_FILE)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get('logged_in'):
            return jsonify({"status": "error", "message": "Unauthorized"}), 401
        return view(*args, **kwargs)
    return wrapped


@app.after_request
def _set_security_headers(resp):
    resp.headers.setdefault('X-Content-Type-Options', 'nosniff')
    resp.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    resp.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    resp.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
    return resp


LOGIN_FORM = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Admin Login</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            theme: { extend: { colors: {
                brand: { navy: '#051025', blue: '#0a2558', cyan: '#00b4d8' }
            }}}
        }
    </script>
</head>
<body class="bg-slate-100 flex items-center justify-center min-h-screen">
    <div class="bg-white p-8 rounded-2xl shadow-xl max-w-sm w-full">
        <h1 class="text-2xl font-bold text-brand-navy text-center mb-6">Admin Login</h1>
        {% if error %}
            <div class="bg-red-100 text-red-700 p-3 rounded-lg mb-4">{{ error }}</div>
        {% endif %}
        <form method="POST" autocomplete="off">
            <div class="mb-4">
                <label class="block text-sm font-medium text-slate-600 mb-1">Username</label>
                <input type="text" name="username" required autofocus
                       class="w-full border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:border-brand-cyan" />
            </div>
            <div class="mb-6">
                <label class="block text-sm font-medium text-slate-600 mb-1">Password</label>
                <input type="password" name="password" required
                       class="w-full border border-slate-300 rounded-lg px-4 py-2 focus:outline-none focus:border-brand-cyan" />
            </div>
            <button type="submit"
                    class="w-full bg-brand-cyan text-white font-bold py-2 rounded-lg hover:bg-brand-blue transition">
                Login
            </button>
        </form>
    </div>
</body>
</html>
'''


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/aboutus')
def aboutus():
    return render_template('aboutus.html')

@app.route('/careers')
def careers():
    return render_template('careers.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/gallery')
def gallery():
    return render_template('gallery.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/services')
def services():
    return render_template('services.html')

@app.route('/estimation')
def estimation():
    return render_template('estimation.html')

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


# Serve uploaded images from the persistent storage folder
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session.clear()
            session['logged_in'] = True
            session.permanent = True
            return redirect('/admin')
        return render_template_string(LOGIN_FORM, error='Invalid credentials')
    if not session.get('logged_in'):
        return render_template_string(LOGIN_FORM)
    return render_template('admin.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/admin')


@app.route('/api/data', methods=['GET'])
def get_data():
    resp = jsonify(load_data())
    resp.headers['Cache-Control'] = 'no-store'
    return resp


@app.route('/api/data', methods=['POST'])
@login_required
def update_data():
    new_data = request.get_json(silent=True)
    if not isinstance(new_data, dict):
        return jsonify({"status": "error", "message": "Invalid data"}), 400
    try:
        save_data(new_data)
    except OSError as exc:
        app.logger.exception("Failed to save data: %s", exc)
        return jsonify({"status": "error", "message": "Could not save data"}), 500
    return jsonify({"status": "success", "message": "Data updated successfully"}), 200


@app.route('/api/upload', methods=['POST'])
@login_required
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400

    safe_name = secure_filename(file.filename) or 'upload'
    ext = safe_name.rsplit('.', 1)[1].lower() if '.' in safe_name else 'bin'
    base = safe_name.rsplit('.', 1)[0][:60] or 'img'
    unique_name = f"{base}_{uuid.uuid4().hex[:12]}.{ext}"
    dest = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)

    try:
        file.save(dest)
    except OSError as exc:
        app.logger.exception("Upload failed: %s", exc)
        return jsonify({'error': 'Could not save file'}), 500

    return jsonify({'filename': unique_name}), 200


@app.errorhandler(413)
def _too_large(_e):
    return jsonify({"status": "error", "message": "File too large (max 16 MB)"}), 413

@app.errorhandler(404)
def _not_found(_e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Not found"}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def _server_error(_e):
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Internal server error"}), 500
    return "<h1>500 - Internal Server Error</h1>", 500


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
