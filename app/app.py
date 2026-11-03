import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import URL, text, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# Read database configuration from environment variables.
# The password is required; there is no hardcoded fallback.
db_password = os.getenv("POSTGRES_PASSWORD")

if not db_password:
    raise RuntimeError("POSTGRES_PASSWORD environment variable is required")

database_url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("POSTGRES_USER", "postgres"),
    password=db_password,
    host=os.getenv("POSTGRES_HOST", "db"),
    port=int(os.getenv("POSTGRES_PORT", "5432")),
    database=os.getenv("POSTGRES_DB", "flask_db"),
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

db = SQLAlchemy(app)


# Database model
class HitCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=0)


# Create the table and initialize the counter if it doesn't exist.
def initialize_database():
    with app.app_context():
        db.create_all()

        # Prevent duplicate counter rows if multiple workers start together.
        statement = (
            insert(HitCounter)
            .values(id=1, count=0)
            .on_conflict_do_nothing(index_elements=[HitCounter.id])
        )

        db.session.execute(statement)
        db.session.commit()


initialize_database()


# Health endpoint used by Docker to check the application and database.
@app.route("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok"}, 200

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Database health check failed")
        return {"status": "database_unavailable"}, 503


# Main application page.
@app.route("/")
def hello():
    try:
        # Increment the counter atomically in the database.
        statement = (
            update(HitCounter)
            .where(HitCounter.id == 1)
            .values(count=HitCounter.count + 1)
            .returning(HitCounter.count)
        )

        hits = db.session.execute(statement).scalar_one()
        db.session.commit()

    except SQLAlchemyError:
        db.session.rollback()
        app.logger.exception("Could not update page counter")
        return "<h1>Database currently unavailable</h1>", 503

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hello World</title>
    </head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
        <h1>Hello World!</h1>
        <p>This page has been viewed <strong>{hits}</strong> times.</p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)