from pgvector.sqlalchemy import Vector
import uuid

from app.extensions import db

class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False, index=True, unique=True)
    description = db.Column(db.Text, nullable=True) # Generated by AI
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(500), nullable=True)
    
    # Embedding vector (1536 dimensions for OpenAI's model)
    embedding = db.Column(Vector(1536), nullable=True)

    def __repr__(self):
        return f"<Product {self.name} (${self.price})>"