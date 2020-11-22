# Imports
from flask import render_template, request, redirect, flash, url_for, g, jsonify, session
from flask_migrate import Migrate
from werkzeug.exceptions import BadRequestKeyError
from models import db, Links, app, IpAddresses, Register, login_manager, Users, OAuth, UserDashboard
from config import Config
from cli import create_db
from wtforms import ValidationError
from flask_login import login_user, logout_user, login_required, current_user
from oauth import facebook, github, google, twitter
import os
import uuid
import re
import string
from random import choices
from ip2geotools.databases.noncommercial import DbIpCity
import pycountry
import json
from collections import Counter

# flask migration connecting the app and the database
Migrate(app, db)

# configuring the app
app.config.from_object(Config)
app.cli.add_command(create_db)
app.register_blueprint(google.blueprint, url_prefix="/login")
app.register_blueprint(twitter.blueprint, url_prefix="/login")
app.register_blueprint(facebook.blueprint, url_prefix="/login")
app.register_blueprint(github.blueprint, url_prefix="/login")
db.init_app(app)
login_manager.init_app(app)

# enabling insecure login for OAuth login
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'


# Views
# Home page
@app.route("/")
def index():
    # if user is not signed in open the home page
    if not session.get('user_id'):
        return render_template("home.html")
    # if user is signed in or user is inside a session
    unique_id = Users.query.filter_by(id=session.get('user_id')).first().unique_id
    # if session ended unexpectedly then end the previous session
    if unique_id is None:
        session.pop('user_id', None)
        return render_template("home.html")
    return redirect(url_for("dashboard", unique_id=unique_id))


# Shortening links without login
@app.route('/add_link', methods=['POST', 'GET'])
def add_link():
    # getting ip address of the user
    try:
        ip = request.environ['HTTP_X_FORWARDED_FOR']  # if behind a proxy
    except KeyError:
        ip = request.environ['REMOTE_ADDR']

    ip_addr = IpAddresses.query.filter_by(ipAddress=ip).first()

    # if IP is in database then increment the count else add the IP in the database
    if ip_addr is not None:
        if ip_addr.count < 6:
            ip_addr.count += 1
    else:
        ip_addr = IpAddresses(ip)
        ip_addr.count = 1
    db.session.add(ip_addr)
    db.session.commit()

    # only if URL shortener requests are less than 4, run the shortener
    if ip_addr.count < 6:

        original_url = request.form['url']  # getting url from the form

        # adding https:// to the url
        if "https://" not in original_url and "http://" not in original_url:
            original_url = "https://" + original_url

        link = Links(original_url=original_url)
        db.session.add(link)
        db.session.commit()

        return jsonify({'result': 'success', 'new_link': link.short_url, 'long_link': link.original_url})
    else:
        return redirect(url_for('index'))


# Redirecting to shortened link
@app.route('/<short_url>')
def redirect_to_url(short_url):
    if not session.get('user_id'):
        # redirect to the original link and increment the visit count
        # if user is not signed in
        link = Links.query.filter_by(short_url=short_url).first_or_404()
        link.visits += 1
        db.session.add(link)
        db.session.commit()
        return redirect(link.original_url)
    else:
        # if user is signed in
        link = UserDashboard.query.filter_by(short_url=short_url).first_or_404()
        # getting user ip address
        try:
            ip = request.environ['HTTP_X_FORWARDED_FOR']  # if behind a proxy
        except KeyError:
            ip = request.environ['REMOTE_ADDR']
        link.ip_address = ip
        # TODO: change to this: response = DbIpCity.get(ip, api_key='free')
        # getting city name using
        response = DbIpCity.get('49.36.134.251', api_key='free')
        current_country_name = pycountry.countries.get(alpha_2=response.country)
        current_country_name = current_country_name.name
        previous_country_name = link.country
        if previous_country_name is None:
            link.country = '{"' + current_country_name + '" : ' + '1' + '}'
            link.max_country_visit = 1
            link.max_country_visit_name = current_country_name
        else:
            country_dict = json.loads(previous_country_name)
            if current_country_name in country_dict:
                country_dict[current_country_name] += 1
                updated_country = json.dumps(country_dict)
            else:
                updated_country = previous_country_name[:-1] + ', "' + current_country_name + '" : ' + '1' + '}'
            country_dict = json.loads(updated_country)
            max_country = Counter(country_dict)
            max_visits = 0
            max_country_name = ""
            for country in max_country:
                if max_country[country] > max_visits:
                    max_visits = max_country[country]
                    max_country_name = country
            link.max_country_visit = max_visits
            link.max_country_visit_name = max_country_name
        link.visits += 1
        db.session.add(link)
        db.session.commit()
        return redirect(link.original_url)


