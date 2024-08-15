from bs4 import BeautifulSoup
from validators.url import url
from urllib.parse import urlparse


def validate(url_str):
    return url(url_str) and len(url_str) <= 255


def normalize(url_str):
    parsed_url = urlparse(url_str)
    return f'{parsed_url.scheme}://{parsed_url.netloc}'


def get_url_info(html):
    soup = BeautifulSoup(html.text, 'html.parser')
    status_code = html.status_code
    h1 = soup.h1.string if soup.h1 else ''
    title = soup.title.string if soup.title else ''
    description = ''
    for link in soup.find_all('meta'):
        if link.get('name') == 'description':
            description = link.get('content')
            break
    return status_code, h1, title, description
