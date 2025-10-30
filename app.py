import os
from flask import Flask, render_template, request, redirect, url_for, session
import uuid

def ensure_secret_key(app: Flask) -> None:
    # Prefer environment variable; fall back to a dev-safe default
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

app = Flask(__name__)
ensure_secret_key(app)


def get_todos():
    return session.setdefault("todos", [])


@app.route("/", methods=["GET"])
def index():
    todos = get_todos()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    if title:
        todos = get_todos()
        todos.append({
            "id": str(uuid.uuid4()),
            "title": title,
            "done": False,
        })
        session.modified = True
    return redirect(url_for("index"))


@app.route("/toggle/<todo_id>", methods=["POST"])
def toggle(todo_id: str):
    todos = get_todos()
    for item in todos:
        if item["id"] == todo_id:
            item["done"] = not item["done"]
            session.modified = True
            break
    return redirect(url_for("index"))


@app.route("/delete/<todo_id>", methods=["POST"])
def delete(todo_id: str):
    todos = get_todos()
    session["todos"] = [t for t in todos if t["id"] != todo_id]
    session.modified = True
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)



