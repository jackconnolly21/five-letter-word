import csv
from datetime import datetime

import sqlalchemy
from sqlalchemy import text, update, func
from sqlalchemy.sql import and_, or_, select

from tables import USERS, GAMES, GUESSES, HIGHSCORES

def get_db_url_prod():
    return 'postgres://xosqkcwzlfunsx:598e2304c4d4dc3ce66a777a6baa6d6af9eb563cb92e928752aeb5f099a1d7b2@ec2-54-243-212-227.compute-1.amazonaws.com:5432/d7ei7va6mpl1id'

def get_db_engine(mode='prod'):
    if mode == 'prod':
        db_url = get_db_url_prod()
    else:
        db_url = 'sqlite:///project.db'
    return sqlalchemy.create_engine(db_url)

def __insert(db_engine, table, row_dict):
    return db_engine.execute(table.insert().returning(table.c.id), **row_dict).fetchone().id

# Get count of guesses for game_id
def get_number_guesses(engine, game_id):
    # stmt = text("SELECT COUNT * FROM guesses WHERE game_id = %d" % (game_id))
    # total_guesses = engine.execute(stmt).fetchone()["COUNT *"]
    stmt = select([func.count()]).select_from(GUESSES).where(GUESSES.c.game_id == game_id)
    total_guesses = engine.execute(stmt).fetchone()[0]
    print("Total guess:", total_guesses)
    return total_guesses
