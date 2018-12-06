from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def films_list():
    return render_template('films_list.html')


if __name__ == "__main__":
    app.run()
