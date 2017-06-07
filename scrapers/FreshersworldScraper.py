from dateutil.parser import parse
from scrapers.RootScraper import RootScraper
from db import get_scraper_session
from scrapers.data import JobInfo


class FreshersworldScraper(RootScraper):
    def __init__(self):
        self.rescrapables = ['https://www.freshersworld.com/']
        self.done_rescrapables = False
        self.whitelist = ['www.freshersworld.com']

    def extract_job_info(self, soup, url):
        job_container = soup.select('.job-container')
        org_desc = None
        organization = None
        country = "India"
        state = None
        city = None
        job_source = url
        job_title = None
        job_created_at = None
        job_desc = None
        last_date = None
        org_domain = None
        qualifications = []
        reviews = []

        for job in job_container:
            if job.select_one('.latest-jobs-title'):
                job_title = job.select_one('.latest-jobs-title').text.strip()

            if job.select_one('.font-13'):
                organization = job.select_one('.font-13').text.strip()

            if job.select_one('.job-location'):
                city = job.select_one('.job-location').text.strip()

            if job.select_one('.qualifications'):
                q = job.select_one('.qualifications').text.strip()
                qualifications = [i.strip() for i in q.split(',')]

            job_apply_container = job.select_one('.view-apply-container')

            if job.select_one('.last-date'):
                last_date = job_apply_container.select_one('.padding-left-4').text.strip()
                last_date = parse(last_date, fuzzy=True)

            if job.find('span', itemprop='datePosted'):
                job_created_at = job.find('span', itemprop='datePosted').text.strip()
                job_created_at = parse(job_created_at, fuzzy=True)

            job_info_div = job.select_one('.margin-top-7')

            if job_info_div:
                if job_info_div.select_one('.padding-none'):
                    job_desc = job_info_div.select_one('.padding-none').text.strip()

            if job.select_one('.company-desc-det'):
                org_desc = job.select_one('.company-desc-det').text.strip()
                company_weblink = job.select_one('.company-desc-det').select_one('.company-weblink')

                if company_weblink:
                    org_domain = company_weblink.find('a').get('href')

        org_fields = dict(org_domain=org_domain, org_desc=org_desc)

        return JobInfo(org_fields, organization, country, state, city,
                       job_source, job_title, job_created_at, job_desc,
                       reviews, last_date, qualifications)

    def parse(self):
        scraper_session = get_scraper_session()
        links = self.rescrapables

        while links:
            if self.done_rescrapables:
                links = self.get_next_links(scraper_session)
            else:
                self.done_rescrapables = True

            for link in links:
                job_info = None

                try:
                    soup = self.make_soup(link)
                except Exception:
                    continue

                if soup.select_one('.company-desc-det'):
                    job_info = self.extract_job_info(soup, link)

                next_links = self.extract_next_links(soup, link)

                self.scrap_in_future(scraper_session, next_links)
                self.onsuccess(scraper_session, link)

                yield job_info
