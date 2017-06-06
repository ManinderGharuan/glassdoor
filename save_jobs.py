from urllib.parse import urlparse
from models import (Domain, Organization, Location, Job, Qualification,
                    JobQualification, AuthorJob, AuthorLocation, Review)


def unduplicate(session, table, data={}):
    table_name = table.__tablename__.lower()
    query = session.query(table)
    result = None

    if table_name == 'organization':
        if not data.get('domain').name:
            result = query.filter(table.name == data.get('name')).first()
        else:
            result = query.filter(table.name == data.get('name'),
                                  table.domain == data.get('domain')).first()
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

        org_data = dict(name=job_info.organization,
                        description=org_fields.get('org_desc'),
                        domain=domain,
                        headquarters_address=org_fields.get(
                            'headquarters_address'),
                        size=org_fields.get('size'),
                        founded_at=org_fields.get('founded_at'),
                        type=org_fields.get('org_type'),
                        industry=org_fields.get('industry'),
                        revenue=org_fields.get('revenue'),
                        competitors=org_fields.get('competitors'))
        organization = unduplicate(session, Organization, org_data)

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
