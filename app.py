from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Hello from my Python app!</h1>
    <p>This app was created with VS Code.</p>
    """

if __name__ == "__main__":
    app.run(debug=True)
