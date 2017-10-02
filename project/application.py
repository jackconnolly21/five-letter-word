from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, jsonify
from flask_session import Session
from flask_jsglue import JSGlue
from passlib.apps import custom_app_context as pwd_context
from tempfile import gettempdir
from datetime import datetime

from helpers import *
from validator import *

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

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# instantiate an instance of the Validator class to check guesses
validator = Validator()

@app.route("/")
@login_required
def index():
    
    # just return index.html, the rest is done in JavaScript
    # this is where the main game is run (via games.js)
    return render_template("index.html")

@app.route("/guess")
@login_required
def guess():
    
    # check to make sure necessary parameters are passed in
    if not request.args.get("guess"):
        raise RuntimeError("missing guess")
    
    # set these equal to local variables to reference later
    # make guess lowercase in order to check against dictionary
    guess = request.args.get("guess").lower()
    game_id = session["game_id"]
    
    # get the mystery word from the SQL games table
    mystery = db.execute("SELECT mystery FROM games WHERE id = :game_id", game_id=game_id)
    # check to make sure a valid game_id was provided
    if len(mystery) == 0:
        raise RuntimeError("game does not exist")
    
    # set mystery equal to the actual word
    mystery = mystery[0]["mystery"]
    
    # use the validator instance to check whether the guess is in the dictionary
    if not validator.validate(guess):
        # score of -1 indicates an invalid word for the JavaScript
        return jsonify({"score": -1})
    
    # helper function to find number of letters in common
    score = common_letters(guess, mystery)
    
    # record this guess in the SQL table guesses    
    db.execute("""INSERT INTO guesses (guess, score, game_id) 
                  VALUES (:guess, :score, :game_id)""", 
                  guess=guess, score=score, 
                  game_id=game_id)
    
    # check if winner
    # if so, find the total_guesses it took and insert into highscores table
    if guess == mystery:
            total_guesses = db.execute("SELECT COUNT (*) FROM guesses WHERE game_id = :game_id", game_id=game_id)[0]["COUNT (*)"]
            db.execute("""INSERT INTO highscores (user_id, score, game_id) 
                          VALUES (:user_id, :score, :game_id)""", 
                          user_id=session["user_id"], score=total_guesses, 
                          game_id=game_id)
            # send the JavaScript a score of 6 to indicate winning
            score = 6
    
    return jsonify({"score": score})

@app.route("/table")
@login_required
def table():
    """Return all guesses for current game"""
    
    # select all guess belonging to current game_id
    guesses = db.execute("SELECT * FROM guesses WHERE game_id = :game_id ORDER BY id", game_id=session["game_id"])
    
    return jsonify(guesses)

@app.route("/highscore")
@login_required
def highscore():
    """Create and print the highscores table"""
    
    # JOIN 3 SQL tables to get desired data
    rows = db.execute("""SELECT U.username, G.mystery, H.score, H.date
                        FROM [highscores] H
                        JOIN users U ON H.user_id = U.id
                        JOIN games G ON H.game_id = G.id
                        ORDER BY H.score""")
    
    return render_template("highscore.html", rows=rows)
    
@app.route("/game_id")
@login_required
def game_id():
    """Send the browser current game_id"""
    
    # use new_game method to start a new game
    # update the session variable "game_id"
    session["game_id"] = new_game()
    
    # return the game_id to the browser
    return jsonify({"id": session["game_id"]})
    
@app.route("/rules")
@login_required
def rules():
    """Create the Rules Page"""
    
    return render_template("rules.html")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""
    
    session.clear()
    
    if request.method == "POST":
        
        # check that username was provided
        if not request.form.get("username"):
            return apology("must provide username")
        # check that password was provided twice
        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("must provide password twice")
        # check that both passwords match    
        elif not request.form.get("password") == request.form.get("confirmation"):
            return apology("passwords must match")
        
        # query database to check if username is taken    
        rows = db.execute("SELECT * FROM users WHERE username = :username", 
                           username=request.form.get("username"))
        if len(rows) != 0:
            return apology("username already taken :(")
        # if not, add user to users table, hash password    
        db.execute("INSERT INTO users (username, hash) VALUES(:username, :hashh)", 
                    username=request.form["username"], 
                    hashh=pwd_context.encrypt(request.form["password"]))
                    
        session["user_id"] = (db.execute("SELECT id FROM users where username = :username", 
                              username=request.form["username"]))[0]["id"]
        # start a new game for the user when registered
        session["game_id"] = new_game()
        
        # redirect to portfolio  
        flash("You are registered!")
        return redirect(url_for("index"))
    
    else:
        return render_template("register.html")

@app.route("/logout")
def logout():
    """Log user out."""

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
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]
        
        # start a new game       
        session["game_id"] = new_game()
        
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
        
        # query for user's hash of password
        rows = db.execute("SELECT hash FROM users WHERE id = :idd", 
                           idd=session["user_id"])
        
        # check all boxes filled, old password is correct, new and confirmation match
        if not request.form.get("old") or not pwd_context.verify(request.form.get("old"), rows[0]["hash"]):
            return apology("incorrect password")
        elif not request.form.get("new") or not request.form.get("confirmation"):
            return apology("must type new password twice")
        elif not request.form.get("new") == request.form.get("confirmation"):
            return apology("new passwords must match")
        
        # update hash in database    
        db.execute("UPDATE users SET hash = :hashh WHERE id = :idd", 
                    hashh=pwd_context.encrypt(request.form.get("new")), 
                    idd=session["user_id"])
        
        # redirect to portfolio
        flash("Password changed!")
        return redirect(url_for("index"))
        
    else:
        return render_template("password.html")
