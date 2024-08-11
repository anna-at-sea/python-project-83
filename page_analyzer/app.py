import os
from page_analyzer.db_manager import get_all_urls_table, add_url, \
    add_url_check, get_urls_list, get_url_id_by_name, get_url_by_id, \
    get_url_checks_by_id
from page_analyzer.url_parser import validate, normalize, \
    get_url_info, check_for_errors
from dotenv import load_dotenv
from flask import Flask, render_template, request, make_response, \
    url_for, redirect, flash, get_flashed_messages


load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


@app.route('/')
def main_page():
    return render_template(
        'main.html'
    )


@app.post('/')
def add_entry():
    entry = request.form.to_dict()['url']
    new_entry = normalize(entry) if validate(entry) else None
    names_list = get_urls_list()
    if not new_entry:
        flash('Некорректный URL', 'danger')
        return render_template('main.html'), 422
    elif new_entry in names_list:
        flash('Страница уже существует', 'info')
    else:
        add_url(new_entry)
        flash('Страница успешно добавлена', 'success')
    new_entry_id = get_url_id_by_name(new_entry)
    response = make_response(
        redirect(url_for('url_page', id=new_entry_id), code=302)
    )
    return response


@app.route('/urls/<int:id>')
def url_page(id):
    current_url = get_url_by_id(id)
    if not current_url:
        return render_template('not_found.html'), 404
    url_name, url_date = current_url
    url_checks = get_url_checks_by_id(id)
    return render_template(
        'url_page.html',
        id=id,
        name=url_name,
        date=url_date,
        url_checks=url_checks
    )


@app.route('/urls')
def all_urls():
    messages = get_flashed_messages(with_categories=True)
    if messages:
        return render_template(
            'main.html'
        ), 422
    all_urls = get_all_urls_table()
    return render_template(
        'all_urls.html',
        all_urls=all_urls
    )


@app.post('/urls/<id>/checks')
def check_url(id):
    name = get_url_by_id(id)[0]
    try:
        check_for_errors(name)
        add_url_check(id, *get_url_info(name))
        flash('Страница успешно проверена', 'success')
    except Exception:
        flash('Произошла ошибка при проверке', 'danger')
    response = make_response(
        redirect(url_for('url_page', id=id), code=302)
    )
    return response
