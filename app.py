from flask import Flask, render_template, redirect, request, session
import hashlib
import binascii
from pymongo import MongoClient
import os
from datetime import datetime
from bson.objectid import ObjectId
import markdown
import sqlite3
from utils import *
import utils

app = Flask(__name__)
app.secret_key = '1500589d2e714969087988503480f9cbdc34a3d2e1eec7bd4b50da1925763528'

IS_SQL_DATABASE = True
POSTS_LIMIT = 10

if IS_SQL_DATABASE:
    conn = sqlite3.connect('instance/blog.sqlite', check_same_thread=False)
    utils.cursor = conn.cursor()
else:
    client = MongoClient('localhost', 27017)
    db = client['blog']
    utils.db = client['blog']


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
    posts = []
    if IS_SQL_DATABASE:
        posts = get_posts()
    else:
        posts = db.posts.find({}, {"author": 1, "title": 1}).limit(POSTS_LIMIT)
    return render_template('index.html', posts=posts)


@app.route('/post/<id>/comment', methods=['POST'])
@app.route('/post/<id>', methods=['GET', 'POST'])
def post(id):
    if request.method == 'GET':
        if IS_SQL_DATABASE:
            post = get_post(id)
        else:
            post = db.posts.find_one(ObjectId(id))

        post['body'] = markdown.markdown(post['body'])

        # Get comments for the post
        comments = []
        if IS_SQL_DATABASE:
            comments = get_comments(id)
        else:
            comments = db.comments.find({"post_id": id})

        return render_template('post.html', post=post, comments=comments)

    elif request.method == 'POST':
        if 'username' not in session:
            return redirect('/login')

        author = session['username']
        content = request.form['content']

        if IS_SQL_DATABASE:
            create_comment(id, author, content)
            conn.commit()
        else:
            db.comments.insert_one({
                "post_id": id,
                "author": author,
                "content": content,
                "created_at": datetime.now(),
            })

        return redirect('/post/' + id)


# @login_required
@app.route('/create', methods=['POST', 'GET'])
def create():
    if request.method == 'POST':
        if 'username' not in session:
            return redirect('/login')
        title = request.form['title']
        body = request.form['body']
        if IS_SQL_DATABASE:
            author_id = get_user_id(session['username'])
            create_post(title, body, author_id)
            conn.commit()
        else:
            posts = db.posts.insert_one({
                "author": session['username'],
                "title": title,
                "body": body,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })

        return render_template('create.html', message="Created Successfully")
    else:
        return render_template('create.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    elif request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if IS_SQL_DATABASE:
            stored_user = get_user_by_email(email)
            stored_username = stored_user[1] if stored_user else ""
            stored_password = stored_user[3] if stored_user else ""

        else:
            stored_user = db.users.find_one({"email": email})
            stored_username = stored_user['username']
            stored_password = stored_user['password']

        if verify_password(stored_password, password):
            session['username'] = stored_username
            return redirect("/")
        else:
            return render_template('login.html', message="login Failed")


@app.route('/sign_up', methods=['POST', 'GET'])
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not is_valid_email(email) and check_email(email):
            return redirect('/login')

        if IS_SQL_DATABASE:
            add_user(username, email, hash_password(password))
            conn.commit()
        else:
            user = db.users.insert_one({
                "username": username,
                "email": email,
                "password": hash_password(password),
            })

        return redirect('/login')

    else:
        return render_template('sign_up.html')


@app.errorhandler(404)
def not_found(error):
    return render_template('error_404.html'), 404


@app.errorhandler(500)
def not_found(error):
    return render_template('error_500.html'), 500


if __name__ == '__main__':
    app.run()
