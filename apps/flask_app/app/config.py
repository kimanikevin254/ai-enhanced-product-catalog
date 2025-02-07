import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_USERNAME = os.getenv("DB_USERNAME", "username")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_DATABASE = os.getenv("DB_DATABASE", "redpanda_article")

    SQLALCHEMY_DATABASE_URI = f"postgresql://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_DATABASE}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False