# Registering a user
@app.route('/a/sign_up', methods=["POST", "GET"])
def signup():
    if session.get('user_id'):
        return redirect(url_for("logout"))
    email_flag = False
    username_flag = False
    password_flag = False

    if request.method == "POST":
        # Accessing username, email, password from the HTML form
        user_name = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # checking for duplicate email and username
        password_flag = check_password(password)
        try:
            email_flag = check_mail(email)
        except ValidationError:
            email_flag = True

        try:
            username_flag = check_username(user_name)
        except ValidationError:
            username_flag = True

        if not username_flag and not email_flag and not password_flag and password_flag != "short":
            # Entering data into Database (Register table)
            users = Register(user_name=user_name, email=email, password=password)
            db.session.add(users)
            db.session.commit()

            # Entering data into Database (User table)
            unique_id = uuid.uuid4().hex[:8]
            user = Users(email=email, unique_id=unique_id)
            db.session.add(user)
            db.session.commit()

            # Logging in the user
            login_user(user)

            return redirect(url_for('dashboard', unique_id=unique_id))

    return render_template('sign-up.html',
                           email_flag=email_flag,
                           username_flag=username_flag,
                           password_flag=password_flag)


# Log in page
@app.route("/a/sign_in", methods=["POST", "GET"])
def sign_in():
    if session.get('user_id'):
        return redirect(url_for("logout"))
    # flag tells if username and password entered is correct
    # flag = False means username and password are right
    flag = False

    if request.method == "POST":
        # checking if email address entered in HTML form is in our database
        # if not then check for username
        # if still none then flag = True
        # if user is found then check the password and if password matches then login the user
        # else flag = True

        user = Register.query.filter_by(email=request.form['username']).first()
        if user is None:
            user = Register.query.filter_by(user_name=request.form['username']).first()
        if user is not None:
            if user.check_password(request.form['password']):
                user = Users.query.filter_by(email=user.email).first()
                unique_id = user.unique_id
                session['user_id'] = user.id
                login_user(user)
                return redirect(url_for("dashboard", unique_id=unique_id))
            else:
                flag = True
        else:
            flag = True
    return render_template("sign-in.html", flag=flag)


# logout the user
@app.route("/logout")
@login_required
def logout():
    session.pop('user_id', None)
    logout_user()
    flash("You have logged out")
    return redirect(url_for("index"))


# Subject to change
@app.route("/<unique_id>/bitlinks", methods=["POST", "GET"])
@login_required
def dashboard(unique_id):
    selected_link_info = None
    name = get_user_name(Users.query.filter_by(unique_id=unique_id).first())
    if UserDashboard.query.filter_by(unique_id=unique_id).first() is not None:
        selected_link = ""
        obj = UserDashboard.query.filter_by(unique_id=unique_id).all()
        for o in obj:
            selected_link = o.short_url
        return redirect(url_for("dashboard_with_links",
                                unique_id=unique_id,
                                selected_link=selected_link,
                                selected_link_info=selected_link_info,
                                name=name))

    check_create_button = False
    if request.method == "POST":
        check_create_button = True
        user = UserDashboard()
        user.unique_id = unique_id
        user.original_url = request.form["long_url"]
        user.title = request.form["long_url"]
        short_url = generate_short_link()
        user.short_url = short_url
        redirect_link = Links()
        redirect_link.original_url = user.original_url
        redirect_link.short_url = user.short_url
        db.session.add_all([redirect_link, user])
        db.session.commit()
        return render_template("dashboard.html",
                               flag=check_create_button,
                               short_url=short_url,
                               unique_id=unique_id,
                               selected_link_info=selected_link_info,
                               name=name)
    return render_template("dashboard.html",
                           flag=check_create_button,
                           unique_id=unique_id,
                           selected_link_info=selected_link_info,
                           name=name)


