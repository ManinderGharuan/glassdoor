from urllib.parse import urlparse
from models import (Domain, Organization, Location, Job, Qualification,
                    JobQualification, AuthorJob, AuthorLocation, Review)


def unduplicate(session, table, data={}):
    table_name = table.__tablename__.lower()
    query = session.query(table)
    result = None

    if table_name == 'organization':
        result = query.filter(table.name == data.get('name')).first()

        if result:
            if not result.name and data.get('name'):
                result.name = data.get('name')

            if not result.description and data.get('description'):
                result.description = data.get('description')

            if not result.domain_id and data.get('domain').id:
                result.domain_id = data.get('domain').id

            if not result.headquarters_address and data.get('headquarters_address'):
                result.headquarters_address = data.get('headquarters_address')

            if not result.size and data.get('size'):
                result.size = data.get('size')

            if not result.founded_at and data.get('founded_at'):
                result.founded_at = data.get('founded_at')

            if not result.type and data.get('type'):
                result.type = data.get('type')

            if not result.industry and data.get('industry'):
                result.industry = data.get('industry')

            if not result.revenue and data.get('revenue'):
                result.revenue = data.get('revenue')

            if not result.competitors and data.get('competitors'):
                result.competitors = data.get('competitors')

            if not result.logo_url and data.get('logo_url'):
                result.logo_url = data.get('logo_url')
    elif table_name == 'job':
        path = urlparse(data.get('source')).path
        result = query.filter(table.source.like('%' + path + '%'),
                              table.organization == data.get('organization')).first()
    else:
        result = query.filter_by(**data).first()

    if not result:
        result = table(**data)
        session.add(result)

    return result


def save_jobs_in_database(session, job_info):
    try:
        org_fields = job_info.org_fields
        reviews = job_info.reviews

        domain_data = dict(name=org_fields.get('org_domain'))
        domain = unduplicate(session, Domain, domain_data)

        org_data = dict(name=org_fields.get('organization'),
                        description=org_fields.get('org_desc'),
                        domain=domain,
                        headquarters_address=org_fields.get(
                            'headquarters_address'),
                        size=org_fields.get('size'),
                        founded_at=org_fields.get('founded_at'),
                        type=org_fields.get('org_type'),
                        industry=org_fields.get('industry'),
                        revenue=org_fields.get('revenue'),
                        competitors=org_fields.get('competitors'),
                        logo_url=org_fields.get('org_logo'))
        organization = unduplicate(session, Organization, org_data)

        if job_info.job_source:
            location_data = dict(country=job_info.country, state=job_info.state,
                                 city=job_info.city)
            location = unduplicate(session, Location, location_data)

            job_data = dict(source=job_info.job_source,
                            title=job_info.job_title,
                            created_at=job_info.job_created_at,
                            description=job_info.job_desc,
                            organization=organization,
                            location=location,
                            last_date=job_info.last_date)
            job = unduplicate(session, Job, job_data)

        for qualification in job_info.qulifications:
            qualification_data = dict(name=qualification)
            qual = unduplicate(session, Qualification, qualification_data)

            job_qualification_data = dict(job=job, qualification=qual)
            unduplicate(session, JobQualification, job_qualification_data)

        for review in reviews:
            author_job_data = dict(job=review.get('author_job'))
            author_job = unduplicate(session, AuthorJob, author_job_data)

            author_location_data = dict(location=review.get('author_location'))
            author_location = unduplicate(
                session, AuthorLocation, author_location_data)

            review_data = dict(review_at=review.get('review_date'),
                               summary=review.get('review_summary'),
                               organization=organization,
                               author_job=author_job,
                               author_location=author_location,
                               review=review.get('review_desc'))
            unduplicate(session, Review, review_data)

        session.commit()
    except Exception as error:
        print("Failed to save in database: ", error)
