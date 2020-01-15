import datetime

import enum
import sqlalchemy as sql
from sqlalchemy.schema import ForeignKey
from sqlalchemy.dialects import sqlite

metadata = sql.MetaData()

GAMES = sql.Table('games', metadata,
                  sql.Column('id', sql.Integer, primary_key=True),
                  sql.Column('mystery', sql.Text, nullable=False),
                  sql.Column('finished', sql.Boolean, nullable=False, default=False)
                  )

GUESSES = sql.Table('guesses', metadata,
                  sql.Column('id', sql.Integer, primary_key=True),
                  sql.Column('guess', sql.Text, nullable=False),
                  sql.Column('score', sql.Integer, nullable=False),
                  sql.Column('game_id', sql.Integer, ForeignKey(GAMES.c.id), nullable=False)
                  )

HIGHSCORES = sql.Table('highscores', metadata,
                sql.Column('id', sql.Integer, primary_key=True),
                sql.Column('name', sql.Text, nullable=False),
                sql.Column('game_id', sql.Integer, ForeignKey(GAMES.c.id), unique=True, nullable=False),
                sql.Column('score', sql.Integer, nullable=False),
                sql.Column('date', sql.DateTime, default=datetime.datetime.utcnow, nullable=False)
                )
