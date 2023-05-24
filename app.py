from flask import Flask, render_template, redirect, request, session
import hashlib
from pymongo import MongoClient
import os
import markdown
import sqlite3
import utils
import binascii
from functools import wraps

app = Flask(__name__)
app.secret_key = '1500589d2e714969087988503480f9cbdc34a3d2e1eec7bd4b50da1925763528'

IS_SQL_DATABASE = True

if IS_SQL_DATABASE:
    conn = sqlite3.connect('instance/blog.sqlite', check_same_thread=False)
    cursor = conn.cursor()
else:
    client = MongoClient('localhost', 27017)
    db = client['blog']


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect('/login')
        return f(*args, **kwargs)

    return decorated_function


def hash_password(password):
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                  salt, 200000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')


def verify_password(stored_password, provided_password):
    salt = stored_password[:64]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  200000)
    stored_password = stored_password[64:]
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password


@app.route('/')
def index():
    posts = utils.get_posts() or []
    return render_template('index.html', posts=posts)


@app.route('/post/<id>', methods=['GET'])
def get_post(id):
    post = utils.get_post(id) or {}
    post['body'] = markdown.markdown(post['body'])
    comments = utils.get_comments(id) or []
    return render_template('post.html', post=post, comments=comments)


@app.route('/post/<id>/comment', methods=['POST'])
@login_required
def create_comment(id):
    """
    :param id:
    :return:
    """
    author = session['username']
    content = request.form['content']
    utils.create_comment(id, author, content)
    return redirect('/post/' + id)


@app.route('/create', methods=['POST', 'GET'])
@login_required
def create():
    """
    :return:
    """
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        utils.create_post(title, body, session['username'])
        return render_template('create.html', message="Created Successfully")
    else:
        return render_template('create.html')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        stored_username, stored_password = utils.get_user_by_email(email)

        if verify_password(stored_password, password):
            session['username'] = stored_username
            return redirect("/")
        else:
            return render_template('login.html', message="login Failed")
    else:
        return render_template('login.html')


@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username'] or ""
        email = request.form['email'] or ""
        password = request.form['password'] or ""

        if not utils.is_valid_email(email) and utils.check_email(email):
            return render_template('sign_up.html', message="Please Write a Valid email")

        if username and password:
            utils.add_user(username, email, hash_password(password))
            return render_template('sign_up.html')

        return redirect('/login')

    else:
        return render_template('sign_up.html')


@app.route('/post/<id>', methods=['DELETE'])
@login_required
def delete_post(post_id):
    post = utils.get_post(post_id)
    if post["author"] != session["username"]:
        abort(403)
    else:
        utils.delete_post()


@app.route('/sign_up', methods=['DELETE'])
@login_required
def delete_comment(comment):
    pass


@app.route('/logout')
def logout():
    """
    :return:
    """
    session.clear()
    return redirect('/')


@app.errorhandler(404)
def not_found(error):
    """
    :param error:
    :return:
    """
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def not_found(error):
    """
    :param error:
    :return:
    """
    return render_template('error_500.html'), 500


if __name__ == '__main__':
    app.run()
