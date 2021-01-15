import datetime
import json
import scrapy
import re

from pathlib import Path
from urllib.parse import unquote 


RE_URL = r"<loc>(https://\D+)</loc>"
RE_PATH = r"/([^a-z | /]+)"  # The last part of the URL


class ProthomAloSpider(scrapy.Spider):
    name = "prothomalo"

    def __init__(self, save_location="./prothomalo", start_date=None, end_date=None):
        self.article_path = re.compile(RE_PATH)
        self.count = 0
        self.save_location = save_location
        self.title_selector = "h1.headline"
        self.writer_selector = "span.contributor-name"
        self.publish_date_selector = "div.time-social-share-wrapper > div > span"
        self.article_selector = "div.story-element-text > div > p"

        if not start_date:
            self.start_date = datetime.date.today()
        else:
            self.start_date = format_date(start_date)
        
        if not end_date:
            # Prothom Alo's oldest sitemap is to this date
            self.end_date = datetime.date(2009, 9, 1) 
        else:
            self.end_date = format_date(end_date)

        Path(save_location).mkdir(parents=True, exist_ok=True)


    def start_requests(self):
        base_url = "https://www.prothomalo.com/sitemap/sitemap-daily-"
        current = self.start_date
        delta = datetime.timedelta(days=-1)
        while current >= self.end_date:
            date_str = current.strftime("%Y-%m-%d")
            current = current + delta
            url = f"{base_url}{date_str}.xml"
            yield scrapy.Request(url=url, callback=self.parse)


    def parse(self, response):
        """
        Parsing the junk that is Prothom Alo Sitemap
        """
        if "poll" in response.url:
            pass

        if "sitemap" in response.url:
            urls = response.selector.re(RE_URL)
            self.log(f"The cout of links: {len(urls)}")
            for url in urls:
                url = url.strip()
                yield scrapy.Request(url=url, callback=self.parse)
        else: 
            title = response.css(f"{self.title_selector}::text").get()
            writer = response.css(f"{self.writer_selector}::text").get()
            publishing_date = response.css(f"{self.publish_date_selector}::text").get()
            article_segments = response.css(f"{self.article_selector}::text").getall()
            article = " ".join(article_segments)

            data_buffer = {
                "title" : title,
                "writer" : writer,
                "publishing_date" : publishing_date,
                "article" : article
            }

            data_buffer_json = json.dumps(data_buffer, ensure_ascii=False)
            filename = unquote(f"{self.article_path.findall(response.url)[0]}.json")
            with open(f"{self.save_location}/{filename}", 'w') as file:
                file.write(data_buffer_json)
                self.log(f"Saved file: {filename}")


def format_date(raw_date):
    """
    Extracts date from YYYY-MM-DD format and returns a date object.
    """
    date_fragments = raw_date.split("-")
    return datetime.date(*[int(i) for i in date_fragments])
    