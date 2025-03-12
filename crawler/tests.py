from django.test import TestCase
from crawler.crawling import *


class TestCrawler(TestCase):

    def test_parse_date(self):
        response = requests.get("https://www.sp-ps.ch/armut-soziale-kaelte/")
        soup = BeautifulSoup(response.text, features="lxml")
        date = get_published_date(soup)

        assert date is not None
        assert type(date) == datetime
