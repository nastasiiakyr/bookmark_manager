from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session  
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///bookmark_manager.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#####
##### Main route
@app.route("/")
@login_required
def home():
    return render_template("index.html")


#####
##### Authorization routes
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log in user"""

    # Handle form submission
    if request.method == "POST":

        # Forget any user_id
        session.clear()

        # Get form data
        username = request.form.get("username")
        password = request.form.get("password")

        # Validate form data
        if not username or not password:
            flash("All fields are required")
            return redirect("/login")

        # Query database for user
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Check if user exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password_hash"], password):
            flash("Invalid username and/or password")
            return redirect("/login")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log out user"""

     # Forget any user_id
    session.clear()

    return redirect("/")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Change user's password"""
    if request.method == "POST":
        # Get data
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")
        new_confirmation = request.form.get("new_confirmation")

        # Query database for username
        user = db.execute(
            "SELECT * FROM users WHERE id = ?", session["user_id"]
        )

        # Ensure old password was submitted
        if not old_password or not check_password_hash(
            user[0]["password_hash"], old_password
        ):
            flash("Provide current password")
            return redirect("/password")

        # Ensure new password was submitted
        elif not new_password:
            flash("Provide new password")
            return redirect("/password")

        elif new_password != new_confirmation:
            flash("New passwords do not match")
            return redirect("/password")

        elif old_password == new_password:
            flash("New password must be different from current password")
            return redirect("/password")

        # Save new data to the database
        db.execute("UPDATE users SET password_hash = ? WHERE id = ?",
                   generate_password_hash(new_password, method='scrypt', salt_length=16), session["user_id"])

        return redirect("/logout")

    else:
        # Show form to change password
        return render_template("password.html")
    

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # Get form data
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Validate form data
        if not username or not password or not confirmation:
            flash("All fields are required")
            return redirect("/register")
        
        # Check if password and confirmation match
        elif password != confirmation:
            flash("Passwords do not match")
            return redirect("/register")
        
        # Save data to the database
        try:
            db.execute("INSERT INTO users (username, password_hash) VALUES(?, ?)", username,
                       generate_password_hash(password, method='scrypt', salt_length=16))
        except ValueError:
            flash("Username already exists")
            return redirect("/register")
        
        # Log the user in (store their user_id in session)
        rows = db.execute("SELECT id FROM users WHERE username = ?", username)
        session["user_id"] = rows[0]["id"]

        return redirect("/")

    else:
        return render_template("register.html")



if __name__ == "__main__":
    app.run(debug=True)