@app.route("/<unique_id>/bitlinks/<selected_link>", methods=["POST", "GET"])
def dashboard_with_links(unique_id, selected_link):
    name = get_user_name(Users.query.filter_by(unique_id=unique_id).first())
    user_info = UserDashboard().query.filter_by(unique_id=unique_id).all()
    total_visits = 0
    max_visits = -1
    max_country_name = ""
    total_links = 0
    labels = []
    bar_chart_data = []
    count_labels = []
    for user in user_info:
        total_visits += user.visits
        total_links += 1
        date = user.date_created.strftime("%d")
        month = user.date_created.strftime("%b")
        out = month + " " + date
        count_labels.append(out)
        if out not in labels:
            labels.append(out)
        if user.max_country_visit > max_visits:
            max_visits = user.max_country_visit
            max_country_name = user.max_country_visit_name
    count_labels_dict = Counter(count_labels)
    for label in count_labels_dict:
        bar_chart_data.append(count_labels_dict[label])
    background_color = ['rgba(215, 146, 104, 1)'] * total_links
    selected_link_info = UserDashboard().query.filter_by(short_url=selected_link).first()
    flag = request.args.get("flag")
    if request.method == "POST" and flag == "True":
        try:
            user = UserDashboard.query.filter_by(short_url=selected_link).first()
            update_link = Links.query.filter_by(short_url=selected_link).first()
            customized_link = (request.form["short_url_customized"])[25:]
            if request.form["short_url_title"] != "":
                user.title = request.form["short_url_title"]
            user.short_url = customized_link
            update_link.short_url = customized_link
            db.session.commit()
            return redirect(url_for("dashboard",
                                    unique_id=unique_id,
                                    flag=False,
                                    selected_link_info=selected_link_info,
                                    bar_chart_data=bar_chart_data,
                                    labels=json.dumps(labels),
                                    background_color=background_color,
                                    name=name,
                                    total_visits=total_visits,
                                    max_visits=max_visits,
                                    max_country_name=max_country_name))
        except BadRequestKeyError:
            return redirect(url_for("dashboard",
                                    unique_id=unique_id,
                                    flag=False,
                                    selected_link_info=selected_link_info,
                                    bar_chart_data=bar_chart_data,
                                    labels=json.dumps(labels),
                                    background_color=background_color,
                                    name=name,
                                    total_visits=total_visits,
                                    max_visits=max_visits,
                                    max_country_name=max_country_name))
    check_create_button = False
    if request.method == "POST" and flag != "True":
        check_create_button = True
        user = UserDashboard()
        user.unique_id = unique_id
        user.original_url = request.form["long_url"]
        user.title = request.form["long_url"]
        short_url = generate_short_link()
        user.short_url = short_url
        redirect_link = Links()
        redirect_link.original_url = user.original_url
        redirect_link.short_url = user.short_url
        db.session.add_all([redirect_link, user])
        db.session.commit()
        return render_template("dashboard.html",
                               flag=check_create_button,
                               short_url=short_url,
                               selected_link_info=selected_link_info,
                               bar_chart_data=bar_chart_data,
                               labels=json.dumps(labels),
                               background_color=background_color,
                               unique_id=unique_id,
                               name=name,
                               total_visits=total_visits,
                               max_visits=max_visits,
                               max_country_name=max_country_name)
    return render_template("dashboard.html",
                           flag=check_create_button,
                           unique_id=unique_id,
                           user_info=user_info,
                           selected_link_info=selected_link_info,
                           bar_chart_data=bar_chart_data,
                           labels=json.dumps(labels),
                           background_color=background_color,
                           name=name,
                           total_visits=total_visits,
                           max_visits=max_visits,
                           max_country_name=max_country_name)


@app.route("/options")
@login_required
def signup_options():
    g.user = current_user.get_id()
    name = ""
    if g.user:
        user_id = int(g.user)
        users = Users.query.get(user_id)
        unique_id = users.unique_id
        if users.onboard_option in ["work", "personal", "both", "skip"]:
            return redirect(url_for("dashboard", unique_id=unique_id))
        name = get_user_name(users)

    return render_template("signup-pg1.html", name=name, unique_id=unique_id)


@app.route('/cancel-signup')
def cancel_signup():
    g.user = current_user.get_id()
    if g.user:
        user_id = int(g.user)
        flask_dance = OAuth.query.filter_by(user_id=user_id).first()
        user = Users.query.get(user_id)
        db.session.delete(flask_dance)
        db.session.commit()
        db.session.delete(user)
        db.session.commit()
    session.pop('user_id', None)
    return redirect(url_for("index"))


@app.route("/<unique_id>/onboard")
@login_required
def oauth_register(unique_id):
    user = Users.query.filter_by(unique_id=unique_id).first()
    user.onboard_option = "skip"
    db.session.add(user)
    db.session.commit()
    return render_template("signup-pg2.html", unique_id=unique_id)


