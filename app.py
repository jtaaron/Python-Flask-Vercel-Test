from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return "Hello from Flask on Vercel!"


if __name__ == "__main__":
    # Local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)



