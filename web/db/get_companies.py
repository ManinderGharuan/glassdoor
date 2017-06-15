def get_companies(session, model, current_page, org_id, search_keyword):
    """
    Returns dictionary of organizations, org_from_id, total_pages
    """
    start = str(current_page - 1) + '0' if current_page > 1 else 0
    organizations = session.query(model).order_by(model.name) \
                                        .limit(10).offset(start).all()
    total_orgs = session.query(model).count()

    if search_keyword:
        organizations = session.query(
            model).filter(model.name.like("%" + search_keyword + "%")) \
                               .limit(10).offset(start).all()
        total_orgs = session.query(
            model).filter(model.name.like('%' + search_keyword + '%')).count()

    if not org_id:
        org_id = organizations[0].id if organizations else None

    org_from_id = session.query(model).filter_by(id=org_id).first()

    pages = int('0' + str(total_orgs)[
        :-1]) + 1 if total_orgs != 0 or total_orgs else 0

    if total_orgs == int(str(pages - 1) + '0'):
        pages -= 1

    return dict(orgs=organizations, org=org_from_id, pages=pages)
