from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_jsglue import JSGlue
from werkzeug.security import check_password_hash, generate_password_hash
from tempfile import gettempdir
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

app.jinja_env.filters["dte"] = convert_time

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
def index():
    print "Loading Home"
    if not session.get('game_id'):
        session["game_id"] = new_game(engine)
        print "Creating new game with game_id =", session["game_id"]

    # Just return index.html, the rest is done in JavaScript (via game.js)
    return render_template("index.html")


@app.route("/guess")
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
        datastore.update_game_finished(engine, game_id)
        # Send the JavaScript a score of 6 to indicate winning
        score = 6
        print "Ending Game...Winner!"

    return json.dumps({"score": score})


@app.route("/table")
def table():
    """Return all guesses for current game"""
    print "Loading table for game_id=%i" % session["game_id"]

    # Select all guess belonging to current game_id
    guesses = datastore.get_guesses_by_game_id(engine, session["game_id"])
    guesses = [dict(g) for g in guesses]

    return json.dumps(guesses)


@app.route("/highscore", methods=["GET", "POST"])
def highscore():
    """Create and print the highscores table"""
    if request.method == "POST":
        if not request.form.get('hs_name'):
            name = "Guest"
        else:
            name = request.form.get('hs_name')

        total_guesses = datastore.get_number_guesses(engine, session["game_id"])
        highscore_dict = {
            'name': name,
            'score': total_guesses,
            'game_id': session['game_id']
        }
        datastore.insert_highscore(engine, highscore_dict)

        return redirect(url_for('highscore'))
    else:
        print "Loading Highscores"

        rows = datastore.get_all_highscores(engine)

        return render_template("highscore.html", rows=rows)


@app.route("/game_id")
def game_id():
    """Send the browser current game_id"""

    # Use new_game method to start a new game
    session.clear()
    session["game_id"] = new_game(engine)
    print "Creating new game with game_id =", session["game_id"]

    # Redirect to home page
    return redirect(url_for("index"))


@app.route("/rules")
def rules():
    """Create the Rules Page"""
    print "Loading Rules"
    return render_template("rules.html")


if __name__ == "__main__":
    app.run()
