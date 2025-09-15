from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
from contextlib import contextmanager
from sqlalchemy.orm import declarative_base

Base = declarative_base()

load_dotenv()


class Database:
    _engine = None
    _SessionLocal = None

    @classmethod
    def initialize(cls):
        try:
            url = os.getenv("DATABASE_URL")
            cls._engine = create_engine(
                url,
                pool_size=20,          # Base connections
                max_overflow=30,       # Additional connections when needed
                pool_pre_ping=True,    # Validate connections before use
                pool_recycle=3600,     # Recycle connections every hour
                echo=False             # Set to True for debugging
            )
            cls._SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls._engine)
            return True
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False

    @classmethod
    @contextmanager
    def get_session(cls):
        if cls._SessionLocal is None:
            cls.initialize()
        db = cls._SessionLocal()
        try:
            yield db
        finally:
            db.close()