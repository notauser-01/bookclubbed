import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

DATABASE_URL = "postgres://posqgmzmkovfzl:c2adb2a5d8d48bc2e4b9d9a9faace2bc1ef1e6750d253c2b8e21db14d1e9d5fc@ec2-34-202-7-83.compute-1.amazonaws.com:5432/d55g4f5l27noee"
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))
#make the tables
db.execute("CREATE TABLE books( \
	key SERIAL PRIMARY KEY, \
	isbn VARCHAR NOT NULL, \
	title VARCHAR NOT NULL, \
	author VARCHAR NOT NULL, \
	year INTEGER NOT NULL)")
db.execute("CREATE TABLE users( \
	id SERIAL PRIMARY KEY, \
	name VARCHAR UNIQUE NOT NULL, \
	password VARCHAR NOT NULL, \
	user_id INTEGER)")
db.execute("CREATE TABLE reviews( \
	key SERIAL PRIMARY KEY, \
	book VARCHAR NOT NULL, \
	user_name VARCHAR NOT NULL, \
	content VARCHAR NOT NULL, \
	rating DECIMAL)")
#bingin the data
books = open("books.csv")
readm = csv.reader(books)
for isbn, title, author, year in readm:
	db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
db.commit()