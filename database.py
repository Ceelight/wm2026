import os
import bcrypt
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User

BASE_DIR = Path(__file__).parent
_default_db = f"sqlite:///{BASE_DIR}/wm2026.db"
DATABASE_URL = os.environ.get("DATABASE_URL", _default_db)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)
    admin_user = os.environ.get("ADMIN_USERNAME", "admin")
    admin_pass = os.environ.get("ADMIN_PASSWORD")
    if not admin_pass:
        return
    db = SessionLocal()
    try:
        if not db.query(User).filter_by(username=admin_user).first():
            pw = bcrypt.hashpw(admin_pass.encode(), bcrypt.gensalt()).decode()
            admin = User(username=admin_user, password_hash=pw, role="admin", language="de")
            db.add(admin)
            db.commit()
    finally:
        db.close()
