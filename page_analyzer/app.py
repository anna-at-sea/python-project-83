from dotenv import load_dotenv
import os
import datetime
import psycopg2
from flask import Flask, render_template, request, make_response, url_for, redirect, get_flashed_messages, flash

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
    return render_template(
        'main.html',
        messages=messages,
        entry=entry
    )

@app.post('/')
def add_entry():
    new_entry = request.form.to_dict()
    cur.execute("INSERT INTO urls (name, created_at) VALUES (%s, %s)", (new_entry['url'], datetime.datetime.now()))
    conn.commit()
    response = make_response(redirect(url_for('main_page'), code=302))
    flash('Website was added successfully', 'success')
    return response
