from flask import Flask, render_template, request, redirect, flash
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from dateutil.parser import parse
from models import User
from web.db import get_session, get_user_session
from web.db.get_companies import get_companies
from scrapers.data import JobInfo
from scrapers.save_jobs import save_jobs_in_database

app = Flask(__name__)
app.secret_key = 'secure'
login_manager = LoginManager()
login_manager.init_app(app)

session = get_session()
user_session = get_user_session()


@login_manager.user_loader
def load_user(user_id):
    return user_session.query(User).filter(User.id == user_id).first()


@app.route('/')
def show_mainpage():
    current_page = int(request.args.get('page')) \
            if request.args.get('page') else 1
    id = int(request.args.get(
        'id')) if request.args.get('id') else request.args.get('id')
    search = request.args.get('keyword')
    data = get_companies(session, current_page, id, search)

    return render_template(
        'template.html', orgs=data.get('orgs'), org=data.get('org'),
        current_page=current_page, pages=data.get('pages'), search=search)


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == "GET":
        return render_template('signup.html')

    query = user_session.query(User)
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password or query \
       .filter_by(email=email).first():
        flash("Are you sure about information?")
        return redirect('/register')

    user = User(username=username, email=email, password=password)
    user_session.add(user)
    user_session.commit()
    login_user(user)

    flash("User successfully registered")
    return redirect('/')


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'GET':
        return render_template('signin.html')

    query = user_session.query(User)
    email = request.form.get('email')
    password = request.form.get('password')
    user = query.filter_by(email=email, password=password).first()

    if user:
        login_user(user)
        flash('Logged in successfully.')
        return redirect('/post')

    flash('Username or Password is invalid')
    return redirect('/login')


@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == 'GET':
        return render_template('postcompany.html')

    session = get_session()
    organization = request.form.get('post_company')
    domain = request.form.get('domain')
    org_desc = request.form.get('description')
    headquarters_address = request.form.get('headquarters_address')
    size = request.form.get('size')
    org_type = request.form.get('type')
    industry = request.form.get('industry')
    revenue = request.form.get('revenue')
    competitors = request.form.get('competitors')
    phone_no = request.form.get('phone_number')
    user_id = current_user.id

    try:
        founded_at = parse(request.form.get('founded_at'), fuzzy=True)
    except ValueError:
        founded_at = None

    if not organization or not domain or not org_desc or not phone_no:
        flash('Please fill every forms')
        return redirect('/post')

    org_fields = dict(organization=organization, org_desc=org_desc, size=size,
                      founded_at=founded_at, phone_no=phone_no,
                      headquarters_address=headquarters_address,
                      org_type=org_type, revenue=revenue, org_domain=domain,
                      competitors=competitors)
    add_organization = JobInfo(org_fields=org_fields, city='Chandigarh',
                               industries=industry, user_id=user_id)
    save_jobs_in_database(session, add_organization)
    flash("New company is added")
    return redirect('/')


@app.route('/logout')
@login_required
def logout():
    flash("Successfully logout")
    logout_user()
    return redirect('/')


@login_manager.unauthorized_handler
def unauthorized():
    flash("Only registerd user allow to add their company")
    return redirect('/login')
