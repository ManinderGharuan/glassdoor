#!/usr/bin/env python3
from GlassdoorScraper import GlassdoorScraper
from db import get_session
from save_jobs import save_jobs_in_database


def scrap():
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
    finally:
        session.close()


if __name__ == "__main__":
    scrap()
