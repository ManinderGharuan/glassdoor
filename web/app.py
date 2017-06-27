from flask import Flask, render_template, request, redirect, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from models import Organization, User
from web.db import get_session, get_user_session
from web.db.get_companies import get_companies

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
    data = get_companies(session, Organization, current_page, id, search)
    orgs = data.get('orgs')
    org = data.get('org')
    pages = data.get('pages')

    return render_template(
        'template.html', orgs=orgs, org=org,
        current_page=current_page, pages=pages, search=search)


@app.route('/register', methods=['GET', 'POST'])
def user_register():
    if request.method == "GET":
        return render_template('signup.html')

    query = user_session.query(User)
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')

    if not username or not email or not password:
        return redirect('/register')

    if query.filter_by(email=email).first():
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
        return redirect('/')

    flash('Username or Password is invalid')
    return redirect('/login')


@app.route('/post')
@login_required
def post():
    pass


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


@login_manager.unauthorized_handler
def unauthorized():
    return redirect('/login')
