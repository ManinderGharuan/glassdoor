from urllib.parse import urlparse
from models import (Domain, Organization, Location, Job, Qualification,
                    JobQualification, AuthorJob, AuthorLocation, Review,
                    Industry, OrganizationIndustry, UserOrganization)


def unduplicate(session, table, data={}):
    table_name = table.__tablename__.lower()
    query = session.query(table)
    result = None

    if table_name == 'organization':
        result = query.filter(table.name == data.get('name')).first()

        if result:
            if not result.description and data.get('description'):
                result.description = data.get('description')

            if not result.domain.name and data.get('domain').name:
                result.domain = data.get('domain')

            if not result.headquarters_address and data.get('headquarters_address'):
                result.headquarters_address = data.get('headquarters_address')

            if not result.size and data.get('size'):
                result.size = data.get('size')

            if not result.founded_at and data.get('founded_at'):
                result.founded_at = data.get('founded_at')

            if not result.type and data.get('type'):
                result.type = data.get('type')

            if not result.revenue and data.get('revenue'):
                result.revenue = data.get('revenue')

            if not result.competitors and data.get('competitors'):
                result.competitors = data.get('competitors')

            if not result.logo_url and data.get('logo_url'):
                result.logo_url = data.get('logo_url')

            if not result.phone_no and data.get('phone_no'):
                result.phone_no = data.get('phone_no')

            if data.get('location'):
                result.location = data.get('location')
    elif table_name == 'location':
        result = query.filter(table.country == data.get('country'),
                              table.city == data.get('city')).first()
        if result:
            if not result.state and data.get('state'):
                result.state = data.get('state')
        else:
            result = query.filter(table.city == data.get('city')).first()

            if result:
                if not result.state and data.get('state'):
                    result.state = data.get('state')

                if not result.country and data.get('country'):
                    result.country = data.get('country')
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

        location_data = dict(country=job_info.country, state=job_info.state,
                             city=job_info.city)
        location = unduplicate(session, Location, location_data)

        org_data = dict(name=org_fields.get('organization'),
                        description=org_fields.get('org_desc'),
                        domain=domain,
                        headquarters_address=org_fields.get(
                            'headquarters_address'),
                        size=org_fields.get('size'),
                        founded_at=org_fields.get('founded_at'),
                        type=org_fields.get('org_type'),
                        revenue=org_fields.get('revenue'),
                        competitors=org_fields.get('competitors'),
                        location=location,
                        logo_url=org_fields.get('org_logo'),
                        phone_no=org_fields.get('phone_no'))
        organization = unduplicate(session, Organization, org_data)

        if job_info.user_id:
            user_org_data = dict(user_id=job_info.user_id,
                                 organization=organization)
            unduplicate(session, UserOrganization, user_org_data)

        for indstry in job_info.industries:
            industry_data = dict(name=indstry)

            industry = unduplicate(session, Industry, industry_data)

            oi_data = dict(organization=organization, industry=industry)
            unduplicate(session, OrganizationIndustry, oi_data)

        if job_info.job_source:
            job_data = dict(source=job_info.job_source,
                            title=job_info.job_title,
                            created_at=job_info.job_created_at,
                            description=job_info.job_desc,
                            organization=organization,
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
