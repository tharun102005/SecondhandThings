from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.utils import secure_filename
import json
import os
import uuid

app = Flask(__name__)
app.secret_key = "mysecretkey"

DATA_FILE = "data.json"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [], "items": []}, f)


# =========================
# FILE PATHS
# =========================
DATA_FILE = "data.json"
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# =========================
# ENSURE FILES / FOLDERS
# =========================
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [], "items": []}, f)

# =========================
# LOAD / SAVE DATA
# =========================


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# =========================
# HOME
# =========================


@app.route("/")
def home():
    return redirect("/login")

# =========================
# LOGIN
# =========================


@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()

    if request.method == "POST":
        mobile = request.form.get("mobile")
        password = request.form.get("password")

        for u in data["users"]:
            if u.get("mobile") == mobile and u.get("password") == password:
                if u.get("status") == "blocked":
                    return render_template(
                        "login.html", error="Account blocked")

                session["user"] = u
                return redirect("/buy")

        return render_template("login.html", error="Invalid login")

    return render_template("login.html")

# =========================
# SIGNUP
# =========================


@app.route("/signup", methods=["GET", "POST"])
def signup():
    data = load_data()

    if request.method == "POST":
        user = {
            "name": request.form.get("name"),
            "mobile": request.form.get("mobile"),
            "email": request.form.get("email"),
            "password": request.form.get("password"),
            "address": "",
            "dob": "",
            "profile_image": "",
            "wishlist": [],
            "status": "active"
        }
        data["users"].append(user)
        save_data(data)
        return redirect("/login")

    return render_template("signup.html")

# =========================
# BUY
# =========================


@app.route("/buy")
def buy():
    if "user" not in session:
        return redirect("/login")
    user = session.get("user", {})
    wishlist = user.get("wishlist", [])
    return render_template("buy.html", wishlist=wishlist)


@app.route("/get-items")
def get_items():
    return jsonify(load_data()["items"])

# =========================
# SELL
# =========================


@app.route("/sell")
def sell():
    if "user" not in session:
        return redirect("/login")
    return render_template("sell.html")

# =========================
# SAVE ITEM
# =========================


@app.route("/save-item", methods=["POST"])
def save_item():
    if "user" not in session:
        return jsonify({"error": "login required"}), 401

    data = load_data()
    user = session["user"]
    item = request.json

    new_item = {
        "id": str(uuid.uuid4()),
        "name": user.get("name"),
        "mobile": user.get("mobile"),
        "email": user.get("email"),
        "price": item.get("price"),
        "model": item.get("model"),
        "type": item.get("type"),
        "address": item.get("address"),
        "about": item.get("about"),
        "images": item.get("images", [])
    }

    data["items"].append(new_item)
    save_data(data)
    return jsonify({"success": True})

# =========================
# USER EDIT ITEM
# =========================


@app.route("/edit-my-item/<item_id>", methods=["GET", "POST"])
def edit_my_item(item_id):
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session["user"]

    # Find item owned by this user
    item = next(
        (i for i in data["items"]
         if i.get("id") == item_id and
         i.get("mobile") == user.get("mobile")),
        None
    )

    if not item:
        return "Item not found or not allowed", 404

    if request.method == "POST":
        item["model"] = request.form.get("model")
        item["price"] = request.form.get("price")
        item["type"] = request.form.get("type")
        item["address"] = request.form.get("address")
        item["about"] = request.form.get("about")

        save_data(data)
        return redirect("/profile")

    return render_template("edit-item.html", item=item)

# =========================
# ITEM VIEW
# =========================


@app.route("/item/<item_id>")
def item_view(item_id):
    user = session.get("user", {})
    wishlist = user.get("wishlist", [])
    for item in load_data()["items"]:
        if item.get("id") == item_id:
            return render_template(
                "item-view.html", item=item, wishlist=wishlist)
    return "Item not found", 404

# =========================
# PROFILE
# =========================


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session.get("user")

    if not user or not user.get("mobile"):
        session.clear()
        return redirect("/login")

    if request.method == "POST":
        user["name"] = request.form.get("name", "")
        user["email"] = request.form.get("email", "")
        user["address"] = request.form.get("address", "")
        user["dob"] = request.form.get("dob", "")

        file = request.files.get("profile_image")
        if file and file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            user["profile_image"] = "/" + path.replace("\\", "/")

        for i, u in enumerate(data["users"]):
            if u.get("mobile") == user.get("mobile"):
                data["users"][i] = user
                break

        session["user"] = user
        save_data(data)
        return redirect("/profile")

    my_items = [i for i in data["items"]
                if i.get("mobile") == user.get("mobile")]

    return render_template("profile.html", user=user, my_items=my_items)

