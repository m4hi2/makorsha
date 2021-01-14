import scrapy
import re
import datetime
import json

from format_date import format_date
from pathlib import Path


RE_PATH = r"/([a-z]+\d+.\w+)$"

class BDnewsSpider(scrapy.Spider):
    """
    Spider for bdnews24.com
    """
    name = "bdnews"
    def __init__(self, save_location="./", start_date=None, end_date=None):
        self.article_path = re.compile(RE_PATH)
        self.count = 0
        self.save_location = save_location
        self.save_location_segment = None
        self.title_selector = "h1.print-only::text"
        self.writer_selector = "span.authorName::text"
        self.publish_date_selector = ".dateline > span:nth-child(2)::text"
        self.article_selector = "div.custombody > p::text"
        self.arternet_article_selector = ".custombody"


        if not start_date:
            self.start_date = datetime.date.today()
        else:
            self.start_date = format_date(start_date)
        
        if not end_date:
            # bdnews24's oldest "usable" sitemap is to this date
            self.end_date = datetime.date(2007, 6, 1) 
        else:
            self.end_date = format_date(end_date)

        Path(save_location).mkdir(parents=True, exist_ok=True)


    def start_requests(self):
        base_url = "https://bangla.bdnews24.com/archive/?date="
        current = self.start_date
        delta = datetime.timedelta(days=-1)
        while current >= self.end_date:
            date_str = current.strftime("%Y-%m-%d")
            current = current + delta
            url = f"{base_url}{date_str}"
            yield scrapy.Request(url=url, callback=self.parse)

    
    def parse(self, response):
        if "archive" in response.url:
            urls = response.css("li.article > a::attr(href)").getall()
            for url in urls:
                url = url.strip()
                yield scrapy.Request(url=url, callback=self.parse)

        else: 
            title = response.css(self.title_selector).get()
            writer = response.css(self.writer_selector).get()
            publishing_date = response.css(self.publish_date_selector).get()
            article_segments = response.css(self.article_selector).getall()
            article = " ".join([s.strip() for s in article_segments])
            if not article:
                article_element = response.css(self.arternet_article_selector).get()
                article_element = article_element.replace("\n", " ")
                article = re.findall(r"</style>(.*)</div>", article_element)
                if len(article) > 0:
                    article = article[0]
                    article = article.replace("<br>", " ")

            article = article.replace("\n", " ")

            data_buffer = {
                "title" : title, 
                "writer" : writer,
                "publishing_date" : publishing_date,
                "article" : article
            }

            data_buffer_json = json.dumps(data_buffer, ensure_ascii=False)
            filename = f"{self.article_path.findall(response.url)[0]}.json"

            if self.count % 10000 == 0:
                self.save_location_segment = self.save_location + "/" + str(self.count // 10000)
                Path(self.save_location_segment).mkdir(parents=True, exist_ok=True)
            
            file_save_path = f"{self.save_location_segment}/{filename}"
            with open(file_save_path, 'w') as file:
                file.write(data_buffer_json)
                self.log(f"Saved file: {file_save_path}")
                self.log(f"Count: {self.count}")
                self.count += 1