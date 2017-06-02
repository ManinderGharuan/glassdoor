from bs4 import BeautifulSoup
from requests import get
from random import choice
from json import loads
from urllib.parse import urljoin, urlparse
from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor
from datetime import datetime
from dateutil.parser import parse
from db import get_scraper_session
from models import Scraper
from data import JobInfo

user_agents = [
    'Googlebot/2.1 (+http://www.google.com/bot.html)',
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (FM Scene 4.6.1) ',
    'AltaVista Intranet V2.0 AVS EVAL search@freeit.com',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36',
    "Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20",
    "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT 5.0 )",
    "Links (2.1pre15; FreeBSD 5.3-RELEASE i386; 196x84)"
    "Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.0.3) Gecko/2008092414 Firefox/3.0.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:9.0) Gecko/20100101 Firefox/9.0",
    "Mozilla/5.0 (X11; U; Linux x86_64; sv-SE; rv:1.8.1.12) Gecko/20080207 Ubuntu/7.10 (gutsy) Firefox/2.0.0.12",
]


class GlassdoorScraper:
    def __init__(self):
        self.rescrapables = ['https://www.glassdoor.co.in/Job/chandigarh-jobs-SRCH_IL.0,10_IC2879615.htm']
        self.done_rescrapables = False
        self.whitelist = ['www.glassdoor.com', 'www.glassdoor.co.in']
        self.company_info_url = "https://www.glassdoor.co.in/Overview/companyOverviewBasicInfoAjax.htm?&employerId={0}&title=Company+Info&linkCompetitors=true"
        self.jobs_info = []

    def make_soup(self, url):
        """
        Takes a url, and return BeautifulSoup for that Url
        """
        header = {
            'user-agent': choice(user_agents)
        }
        print("Downloading page: " + url)

        return BeautifulSoup(get(url, headers=header).
                             content, 'html5lib')

    def get_next_links(self, session):
        """
        Returns next links from scraper database
        """
        try:
            while True:
                urls = session.query(Scraper.url) \
                              .filter(Scraper.scraped_at == None) \
                              .limit(50).all()

                for url in urls:
                    yield url[0]
        except Exception as error:
            print("Error while fetching url from scraper database: ", error)

    def scrap_in_future(self, session, urls):
        for url in urls:
            dup = session.query(Scraper).filter(
                Scraper.url.like('%' + url['url'] + '%')).first()

            if not dup:
                link = Scraper(**url)
                session.add(link)

    def extract_next_links(self, soup, base_url):
        """
        Returns links to scrap next from the soup
        """
        try:
            next_links = []

            for a in soup.select('a'):
                if a.get('href'):
                    link = urljoin(base_url, a.get('href'))

                    if urlparse(link).hostname in self.whitelist:
                        next_links.append(dict(url=link))

            return next_links
        except Exception as error:
            print("Exception in extracting next links: ", error)

    def onsuccess(self, session, link):
        scraper = session.query(Scraper).filter_by(url=link).first()

        if scraper:
            print("Done with: ", link)
            print("******" * 13)
            scraper.scraped_at = datetime.today()
            session.commit()

    def _extract_employe(self, employe_id):
        org_domain = None
        org_desc = ''
        headquarters_address = None
        size = None
        founded_at = None
        org_type = None
        industry = None
        revenue = None
        competitors = None

        soup = self.make_soup(self.company_info_url .format(employe_id))

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

        return dict(org_domain=org_domain, org_desc=org_desc,
                    headquarters_address=headquarters_address, size=size,
                    founded_at=founded_at, org_type=org_type,
                    industry=industry, revenue=revenue,
                    competitors=competitors)

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
            reviews = []

            script = soup.find('script').text
            parser = Parser()
            tree = parser.parse(script)
            fields = {
                getattr(
                    node.left, 'value', ''): getattr(node.right, 'value', '')
                for node in nodevisitor.visit(tree)
                if isinstance(node, ast.Assign)
            }
            country = fields.get("'country'").replace('"', "")
            country = country if country != '' else None
            state = fields.get("'state'").replace('"', "")
            state = state if state != '' else None
            city = fields.get("'city'").replace('"', "")
            city = city if city != '' else None
            job_source = fields.get("'untranslatedUrl'").replace('"', "")

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

            organization = content.get('hiringOrganization').get('name')
            employe_id = soup.select_one('.empBasicInfo').get('data-emp-id')
            org_fields = self._extract_employe(employe_id)

            if soup.select_one('.padBot'):
                review_link = urljoin(
                    base_url, soup.select_one('.padBot').get('href'))
                reviews = self._extract_reviews(review_link, base_url)

            return JobInfo(org_fields, organization, country, state,
                           city, job_source, job_title, job_created_at,
                           job_desc, reviews)
        except Exception as error:
            print("Cannot extract job information: ", error)
            raise Exception(error)

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
                soup = self.make_soup(link)

                if soup.select_one('.empBasicInfo'):
                    try:
                        if soup.find('script', type="application/ld+json"):
                            loads(soup.find(
                                'script', type="application/ld+json").text)
                    except ValueError:
                        job_info = self.extract_job_info(soup, link)
                        self.jobs_info.append(job_info)

                next_links = self.extract_next_links(soup, link)

                self.scrap_in_future(scraper_session, next_links)
                self.onsuccess(scraper_session, link)

                yield job_info
