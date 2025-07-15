from .. import db
from sqlalchemy import Index

class URL(db.Model):
    __bind_key__ = 'blacklist_db'
    __tablename__ = 'url'
    id = db.Column(db.Integer, primary_key=True, index=True, autoincrement=True)  
    url = db.Column(db.Text, unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)
    date_added = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    source = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Boolean, default=True)       

Index('idx_url_category', URL.url, URL.category)