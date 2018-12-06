from flask import Flask, render_template
from werkzeug.contrib.fixers import ProxyFix
import cinemas
app = Flask(__name__)


@app.route('/')
def films_list():
    movies = cinemas.cached_top_10()
    return render_template(
        'films_list.html',
        movies=movies
    )


app.wsgi_app = ProxyFix(app.wsgi_app)
if __name__ == "__main__":
    app.run()
