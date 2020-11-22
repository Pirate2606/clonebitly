from flask import flash, session
from flask_login import current_user, login_user
from flask_dance.contrib.facebook import make_facebook_blueprint
from flask_dance.consumer import oauth_authorized, oauth_error
from flask_dance.consumer.storage.sqla import SQLAlchemyStorage
from sqlalchemy.orm.exc import NoResultFound
from models import db, Users, OAuth
import uuid

blueprint = make_facebook_blueprint(
    storage=SQLAlchemyStorage(OAuth, db.session, user=current_user),
    redirect_to="signup_options",
)


# create/login local user on successful OAuth login
@oauth_authorized.connect_via(blueprint)
def facebook_logged_in(blueprint, token):
    if not token:
        flash("Failed to log in.", category="error")
        return False

    resp = blueprint.session.get("/me")
    if not resp.ok:
        msg = "Failed to fetch user info."
        flash(msg, category="error")
        return False

    info = resp.json()
    user_id = info["id"]

    # Find this OAuth token in the database, or create it
    query = OAuth.query.filter_by(provider=blueprint.name, provider_user_id=user_id)
    try:
        oauth = query.one()
    except NoResultFound:
        oauth = OAuth(provider=blueprint.name, provider_user_id=user_id, token=token)

    if oauth.user:
        session['user_id'] = oauth.user_id
        login_user(oauth.user)
        flash("Successfully signed in.")

    else:
        # Create a new local user account for this user
        unique_id = uuid.uuid4().hex[:8]
        user = Users(facebook_name=info["name"], unique_id=unique_id)
        # Associate the new local user account with the OAuth token
        oauth.user = user
        # Save and commit our database models
        db.session.add_all([user, oauth])
        db.session.commit()
        # Log in the new local user account
        session['user_id'] = Users.query.filter_by(unique_id=unique_id).first().id
        login_user(user)
        flash("Successfully signed in.")

    # Disable Flask-Dance's default behavior for saving the OAuth token
    return False


# notify on OAuth provider error
@oauth_error.connect_via(blueprint)
def facebook_error(blueprint, message, response):
    msg = "OAuth error from {name}! " "message={message} response={response}".format(
        name=blueprint.name, message=message, response=response
    )
    flash(msg, category="error")
