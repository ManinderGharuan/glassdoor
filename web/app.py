from flask import Flask, render_template, request
from models import Organization
from web.db import get_session
from web.db.get_companies import get_companies

app = Flask(__name__)

session = get_session()


@app.route('/')
def show_mainpage():
    current_page = int(request.args.get('page')) \
            if request.args.get('page') else 1
    id = int(request.args.get(
        'id')) if request.args.get('id') else request.args.get('id')
    search = request.args.get('keyword')
    data = get_companies(session, Organization, current_page, id, search)
    orgs = data.get('orgs')
    org = data.get('org')
    pages = data.get('pages')

    return render_template(
        'template.html', orgs=orgs, org=org,
        current_page=current_page, pages=pages, search=search
    )
