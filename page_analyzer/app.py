from flask import (
    Flask,
    render_template,
    redirect,
    url_for
)

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/urls')
def urls_get():
    return render_template('urls.html')


@app.post('/urls')
def urls_post():
    return redirect(url_for('urls_get'))
