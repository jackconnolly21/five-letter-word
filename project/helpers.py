import csv
from datetime import datetime
from sqlalchemy import and_, text, select
import sqlalchemy
import tables

from flask import redirect, render_template, request, session, url_for
from functools import wraps
from validator import *

# configure sqlalchemy Library to use SQLite database
engine = sqlalchemy.create_engine("sqlite:///project.db")

# instantiate validator object with the dictionary of possible mystery words
validator = Validator("dicts/mystery.txt")

def apology(message, code=400):
    """Renders message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.11/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login", next=url_for("index")))
        return f(*args, **kwargs)
    return decorated_function

def common_letters(word, mystery):
    """Returns the how many letters two words have in common"""

    # if the two words are different lengths, its invalid - return None
    if len(word) != len(mystery):
        return None

    # make both words into a set in order to use set operations
    w = set(word)
    m = set(mystery)

    # the '&' operator returns the intersection of w and m
    if w & m is None:
        return 0

    # the length of this set is how many letters the words have in common
    return len(w & m)

def new_game():
    """Starts a new game for the user"""

    # Use the validator class to randomly get a new mystery word
    mystery = validator.get_mystery()

    # record this new game in the SQL table "games"
    # return the id of the last inserted row (in order to set the session variable in application)
    return sql_insert(engine, tables.GAMES, {'mystery': mystery, 'user_id': session['user_id']})

def get_db_url_prod():
    return 'postgres://xosqkcwzlfunsx:598e2304c4d4dc3ce66a777a6baa6d6af9eb563cb92e928752aeb5f099a1d7b2@ec2-54-243-212-227.compute-1.amazonaws.com:5432/d7ei7va6mpl1id'

def get_db_engine(mode='prod'):
    if mode == 'prod':
        db_url = get_db_url_prod()
    else:
        db_url = 'sqlite:///project.db'
    return sqlalchemy.create_engine(db_url)

def sql_insert(db_engine, table, row_dict):
    return db_engine.execute(table.insert(), **row_dict).lastrowid
