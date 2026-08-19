from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    job_matches = relationship("JobMatch", back_populates="user", cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=True)
    headline = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="profile")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("user_id", "safe_filename", name="uq_document_user_safe_filename"),
        {"extend_existing": True},
    )

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    safe_filename = Column(String(255), nullable=False)
    document_type = Column(String(64), default="other", nullable=False)
    pages = Column(Integer, default=0, nullable=False)
    chunks = Column(Integer, default=0, nullable=False)
    status = Column(String(32), default="indexed", nullable=False)
    document_metadata = Column("metadata", JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="documents")
    chat_sessions = relationship("ChatSession", back_populates="document")
    resume_matches = relationship("JobMatch", foreign_keys="JobMatch.resume_document_id", back_populates="resume_document")
    job_matches = relationship("JobMatch", foreign_keys="JobMatch.job_document_id", back_populates="job_document")


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), default="New conversation", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    document_id = Column(String, ForeignKey("documents.id"), nullable=True, index=True)
    document = relationship("Document", back_populates="chat_sessions")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    session = relationship("ChatSession", back_populates="messages")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    job_document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    interview_type = Column(String(64), default="mixed", nullable=False)
    difficulty = Column(String(32), default="medium", nullable=False)
    question_count = Column(Integer, default=10, nullable=False)
    status = Column(String(32), default="started", nullable=False)
    current_question_id = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")
    answers = relationship("InterviewAnswer", back_populates="session", cascade="all, delete-orphan")
    evaluations = relationship("InterviewEvaluation", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(String, nullable=False)
    prompt = Column(Text, nullable=False)
    category = Column(String(64), default="Mixed")
    skill = Column(String(128), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    session = relationship("InterviewSession", back_populates="questions")


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(String, nullable=False, index=True)
    answer = Column(Text, nullable=False)
    score = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    session = relationship("InterviewSession", back_populates="answers")


class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("interview_sessions.id"), nullable=False, index=True)
    question_id = Column(String, nullable=False, index=True)
    overall_score = Column(Integer, default=0, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    session = relationship("InterviewSession", back_populates="evaluations")


class JobMatch(Base):
    __tablename__ = "job_matches"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    resume_document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    job_document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    match_percentage = Column(Integer, default=0, nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="job_matches")
    resume_document = relationship("Document", foreign_keys="[JobMatch.resume_document_id]", back_populates="resume_matches")
    job_document = relationship("Document", foreign_keys="[JobMatch.job_document_id]", back_populates="job_matches")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = {"extend_existing": True}

    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(32), default="medium", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
