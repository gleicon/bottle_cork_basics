# coding: utf-8
#!/usr/bin/env python
#  admin/admin, demo/demo

import gevent
from gevent import monkey
monkey.patch_all()

import config
import sys
import bottle
import dbauth
from beaker.middleware import SessionMiddleware
from cork import Cork
import logging

conf = config.parse_config(sys.argv[1])
logging.basicConfig(format='localhost - - [%(asctime)s] %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)

app = bottle.app()
session_opts = {
    'session.cookie_expires': bool(conf.session_cookie_expires),
    'session.encrypt_key': conf.session_encrypt_key,
    'session.httponly': bool(conf.session_httponly),
    'session.timeout': int(conf.session_timeout),
    'session.type': conf.session_type,
    'session.validate_key': bool(conf.session_validate_key),
}

app = SessionMiddleware(app, session_opts)
b = dbauth.initialize_sqlite_backend(conf.session_database_path)
authenticator = Cork(backend=b, email_sender=conf.server_email, smtp_url=conf.server_smtp_url)
authorize = authenticator.make_auth_decorator(fail_redirect="/login", role="user")

def postd():
    return bottle.request.forms

def post_get(name, default=''):
    return bottle.request.POST.get(name, default).strip()

@bottle.post('/login')
def login():
    """Authenticate users"""
    username = post_get('username')
    password = post_get('password')
    authenticator.login(username, password, success_redirect='/', fail_redirect='/login')

@bottle.route('/logout')
def logout():
    authenticator.logout(success_redirect='/login')


@bottle.post('/register')
def register():
    """Send out registration email"""
    authenticator.register(post_get('username'), post_get('password'), post_get('email_address'))
    return 'Please check your mailbox.'


@bottle.route('/validate_registration/:registration_code')
def validate_registration(registration_code):
    """Validate registration, create user account"""
    authenticator.validate_registration(registration_code)
    return 'Thanks. <a href="/login">Go to login</a>'


@bottle.post('/reset_password')
def send_password_reset_email():
    """Send out password reset email"""
    authenticator.send_password_reset_email(
        username=post_get('username'),
        email_addr=post_get('email_address')
    )
    return 'Please check your mailbox.'


@bottle.route('/change_password/:reset_code')
@bottle.view('password_change_form')
def change_password(reset_code):
    """Show password change form"""
    return dict(reset_code=reset_code)


@bottle.post('/change_password')
def change_password():
    """Change password"""
    authenticator.reset_password(post_get('reset_code'), post_get('password'))
    return 'Thanks. <a href="/login">Go to login</a>'


@bottle.route('/')
@bottle.route('/index.html')
@authorize()
@bottle.view('index')
def index():
    return dict(
        current_user=authenticator.current_user,
    )

@bottle.route('/dashboard/:site_id')
@authorize()
@bottle.view('dashboard')
def dashboard(site_id):
    return dict(
        current_user=authenticator.current_user,
        site_id=site_id
    )

# Static pages

@bottle.route('/login')
@bottle.view('login_form')
def login_form():
    """Serve login form"""
    return {}

@bottle.route('/:type/:filename#.*#')
def send_static(type, filename):
    if type in ["css", "js", "img", "fonts"]:
        return bottle.static_file(filename, root="./static/%s/" % type)
    else:
        abort(404, "File not found")

def main():
    debug = bool(conf.server_debug)
    bottle.debug(debug)
    bottle.run(app=app, reloader=False, port=conf.server_port, host=conf.server_address, server='gevent')

if __name__ == "__main__":
    main()
