import os

from flask import Flask, request, render_template_string, redirect, url_for, flash
from pymongo import MongoClient
from pymongo.errors import PyMongoError, ServerSelectionTimeoutError
import time

MONGO_ADMIN_USER = os.getenv("MONGO_ADMIN_USER", "admin")
MONGO_ADMIN_PASSWORD = os.getenv("MONGO_ADMIN_PASSWORD", "password")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_URI = (
    f"mongodb://{MONGO_ADMIN_USER}:{MONGO_ADMIN_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    "?authSource=admin"
)
DB_NAME = "user-account"
COLLECTION_NAME = "users"

app = Flask(__name__)
app.secret_key = "12344556"


def get_db_collection():
  # Create client with a short server selection timeout and retry a few times
  client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
  retries = 5
  for attempt in range(1, retries + 1):
    try:
      client.admin.command('ping')
      break
    except ServerSelectionTimeoutError:
      if attempt == retries:
        raise
      time.sleep(2)
  db = client[DB_NAME]
  return db[COLLECTION_NAME]


def add_user(username: str, email: str, interest: str) -> str:
    collection = get_db_collection()
    user_doc = {
        "username": username,
        "email": email,
        "interest": interest,
    }
    result = collection.insert_one(user_doc)
    return str(result.inserted_id)


def update_user(username: str, email: str = None, interest: str = None) -> int:
    collection = get_db_collection()
    update_fields = {}
    if email is not None:
        update_fields["email"] = email
    if interest is not None:
        update_fields["interest"] = interest

    if not update_fields:
        return 0

    result = collection.update_one(
        {"username": username},
        {"$set": update_fields}
    )
    return result.modified_count


def get_user(username: str) -> dict:
    collection = get_db_collection()
    return collection.find_one({"username": username}, {"_id": 0})


def get_all_users() -> list:
    collection = get_db_collection()
    return list(collection.find({}, {"_id": 0}))

HOME_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>MongoDB User UI</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 20px; }
      input, textarea { width: 100%; padding: 8px; margin: 4px 0; }
      label { font-weight: bold; }
      table { width: 100%; border-collapse: collapse; margin-top: 20px; }
      th, td { border: 1px solid #ddd; padding: 8px; }
      th { background: #f4f4f4; }
      .alert { padding: 10px; background: #f8d7da; color: #721c24; margin-bottom: 10px; }
    </style>
  </head>
  <body>
    <h1>MongoDB User UI</h1>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <div class="alert">{{ messages[0] }}</div>
      {% endif %}
    {% endwith %}

    <h2>Add User</h2>
    <form action="{{ url_for('create_user') }}" method="post">
      <label for="username">Username</label>
      <input name="username" id="username" required />
      <label for="email">Email</label>
      <input name="email" id="email" type="email" required />
      <label for="interest">Interest</label>
      <textarea name="interest" id="interest" rows="3" required></textarea>
      <button type="submit">Add User</button>
    </form>

    <h2>Update User</h2>
    <form action="{{ url_for('modify_user') }}" method="post">
      <label for="update_username">Username</label>
      <input name="username" id="update_username" required />
      <label for="update_email">New Email</label>
      <input name="email" id="update_email" type="email" />
      <label for="update_interest">New Interest</label>
      <textarea name="interest" id="update_interest" rows="3"></textarea>
      <button type="submit">Update User</button>
    </form>

    <h2>All Users</h2>
    <table>
      <thead>
        <tr><th>Username</th><th>Email</th><th>Interest</th></tr>
      </thead>
      <tbody>
        {% for user in users %}
        <tr>
          <td>{{ user.username }}</td>
          <td>{{ user.email }}</td>
          <td>{{ user.interest }}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    users = get_all_users()
    return render_template_string(HOME_TEMPLATE, users=users)


@app.route("/create", methods=["POST"])
def create_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip()
    interest = request.form.get("interest", "").strip()

    if not username or not email or not interest:
        flash("Username, email, and interest are required.")
        return redirect(url_for("home"))

    try:
        add_user(username, email, interest)
        flash("User added successfully.")
    except PyMongoError as err:
        flash(f"MongoDB error: {err}")

    return redirect(url_for("home"))


@app.route("/update", methods=["POST"])
def modify_user():
    username = request.form.get("username", "").strip()
    email = request.form.get("email", "").strip() or None
    interest = request.form.get("interest", "").strip() or None

    if not username:
        flash("Username is required for update.")
        return redirect(url_for("home"))

    try:
        modified = update_user(username, email=email, interest=interest)
        if modified:
            flash("User updated successfully.")
        else:
            flash("No matching user found or no fields changed.")
    except PyMongoError as err:
        flash(f"MongoDB error: {err}")

    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
