import os
import requests
from page_analyzer.db_manager import get_all_urls_table, add_url, \
    add_url_check, get_url_id_by_name, get_url_by_id, \
    get_url_checks_by_id
from page_analyzer.url_parser import validate, normalize, \
    get_url_info
from dotenv import load_dotenv
from flask import Flask, render_template, request, \
    url_for, redirect, flash
from psycopg2.errors import UniqueViolation


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def main_page():
    return render_template(
        'pages/main.html'
    )


@app.post('/urls')
def add_entry():
    entry = request.form.to_dict()['url']
    new_entry = normalize(entry) if validate(entry) else None
    if not new_entry:
        flash('Некорректный URL', 'danger')
        return render_template(
            'pages/main.html',
            checked_url=entry
        ), 422
    try:
        new_entry_id = add_url(new_entry)
        flash('Страница успешно добавлена', 'success')
    except UniqueViolation:
        new_entry_id = get_url_id_by_name(new_entry)
        flash('Страница уже существует', 'info')
    return redirect(url_for('url_page', id=new_entry_id), code=302)


@app.route('/urls/<int:id>')
def url_page(id):
    current_url = get_url_by_id(id)
    if not current_url:
        return render_template('pages]/not_found.html'), 404
    url_checks = get_url_checks_by_id(id)
    return render_template(
        'pages/url_page.html',
        id=id,
        name=current_url['name'],
        date=current_url['date'],
        url_checks=url_checks
    )


@app.route('/urls')
def all_urls():
    all_urls = get_all_urls_table()
    return render_template(
        'pages/all_urls.html',
        all_urls=all_urls
    )


@app.post('/urls/<id>/checks')
def check_url(id):
    name = get_url_by_id(id)['name']
    try:
        response = requests.get(name)
        response.raise_for_status()
        add_url_check(id, response.status_code, *get_url_info(response.content))
        flash('Страница успешно проверена', 'success')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')
    return redirect(url_for('url_page', id=id), code=302)
