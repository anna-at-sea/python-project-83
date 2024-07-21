import requests
from bs4 import BeautifulSoup
from validators.url import url
from urllib.parse import urlparse


def validate_and_normalize(url_str):
    if url(url_str) and len(url_str) <= 255:
        parsed_url = urlparse(url_str)
        return f'{parsed_url.scheme}://{parsed_url.netloc}'


class URLInfo:
    def __init__(self, url):
        self.html = requests.get(url)
        self.soup = BeautifulSoup(self.html.text, 'html.parser')

    def check_for_errors(self):
        return requests.Response.raise_for_status(self.html)

    def get_status_code(self):
        return self.html.status_code

    def get_h1(self):
        return self.soup.h1.string if self.soup.h1 else ''

    def get_title(self):
        return self.soup.title.string if self.soup.title else ''

    def get_description(self):
        for link in self.soup.find_all('meta'):
            if link.get('name') == 'description':
                return link.get('content')
        return ''
