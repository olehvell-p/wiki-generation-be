from sqlalchemy import Column, String, DateTime, Boolean, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .config import Base

import uuid


class AnalyzeJobs(Base):
    """
    Repository model to store GitHub repository information
    """

    __tablename__ = "analyze_jobs"

    # Primary key - UUID for the repository
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    # GitHub repository URL
    github_url = Column(String(500), nullable=False, index=True)

    # Repository owner
    owner = Column(String(100), nullable=False, index=True)

    # Repository name
    repo_name = Column(String(100), nullable=False, index=True)

    # Repository description
    description = Column(String(500), nullable=True)

    # default branch
    default_branch = Column(String(100), nullable=False, default="main")

    # readme url
    readme_url = Column(String(500), nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self):
        return f"<AnalyzeJobs(uuid='{self.id}', github_url='{self.github_url}', owner='{self.owner}', repo_name='{self.repo_name}')>"


class RepoModel(Base):
    """
    Repository model data to store processed repository information
    """

    __tablename__ = "repo_models"

    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    analyze_job_id = Column(
        UUID, ForeignKey("analyze_jobs.id"), nullable=False, unique=True
    )

    # JSON data representing the processed repository structure
    model_data = Column(
        Text, nullable=True
    )  # Store JSON representation of Repo from types

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<RepoModel(id='{self.id}', created_at='{self.created_at}')>"


class OverviewModel(Base):
    """
    Overview model to store repository overview information
    """

    __tablename__ = "overview_models"

    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    analyze_job_id = Column(
        UUID, ForeignKey("analyze_jobs.id"), nullable=False, unique=True
    )

    # JSON data representing repository overview
    overview_data = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return (
            f"<OverviewModel(id='{self.id}', analyze_job_id='{self.analyze_job_id}')>"
        )


class AuthModel(Base):
    """
    Authentication analysis model to store authentication-related information
    """

    __tablename__ = "auth_models"

    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    analyze_job_id = Column(
        UUID, ForeignKey("analyze_jobs.id"), nullable=False, unique=True
    )

    # JSON data representing authentication analysis
    auth_data = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<AuthModel(id='{self.id}', analyze_job_id='{self.analyze_job_id}')>"


class DataModel(Base):
    """
    Data model analysis to store data structure and model information
    """

    __tablename__ = "data_models"

    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    analyze_job_id = Column(
        UUID, ForeignKey("analyze_jobs.id"), nullable=False, unique=True
    )

    # JSON data representing data model analysis
    data_structure = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"<DataModel(id='{self.id}', analyze_job_id='{self.analyze_job_id}')>"


class EntryPointsModel(Base):
    """
    How-to-use analysis model to store usage instructions and examples
    """

    __tablename__ = "entry_points_models"

    # Primary key
    id = Column(UUID, primary_key=True, index=True, default=uuid.uuid4)

    analyze_job_id = Column(
        UUID, ForeignKey("analyze_jobs.id"), nullable=False, unique=True
    )

    # JSON data representing how-to-use analysis
    usage_data = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    def __repr__(self):
        return (
            f"<EntryPointsModel(id='{self.id}', analyze_job_id='{self.analyze_job_id}')>"
        )
