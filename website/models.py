from flask_login import UserMixin
from datetime import datetime
from . import db  # Import db from the package, don't redefine it here

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))

class UserInteraction(db.Model):
    __tablename__ = 'user_interactions'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))
    country = db.Column(db.String(100))
    user_id = db.Column(db.String(100))
    product_name = db.Column(db.String(100))
    demo_requested = db.Column(db.Boolean, default=False)
    promo_event_interested = db.Column(db.Boolean, default=False)
    ai_assistant_used = db.Column(db.Boolean, default=False)
    duration_on_site = db.Column(db.Float)
    pages_visited = db.Column(db.Integer)
    conversion = db.Column(db.Boolean, default=False)
    revenue_generated = db.Column(db.Float, default=0.0)
    user_device = db.Column(db.String(50))
    browser = db.Column(db.String(50))
    cost_incurred = db.Column(db.Float, default=0.0)
    num_jobs_placed = db.Column(db.Integer, default=0)
    job_type = db.Column(db.String(100), nullable=True)