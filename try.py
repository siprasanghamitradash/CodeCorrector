from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>Hello! This is my first and Flask website.</h1>"

if __name__ == "__main__":
    app.run(debug=True)
