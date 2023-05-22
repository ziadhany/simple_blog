import re
import app


def check_email(email):
    """
    :param email:
    :return:
    """
    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    if cursor.fetchone():
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
    global cursor
    cursor.execute("SELECT * FROM user WHERE email = ?", (email,))
    return cursor.fetchone()


def get_user_id(username):
    """
    :param username:
    :return:
    """
    global cursor
    cursor.execute("SELECT id FROM user WHERE name = ?", (username,))
    return cursor.fetchone()[0]


def get_username(user_id):
    """
    :param username:
    :return:
    """
    global cursor
    cursor.execute("SELECT name FROM user WHERE id = ?", (user_id,))
    return cursor.fetchone()


def add_user(name, email, password):
    """
    :param name:
    :param email:
    :param password:
    :return:
    """
    global cursor
    cursor.execute("INSERT INTO user (name , email , password) VALUES (? , ? , ?)", (name, email, password))


def make_post(title, body, user_id):
    """
    :param title:
    :param body:
    :param user_id:
    :return:
    """
    global cursor
    cursor.execute("INSERT INTO post (title, body, user_id) VALUES (?, ? ,? )",
                   (title, body, user_id))


def get_posts():
    """
    :return: the list of dict of post_id, post_title, username
    """
    global cursor
    cursor.execute(f"SELECT post.id, post.title, user.name FROM post "
                   f"INNER JOIN user ON post.user_id = user.id LIMIT {app.POSTS_LIMIT}")
    records = cursor.fetchall()
    result = [{"_id": row[0], "title": row[1], "author": row[2]} for row in records]
    return result


def get_post(post_id):
    """"""
    global cursor
    cursor.execute("SELECT * FROM post WHERE id = ?", (post_id,))
    row = cursor.fetchone()
    author = get_username(row[5])  # user_id
    return {"_id": row[0],
            "title": row[1],
            "body": row[2],
            "created_at": row[4],
            "updated_at": row[3],
            "author": author[0]
            }

# def change_name(email, password, new_name):
#     user = getUser(email, password)
#
#     if user is None:
#         return False
#     try:
#         cursor.execute("UPDATE user SET name = ? WHERE email =? and password = ? ", (new_name, email, password,))
#         conn.commit()
#     except:
#         return False
#     return True
