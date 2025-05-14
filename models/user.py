from db import db
from sqlalchemy.sql import func


class UserModel(db.Model):
    """Represents a User object"""

    __tablename__ = "users"
    # __table_args__ = {"schema": ""}

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    name = db.Column(db.String)
    surname = db.Column(db.String)
    status = db.Column(db.Boolean)
    mailings = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime(timezone=True), onupdate=func.now())
    role = db.Column(db.String, default="Company User")
    display_name = db.Column(db.String, default="")
