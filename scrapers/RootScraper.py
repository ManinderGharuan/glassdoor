from bs4 import BeautifulSoup
from requests import get
from random import choice
from datetime import datetime
from urllib.parse import urljoin, urlparse

user_agents = [
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


class RootScraper():
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

    def get_next_links(self, session, model):
        """
        Returns next links from scraper database
        """
        try:
            while True:
                urls = []
                for i in self.whitelist:
                    urls += session.query(model.url) \
                                  .filter(model.scraped_at == None,
                                          model.url.like('%' + i + '%')) \
                                  .limit(50).all()

                for url in urls:
                    yield url[0]
        except Exception as error:
            print("Error while fetching url from scraper database: ", error)

    def scrap_in_future(self, session, model, urls):
        for url in urls:
            url = urlparse(url['url'])

            if url.hostname == 'www.vcsdata.com':
                dup = session.query(model) \
                             .filter(model.url == url['url']).first()
            else:
                dup = session.query(model).filter(
                    model.url.like('%' + url.path + '%')).first()

            if not dup:
                link = model(**url)
                session.add(link)
                session.commit()

    def onsuccess(self, session, model, link):
        scraper = session.query(model).filter_by(url=link).first()

        if scraper:
            print("Done with: ", link)
            print("******" * 13)
            scraper.scraped_at = datetime.today()
            session.commit()

    def parse(self):
        """
        Should return list of jobs_info after assigning them to
        ~self.jobs_info~.
        To be implemented by child scrapers.
        """
        raise Exception("Implement it dumbfuck")