# =========================
# USER DELETE ITEM IMAGE
# =========================


@app.route("/delete-item-image/<item_id>/<int:index>")
def delete_item_image(item_id, index):
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session["user"]

    # Find item owned by logged-in user
    item = next(
        (i for i in data.get("items", [])
         if i.get("id") == item_id and
         i.get("mobile") == user.get("mobile")),
        None
    )

    if not item:
        return redirect("/profile")

    # Remove image safely
    images = item.get("images", [])
    if 0 <= index < len(images):
        images.pop(index)

    save_data(data)
    return redirect(f"/edit-my-item/{item_id}")


# =========================
# DELETE MY ITEM
# =========================


@app.route("/delete-my-item/<item_id>")
def delete_my_item(item_id):
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session["user"]

    data["items"] = [
        i for i in data["items"]
        if not (i.get("id") == item_id and
                i.get("mobile") == user.get("mobile"))
    ]

    save_data(data)
    return redirect("/profile")

# =========================
# WISHLIST
# =========================


@app.route("/toggle-wishlist/<item_id>")
def toggle_wishlist(item_id):
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session["user"]
    user.setdefault("wishlist", [])

    if item_id in user["wishlist"]:
        user["wishlist"].remove(item_id)
    else:
        user["wishlist"].append(item_id)

    for u in data["users"]:
        if u.get("mobile") == user.get("mobile"):
            u["wishlist"] = user["wishlist"]

    session["user"] = user
    save_data(data)
    return redirect(request.referrer or "/buy")


@app.route("/wishlist")
def wishlist():
    if "user" not in session:
        return redirect("/login")

    data = load_data()
    user = session["user"]

    items = [i for i in data["items"]
             if i.get("id") in user.get("wishlist", [])]
    return render_template("wishlist.html", items=items)

# =========================
# LOGOUT
# =========================


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# =========================
# ADMIN
# =========================
ADMIN_USERNAME = "tharun"
ADMIN_PASSWORD = "12345"


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if (request.form.get("username") == ADMIN_USERNAME and
                request.form.get("password") == ADMIN_PASSWORD):
            session["admin"] = True
            return redirect("/admin")
        return render_template("admin-login.html", error="Invalid login")

    return render_template("admin-login.html")


@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/admin-login")

    data = load_data()
    return render_template(
        "admin.html", users=data["users"], items=data["items"])


@app.route("/admin-user-items/<mobile>")
def admin_user_items(mobile):
    if not session.get("admin"):
        return redirect("/admin-login")

    data = load_data()
    user = next((u for u in data["users"] if u.get("mobile") == mobile),
                None)

    if not user:
        return "User not found", 404

    items = [i for i in data["items"] if i.get("mobile") == mobile]
    return render_template("admin-user-items.html", user=user, items=items)


@app.route("/admin-edit-item/<item_id>", methods=["GET", "POST"])
def admin_edit_item(item_id):
    if not session.get("admin"):
        return redirect("/admin-login")

    data = load_data()
    item = next((i for i in data["items"] if i.get("id") == item_id), None)

    if not item:
        return "Item not found", 404

    if request.method == "POST":
        item["model"] = request.form.get("model")
        item["price"] = request.form.get("price")
        item["type"] = request.form.get("type")
        item["address"] = request.form.get("address")
        item["about"] = request.form.get("about")
        save_data(data)
        return redirect(f"/admin-user-items/{item.get('mobile')}")

    return render_template("admin-edit-item.html", item=item)


@app.route("/admin-delete-item/<item_id>")
def admin_delete_item(item_id):
    if not session.get("admin"):
        return redirect("/admin-login")

    data = load_data()
    data["items"] = [i for i in data["items"] if i.get("id") != item_id]
    save_data(data)
    return redirect("/admin")


@app.route("/admin-logout")
def admin_logout():
    session.pop("admin", None)
    return redirect("/admin-login")

# =========================
# ADMIN DELETE USER (JSON)
# =========================


@app.route("/admin-delete-user/<mobile>")
def admin_delete_user(mobile):
    if not session.get("admin"):
        return redirect("/admin-login")

    data = load_data()

    data["users"] = [u for u in data["users"]
                     if u.get("mobile") != mobile]
    data["items"] = [i for i in data["items"]
                     if i.get("mobile") != mobile]

    save_data(data)
    return redirect("/admin")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(debug=True)
