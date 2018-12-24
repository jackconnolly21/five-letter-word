import csv
from datetime import datetime

import sqlalchemy
from sqlalchemy import text, update, func
from sqlalchemy.sql import and_, or_, select

from tables import USERS, GAMES, GUESSES, HIGHSCORES

# General Engine Creation
def get_db_url_prod():
    return 'postgres://xosqkcwzlfunsx:598e2304c4d4dc3ce66a777a6baa6d6af9eb563cb92e928752aeb5f099a1d7b2@ec2-54-243-212-227.compute-1.amazonaws.com:5432/d7ei7va6mpl1id'

def get_db_engine(mode='prod'):
    if mode == 'prod':
        db_url = get_db_url_prod()
    else:
        db_url = 'sqlite:///project.db'
    return sqlalchemy.create_engine(db_url)

# Insertion
def __insert(db_engine, table, row_dict):
    return db_engine.execute(table.insert().returning(table.c.id), **row_dict).fetchone().id

# USERS
def insert_user(db_engine, row_dict):
    return __insert(db_engine, USERS, row_dict)

def get_user_by_username(db_engine, username):
    stmt = USERS.select().where(USERS.c.username == username)
    return db_engine.execute(stmt).fetchall()

def get_user_by_user_id(db_engine, user_id):
    stmt = USERS.select().where(USERS.c.id == user_id)
    return db_engine.execute(stmt).fetchone()

def update_password_hash(db_engine, user_id, pw_hash):
    stmt = USERS.update()
    stmt = stmt.where(USERS.c.id == user_id)
    stmt = stmt.values({'hash': pw_hash})
    return db_engine.execute(stmt)

# GAMES
def insert_game(db_engine, row_dict):
    return __insert(db_engine, GAMES, row_dict)

def get_game_info(db_engine, game_id):
    stmt = GAMES.select()
    stmt = stmt.where(GAMES.c.id == game_id)
    return db_engine.execute(stmt).fetchone()

def update_game_finished(db_engine, game_id):
    stmt = GAMES.update()
    stmt = stmt.where(GAMES.c.id == game_id)
    stmt = stmt.values({'finished': True})
    return db_engine.execute(stmt)

# GUESSES
def insert_guess(db_engine, row_dict):
    return __insert(db_engine, GUESSES, row_dict)

def get_number_guesses(engine, game_id):
    stmt = select([func.count()]).select_from(GUESSES).where(GUESSES.c.game_id == game_id)
    return engine.execute(stmt).fetchone()[0]

def get_guesses_by_game_id(db_engine, game_id):
    stmt = GUESSES.select()
    stmt = stmt.where(GUESSES.c.game_id == game_id)
    stmt = stmt.order_by(GUESSES.c.id)
    return db_engine.execute(stmt).fetchall()

# HIGHSCORES
def insert_highscore(db_engine, row_dict):
    return __insert(db_engine, HIGHSCORES, row_dict)

def get_all_highscores(db_engine):
    j = HIGHSCORES.join(GAMES)
    stmt = select([HIGHSCORES.c.name, GAMES.c.mystery, HIGHSCORES.c.score, HIGHSCORES.c.date])
    stmt = stmt.where(HIGHSCORES.c.game_id == GAMES.c.id)
    stmt = stmt.order_by(HIGHSCORES.c.score)
    stmt = stmt.select_from(j)
    return db_engine.execute(stmt).fetchall()
