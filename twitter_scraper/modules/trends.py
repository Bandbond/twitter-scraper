from requests_html import HTML, HTMLSession
from .headers import get_headers


def get_trends():
    session = HTMLSession()
    html = session.get("https://twitter.com/i/trends", headers=get_headers())
    html = html.json()["module_html"]
    html = HTML(html=html, url="bunk", default_encoding="utf-8")
    for trend_item in html.find("li"):
        trend_text = trend_item.attrs["data-trend-name"]
        yield trend_text
