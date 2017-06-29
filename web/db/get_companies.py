from models import Organization, Industry, OrganizationIndustry
from itertools import groupby


def normalize_company(companies):
    """
    Returns list of organziations after removing the duplicate items
    """
    organizations = []

    for (org_model, duplicates) in groupby(companies, lambda row: row[0]):
        industry = []

        for row in duplicates:
            industry.append(row[1])

        organization = org_model.__dict__
        organization.update({'industry': ' \ '.join(industry),
                             'domain': org_model.domain})
        organizations.append(organization)

    return organizations


def sampling(selection, offset=0, limit=10):
    return selection[offset:(limit + offset if limit is not None else None)]


def get_companies(session, current_page, org_id, search_keyword):
    """
    Returns dictionary of organizations, org_from_id, total_pages
    """
    start = current_page * 10 + 1 - 10 if current_page > 1 else 0
    organizations = session.query(Organization, Industry.name).filter(
        OrganizationIndustry.organization_id == Organization.id,
        Industry.id == OrganizationIndustry.industry_id).group_by(
            Organization.name).all()

    if search_keyword:
        organizations = session.query(Organization, Industry.name).filter(
            Organization.name.like("%" + search_keyword + "%"),
            OrganizationIndustry.organization_id == Organization.id,
            Industry.id == OrganizationIndustry.industry_id).group_by(
                Organization.name).all()

    organizations = normalize_company(organizations)
    total_orgs = len(organizations)
    organizations = sampling(organizations, int(start))

    if not org_id:
        org_id = organizations[0].get('id') if organizations else None

    org_from_id = session.query(Organization, Industry.name).filter(
        Organization.id == org_id,
        OrganizationIndustry.organization_id == Organization.id,
        Industry.id == OrganizationIndustry.industry_id).all()
    org_from_id = normalize_company(org_from_id)[0]
    pages = int(total_orgs / 10)
    pages = pages if pages > 1 else 1

    return dict(orgs=organizations, org=org_from_id, pages=pages)
