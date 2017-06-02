class JobInfo():
    """Represents a single job info extracted by scraper"""
    def __init__(self, org_fields, organization, country, state, city,
                 job_source, job_title, job_created_at, job_desc,
                 reviews):
        self.org_fields = org_fields
        self.organization = organization
        self.country = country
        self.state = state
        self.city = city
        self.job_source = job_source
        self.job_title = job_title
        self.job_created_at = job_created_at
        self.job_desc = job_desc
        self.reviews = reviews

    def __repr__(self):
        return "<organization: {}>" .format(self.organization)
