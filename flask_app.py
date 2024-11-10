from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
import random
import string
import qrcode
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database model for URLs
class URLs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    long = db.Column(db.String(500), nullable=False)
    short = db.Column(db.String(10), unique=True, nullable=False)

# Generate a random short code
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    while True:
        short_code = ''.join(random.choices(characters, k=length))
        if not URL.query.filter_by(short=short_code).first():
            return short_code

# Home route
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        longURL = request.form.get('link')
        custom_suffix = request.form.get('custom_suffix')
        generate_qr = 'generate_qr' in request.form  # Check if QR checkbox is ticked

        # Check if a custom suffix is provided
        if custom_suffix:
            if URL.query.filter_by(short_code=custom_suffix).first():
                flash('Custom suffix is already taken. Please choose another one.', 'danger')
                return redirect(url_for('home'))
            short_code = custom_suffix
        else:
            short_code = generate_short_code()
        
        # Save the URL and short code to the database
        new_url = URL(long=longURL, short=short_code)
        db.session.add(new_url)
        db.session.commit()

        # Generate QR code if requested
        qr_code_path = None
        full_short_url = request.host_url + short_code
        qr = qrcode.make(full_short_url)
        qr_code_path = f'static/qr_images/{short_code}.png'
        os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)
        qr.save(qr_code_path)

        # Redirect to the page that shows the shortened link (and optionally the QR code)
        return redirect(url_for('shortened_link', short_code=short_code, qr=qr_code_path))
    
    return render_template('index.html')

# Display the shortened link and QR code (if generated)
@app.route('/link/<short_code>')
def shortened_link(short_code):
    full_short_url = request.host_url + short_code
    qr_code_path = request.args.get('qr')
    return render_template('shortened_link.html', full_short_url=full_short_url, qr_code_path=qr_code_path)

# Redirect to the original URL
@app.route('/<short_code>')
def redirect_to_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first_or_404()
    if url.long:
        return redirect(url.long)
    else:
        render_template("notfound.html")

# Initialize the database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)