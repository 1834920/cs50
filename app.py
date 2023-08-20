import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

# from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Custom filter
# app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///movies.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/addfavorites", methods=["GET", "POST"])
def addfavorites():
    if request.method == "POST":
        underappreciated_type = request.form.get("type")
        name = request.form.get("name").title()
        description = request.form.get("description")

        if underappreciated_type == "person":
            # Insert data into the favorite_persons table
            db.execute("INSERT INTO favorite_persons (person_name, description) VALUES (?, ?)",
                       name, description)
        elif underappreciated_type == "movie":
            # Insert data into the favorite_movies table
            db.execute("INSERT INTO favorite_movies (movie_title, description) VALUES (?, ?)",
                       name, description)

        # Redirect to the list page after processing
        return redirect("/list")

    return render_template("addfavorites.html")

@app.route("/list")
def list():
    # Retrieve data from favorite_persons and favorite_movies tables
    persons = db.execute("SELECT * FROM favorite_persons")
    movies = db.execute("SELECT * FROM favorite_movies")

    # Create a list to store combined data for persons and movies
    combined_data = []

    # Loop through the movies to get their details and ratings
    for movie in movies:
        # Get the movie's ID based on the title
        movie_id = db.execute("SELECT id FROM movies WHERE LOWER(title) = LOWER(?)", movie['movie_title'])
        if movie_id:
            rating_data = db.execute("SELECT rating FROM ratings WHERE movie_id = ?", movie_id[0]['id'])
            rating = rating_data[0]['rating'] if rating_data else None
            combined_data.append({
                "item_type": "movie",
                "name": movie['movie_title'],
                "rating": rating,
                "description": movie['description']
            })

    # Loop through the persons and add them to the combined data
    for person in persons:
        # Get the person's ID based on the name
        person_id = db.execute("SELECT id FROM people WHERE LOWER(name) = LOWER(?)", person['person_name'])
        print("Person_id", person_id)
        if person_id:
            # Use the retrieved person ID to get the movies associated with the person
            print("Before movie_ids query")
            movie_ids = db.execute("SELECT movie_id FROM stars WHERE person_id = ?", person_id[0]['id'])
            print("After movie_ids query")
            # List to store the ratings for movies associated with the person
            ratings_for_person = {}

            # Loop through the movie IDs to get the ratings
            for movie_id in movie_ids:
                rating_data = db.execute("SELECT rating FROM ratings WHERE movie_id = ?", movie_id['movie_id'])
                if rating_data:
                    ratings_for_person[movie_id['movie_id']] = rating_data[0]['rating']

            # Find the movie ID with the highest rating
            highest_rated_movie_id = max(ratings_for_person, key=ratings_for_person.get, default=None)

            # Get the title and rating of the highest-rated movie for the person
            highest_rated_movie = db.execute("SELECT title FROM movies WHERE id = ?", highest_rated_movie_id)
            highest_rated_movie_title = highest_rated_movie[0]['title'] if highest_rated_movie else None
            highest_rated_movie_rating = ratings_for_person.get(highest_rated_movie_id, None)

            combined_data.append({
                "item_type": "person",
                "name": person['person_name'],
                "rating": highest_rated_movie_rating,
                "description": person['description'],
                "highest_rated_movie_title": highest_rated_movie_title
            })

    return render_template("list.html", combined_data=combined_data)
