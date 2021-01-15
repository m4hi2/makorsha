import scrapy 
import re
import datetime
import json

from pathlib import Path
# need to add the base link https://www.anandabazar.com to the return of this.
# article = response.css()"p::text".getall()

RE_PATH = r"/([a-z]+\-.+)$"

class AnadaBazar(scrapy.Spider):
    name = "anandabazar"

    def __init__(self, save_location="./anandabazar", start_page=1, end_page=50):
        self.article_path = re.compile(RE_PATH)
        self.archive_base_urls = [
            "https://www.anandabazar.com/entertainment/archive?page=",
            "https://www.anandabazar.com/state/archive?page=",
            "https://www.anandabazar.com/district/north-bengal/archive?page=",
            "https://www.anandabazar.com/district/howrah-hoogly/archive?page=",
            "https://www.anandabazar.com/district/24-paraganas/archive?page=",
            "https://www.anandabazar.com/district/nadia-murshidabad/archive?page=",
            "https://www.anandabazar.com/district/purulia-birbhum-bankura/archive?page=",
            "https://www.anandabazar.com/district/bardhaman/archive?page=",
            "https://www.anandabazar.com/district/midnapore/archive?page=",
            "https://www.anandabazar.com/calcutta/archive?page=",
            "https://www.anandabazar.com/national/archive?page=",
            "https://www.anandabazar.com/international/archive?page=",
            "https://www.anandabazar.com/bangladesh-news/archive?page=",
            "https://www.anandabazar.com/business/archive?page=",
            "https://www.anandabazar.com/editorial/archive?page=",
            "https://www.anandabazar.com/supplementary/sahisomachar/archive?page=",
            "https://www.anandabazar.com/others/science/archive?page=",
            "https://www.anandabazar.com/sport/archive?page=",
            "https://www.anandabazar.com/lifestyle/archive?page=",
            "https://www.anandabazar.com/women/archive?page=",
            "https://www.anandabazar.com/travel/archive?page=",
            ]
        self.article_links_selector = "article.search-result > div > h3 > a::attr('href')"
        self.article_selector = "p::text"
        self.writer_selector = "li.name:nth-child(2)::text"
        self.publishing_date_selector = ".author-block > ul:nth-child(2) > li:nth-child(2)::text"
        self.title_selector = ".abp-storypage-headline > h1:nth-child(1)::text"
        self.base_url = "https://www.anandabazar.com"
        self.count = 0
        self.save_location = save_location
        self.start_page = int(start_page)
        self.end_page = int(end_page)

        Path(save_location).mkdir(parents=True, exist_ok=True)

    def start_requests(self):
        for category in self.archive_base_urls:
            current_page = self.start_page
            while current_page <= self.end_page:
               url = category + str(current_page)
               current_page += 1
               yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        if "archive" in response.url:
            article_links = response.css(self.article_links_selector).getall()
            for link in article_links:
                url = self.base_url + link
                yield scrapy.Request(url=url, callback=self.parse) 

        else:
            article_fragments = response.css(self.article_selector).getall()
            for i in range(article_fragments.count("Advertisement")):
                article_fragments.remove("Advertisement")
            article = " ".join(article_fragments)
            writer = response.css(self.writer_selector).get()
            writer = writer.strip()
            publishing_date = response.css(self.publishing_date_selector).get()
            publishing_date = publishing_date.strip()
            title = response.css(self.title_selector).get()
            title = title.strip()

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