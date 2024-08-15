from bs4 import BeautifulSoup
from validators.url import url
from urllib.parse import urlparse


def validate(url_str):
    return url(url_str) and len(url_str) <= 255


def normalize(url_str):
    parsed_url = urlparse(url_str)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'


def get_url_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = soup.find('meta', {'name': 'description'})
    return h1, title, description.get('content') if description else ''
