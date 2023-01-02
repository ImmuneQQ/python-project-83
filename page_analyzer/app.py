from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash,
    get_flashed_messages
)
import psycopg2
import os
from datetime import datetime
import validators
from urllib.parse import urlparse


DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
conn.set_session(autocommit=True)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_get():
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls ORDER BY id DESC;")
    sites = cur.fetchall()
    return render_template('urls.html', sites=sites)


@app.post('/urls')
def urls_post():
    url = request.form['url']
    url_is_valid = validators.url(url)
    url_is_empty = len(url) == 0
    url_is_too_long = len(url) > 255
    time_now = datetime.now()

    if url_is_valid and not url_is_empty and not url_is_too_long:
        parsed_url = urlparse(url)
        norm_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        cur = conn.cursor()
        cur.execute(f"SELECT * FROM urls WHERE name='{norm_url}';")
        found_site = cur.fetchone()
        if found_site:
            flash('Страница уже существует', 'alert-info')
        else:
            cur.execute(f"""INSERT INTO urls (name, created_at)
                            VALUES ('{norm_url}', '{time_now}');""")
            cur.execute(f"SELECT * FROM urls WHERE name='{norm_url}';")
            found_site = cur.fetchone()
            flash('Страница успешно добавлена', 'alert-success')
        messages = get_flashed_messages(with_categories=True)
        return redirect(url_for('url_item', id=found_site[0]))
    else:
        if not url_is_valid:
            flash('Некорректный URL', 'alert-danger')
        if url_is_empty:
            flash('URL обязателен', 'alert-danger')
        if url_is_too_long:
            flash('URL превышает 255 символов', 'alert-danger')
        messages = get_flashed_messages(with_categories=True)
        return render_template(
            'index.html',
            url=url, messages=messages
            ), 422


@app.get('/urls/<id>')
def url_item(id):
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM urls WHERE id={id};")
    site = cur.fetchone()
    name = site[1]
    created_at = site[2].date()
    return render_template(
        'url_item.html',
        id=id,
        name=name,
        created_at=created_at
        )
