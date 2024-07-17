import os
import psycopg2
import requests
from dotenv import load_dotenv
from datetime import date
from validators.url import url
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, make_response, \
    url_for, redirect, get_flashed_messages, flash


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')


def connect():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    return conn, cur


def validate_and_normalize(url_str):
    if url(url_str) and len(url_str) <= 255:
        parsed_url = urlparse(url_str)
        return f'{parsed_url.scheme}://{parsed_url.netloc}'


def get_all_urls():
    conn, cur = connect()
    cur.execute("SELECT name FROM urls;")
    all_entries = cur.fetchall()
    return [entry[0] for entry in all_entries]


@app.route('/')
def main_page():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'main.html',
        messages=messages
    )


@app.post('/')
def add_entry():
    new_entry = validate_and_normalize(request.form.to_dict()['url'])
    all_entries = get_all_urls()
    if not new_entry:
        flash('Некорректный URL', 'danger')
        return make_response(redirect(url_for('main_page'), code=302))
    elif new_entry in all_entries:
        flash('Страница уже существует', 'info')
    else:
        conn, cur = connect()
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s)",
            (new_entry, date.today())
        )
        conn.commit()
        flash('Страница успешно добавлена', 'success')
    conn, cur = connect()
    cur.execute("SELECT id FROM urls WHERE name = %s", (new_entry,))
    new_entry_id = cur.fetchall()[0][0]
    response = make_response(
        redirect(url_for('url_page', id=new_entry_id), code=302)
    )
    return response


@app.route('/urls/<int:id>')
def url_page(id):
    messages = get_flashed_messages(with_categories=True)
    conn, cur = connect()
    cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
    current_url = cur.fetchall()
    if not current_url:
        return render_template('not_found.html'), 404
    url_name = current_url[0][1]
    url_date = current_url[0][2]
    conn, cur = connect()
    cur.execute(
        "SELECT id, created_at, status_code, h1, title, description \
        FROM url_checks \
        WHERE url_id = %s \
        ORDER BY id DESC;",
        (id,)
    )
    url_checks = cur.fetchall()
    return render_template(
        'url_page.html',
        id=id,
        name=url_name,
        date=url_date,
        messages=messages,
        url_checks=url_checks
    )


@app.route('/urls')
def all_urls():
    conn, cur = connect()
    cur.execute(
        "WITH filtered_checks \
        AS (\
        SELECT url_id, MAX(created_at) AS created_at, status_code \
        FROM url_checks \
        GROUP BY url_id, status_code\
        ) \
        SELECT urls.id, urls.name, filtered_checks.created_at, \
        filtered_checks.status_code \
        FROM urls \
        LEFT JOIN filtered_checks \
        ON urls.id = filtered_checks.url_id \
        ORDER BY id DESC;"
    )
    all_urls = cur.fetchall()
    return render_template(
        'all_urls.html',
        all_urls=all_urls
    )


@app.post('/urls/<id>/checks')
def check_url(id):
    conn, cur = connect()
    cur.execute("SELECT name FROM urls WHERE id = %s;", (id,))
    name = cur.fetchall()[0][0]
    try:
        r = requests.get(name)
        requests.Response.raise_for_status(r)
        status_code = r.status_code
        soup = BeautifulSoup(r.text, 'html.parser')
        h1 = soup.h1.string if soup.h1 else ''
        title = soup.title.string if soup.title else ''
        for link in soup.find_all('meta'):
            if link.get('name') == 'description':
                description = link.get('content')
                break
            else:
                description = ''
        conn, cur = connect()
        cur.execute(
            "INSERT INTO url_checks \
            (url_id, created_at, status_code, h1, title, description) \
            VALUES (%s, %s, %s, %s, %s, %s)",
            (id, date.today(), status_code, h1, title, description)
        )
        conn.commit()
        flash('Страница успешно проверена', 'success')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')
    response = make_response(
        redirect(url_for('url_page', id=id), code=302)
    )
    return response
