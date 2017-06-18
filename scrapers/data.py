class JobInfo():
    """Represents a single job info extracted by scraper"""
    def __init__(self, org_fields={}, country=None, state=None, city=None,
                 job_source=None, job_title=None, job_created_at=None,
                 job_desc=None, reviews=[], last_date=None,
                 qualifications=[], pin_code=[], industries=[]):
        self.org_fields = org_fields
        self.country = country
        self.state = state
        self.city = city
        self.pin_code = pin_code
        self.job_source = job_source
        self.job_title = job_title
        self.job_created_at = job_created_at
        self.job_desc = job_desc
        self.reviews = reviews
        self.last_date = last_date
        self.qulifications = qualifications
        self.industries = industries

    def __repr__(self):
        return "<job_title: {}, organization: {}>"\
            .format(self.job_title, self.org_fields.get('organization'))
