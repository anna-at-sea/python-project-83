import os
import requests
from page_analyzer.db_manager import select_from_bd, insert_into_bd, \
    get_all_urls_table
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


def validate_and_normalize(url_str):
    if url(url_str) and len(url_str) <= 255:
        parsed_url = urlparse(url_str)
        return f'{parsed_url.scheme}://{parsed_url.netloc}'


@app.route('/')
def main_page():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'main.html',
        messages=messages
    )


@app.post('/')
def add_entry():
    entry = request.form.to_dict()['url']
    new_entry = validate_and_normalize(entry)
    all_names = select_from_bd('urls', ['name'])
    names_list = [name[0] for name in all_names]
    if not new_entry:
        flash('Некорректный URL', 'danger')
        return make_response(redirect(url_for('all_urls'), code=302))
    elif new_entry in names_list:
        flash('Страница уже существует', 'info')
    else:
        insert_into_bd(
            'urls',
            ['name', 'created_at'],
            (new_entry, date.today())
        )
        flash('Страница успешно добавлена', 'success')
    new_entry_id = select_from_bd('urls', ['id'], {'name': new_entry})[0][0]
    response = make_response(
        redirect(url_for('url_page', id=new_entry_id), code=302)
    )
    return response


@app.route('/urls/<int:id>')
def url_page(id):
    messages = get_flashed_messages(with_categories=True)
    current_url = select_from_bd('urls', where={'id': id})
    if not current_url:
        return render_template('not_found.html'), 404
    url_name = current_url[0][1]
    url_date = current_url[0][2]
    url_checks = select_from_bd(
        'url_checks',
        ['id', 'created_at', 'status_code', 'h1', 'title', 'description'],
        {'url_id': id},
        True)
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
    messages = get_flashed_messages(with_categories=True)
    if messages:
        return render_template(
            'main.html',
            messages=messages
        ), 422
    all_urls = get_all_urls_table()
    return render_template(
        'all_urls.html',
        all_urls=all_urls
    )


@app.post('/urls/<id>/checks')
def check_url(id):
    name = select_from_bd('urls', ['name'], {'id': id})[0][0]
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
        insert_into_bd(
            'url_checks',
            ['url_id', 'created_at', 'status_code',
             'h1', 'title', 'description'],
            (id, date.today(), status_code, h1, title, description)
        )
        flash('Страница успешно проверена', 'success')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')
    response = make_response(
        redirect(url_for('url_page', id=id), code=302)
    )
    return response
