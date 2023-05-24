import re
import app
from bson.objectid import ObjectId
from datetime import datetime

POSTS_LIMIT = 10


def get_posts():
    """
    :return: the list of dict of post_id, post_title, username
    """
    if app.IS_SQL_DATABASE:
        app.cursor.execute(f"SELECT post.id, post.title, user.name FROM post "
                           f"INNER JOIN user ON post.user_id = user.id LIMIT {POSTS_LIMIT}")
        records = app.cursor.fetchall()
        result = [{"_id": row[0], "title": row[1], "author": row[2]} for row in records]
        return result
    else:
        return app.db.posts.find({}, {"author": 1, "title": 1}).limit(POSTS_LIMIT)


def get_post(post_id):
    """
    :param post_id:
    :return: the list of posts
    """
    if app.IS_SQL_DATABASE:
        app.cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,))
        row = app.cursor.fetchone()
        author = get_username(row[5])
        return {"_id": row[0],
                "title": row[1],
                "body": row[2],
                "created_at": row[4],
                "updated_at": row[3],
                "author": author[0]
                }
    else:
        return app.db.posts.find_one(ObjectId(post_id))


def add_user(name, email, password):
    """
    :param name:
    :param email:
    :param password:
    :return:
    """
    if app.IS_SQL_DATABASE:
        app.cursor.execute("INSERT INTO user (name , email , password) VALUES (? , ? , ?)", (name, email, password))
        app.conn.commit()
    else:
        user = app.db.users.insert_one({
            "username": name,
            "email": email,
            "password": password,
        })


def get_comments(post_id):
    """
    :param post_id:
    :return:
    """
    if app.IS_SQL_DATABASE:
        app.cursor.execute(
            "SELECT name , body , comment.created_at FROM comment "
            "LEFT JOIN user on user.id = user_id WHERE post_id = ?",
            (post_id,))

        records = app.cursor.fetchall()
        return [{
            "author": row[0],
            "created_at": row[1],
            "body": row[2]} for row in records]
    else:
        result = app.db.posts.find({"_id": ObjectId(post_id)},
                                   {"comments": 1, "_id": 0})

        return result[0]["comments"]


def check_email(email):
    """
    :param email:
    :return:
    """
    app.cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    if app.cursor.fetchone():
        return True
    return False


def is_valid_email(email):
    """
    :param email:
    :return:
    """
    # Check if the email address has the @ symbol.
    if "@" not in email:
        return False

    # Check if the email address has a valid domain name.
    match = re.match(r"[^@]+@[^@]+\.[^@]+", email)
    if not match:
        return False

    return True


def get_user_by_email(email):
    """
    :param email:
    :return:
    """
    if app.IS_SQL_DATABASE:
        app.cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
        stored_user = app.cursor.fetchone()
        stored_username = stored_user[1] if stored_user else ""
        stored_password = stored_user[3] if stored_user else ""
        return stored_username, stored_password

    else:
        stored_user = app.db.users.find_one({"email": email})
        stored_username = stored_user['username'] if stored_user else ""
        stored_password = stored_user['password'] if stored_user else ""
        return stored_username, stored_password


def get_user_id(username):
    """
    :param username:
    :return:
    """
    app.cursor.execute("SELECT id FROM user WHERE name = ?", (username,))
    return app.cursor.fetchone()[0]


def get_username(user_id):
    """
    :param username:
    :return:
    """
    app.cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
    return app.cursor.fetchone()


def create_post(title, body, username):
    """
    :param username:
    :param title:
    :param body:
    :return:
    """
    if app.IS_SQL_DATABASE:
        user_id = get_user_id(username)
        app.cursor.execute("INSERT INTO post (title, body, user_id) VALUES (?, ? ,? )",
                           (title, body, user_id))
        app.conn.commit()
    else:
        posts = app.db.posts.insert_one({
            "author": username,
            "title": title,
            "body": body,
            "comments": [],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        })


def update_post(post_id, title, body):
    if app.IS_SQL_DATABASE:
        app.cursor.execute("UPDATE post SET title=?, body =? WHERE id = ?", (title, body, post_id))
        app.conn.commit()
    else:
        app.db.posts.update_one({"_id": ObjectId(post_id)}, {"$set": {"title": title, "body": body}})


def delete_post(post_id):
    if app.IS_SQL_DATABASE:
        app.cursor.execute("DELETE FROM comment WHERE post_id = ?", (post_id,))
        app.cursor.execute("DELETE FROM post WHERE id = ?", (post_id,))
        app.conn.commit()
    else:
        app.db.posts.delete_one({"_id": ObjectId(post_id)})


def create_comment(post_id, author, body):
    created_at = datetime.now()
    if app.IS_SQL_DATABASE:
        user_id = get_user_id(author)

        app.cursor.execute("INSERT INTO comment (body, created_at, user_id, post_id)"
                           "VALUES (?,?,?,?)",
                           (body, created_at, user_id, post_id))
        app.conn.commit()

    else:
        app.db.posts.update_one({"_id": ObjectId(post_id)}, {'$push': {'comments': {
            "body": body,
            "author": author,
            "created_at": created_at,
        }}})


def import_posts_from_csv_file():
    # FIXME
    import csv
    if app.IS_SQL_DATABASE:
        with open("sql_data.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                app.cursor.execute("INSERT INTO post (title, body, user_id ,created_at) VALUES (%s, %s, %s ,%s)", row)
        app.conn.commit()
    else:
        with open("no_sql_data.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                app.db.posts.insert_one({
                    "author": username,
                    "title": title,
                    "body": body,
                    "comments": [],
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                })
