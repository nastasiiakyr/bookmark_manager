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

# Define a dictionary of colors for tags
COLORS = {
    "blue": "#3b82f6",
    "green": "#22c55e",
    "red": "#ef4444",
    "purple": "#a855f7",
    "gray": "#6b7280"
}

# Define cost types
COSTS = {
    "free": "✅ Free",
    "freemium": "💰 Freemium",
    "premium": "💸 Premium"
}

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


#####
##### Main route
@app.route("/", methods=["GET"])
@login_required
def home():
    """Show all bookmarks for the logged-in user"""
    # Get bookmarks from the database
    bookmarks = db.execute("SELECT id, name, url, favicon, cost, description FROM bookmarks WHERE user_id = ? ORDER BY name", session["user_id"])

    # Get tags associated with bookmarks
    bookmark_tags = db.execute("SELECT bt.bookmark_id, t.id, t.name, t.color FROM bookmark_tags AS bt JOIN tags AS t ON bt.tag_id = t.id WHERE t.user_id = ?", session["user_id"])

    # Add tags to bookmarks
    for bookmark in bookmarks:
        bookmark["tags"] = []

    for bookmark in bookmarks:
        for tag in bookmark_tags:
            if bookmark["id"] == tag["bookmark_id"]:
                bookmark["tags"].append(tag)
    
    return render_template("index.html", bookmarks=bookmarks, costs=COSTS, colors=COLORS)


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


#####
##### Bookmark routes
@app.route("/create-bookmark", methods=["GET", "POST"])
@login_required
def create_bookmark():
    """Create a new bookmark"""
    # Get user's tags from the database
    user_tags = db.execute("SELECT id, name FROM tags WHERE user_id = ?", session["user_id"])

    # Handle form submission
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        url = request.form.get("url")
        favicon = request.form.get("favicon")
        tags = request.form.getlist("tags")
        cost = request.form.get("cost")
        description = request.form.get("description")

        # Validate form data
        if not name or not url or not tags:
            flash("Bookmark name, URL and tags are required")
            return redirect("/create-bookmark")
        
        # Validate url format
        if not url.startswith("http://") and not url.startswith("https://"):
            flash("Invalid URL format")
            return redirect("/create-bookmark")
        
        # Validate favicon url format if provided
        if favicon and not (favicon.startswith("http://") or favicon.startswith("https://")):
            flash("Invalid favicon URL format")
            return redirect("/create-bookmark")
        
        # Validate tags selection
        for tag in tags:
            if not any(t["id"] == int(tag) for t in user_tags):
                flash("Invalid tag selected")
                return redirect("/create-bookmark")
            
        # Validate cost selection
        if cost and cost not in COSTS:
            flash("Invalid cost type selected")
            return redirect("/create-bookmark")    

        # Save data to the database
        bookmark_id =db.execute("INSERT INTO bookmarks (user_id, name, url, favicon, cost, description) VALUES(?, ?, ?, ?, ?, ?)", session["user_id"], name, url, favicon, cost, description)

        for tag in tags:
            db.execute("INSERT INTO bookmark_tags (bookmark_id, tag_id) VALUES(?, ?)", bookmark_id, tag)

        return redirect("/")

    else:
        return render_template("create_bookmark.html", tags=user_tags, costs=COSTS)
   


#####
##### Tag routes
@app.route("/tags", methods=["GET"])
@login_required
def tags():
    """Show all tags for the logged-in user"""
    tags = db.execute("SELECT id, name, color FROM tags WHERE user_id = ? ORDER BY name", session["user_id"])
    return render_template("tags.html", tags=tags, colors=COLORS)


@app.route("/create-tag", methods=["GET", "POST"])
@login_required
def create_tag():
    """Create a new tag"""
    if request.method == "POST":
        # Get form data
        name = request.form.get("name")
        color = request.form.get("color")

        # Validate form data
        if not name or not color:
            flash("All fields are required")
            return redirect("/create-tag")
        
        # Validate color selection
        if color not in COLORS:
            flash("Invalid color selected")
            return redirect("/create-tag")

        # Save data to the database
        db.execute("INSERT INTO tags (user_id, name, color) VALUES(?, ?, ?)", session["user_id"], name, color)

        return redirect("/tags")

    else:
        return render_template("create_tag.html", colors=COLORS)


@app.route("/edit-tag", methods=["GET", "POST"])
@login_required
def edit_tag():
    """Edit an existing tag"""
    if request.method == "POST":

        tag_id = request.form.get("id")
        name = request.form.get("name")
        color = request.form.get("color")

        if not tag_id:
            flash("Something went wrong")
            return redirect("/tags")

        if not name or not color:
            flash("All fields are required")
            return redirect(f"/edit-tag?id={tag_id}")

        if color not in COLORS:
            flash("Invalid color")
            return redirect(f"/edit-tag?id={tag_id}")

        db.execute("UPDATE tags SET name = ?, color = ? WHERE id = ? AND user_id = ?", name, color, tag_id, session["user_id"])

        return redirect("/tags")

    else:
        tag_id = request.args.get("id")

        tag = db.execute("SELECT id, name, color FROM tags WHERE id = ? AND user_id = ?", tag_id, session["user_id"])

        if not tag:
            flash("Tag not found")
            return redirect("/tags")

        return render_template("edit_tag.html", tag=tag[0], colors=COLORS)


@app.route("/delete-tag", methods=["POST"])
@login_required
def delete_tag():
    """Delete a tag"""
    tag_id = request.form.get("id")

    if not tag_id:
        flash("Something went wrong")
        return redirect("/tags")

    db.execute("DELETE FROM tags WHERE id = ? AND user_id = ?", tag_id, session["user_id"])

    return redirect("/tags")

if __name__ == "__main__":
    app.run(debug=True)