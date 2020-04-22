import os, requests, random, string

from flask import * 
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

DATABASE_URL = "postgres://posqgmzmkovfzl:c2adb2a5d8d48bc2e4b9d9a9faace2bc1ef1e6750d253c2b8e21db14d1e9d5fc@ec2-34-202-7-83.compute-1.amazonaws.com:5432/d55g4f5l27noee"
engine = create_engine(DATABASE_URL)
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():
	db.execute("UPDATE users SET user_id = NULL")
	db.commit()
	return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/login")
def login():
    return render_template("login.html")

#needs to check name and password from register agains existing
@app.route("/welcome", methods=["GET", "POST"])
def welcome():
	#check request method
	if request.method == "GET":
		message = "You fucked up the request method."
		return render_template("fuckup0.html", message=message)
	#get name and password
	name = request.form.get("name")
	pw = request.form.get("pw")
	#no blank name or password
	if name == "" or pw =="":
		message = "What did you forget?"
		return render_template("fuckup0.html", message=message)
	#username exists?
	check = db.execute("SELECT * FROM users WHERE name = :name", \
				{"name": name}).fetchone()
	#new user:
	if check is None:
		db.execute("INSERT INTO users (name, password) VALUES (:name, :pw)", {"name": name, "pw": pw})
		db.commit()
		check = db.execute("SELECT * FROM users WHERE name = :name AND password = :pw", \
				{"name": name, "pw": pw}).fetchone()
		return render_template("welcome.html", name=check[1], pw=check[2])
	#existing user, wrong password
	if pw != check[2]:
		message = "You fucked up and got the wrong password."
		return render_template("fuckup0.html", message=message)
	#existing user, did it right
	else:
		user_id = random.randint(10**8, 10**9 - 1)	
		db.execute("UPDATE users SET user_id = :user_id WHERE name = :name", \
				{"user_id": user_id, "name": name})
		db.commit()
		return redirect(url_for('dashboard', user_id=user_id))

@app.route("/dashboard/<int:user_id>", methods=["GET", "POST"])
def dashboard(user_id):
	user = db.execute("SELECT * FROM users WHERE user_id = :user_id", \
				{"user_id": user_id}).fetchone()
	name = user[1]
	return render_template("dashboard.html", name=name, user_id=user_id)

@app.route("/searched/<int:user_id>", methods=["GET","POST"])
def searched(user_id):
	search = request.form.get('search')
	query = [search, \
			"%" + string.capwords(search, sep=None) + "%", \
			"%" + search + "%"]
	results = []
	for i in query:
		find = db.execute("SELECT * FROM books WHERE author LIKE :string OR title LIKE :string OR isbn LIKE :string", \
				{"string": i}).fetchall()
		for match in find:
			if match not in results:
				results.append(match)
	result_count = len(results)
	book = ""
	return render_template("results.html", result_count=result_count, results=results, user_id=user_id, book=book)

@app.route("/book/<int:user_id>/<string:book>", methods=["GET", "POST"])
def book(user_id, book):
	user_name = db.execute("SELECT name FROM users WHERE user_id = :user_id", \
			{"user_id": user_id}).fetchone()[0]
	check = db.execute("SELECT content FROM reviews JOIN users ON users.name = reviews.user_name WHERE user_id = :user_id AND book = :book", \
			{"user_id": user_id, "book": book}).fetchone()
	#user generated content
	content = request.form.get("review")
	rating = request.form.get("rating")

	#NO REVIEW SAME BOOK TWICE!
	if request.method == "POST" and check != None:
		message = "You fucked up: no user can review the same book twice."
		return render_template("fuckup1.html", message=message, user_id=user_id)
	#MUST RATE NO BLANK!
	if content == "" or rating == None and request.method == "POST":
		message = "What did you forget?"
		return render_template("fuckup1.html", message=message, user_id=user_id)
	#post a review
	if request.method == "POST" and check == None:
		db.execute("INSERT INTO reviews (book, user_name, content, rating) VALUES (:book, :user_name, :content, :rating)", \
			{"book": book, "user_name": user_name, "content": content, "rating": rating})
		db.commit()

	reviews = db.execute("SELECT * FROM reviews WHERE book = :book ORDER BY key DESC", \
			{"book": book}).fetchall()
	count = len(reviews)
	info = db.execute("SELECT * FROM books WHERE title = :book", \
			{"book": book}).fetchone()

	#Compute overall rating:
	if db.execute("SELECT AVG(rating) FROM reviews WHERE book = :book", \
			{"book": book}).scalar() != None:
		overall_rating = round(db.execute("SELECT AVG(rating) FROM reviews WHERE book = :book", \
			{"book": book}).scalar(), 1)
	else:
		overall_rating = 0
	
	#get the goodshits:
	isbn = info[1]
	shit = requests.get("https://www.goodreads.com/book/review_counts.json", \
				params={"key": "dROvCNBfL6KL3pVQ2NUzEg", "isbns": isbn})
	#don't let .json() break your app
	if "404" in shit.headers["Status"]:
		nogo = True
		stuff = ""
	else:
		nogo = False
		stuff = shit.json()

	return render_template("book.html", stuff=stuff, nogo=nogo, check=check, reviews=reviews, info=info, count=count, rating=rating, user_id=user_id, book=book, overall_rating=overall_rating)

@app.route("/api/<string:isbn>")
def api(isbn):
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", 
			{"isbn": isbn}).fetchone()
	#make sure the isbn is in the database (required 404 fuckup)
	if book is None:
		return jsonify({"404 Fuckup": "Book Not Found"}), 404
	
	book = db.execute("SELECT * FROM books WHERE isbn = :isbn", 
			{"isbn": isbn}).fetchone()
	rating = db.execute("SELECT AVG(rating) FROM reviews WHERE book = :book", \
			{"book": book.title}).scalar()
	review_count = db.execute("SELECT COUNT(*) FROM reviews WHERE book = :book", \
			{"book": book.title}).scalar()
	title, author, year, isbn = (book.title, book.author, book.year, book.isbn)
	
	if rating != None:
		rating = str(round(rating, 1))

	return jsonify({
			"title": title,
			"author": author,
			"year": year,
			"isbn": isbn,
			"review_count": review_count,
			"average_score": rating
		})