@app.route("/<unique_id>/onboard/work", methods=["POST", "GET"])
@login_required
def for_work(unique_id):
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        organization = request.form["organization"]
        title = request.form.get("title")
        department = request.form.get("department")
        organization_size = request.form.get("organization_size")
        options = request.form.getlist('options')

        if "other" in options:
            options.append(request.form["other_input"])

        user = Users.query.filter_by(unique_id=unique_id).first()
        user.onboard_option = "work"
        user.first_name = first_name
        user.last_name = last_name
        user.options = str(options)
        user.organization = organization
        user.title = title
        user.department = department
        user.organization_size = organization_size
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("dashboard", unique_id=unique_id))

    return render_template("for-work.html", unique_id=unique_id)


@app.route("/<unique_id>/onboard/personal", methods=["POST", "GET"])
@login_required
def personal(unique_id):
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        options = request.form.getlist('options')

        if "other" in options:
            options.append(request.form["other_input"])

        user = Users.query.filter_by(unique_id=unique_id).first()
        user.onboard_option = "personal"
        user.first_name = first_name
        user.last_name = last_name
        user.options = str(options)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("dashboard", unique_id=unique_id))
    return render_template("personal.html", unique_id=unique_id)


@app.route("/<unique_id>/onboard/both", methods=["POST", "GET"])
@login_required
def both(unique_id):
    if request.method == "POST":
        first_name = request.form["first_name"]
        last_name = request.form["last_name"]
        organization = request.form["organization"]
        title = request.form.get("title")
        department = request.form.get("department")
        organization_size = request.form.get("organization_size")
        options = request.form.getlist('options')

        if "other" in options:
            options.append(request.form["other_input"])

        user = Users.query.filter_by(unique_id=unique_id).first()
        user.onboard_option = "both"
        user.first_name = first_name
        user.last_name = last_name
        user.options = str(options)
        user.organization = organization
        user.title = title
        user.department = department
        user.organization_size = organization_size
        db.session.add(user)
        db.session.commit()

        return redirect(url_for("dashboard", unique_id=unique_id))

    return render_template("both.html", unique_id=unique_id)


@app.route("/pages/privacy")
def privacy():
    return render_template("privacy-policy.html")


@app.route("/pages/terms-of-service")
def terms():
    return render_template("terms.html")


@app.route("/pages/why-bitly/bitly-101")
def bitly_101():
    return render_template("bitly101.html")


@app.route("/pages/why-bitly/integrations-api")
def integrations_api():
    return render_template("integrations-api.html")


@app.route("/pages/why-bitly/enterprise-class")
def enterprise_class():
    return render_template("enterprise-class.html")


@app.route("/pages/features/branded-links")
def branded_links():
    return render_template("branded-links.html")


@app.route("/pages/features/link-management")
def link_management():
    return render_template("link-management.html")


@app.route("/pages/features/mobile-links")
def mobile_links():
    return render_template("mobile-links.html")


@app.route("/pages/features/campaign-management-analytics")
def campaign():
    return render_template("campaign.html")


@app.route("/pages/solutions/customer-services")
def customer_services():
    return render_template("customer-service.html")


@app.route("/pages/solutions/digital-marketing")
def digital_marketing():
    return render_template("digital-marketing.html")


@app.route("/pages/solutions/for-developers")
def for_developer():
    return render_template("for-developers.html")


@app.route("/pages/solutions/social-media")
def social_media():
    return render_template("social-media.html")


@app.route("/pages/pricing")
def pricing():
    return render_template("pricing.html")


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


# FUNCTIONS
def check_mail(data):
    if Register.query.filter_by(email=data).first():
        raise ValidationError('Your email is already registered.')
    else:
        return False


def check_username(data):
    if Register.query.filter_by(user_name=data).first():
        raise ValidationError('This username is already registered.')
    else:
        return False


def check_password(data):
    special_char = string.punctuation
    if len(data) < 6:
        return "short"
    elif not re.search("[a-zA-Z]", data):
        return True
    elif not re.search("[0-9]", data):
        return True
    for char in data:
        if char in special_char:
            break
    else:
        return True
    return False


def generate_short_link():
    characters = string.digits + string.ascii_letters
    short_url = ''.join(choices(characters, k=5))

    link = UserDashboard.query.filter_by(short_url=short_url).first()

    if link:
        return generate_short_link()

    return short_url


def get_user_name(users):
    name = ""
    if users.google_name is not None:
        name = users.google_name
    elif users.facebook_name is not None:
        name = users.facebook_name
    elif users.github_username is not None:
        name = users.github_username
    elif users.twitter_name is not None:
        name = users.twitter_name
    elif users.email is not None:
        name = Register.query.filter_by(email=users.email).first().user_name

    return name


if __name__ == '__main__':
    app.run(debug=True)
