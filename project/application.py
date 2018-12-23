from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import gettempdir
from datetime import datetime
import sqlalchemy
import json
from sqlalchemy import and_, text, select

from helpers import *
from validator import *
import datastore

# Configure application
app = Flask(__name__)
JSGlue(app)

# Ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure sqlalchemy library to use database
engine = datastore.get_db_engine(mode='prod')

# Instantiate an instance of the Validator class to check guesses
validator = Validator()

@app.route("/")
@login_required
def index():
    print "Loading Home"
    # Just return index.html, the rest is done in JavaScript (via game.js)
    return render_template("index.html")

@app.route("/guess")
@login_required
def guess():

    print "Submitting Guess"
    # Check to make sure necessary parameters are passed in
    if not request.args.get("guess"):
        raise RuntimeError("missing guess")

    # Set these equal to local variables to reference later
    # Make guess lowercase in order to check against dictionary
    guess = request.args.get("guess").lower()
    game_id = session["game_id"]

    # Get the mystery word from the SQL games table
    game_info = datastore.get_game_info(engine, game_id)

    # Check to make sure a valid game_id was provided
    if len(game_info) == 0:
        raise RuntimeError("game does not exist")
    if game_info['finished']:
        print("Game already finished")
        return json.dumps({'score': -2})

    # Use the validator instance to check whether the guess is in the dictionary
    if not validator.validate(guess):
        # Score of -1 indicates an invalid word for the JavaScript
        return json.dumps({"score": -1})

    # Helper function to find number of letters in common
    score = common_letters(guess, game_info['mystery'])

    # Record this guess in the SQL table guesses
    guess_dict = {'guess': guess, 'score': score, 'game_id': game_id}
    datastore.insert_guess(engine, guess_dict)
    print "Guess: %s" % (guess)
    print "Score: %d" % (score)

    # Check if winner
    # If so, find the total_guesses it took and insert into highscores table
    if guess == game_info['mystery']:
        total_guesses = datastore.get_number_guesses(engine, game_id)
        highscore_dict = {
            'user_id': session['user_id'],
            'score': total_guesses,
            'game_id': game_id
        }
        datastore.insert_highscore(engine, highscore_dict)
        datastore.update_game_finished(engine, game_id)
        # Send the JavaScript a score of 6 to indicate winning
        score = 6
        print "Ending Game...Winner!"

    return json.dumps({"score": score})

@app.route("/table")
@login_required
def table():
    """Return all guesses for current game"""
    print "Loading table for game_id=%i" % session['game_id']

    # Select all guess belonging to current game_id
    guesses = datastore.get_guesses_by_game_id(engine, session['game_id'])
    guesses = [dict(g) for g in guesses]

    return json.dumps(guesses)

@app.route("/highscore")
@login_required
def highscore():
    """Create and print the highscores table"""
    print "Loading Highscores"
    # JOIN 3 SQL tables to get desired data
    rows = datastore.get_all_highscores(engine)

    return render_template("highscore.html", rows=rows)

@app.route("/game_id")
@login_required
def game_id():
    """Send the browser current game_id"""

    # Use new_game method to start a new game
    session["game_id"] = new_game(engine)
    print "Creating new game with game_id=", session["game_id"]

    # Redirect to home page
    return redirect(url_for("index"))

@app.route("/rules")
@login_required
def rules():
    """Create the Rules Page"""
    print "Loading Rules"
    return render_template("rules.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""

    session.clear()
    print "Registering New User..."

    if request.method == "POST":
        # Check that username was provided
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Check that password was provided twice
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password twice", 403)
        # Check that both passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Add user to database
        try:
            hash_ = generate_password_hash(request.form.get("password"))
            user_dict = {'username': request.form.get("username"), 'hash': hash_}
            id_ = datastore.insert_user(engine, user_dict)
        except:
            # Unique constraint will make this fail if username exists
            return apology("Username %s is taken" % request.form.get('username'))

        session["user_id"] = id_

        # start a new game for the user when registered
        session["game_id"] = new_game(engine)

        print "Registered user %s" % (request.form.get('username'))
        print "Created new game %d" % (session['game_id'])
        # redirect to portfolio
        flash("You are registered!")
        return redirect(url_for("index"))

    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out."""
    print "User logged out"
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # Forget any user_id/game_id
    session.clear()

    # If user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = datastore.get_user_by_username(engine, request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Start a new game
        session["game_id"] = new_game(engine)
        print "Created new game with id=%i" % session['game_id']

        print "Logged in user %s" % (request.form.get('username'))
        # Redirect user to game
        return redirect(url_for("index"))

    # Else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Allow user to change password"""

    if request.method == "POST":
        print "Changing password"
        # Query for user's hash of password
        rows = datastore.get_user_by_user_id(engine, session['user_id'])
        print("old hash", rows['hash'])
        print("old form hash", generate_password_hash(request.form.get('old')))
        # Check all boxes filled, old password is correct, new and confirmation match
        if not request.form.get("old") or not check_password_hash(request.form.get("old"), rows["hash"]):
            return apology("incorrect password")
        elif not request.form.get("new") or not request.form.get("confirmation"):
            return apology("must type new password twice")
        elif not request.form.get("new") == request.form.get("confirmation"):
            return apology("new passwords must match")

        # Update hash in database
        pw_hash = generate_password_hash(request.form.get('new'))
        datastore.update_password_hash(engine, user_id, pw_hash)

        # Redirect to portfolio
        flash("Password changed!")
        print "Password changed!"
        return redirect(url_for("index"))

    else:
        return render_template("password.html")

def errorhandler(e):
    """Handle error"""
    return apology(e.name, e.code)

if __name__ == "__main__":
    app.run()
