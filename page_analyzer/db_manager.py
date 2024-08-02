import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def connect():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    return conn, cur


def select_from_bd(table, columns=[], where={}, desc=False):
    columns_to_str = '' if columns != [] else '*'
    for column in columns:
        columns_to_str += f'{column}, '
    where_to_str = ''
    val = None
    if where:
        for key, value in where.items():
            where_to_str = f' WHERE {key} = %s'
            val = (value,)
    order_by = ' ORDER BY id DESC' if desc else ''
    query_without_where = f"SELECT {columns_to_str.strip(' ,')} \
    FROM {table}{where_to_str}{order_by};"
    _, cur = connect()
    if not val:
        cur.execute(query_without_where)
    else:
        cur.execute(query_without_where, val)
    return cur.fetchall()


def add_url(name):
    conn, cur = connect()
    cur.execute("INSERT INTO urls (name) VALUES (%s)", (name,))
    conn.commit()


def add_url_check(*values):
    conn, cur = connect()
    cur.execute(
        "INSERT INTO url_checks (url_id, status_code, h1, title, description) \
        VALUES (%s, %s, %s, %s, %s)", (values)
    )
    conn.commit()


def get_all_urls_table():
    _, cur = connect()
    cur.execute(
        "WITH filtered_checks \
        AS (\
        SELECT url_id, MAX(DATE(created_at)) AS created_at, status_code \
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
    return cur.fetchall()
