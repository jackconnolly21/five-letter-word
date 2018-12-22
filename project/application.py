from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import gettempdir
from datetime import datetime
import sqlalchemy
import tables
import json
from sqlalchemy import and_, text, select

from helpers import *
from validator import *
import datastore

# configure application
app = Flask(__name__)
JSGlue(app)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = gettempdir()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure sqlalchemy Library to use SQLite database
engine = datastore.get_db_engine(mode='prod')

# instantiate an instance of the Validator class to check guesses
validator = Validator()

@app.route("/")
@login_required
def index():
    print "Loading Home"
    # just return index.html, the rest is done in JavaScript
    # this is where the main game is run (via games.js)
    return render_template("index.html")

@app.route("/guess")
@login_required
def guess():

    print "Submitting Guess"
    # check to make sure necessary parameters are passed in
    if not request.args.get("guess"):
        raise RuntimeError("missing guess")

    # set these equal to local variables to reference later
    # make guess lowercase in order to check against dictionary
    guess = request.args.get("guess").lower()
    game_id = session["game_id"]
    print("Guess, game_id = %i" % game_id)

    # get the mystery word from the SQL games table
    stmt = text("SELECT mystery FROM games WHERE id = %d" % (game_id))
    mystery = engine.execute(stmt).fetchall()
    # check to make sure a valid game_id was provided
    if len(mystery) == 0:
        raise RuntimeError("game does not exist")

    # set mystery equal to the actual word
    mystery = mystery[0]["mystery"]

    # use the validator instance to check whether the guess is in the dictionary
    if not validator.validate(guess):
        # score of -1 indicates an invalid word for the JavaScript
        return json.dumps({"score": -1})

    # helper function to find number of letters in common
    score = common_letters(guess, mystery)

    # record this guess in the SQL table guesses
    datastore.__insert(engine, tables.GUESSES, {'guess': guess, 'score': score, 'game_id': game_id})
    print "Guess: %s" % (guess)
    print "Score: %d" % (score)

    # check if winner
    # if so, find the total_guesses it took and insert into highscores table
    if guess == mystery:
        total_guesses = datastore.get_number_guesses(engine, game_id)
        # stmt = text("INSERT INTO highscores (user_id, score, game_id) VALUES (%d, %d, %d)" % (session["user_id"], total_guesses, game_id))
        datastore.__insert(engine, tables.HIGHSCORES, {'user_id': session['user_id'], 'score': total_guesses, 'game_id': game_id})
        # send the JavaScript a score of 6 to indicate winning
        score = 6
        print "Ending Game...Winner!"

    return json.dumps({"score": score})

@app.route("/table")
@login_required
def table():
    """Return all guesses for current game"""
    print "Loading Table"
    # select all guess belonging to current game_id
    stmt = text("SELECT * FROM guesses WHERE game_id = %d ORDER BY id" % (session["game_id"]))
    guesses = [dict(g) for g in engine.execute(stmt).fetchall()]

    return json.dumps(guesses)

@app.route("/highscore")
@login_required
def highscore():
    """Create and print the highscores table"""
    print "Loading Highscores"
    # JOIN 3 SQL tables to get desired data
    stmt = text("""SELECT U.username, G.mystery, H.score, H.date
                        FROM highscores H
                        JOIN users U ON H.user_id = U.id
                        JOIN games G ON H.game_id = G.id
                        ORDER BY H.score""")
    rows = engine.execute(stmt).fetchall()

    return render_template("highscore.html", rows=rows)

@app.route("/game_id")
@login_required
def game_id():
    """Send the browser current game_id"""

    # use new_game method to start a new game
    # update the session variable "game_id"
    session["game_id"] = new_game(engine)
    print "Creating new game with game_id=", session['game_id']
    # return the game_id to the browser
    return json.dumps({"id": session["game_id"]})

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
        # check that username was provided
        if not request.form.get("username"):
            return apology("must provide username", 403)
        # check that password was provided twice
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password twice", 403)
        # check that both passwords match
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Add user to database
        id = datastore.__insert(engine, tables.USERS, {'username': request.form.get("username"), 'hash': generate_password_hash(request.form.get("password"))})
        print(id)
        if not id:
            return apology("username taken")

        session["user_id"] = id

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
    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        print request.form.get("username")
        # Query database for username
        stmt = text("SELECT * FROM users WHERE username = '%s'" % (request.form.get("username")))
        rows = engine.execute(stmt).fetchall()

        # ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # start a new game
        session["game_id"] = new_game(engine)
        print "Created new game with id=%i" % session['game_id']

        print "Logged in user %s" % (request.form.get('username'))
        # redirect user to game
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    """Allow user to change password"""

    if request.method == "POST":
        print "Changing password"
        # query for user's hash of password
        stmt = text("SELECT hash FROM users WHERE id = %d" % (session["user_id"]))
        rows = engine.execute(stmt).fetchone()

        # check all boxes filled, old password is correct, new and confirmation match
        if not request.form.get("old") or not check_password_hash(request.form.get("old"), rows["hash"]):
            return apology("incorrect password")
        elif not request.form.get("new") or not request.form.get("confirmation"):
            return apology("must type new password twice")
        elif not request.form.get("new") == request.form.get("confirmation"):
            return apology("new passwords must match")

        # update hash in database
        stmt = text("UPDATE users SET hash = %s WHERE id = %d" % (generate_password_hash(request.form.get("new")), session["user_id"]))
        engine.execute(stmt)

        # redirect to portfolio
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
