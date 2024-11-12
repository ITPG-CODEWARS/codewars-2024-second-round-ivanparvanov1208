from flask import Flask, render_template, request, redirect, url_for, flash, send_file  # Импортиране на необходимите модули от Flask
from flask_sqlalchemy import SQLAlchemy  # Импортиране на SQLAlchemy за работа с бази данни
import random  # Импортиране на модула random за генериране на случайни стойности
import string  # Импортиране на модула string за работа с низове
import qrcode  # Импортиране на модула qrcode за генериране на QR кодове
import os  # Импортиране на модула os за работа с файловата система

app = Flask(__name__, static_url_path="/static")  # Създаване на Flask приложение с определен статичен URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///urls.db'  # Конфигуриране на URI за SQLite база данни
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Деактивиране на проследяването на модификации в базата данни
app.config['SECRET_KEY'] = 'your_secrets_key'  # Определяне на секретен ключ за сесии и формуляри

db = SQLAlchemy(app)  # Инициализиране на SQLAlchemy с Flask приложението

@app.before_request
def create_tables():  # Декорирана функция, която се изпълнява преди всяка заявка
    db.create_all()  # Създава всички таблици в базата данни, ако не съществуват

class Urls(db.Model):  # Дефиниция на модел Urls, който представлява таблица в базата данни
    id = db.Column(db.Integer, primary_key=True)  # Идентификатор на URL (първичен ключ)
    long = db.Column(db.String(500), nullable=False)  # Дълъг URL адрес (не може да бъде null)
    short = db.Column(db.String(10), unique=True, nullable=False)  # Кратък URL адрес (уникален и не може да бъде null)

    def __init__(self, long, short):  # Инициализатор за модела Urls
        self.long = long  # Задаване на дългия URL адрес
        self.short = short  # Задаване на краткия URL адрес

def generate_short_code():  # Функция за генериране на кратък код
    urlSize = request.form.get("urlSize")  # Получаване на желаната дължина на кода от формуляра
    characters = string.ascii_letters + string.digits  # Определяне на допустимите символи за кода
    while True:  # Безкраен цикъл за генериране на код
        if not urlSize:  # Ако не е зададена дължина
            short_code = ''.join(random.choices(characters, k=6))  # Генериране на код с дължина 6
        else:  # Ако е зададена дължина
            short_code = ''.join(random.choices(characters, k=int(urlSize)))  # Генериране на код с зададената дължина
        if not Urls.query.filter_by(short=short_code).first():  # Проверка дали кодът вече съществува
            return short_code  # Връщане на уникалния кратък код

@app.route('/', methods=['GET', 'POST'])  # Декориране на функцията home с маршрут за главната страница
def home():
    if request.method == 'POST':  # Проверка дали заявката е POST
        longURL = request.form.get('longUrl')  # Получаване на дългия URL от формуляра
        custom_suffix = request.form.get('customAlias')  # Получаване на потребителски суфикс от формуляра

        existing_url = Urls.query.filter_by(long=longURL).first()  # Проверка дали дългият URL вече съществува
        if existing_url:  # Ако съществува
            full_short_url = request.host_url + existing_url.short  # Създаване на пълен кратък URL
            qr_code_path = f'static/img/qr_images/{existing_url.short}.png'  # Път до QR кода
            return redirect(url_for('shortened_link', short_code=existing_url.short, qr= qr_code_path))  # Пренасочване към страницата с краткия линк и QR кода
        else:  # Ако не съществува
            if custom_suffix:  # Проверка дали е зададен потребителски суфикс
                short_code = custom_suffix  # Използване на потребителския суфикс за краткия код
            else:  # Ако не е зададен потребителски суфикс
                short_code = generate_short_code()  # Генериране на нов кратък код

            if longURL:  # Проверка дали дългият URL е предоставен
                new_url = Urls(long=longURL, short=short_code)  # Създаване на нов запис в базата данни
                db.session.add(new_url)  # Добавяне на новия запис в сесията
                db.session.commit()  # Записване на промените в базата данни

                qr_code_path = None  # Инициализиране на променлива за пътя до QR кода
                full_short_url = request.host_url + short_code  # Създаване на пълен кратък URL
                qr = qrcode.make(full_short_url)  # Генериране на QR код за краткия URL
                qr_code_path = f'static/img/qr_images/{short_code}.png'  # Определяне на пътя за запазване на QR кода
                os.makedirs(os.path.dirname(qr_code_path), exist_ok=True)  # Създаване на директория, ако не съществува
                qr.save(qr_code_path)  # Запазване на QR кода в указаната директория

                return redirect(url_for('shortened_link', short_code=short_code, qr=qr_code_path))  # Пренасочване към страницата с краткия линк и QR кода
    
    else:  # Ако заявката е GET
        return render_template('index.html')  # Връщане на основния шаблон

@app.route('/link/<short_code>')  # Декориране на функцията shortened_link с маршрут за краткия линк
def shortened_link(short_code):
    full_short_url = request.host_url + short_code  # Създаване на пълен кратък URL
    qr_code_path = request.args.get('qr')  # Получаване на пътя до QR кода от параметрите на заявката
    return render_template('shorturl.html', full_short_url=full_short_url, qr_code_path=qr_code_path)  # Връщане на шаблона с краткия линк и QR кода

@app.route('/<short_code>')  # Декориране на функцията redirect_to_url с маршрут за пренасочване
def redirect_to_url(short_code):
    url = Urls.query.filter_by(short=short_code).first()  # Търсене на URL по краткия код
    if url:  # Ако URL е намерен
        return redirect(url.long)  # Пренасочване към дългия URL
    else:  # Ако URL не е намерен
        return render_template('notfound.html'), 404  # Връщане на страница за не намерен ресурс

if __name__ == '__main__':  # Проверка дали скриптът се изпълнява директно
    app.run(host="0.0.0.0", port="5000")  # Стартиране на Flask приложението на порт 5000 ⬤