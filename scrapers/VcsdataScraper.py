from scrapers.RootScraper import RootScraper
from web.db import get_scraper_session
from models import Scraper
from scrapers.data import JobInfo


class VcsdataScraper(RootScraper):
    def __init__(self):
        self.rescrapables = ['http://www.vcsdata.com/ajax.php?gofor=show_listing_city&tot_page=8&&page={}&city=Chandigarh&scrpt_name=companies_chandigarh.php']
        self.done_rescrapables = False
        self.whitelist = ['www.vcsdata.com']

    def extract_organization(self, soup, base_url):
        organization = None
        org_domain = None
        phone_no = None
        country = "India"
        state = None
        city = None
        headquarters = None
        industries = []
        org_type = None
        revenue = None
        size = None
        pin = None
        org_desc = None

        metadata = soup.select_one('.contentlisting')

        if metadata.select_one('.repeater'):
            repeater_metadata = [j for j in [
                i.text.strip().split(':')
                for i in metadata.select('.repeater')]
            ]

        if metadata.select_one('.list1'):
            list_metadata = [j for j in [
                i.text.strip().split(':')
                for i in metadata.select('.list1')]
            ]

        if metadata.select_one('.pull_left'):
            industries = [i .strip()for i in metadata.select_one(
                '.pull_left').text.split(':')[1].split('/')]

        if metadata.select_one('.listRow'):
            organization = metadata.select_one('.listRow').text.strip()

        if metadata.find(itemprop='url'):
            org_domain = metadata.find(itemprop='url').text.strip()

        if metadata.find(itemprop='telephone'):
            phone_no = metadata.find(itemprop='telephone').text.strip()

        if metadata.find(itemprop='location'):
            city = metadata.find(itemprop='location').text.strip()

        if metadata.find(itemprop='address'):
            headquarters = metadata.find(itemprop='address').text.strip()

        if len(metadata.select('.TabbedPanelsContent')) > 2:
            org_desc = metadata.select_one('.TabbedPanelsContent').text.strip()

        for text in repeater_metadata:
            if text[0].strip().lower() == 'sector':
                org_type = text[1].strip()

            if text[0].strip().lower() == 'total turnover':
                revenue = text[1].strip()

            if text[0].strip().lower() == 'no of employees':
                size = text[1].strip() + ' employees'

        for text in list_metadata:
            if text[0].strip().lower() == 'state':
                state = text[1].strip()

            if text[0].strip().lower() == 'pin code':
                pin = text[1].strip()

        org_fields = dict(organization=organization, org_domain=org_domain,
                          org_desc=org_desc, headquarters_address=headquarters,
                          size=size, org_type=org_type, revenue=revenue,
                          phone_no=phone_no)

        return JobInfo(org_fields, country, state, city,
                       pin_code=pin, industries=industries)

    def parse(self):
        scraper_session = get_scraper_session()
        links = self.rescrapables

        while links:
            if self.done_rescrapables:
                links = self.get_next_links(scraper_session, Scraper)
            else:
                self.done_rescrapables = True
                next_links = []
                soup = self.make_soup(links[0].format(1))
                pages = int([i.text for i in soup.select_one(
                    '.pagination').select('a')][-2])

                for i in range(1, pages+1):
                    next_links.append(dict(url=links[0].format(i)))

                self.scrap_in_future(scraper_session, Scraper, next_links)
                continue

            for link in links:
                org_info = None

                try:
                    soup = self.make_soup(link)
                except Exception:
                    continue

                if soup.select_one('.repeater'):
                    org_info = self.extract_organization(soup, link)

                next_links = self.extract_next_links(soup, link)

                self.scrap_in_future(scraper_session, Scraper, next_links)
                self.onsuccess(scraper_session, Scraper, link)

                yield org_info
