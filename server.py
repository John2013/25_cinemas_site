from flask import Flask, render_template
from werkzeug.contrib.fixers import ProxyFix
import cinemas
import gevent.monkey
app = Flask(__name__)


gevent.monkey.patch_all()


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
