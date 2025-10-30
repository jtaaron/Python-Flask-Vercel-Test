import os
from flask import Flask, render_template, request, redirect, url_for
from datetime import datetime
from sqlalchemy import create_engine, String, Boolean, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session, DeclarativeBase, Mapped, mapped_column
from sqlalchemy.pool import NullPool

def ensure_secret_key(app: Flask) -> None:
    # Prefer environment variable; fall back to a dev-safe default
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

app = Flask(__name__)
ensure_secret_key(app)

# --- Database setup ---

class Base(DeclarativeBase):
    pass


class Todo(Base):
    __tablename__ = "todos"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if url:
        # Allow DATABASE_URL formats that may start with postgres://
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and "+psycopg" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url
    # Local development fallback (not used on Vercel)
    return "sqlite:///local.db"


DATABASE_URL = get_database_url()

engine_kwargs = {}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # serverless-friendly
    future=True,
    **engine_kwargs,
)

SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, expire_on_commit=False))


@app.before_request
def _ensure_tables():
    # Create tables on first request (idempotent). In production, use migrations.
    Base.metadata.create_all(bind=engine)

@app.teardown_appcontext
def shutdown_session(exception=None):
    SessionLocal.remove()


@app.route("/", methods=["GET"])
def index():
    db = SessionLocal()
    todos = db.query(Todo).order_by(Todo.created_at.desc()).all()
    return render_template("index.html", todos=todos)


@app.route("/add", methods=["POST"])
def add():
    from uuid import uuid4
    title = request.form.get("title", "").strip()
    if title:
        db = SessionLocal()
        db.add(Todo(id=str(uuid4()), title=title, done=False))
        db.commit()
    return redirect(url_for("index"))


@app.route("/toggle/<todo_id>", methods=["POST"])
def toggle(todo_id: str):
    db = SessionLocal()
    todo = db.get(Todo, todo_id)
    if todo:
        todo.done = not todo.done
        db.commit()
    return redirect(url_for("index"))


@app.route("/delete/<todo_id>", methods=["POST"])
def delete(todo_id: str):
    db = SessionLocal()
    todo = db.get(Todo, todo_id)
    if todo:
        db.delete(todo)
        db.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    # Local dev server
    app.run(host="127.0.0.1", port=5000, debug=True)



