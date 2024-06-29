from dotenv import load_dotenv
import os
from datetime import date
import psycopg2
from validators.url import url
from urllib.parse import urlparse
from flask import Flask, render_template, request, make_response, \
    url_for, redirect, get_flashed_messages, flash


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()


@app.route('/')
def main_page():
    messages = get_flashed_messages(with_categories=True)
    entry = {'name': ''}
    all_entries = get_all_urls()
    return render_template(
        'main.html',
        messages=messages,
        entry=entry,
        all_entries=all_entries
    )


@app.post('/')
def add_entry():
    new_entry = validate_and_normalize(request.form.to_dict()['url'])
    if not new_entry:
        flash('Incorrect URL', 'error')
    elif new_entry in get_all_urls():
        flash('URL already exists', 'warning')
    else:
        cur.execute(
            "INSERT INTO urls (name, created_at) VALUES (%s, %s)",
            (new_entry, date.today())
        )
        conn.commit()
        flash('Website was added successfully', 'success')
    response = make_response(redirect(url_for('main_page'), code=302))
    return response


def validate_and_normalize(url_str):
    if url(url_str) and len(url_str) <= 255:
        parsed_url = urlparse(url_str)
        return f'{parsed_url.scheme}://{parsed_url.netloc}'


def get_all_urls():
    cur.execute("SELECT name FROM urls;")
    all_entries = cur.fetchall()
    return [entry[0] for entry in all_entries]
