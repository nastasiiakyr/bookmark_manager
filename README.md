# BOOKMARK MANAGER

#### Video Demo: <URL HERE>

## Description

In my life and work, I frequently find myself needing to save websites. Chrome already lets you do this, but if you just dump everything into folders without any real filtering, finding anything later becomes a mess. On the other hand, if you try to organize bookmarks into thematic folders from the start, you often end up saving the same link in two or three different folders because it fits more than one category. That annoyed me enough that I decided to build my own tool for it.

So my goal with this project was pretty simple: let a user save a website once, attach as many tags to it as they want, and then be able to find it again quickly through search or filters, no matter which "category" they were thinking of when they saved it originally.

This is my final project for CS50, and it's a Flask web app backed by SQLite. It has user accounts, so bookmarks are private to whoever saved them, and it supports full CRUD (create, read, update, delete) for both bookmarks and tags.

## Application Features

1. User registration and login/logout, with hashed passwords.
2. Password change page for logged-in users.
3. Tag management - create, edit, delete, and view tags, each with its own color so they're easier to tell apart visually.
4. Bookmark management — add, edit, delete, and view saved websites, each of which can have a cost label (free, freemium, premium) and multiple tags attached.
5. Global search across name, URL, description, cost, and tag names at the same time.
6. Filtering by one or more tags and one or more cost types, combinable with the search.

## Technologies

- **Frontend:** HTML, CSS, Bootstrap, Jinja2
- **Backend:** Python, Flask
- **Database:** SQLite (CS50 SQL Library)
- **Authentication:** Flask-Session, Werkzeug password hashing

## Project Structure

### app.py

The main application file. It contains all Flask routes, form validation, database queries, authentication logic, search, filtering, and CRUD operations.
I kept it as one file instead of splitting into blueprints, mostly because the project isn't huge and I didn't want to overcomplicate things for myself while still learning Flask.

- Authentication routes
  - `/register` - shows the registration form on GET, and on POST checks that the username isn't taken and the password meets the rules, then hashes it with Werkzeug before saving.
  - `/login` - checks the submitted username/password against the hash stored in the database and starts a session if it matches.
  - `/logout` - clears the current Flask session and logs the user out.
  - `/password` - lets a logged-in user change their password after confirming the old one.

- Bookmark Management
  - `/` - the main page shows all of the user's bookmarks, and handles both search and filtering.
  - `/create-bookmark` - adds a new bookmark, with a URL field, name, favicon URL, description, cost, and tag checkboxes.
  - `/edit-bookmark` - shows the same form but pre-filled with the existing data of chosen bookmark and edits bookmark data in database.
  - `/delete-bookmark` - deletes the bookmark from database and cleans up its rows in bookmark_tags so there's no leftover data pointing to nothing.

- Tag Management
  - `/tags` - shows all of the user's tags.
  - `/create-tag` - adds a new tag, with a tag name and tag color selection.
  - `/edit-tag` - shows the same form but pre-filled with the existing data of chosen tag and edits tag data in database.
  - `/delete-tag` - removes a tag from the database and cleans up its rows in bookmark_tags so there's no leftover data pointing to nothing.

### helpers.py

Just one function here, `login_required`, a decorator that redirects to the login page if there's no active session. I copied the general idea from the CS50 Finance problem set and adapted it here, since basically every route except login/register needs it.

### schema.sql

Contains the SQLite database schema. It creates four tables: `users`, `tags`, `bookmarks`, `bookmark_tags`. The last one is a join table that connects bookmarks to tags in a many-to-many relationship.

### templates/

All the Jinja templates.

- `layout.html` is the base template with the navbar and shared styling that everything else extends.
- `index.html` is the main page with search, filters, and the bookmark list.
- `login.html` and `register.html` are the authentication forms.
- `password.html` is the password-change form.
- `create_bookmark.html` and `edit_bookmark.html` hold the bookmarks' create/editing forms.
- `tags.html` shows tags with edit/delete buttons.
- `create_tag.html` and `edit_tag.html` hold the tag's create/editing forms.

### static/

Contains static resources. Just `styles.css` — custom application styles that Bootstrap doesn't cover.

## Design Decisions

One of the first design decisions was to handle categories. My first idea was to just add a category column to the bookmarks table. But that breaks down immediately once a bookmark fits more than one category - which, in practice, is most of them. So I switched to a proper many-to-many setup with tags and bookmark_tags, which is a bit more work up front but avoids duplicating bookmarks entirely.

The search and filter page gave me more trouble than I expected. Originally I was going to make separate pages for "search results" and "filtered results," but that felt clunky, and users would probably want to combine both anyway (e.g., search for "tutorial" AND filter by the "coding" tag). So everything happens on / through query parameters, and the SQL query is built dynamically depending on which filters are active. Getting the number of ? placeholders to line up with the number of selected tags/costs took a few tries to get right: I had a bug for a while where filtering by more than one tag would silently return nothing, which turned out to be a mismatch between the placeholders and the parameters passed to db.execute.

For the security reasons all passwords are hashed with Werkzeug. Also every SQL query is written to protect against SQL injection, and every bookmark or tag belongs only to the currently logged-in user.

## How to Run

1. Clone the repository

   ```
   git clone <repository-url>
   ```

2. Open the project folder

   ```
   cd bookmark-manager
   ```

3. Create a virtual environment

   ```
   python -m venv .venv
   ```

4. Activate the virtual environment
   - macOS/Linux:

     ```
     source .venv/bin/activate
     ```

   - Windows:

     ```
     .venv\Scripts\activate
     ```

5. Install the required packages

   ```
   pip install -r requirements.txt
   ```

6. Initialize the database

   ```
   sqlite3 bookmarks.db < schema.sql
   ```

7. Run the application

   ```
   flask run
   ```

8. Open your browser and visit:

   ```
   http://127.0.0.1:5000
   ```
