import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')


def connection():
    return psycopg2.connect(DATABASE_URL)


def get_urls_list():
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM urls;")
        return [name[0] for name in cur.fetchall()]


def get_url_id_by_name(name):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM urls WHERE name = %s;", (name,))
        return cur.fetchall()[0][0]


def get_url_by_id(id):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, DATE(created_at) FROM urls WHERE id = %s;", (id,)
        )
        name, created_at = cur.fetchall()[0]
        return name, created_at


def get_url_checks_by_id(id):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, DATE(created_at), status_code, h1, title, description \
            FROM url_checks WHERE url_id = %s ORDER BY id DESC;", (id,)
        )
        return cur.fetchall()


def add_url(name):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO urls (name) VALUES (%s) RETURNING id;", (name,)
        )
        id = cur.fetchall()[0][0]
        conn.commit()
    return id


def add_url_check(*values):
    with connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO url_checks \
            (url_id, status_code, h1, title, description) \
            VALUES (%s, %s, %s, %s, %s)", (values)
        )
        conn.commit()


def get_all_urls_table():
    with connection() as conn:
        cur = conn.cursor()
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
