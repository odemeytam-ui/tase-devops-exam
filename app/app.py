from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Fetch database configuration from environment variables
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "secret")
DB_HOST = os.getenv("POSTGRES_HOST", "db")
DB_NAME = os.getenv("POSTGRES_DB", "flask_db")

app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define a simple counter model
class HitCounter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0, nullable=False)

# Ensure database tables exist
with app.app_context():
    db.create_all()
    # Initialize the counter row if empty
    if not HitCounter.query.first():
        db.session.add(HitCounter(id=1, count=0))
        db.session.commit()

@app.route('/')
def hello():
    try:
        # Atomic increment inside a transaction block
        counter = db.session.with_for_update().get(HitCounter, 1)
        counter.count += 1
        db.session.commit()
        hits = counter.count
    except Exception as e:
        db.session.rollback()
        hits = "Database currently unavailable"

    return f'''
    <!DOCTYPE html>
    <html>
    <head><title>Hello World</title></head>
    <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
        <h1>Hello World!</h1>
        <p>This page has been viewed <strong>{hits}</strong> times.</p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)