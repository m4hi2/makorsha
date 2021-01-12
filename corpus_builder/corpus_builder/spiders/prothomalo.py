import datetime
import scrapy
import re

from pathlib import Path
from urllib.parse import unquote 


RE_URL = r"<loc>(https://\D+)</loc>"
RE_PATH = r"/([^a-z | /]+)"  # The last part of the URL


class ProthomAloSpider(scrapy.Spider):
    name = "prothomalo"

    def __init__(self, save_location="./"):
        self.article_path = re.compile(RE_PATH)
        self.count = 0
        self.save_location = save_location
        Path(save_location).mkdir(parents=True, exist_ok=True)


    def start_requests(self):
        base_url = "https://www.prothomalo.com/sitemap/sitemap-daily-"
        current = datetime.date.today()
        delta = datetime.timedelta(days=-1)
        while int(current.strftime("%Y")) > 2009:
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
            filename = unquote(f"{self.article_path.findall(response.url)[0]}.html")
            with open(f"{self.save_location}/{filename}", 'wb') as file:
                file.write(response.body)
                self.log(f"Saved file: {filename}")