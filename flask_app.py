from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import random
import string
import qrcode
import os

app = Flask(__name__, static_url_path="/static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secrets_key'

db = SQLAlchemy(app)

@app.before_request
def create_tables():
    db.create_all()

# Database model for URLs
class Urls(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long = db.Column(db.String(500), nullable=False)
    short = db.Column(db.String(10), unique=True, nullable=False)

    def __init__(self, long, short):
        self.long = long
        self.short = short

# Generate a random short code
def generate_short_code():
    urlSize = request.form.get("urlSize")
    characters = string.ascii_letters + string.digits
    while True:
        if not urlSize:
            short_code = ''.join(random.choices(characters, k=6))
        else:
            short_code = ''.join(random.choices(characters, k=int(urlSize)))
        if not Urls.query.filter_by(short=short_code).first():
            return short_code

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        longURL = request.form.get('longUrl')
        custom_suffix = request.form.get('customAlias')

        # Check if a custom suffix is provided
        if custom_suffix:
            short_code = custom_suffix
        else:
            short_code = generate_short_code()
        
        # Save the URL and short code to the database only if longURL is valid
        if longURL:
            new_url = Urls(long=longURL, short=short_code)
            db.session.add(new_url)
            db.session.commit()

            # Generate QR code if requested
            qr_code_path = None
            full_short_url = request.host_url + short_code
            qr = qrcode.make(full_short_url)
            qr_code_path = f'static/img/qr_images/{short_code}.png'
            os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
            qr.save(qr_code_path)

            # Redirect to the page that shows the shortened link (and optionally the QR code)
            return redirect(url_for('shortened_link', short_code=short_code, qr=qr_code_path))
    
    else:
        return render_template('index.html')

# Display the shortened link and QR code (if generated)
@app.route('/link/<short_code>')
def shortened_link(short_code):
    full_short_url = request.host_url + short_code
    qr_code_path = request.args.get('qr')
    return render_template('shorturl.html', full_short_url=full_short_url, qr_code_path=qr_code_path)

# Redirect to the original URL
@app.route('/<short_code>')
def redirect_to_url(short_code):
    url = Urls.query.filter_by(short=short_code).first()
    if url:
        return redirect(url.long)
    else:
        # Return a 404 error or render a not found page instead of redirecting
        return render_template('notfound.html'), 404  # Make sure to create a notfound.html template

if __name__ == '__main__':
    app.run(host="0.0.0.0", port="8080")