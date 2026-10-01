from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return """
    <h1>Hello from my Python app!</h1>
    <p>This app was created with VS Code.</p>
    <a href="/about">About</a>
    """


@app.route("/about")
def about():
    return """
    <h1>About This App</h1>
    <p>This is my first Flask application.</p>
    <a href="/">Home</a>
    """


if __name__ == "__main__":
    app.run(debug=True)
