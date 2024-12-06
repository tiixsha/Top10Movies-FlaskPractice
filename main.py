from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms.validators import InputRequired, Length, ValidationError
from wtforms import StringField, SubmitField, IntegerField
from wtforms.form import BaseForm
from wtforms.validators import DataRequired
import requests

MOVIE_DB_API_KEY = "NOT_A_REAL_KEY"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

app = Flask(__name__)
app.config['SECRET_KEY'] = '1234'
Bootstrap5(app)

class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)

class UpdateForm(FlaskForm):
    rating = StringField(validators=[
        InputRequired(), Length(min=1, max=4)], render_kw={"placeholder": "Rating"})
    review = StringField(validators=[
        InputRequired(), Length(min=1, max=50)], render_kw={"placeholder": "Review"})

    submit = SubmitField('Update')

class AddForm(FlaskForm):
    title = StringField(validators = [InputRequired()],render_kw = {"placeholder":"Title"})
    submit = SubmitField('Add')


class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

# new_movie = Movie(
#     title="Phone Booth",
#     year=2002,
#     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
#     rating=7.3,
#     ranking=10,
#     review="My favourite character was the caller.",
#     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
# )
# second_movie = Movie(
#         title="Avatar The Way of Water",
#         year=2022,
#         description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#         rating=7.3,
#         ranking=9,
#         review="I liked the water.",
#         img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
#     )
#
# with app.app_context():
#     db.session.add( second_movie )
#     db.session.commit()


@app.route('/')
def home():\
    # .select selects all the entries from the database and .execute fetches the data from the database
    result = db.session.execute(db.select(Movie))
    #.scalars(): This method is used to extract scalar values from the result. In SQLAlchemy,
    # a scalar refers to individual elements (usually rows or specific columns) in a query result,
    # rather than complex row-like objects or tuples.
    all_movies = result.scalars().all()
    movies = Movie.query.filter_by(id=all_movies.id).order_by(Movie.rating.dsc()).all
    for i in range(len(movies)):
        movies[i].ranking = len(movies) - i
    db.session.commit()

    return render_template('index.html', movies=movies)


@app.route('/update',methods = ['GET','POST'])
def update():
    form = UpdateForm()
    movie_id = request.args.get("movie_id") #gets the movie id from url sent from index.html
    movie = db.get_or_404(Movie,movie_id) # gets the data from database that matches the movie id or gives 404  error
    if form.validate_on_submit():
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie = movie, form = form)

@app.route('/delete/<int:movie_id>', methods = ['GET','POST'])
def delete(movie_id):
    movie_delete = Movie.query.filter_by(id = movie_id).first()
    db.session.delete(movie_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/add', methods = ['GET','POST'])
def add():
    form = AddForm()
    if form.validate_on_submit():
        if form.validate_on_submit():
            movie_title = form.title.data
            response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
            data = response.json()["results"]
            return render_template("select.html", options=data)
    return render_template('add.html',form = form)

@app.route('find')
def find():
    movie_api_id = request.args.get("id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = Movie(
            title=data["title"],
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]
        )
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for("edit", id = new_movie.id))


if __name__ == '__main__':
    app.run(debug=True)