from Scrapers.RootScraper import RootScraper
from json import loads, JSONDecodeError
from urllib.parse import urljoin
from slimit import ast
from slimit.parser import Parser
from slimit.visitors import nodevisitor
from dateutil.parser import parse
from db import get_scraper_session
from scrapers.data import JobInfo


class GlassdoorScraper(RootScraper):
    def __init__(self):
        self.rescrapables = ['https://www.glassdoor.co.in/Job/chandigarh-jobs-SRCH_IL.0,10_IC2879615.htm']
        self.done_rescrapables = False
        self.whitelist = ['www.glassdoor.com', 'www.glassdoor.co.in']
        self.company_info_url = "https://www.glassdoor.co.in/Overview/companyOverviewBasicInfoAjax.htm?&employerId={0}&title=Company+Info&linkCompetitors=true"

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

    def parse(self):
        scraper_session = get_scraper_session()
        links = self.rescrapables

        while links:
            if self.done_rescrapables:
                links = self.get_next_links(scraper_session)
            else:
                self.done_rescrapables = True

            for link in links:
                item_link = False
                job_info = None

                try:
                    soup = self.make_soup(link)
                except Exception:
                    continue

                if soup.select_one('.empBasicInfo'):
                    try:
                        if soup.find('script', type="application/ld+json"):
                            loads(soup.find(
                                'script', type="application/ld+json").text)
                    except JSONDecodeError:
                        item_link = True
                        pass

                if item_link:
                    job_info = self.extract_job_info(soup, link)
                    self.jobs_info.append(job_info)

                next_links = self.extract_next_links(soup, link)

                self.scrap_in_future(scraper_session, next_links)
                self.onsuccess(scraper_session, link)

                yield job_info
