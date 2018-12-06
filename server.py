from flask import Flask, render_template
import cinemas
app = Flask(__name__)


@app.route('/')
def films_list():
    movies = cinemas.cached_top_10()
    return render_template(
        'films_list.html',
        movies=movies
    )


if __name__ == "__main__":
    app.run()
