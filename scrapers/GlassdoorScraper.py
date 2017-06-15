from scrapers.RootScraper import RootScraper
from json import loads
from urllib.parse import urljoin
from dateutil.parser import parse
from web.db import get_scraper_session
from scrapers.data import JobInfo
from models import Scraper


class GlassdoorScraper(RootScraper):
    def __init__(self):
        self.rescrapables = ['https://www.glassdoor.co.in/Reviews/chandigarh-reviews-SRCH_IL.0,10_IC2879615.htm']
        self.done_rescrapables = False
        self.whitelist = ['www.glassdoor.com', 'www.glassdoor.co.in']

    def extract_employe(self, soup):
        org_domain = None
        org_desc = ''
        headquarters_address = None
        size = None
        founded_at = None
        org_type = None
        industry = None
        revenue = None
        competitors = None
        org_logo = None

        for row in soup.select('.infoEntity'):
            if row.find('label').text.lower() == 'website':
                org_domain = row.find('span').text.strip()

            if row.find('label').text.lower() == 'headquarters':
                headquarters_address = row.find('span').text.strip()

            if row.find('label').text.lower() == 'size':
                size = row.find('span').text.strip()

            if row.find('label').text.lower() == 'founded':
                try:
                    founded_at = parse(row.find('span').text, fuzzy=True)
                except ValueError:
                    pass

            if row.find('label').text.lower() == 'type':
                org_type = row.find('span').text.strip()

            if row.find('label').text.lower() == 'industry':
                industry = row.find('span').text.strip()

            if row.find('label').text.lower() == 'revenue':
                revenue = row.find('span').text.strip()

            if row.find('label').text.lower() == 'competitors':
                competitors = row.find('span').text.strip()

        for desc in soup.select('div'):
            if desc.get('data-full'):
                org_desc += desc.get('data-full').strip()

        for desc in soup.select('p'):
            if desc.get('data-full'):
                org_desc += desc.get('data-full').strip()

        org_desc = org_desc if org_desc != '' else None

        if soup.select_one('.logoOverlay').find('img'):
            org_logo = soup.select_one('.logoOverlay').find('img').get('src')

        if soup.select_one('.tightAll'):
            organization = soup.select_one('.tightAll').text.strip()

        org_fields = dict(organization=organization, org_domain=org_domain,
                          org_desc=org_desc, org_logo=org_logo,
                          headquarters_address=headquarters_address, size=size,
                          founded_at=founded_at, org_type=org_type,
                          industry=industry, revenue=revenue,
                          competitors=competitors)

        return JobInfo(org_fields)

    def _extract_reviews(self, review_link, base_url):
        reviews = []

        while review_link:
            review_soup = self.make_soup(review_link)
            review_link = None
            next_link = review_soup.select_one('.next')

            if next_link:
                review_link = urljoin(
                    base_url, next_link.find('a').get('href')
                ) if next_link.find('a') else None

            for div in review_soup.select('.hreview'):
                try:
                    review_date = parse(div.select_one(
                        '.cf').text.strip(), fuzzy=True)
                except ValueError:
                    review_date = None

                review_summary = div.select_one('.h2').text.strip()
                author_job = div.select_one('.authorJobTitle').text.strip(
                ) if div.select_one('.authorJobTitle') else None
                author_location = div.select_one('.authorLocation').text.strip(
                ) if div.select_one('.authorLocation') else None
                review_desc = div.select_one('.description').text.strip()

                reviews.append(dict(review_date=review_date,
                                    review_summary=review_summary,
                                    author_job=author_job,
                                    author_location=author_location,
                                    review_desc=review_desc))

        return reviews

    def extract_job_info(self, soup, base_url):
        try:
            organization = None
            job_source = None
            job_title = None
            country = None
            state = None
            city = None
            reviews = []

            job_desc = soup.select_one('.jobDescriptionContent').text.strip(
            ) if soup.select_one('.jobDescriptionContent') else None

            content = loads(soup.find(
                'script', type="application/ld+json").text, strict=False)
            job_title = content.get('title')
            job_source = content.get('url')

            try:
                job_created_at = parse(content.get('datePosted'), fuzzy=True)
            except ValueError:
                job_created_at = None

            try:
                last_date = parse(content.get('validThrough'), fuzzy=True)
            except ValueError:
                last_date = None

            organization = content.get('hiringOrganization').get('name')
            org_logo = content.get('image')
            city = content.get('addressLocality')

            if soup.select_one('.padBot'):
                review_link = urljoin(
                    base_url, soup.select_one('.padBot').get('href'))
                reviews = self._extract_reviews(review_link, base_url)

            org_fields = dict(organization=organization, org_logo=org_logo)

            return JobInfo(org_fields, country, state, city, job_source,
                           job_title, job_created_at, job_desc, reviews,
                           last_date)
        except Exception as error:
            print("Cannot extract job information: ", error)

    def parse(self):
        scraper_session = get_scraper_session()
        links = self.rescrapables

        while links:
            if self.done_rescrapables:
                links = self.get_next_links(scraper_session, Scraper)
            else:
                self.done_rescrapables = True

            for link in links:
                job_info = None

                try:
                    soup = self.make_soup(link)
                except Exception:
                    continue

                if soup.select_one('#JobDescContainer'):
                    job_info = self.extract_job_info(soup, link)

                if soup.select_one('.empBasicInfo'):
                    if soup.select_one('.empBasicInfo').select('.infoEntity'):
                        job_info = self.extract_employe(soup)

                next_links = self.extract_next_links(soup, link)

                self.scrap_in_future(scraper_session, Scraper, next_links)
                self.onsuccess(scraper_session, Scraper, link)

                yield job_info
