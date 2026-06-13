from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    role = Column(String(16), nullable=False, default="player")  # admin | player
    language = Column(String(4), nullable=False, default="de")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    tips = relationship("Tip", back_populates="user")


class Match(Base):
    __tablename__ = "matches"
    id = Column(Integer, primary_key=True)
    match_number = Column(Integer, unique=True, nullable=False)
    api_id = Column(Integer, unique=True)           # football-data.org match ID
    round = Column(String(32), nullable=False)      # "Gruppe A" | "Achtelfinale" | ...
    team1 = Column(String(64), nullable=False)
    team2 = Column(String(64), nullable=False)
    venue = Column(String(128))
    city = Column(String(64))
    kickoff_utc = Column(DateTime, nullable=False)
    score1 = Column(Integer)  # None = not played yet
    score2 = Column(Integer)
    status = Column(String(16), default="scheduled")  # scheduled | live | finished
    tips_open = Column(Boolean, default=False)  # Admin-Override: Nachtragen erlauben
    tips = relationship("Tip", back_populates="match")


class Tip(Base):
    __tablename__ = "tips"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    tip_score1 = Column(Integer)
    tip_score2 = Column(Integer)
    points = Column(Integer, default=0)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    user = relationship("User", back_populates="tips")
    match = relationship("Match", back_populates="tips")


class Setting(Base):
    __tablename__ = "settings"
    key = Column(String(64), primary_key=True)
    value = Column(String(512), nullable=False, default="")
