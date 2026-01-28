from flask import Flask, render_template, request, jsonify, redirect, session
from werkzeug.utils import secure_filename
import json
import os
import uuid
import random
import string
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ========================
# EMAIL CONFIGURATION (HARDCODED)
# ========================
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "tharun060828@gmail.com"
SENDER_PASSWORD = "zllz vdgs jtxi voty"
DEBUG_MODE = False

app = Flask(__name__)
app.secret_key = "mysecretkey"

DATA_FILE = "data.json"
UPLOAD_FOLDER = "static/uploads"
OTP_FILE = "otp_store.json"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"users": [], "items": []}, f)

if not os.path.exists(OTP_FILE):
    with open(OTP_FILE, "w") as f:
        json.dump({}, f)


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
# OTP HELPER FUNCTIONS
# =========================


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))


def load_otp_store():
    """Load OTP storage from file"""
    try:
        with open(OTP_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_otp_store(otp_store):
    """Save OTP storage to file"""
    with open(OTP_FILE, "w") as f:
        json.dump(otp_store, f, indent=4)


def store_otp(mobile, otp):
    """Store OTP with expiration (5 minutes)"""
    otp_store = load_otp_store()
    otp_store[mobile] = {
        "otp": otp,
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat()
    }
    save_otp_store(otp_store)


def verify_otp(mobile, otp):
    """Verify OTP against stored value"""
    otp_store = load_otp_store()
    if mobile not in otp_store:
        return False, "OTP not found. Please request a new OTP."
    
    stored_data = otp_store[mobile]
    expires_at = datetime.fromisoformat(stored_data["expires_at"])
    
    if datetime.now() > expires_at:
        return False, "OTP has expired. Please request a new OTP."
    
    if stored_data["otp"] != otp:
        return False, "Invalid OTP."
    
    return True, "OTP verified successfully"


def clear_otp(mobile):
    """Clear OTP after successful verification"""
    otp_store = load_otp_store()
    if mobile in otp_store:
        del otp_store[mobile]
        save_otp_store(otp_store)


# =========================
# EMAIL SENDING FUNCTION
# =========================

def send_email_otp(email, otp):
    """Send OTP to email using SMTP"""
    
    # Print to console for development/debugging
    print(f"\n{'='*60}")
    print(f"Email OTP Sent to: {email}")
    print(f"OTP: {otp}")
    print(f"{'='*60}\n")
    
    if DEBUG_MODE:
        return True
    
    try:
        # Create email message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your OTP for Email Verification"
        message["From"] = SENDER_EMAIL
        message["To"] = email
        
        # Create plain text and HTML versions of the email
        text = f"""
        Your OTP for Email Verification is: {otp}
        
        This OTP is valid for 5 minutes.
        Do not share this OTP with anyone.
        
        If you didn't request this, please ignore this email.
        """
        
        html = f"""\
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #667eea;">Email Verification</h2>
                    <p>Thank you for signing up! Here's your OTP to verify your email address:</p>
                    
                    <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #667eea; font-size: 36px; letter-spacing: 5px; margin: 0;">{otp}</h1>
                    </div>
                    
                    <p><strong>OTP Validity:</strong> 5 minutes</p>
                    
                    <p style="color: #666; font-size: 14px;">
                        <strong>Important:</strong> Do not share this OTP with anyone. We will never ask you for your OTP.
                    </p>
                    
                    <p style="color: #666; font-size: 14px;">
                        If you didn't request this OTP, please ignore this email.
                    </p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This is an automated email. Please do not reply.
                    </p>
                </div>
            </body>
        </html>
        """
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")
        
        message.attach(part1)
        message.attach(part2)
        
        # Send email
        print(f"Connecting to SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            print("TLS connection established")
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print(f"Logged in as: {SENDER_EMAIL}")
            server.sendmail(SENDER_EMAIL, email, message.as_string())
            print(f"Email sent successfully to {email}")
        
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication Error: {str(e)}")
        print(f"Check if app password is correct: {SENDER_PASSWORD}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

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
        email = request.form.get("email")
        password = request.form.get("password")

        for u in data["users"]:
            if u.get("email") == email and u.get("password") == password:
                if u.get("status") == "blocked":
                    return render_template(
                        "login.html", error="Account blocked")

                # Direct login without OTP
                session["user"] = u
                return redirect("/buy")

        return render_template("login.html", error="Invalid email or password")

    return render_template("login.html")


# =========================
# SIGNUP
# =========================


@app.route("/signup", methods=["GET", "POST"])
def signup():
    data = load_data()

    if request.method == "POST":
        email = request.form.get("email")
        
        # Check if email already exists
        if any(u.get("email") == email for u in data["users"]):
            return render_template("signup.html", error="Email already registered")
        
        # Check if mobile already exists
        mobile = request.form.get("mobile")
        if any(u.get("mobile") == mobile for u in data["users"]):
            return render_template("signup.html", error="Mobile number already registered")
        
        # Generate OTP and send to email
        otp = generate_otp()
        store_otp(email, otp)
        
        # Send OTP via email
        send_email_otp(email, otp)
        
        # Store user data temporarily for verification
        user_data = {
            "name": request.form.get("name"),
            "mobile": mobile,
            "email": email,
            "password": request.form.get("password"),
            "address": "",
            "dob": "",
            "profile_image": "",
            "wishlist": [],
            "status": "active"
        }
        
        session["email_for_otp"] = email
        session["temp_user_data"] = user_data
        
        return redirect("/verify-otp-signup")

    return render_template("signup.html")

# =========================
# VERIFY OTP SIGNUP
# =========================


@app.route("/verify-otp-signup", methods=["GET", "POST"])
def verify_otp_signup():
    if "email_for_otp" not in session or "temp_user_data" not in session:
        return redirect("/signup")
    
    email = session.get("email_for_otp")
    
    if request.method == "POST":
        otp = request.form.get("otp")
        
        is_valid, message = verify_otp(email, otp)
        
        if is_valid:
            clear_otp(email)
            
            # Save user to database
            data = load_data()
            user = session.get("temp_user_data")
            data["users"].append(user)
            save_data(data)
            
            session.pop("email_for_otp", None)
            session.pop("temp_user_data", None)
            
            return redirect("/login")
        else:
            return render_template("verify-otp-signup.html", 
                                 error=message, email=email)
    
    return render_template("verify-otp-signup.html", email=email)

# =========================
# RESEND OTP
# =========================


@app.route("/resend-otp", methods=["POST"])
def resend_otp():
    email = request.form.get("email")
    
    if not email:
        return jsonify({"error": "Email required"}), 400
    
    # Generate new OTP
    otp = generate_otp()
    store_otp(email, otp)
    
    # Send OTP via email
    send_email_otp(email, otp)
    
    return jsonify({"success": True, "message": "OTP sent successfully to your email"})

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
