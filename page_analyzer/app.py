import os
import requests
from page_analyzer.db_manager import get_all_urls_table, add_url, \
    add_url_check, get_url_id_by_name, get_url_by_id, \
    get_url_checks_by_id
from page_analyzer.url_parser import validate, normalize, \
    get_url_info
from dotenv import load_dotenv
from flask import Flask, render_template, request, make_response, \
    url_for, redirect, flash
from psycopg2.errors import UniqueViolation


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def main_page():
    return render_template(
        'layouts/main.html'
    )


@app.post('/urls')
def add_entry():
    entry = request.form.to_dict()['url']
    new_entry = normalize(entry) if validate(entry) else None
    if not new_entry:
        flash('Некорректный URL', 'danger')
        return render_template(
            'layouts/main.html',
            checked_url=entry
        ), 422
    try:
        new_entry_id = add_url(new_entry)
        flash('Страница успешно добавлена', 'success')
    except UniqueViolation:
        new_entry_id = get_url_id_by_name(new_entry)
        flash('Страница уже существует', 'info')
    response = make_response(
        redirect(url_for('url_page', id=new_entry_id), code=302)
    )
    return response


@app.route('/urls/<int:id>')
def url_page(id):
    current_url = get_url_by_id(id)
    if not current_url:
        return render_template('layouts/not_found.html'), 404
    url_checks = get_url_checks_by_id(id)
    return render_template(
        'layouts/url_page.html',
        id=id,
        name=current_url['name'],
        date=current_url['date'],
        url_checks=url_checks
    )


@app.route('/urls')
def all_urls():
    all_urls = get_all_urls_table()
    return render_template(
        'layouts/all_urls.html',
        all_urls=all_urls
    )


@app.post('/urls/<id>/checks')
def check_url(id):
    name = get_url_by_id(id)['name']
    try:
        html = requests.get(name)
        requests.Response.raise_for_status(html)
        add_url_check(id, *get_url_info(html))
        flash('Страница успешно проверена', 'success')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')
    response = make_response(
        redirect(url_for('url_page', id=id), code=302)
    )
    return response
