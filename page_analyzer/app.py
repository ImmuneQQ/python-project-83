from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    request,
    flash
)
from psycopg2 import connect
import os
from datetime import datetime
import validators
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_get():
    conn = connect(DATABASE_URL)
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT ON (urls.id)
                urls.id,
                urls.name,
                url_checks.created_at,
                url_checks.status_code
            FROM urls LEFT JOIN url_checks ON urls.id = url_checks.url_id
            ORDER BY urls.id DESC, url_checks.created_at DESC;
        """)
        sites = cur.fetchall()
    conn.close()
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
        conn = connect(DATABASE_URL)
        conn.set_session(autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"SELECT * FROM urls WHERE name='{norm_url}';")
            found_site = cur.fetchone()
        conn.close()
        if found_site:
            flash('Страница уже существует', 'alert-info')
        else:
            conn = connect(DATABASE_URL)
            conn.set_session(autocommit=True)
            with conn.cursor() as cur:
                cur.execute(f"""INSERT INTO urls (name, created_at)
                                VALUES ('{norm_url}', '{time_now}');""")
                cur.execute(f"SELECT * FROM urls WHERE name='{norm_url}';")
                found_site = cur.fetchone()
            conn.close()
            flash('Страница успешно добавлена', 'alert-success')
        
        return redirect(url_for('url_item', id=found_site[0]))
    else:
        if not url_is_valid:
            flash('Некорректный URL', 'alert-danger')
        if url_is_empty:
            flash('URL обязателен', 'alert-danger')
        if url_is_too_long:
            flash('URL превышает 255 символов', 'alert-danger')
        return render_template(
            'index.html',
            url=url), 422


@app.get('/urls/<id>')
def url_item(id):
    conn = connect(DATABASE_URL)
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        cur.execute(f"SELECT * FROM urls WHERE id={id};")
        site = cur.fetchone()
    conn.close()
    conn = connect(DATABASE_URL)
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        cur.execute(f"""SELECT * FROM url_checks
                        WHERE url_id={id}
                        ORDER BY id DESC;""")
        url_checks = cur.fetchall()
    conn.close()
    name = site[1]
    created_at = site[2].date()
    return render_template(
        'url_item.html',
        id=id,
        name=name,
        created_at=created_at,
        url_checks=url_checks
        )


@app.post('/urls/<id>/checks')
def url_check(id):
    time_now = datetime.now()
    conn = connect(DATABASE_URL)
    conn.set_session(autocommit=True)
    with conn.cursor() as cur:
        cur.execute(f"SELECT name FROM urls WHERE id = {id};")
        url_name = cur.fetchone()[0]
    conn.close()
    try:
        r = requests.get(url_name)
    except requests.ConnectionError:
        flash('Произошла ошибка при проверке', 'alert-danger')
    else:
        status_code = r.status_code
        content = r.text
        soup = BeautifulSoup(content, 'html.parser')
        h1 = soup.h1
        h1_text = h1.string if h1 else ""
        title = soup.title
        title_text = title.string if title else ""
        description = soup.select_one("meta[name='description']")
        description_text = description.get('content') if description else ""
        conn = connect(DATABASE_URL)
        conn.set_session(autocommit=True)
        with conn.cursor() as cur:
            cur.execute(f"""INSERT INTO url_checks (
                                url_id,
                                status_code,
                                h1,
                                title,
                                description, created_at
                                )
                            VALUES (
                                {id},
                                {status_code},
                                '{h1_text}',
                                '{title_text}',
                                '{description_text}',
                                '{time_now}'
                                );""")
        conn.close()
        flash('Страница успешно проверена', 'alert-success')
    return redirect(url_for('url_item', id=id))
