from flask import Flask, render_template
from models import Organization
from web.db import get_session

app = Flask(__name__)

session = get_session()


@app.route('/')
def show_mainpage(id=1):
    orgs = session.query(Organization).all()
    org = session.query(Organization).filter_by(id=id).first()

    return render_template('template.html', orgs=orgs, org=org)


@app.route('/organization/<int:id>')
def get_organization_by_id(id):
    org = session.query(Organization).filter_by(id=id).first()

    return render_template('organization.html', org=org)


@app.route('/<int:id>')
def get_organizations(id):
    orgs = session.query(Organization).all()
    org = session.query(Organization).filter_by(id=id).first()

    return render_template('template.html', orgs=orgs, org=org)


def organization(id):
    return session.query(Organization).filter_by(id=id).first()

