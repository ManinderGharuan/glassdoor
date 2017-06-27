from scrapers.GlassdoorScraper import GlassdoorScraper
from scrapers.FreshersworldScraper import FreshersworldScraper
from scrapers.VcsdataScraper import VcsdataScraper
from web.db import get_session
from scrapers.save_jobs import save_jobs_in_database


def scrapers():
    """
    Run scraper and save job_info in database
    """
    session = get_session()

    try:
        g = GlassdoorScraper()

        for info in g.parse():
            if info:
                print("Got a job: ", info)
                print("******" * 13)
                save_jobs_in_database(session, info)
    except Exception as error:
        print('Exception in GlassdoorScraper: ', error)

    try:
        f = FreshersworldScraper()

        for info in f.parse():
            if info:
                print("Got a job: ", info)
                print("******" * 13)
                save_jobs_in_database(session, info)
    except Exception as error:
        print("Exception in FreshersworldScraper: ", error)

    try:
        vcs = VcsdataScraper()

        for info in vcs.parse():
            if info:
                print("Got a organization: ", info)
                print("******" * 13)
                save_jobs_in_database(session, info)
    except Exception as error:
        print("Exception in VcsdataScraper: ", error)
    finally:
        session.close()
