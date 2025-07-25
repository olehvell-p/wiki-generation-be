from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from .models import AnalyzeJobs


class AnalyzeJobService:
    """
    Service class for repository database operations
    """

    @staticmethod
    async def create_analyze_job(
        db: AsyncSession,
        github_url: str,
        owner: str,
        repo_name: str,
        description: str,
        default_branch: str,
    ) -> Optional[AnalyzeJobs]:
        """
        Create a new repository record in the database

        Args:
            db: Database session
            uuid: UUID for the repository
            github_url: GitHub repository URL
            owner: Repository owner
            repo_name: Repository name
            canonical_github_url: Canonical GitHub URL
            is_public: Whether the repository is public
            original_url: Original URL that was submitted

        Returns:
            Created Repo object or None if creation failed
        """
        try:
            job = AnalyzeJobs(
                github_url=github_url,
                owner=owner,
                repo_name=repo_name,
                description=description,
                default_branch=default_branch,
            )

            db.add(job)
            await db.commit()
            await db.refresh(job)
            return job

        except IntegrityError as error:
            print(error)
            await db.rollback()
            return None

    @staticmethod
    async def get_repo_by_uuid(db: AsyncSession, uuid: str) -> Optional[AnalyzeJobs]:
        """
        Get a repository by UUID

        Args:
            db: Database session
            uuid: Repository UUID

        Returns:
            Repo object or None if not found
        """
        result = await db.execute(select(AnalyzeJobs).where(AnalyzeJobs.id == uuid))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_repo_by_github_url(
        db: AsyncSession, github_url: str
    ) -> Optional[AnalyzeJobs]:
        """
        Get a repository by GitHub URL

        Args:
            db: Database session
            github_url: GitHub repository URL

        Returns:
            Repo object or None if not found
        """
        result = await db.execute(
            select(AnalyzeJobs).where(AnalyzeJobs.github_url == github_url)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_repos_by_owner(db: AsyncSession, owner: str) -> List[AnalyzeJobs]:
        """
        Get all repositories by owner

        Args:
            db: Database session
            owner: Repository owner

        Returns:
            List of Repo objects
        """
        result = await db.execute(
            select(AnalyzeJobs)
            .where(AnalyzeJobs.owner == owner)
            .order_by(AnalyzeJobs.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_all_repos(
        db: AsyncSession, limit: int = 100, offset: int = 0
    ) -> List[AnalyzeJobs]:
        """
        Get all repositories with pagination

        Args:
            db: Database session
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of Repo objects
        """
        result = await db.execute(
            select(AnalyzeJobs)
            .order_by(AnalyzeJobs.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def delete_repo_by_uuid(db: AsyncSession, uuid: str) -> bool:
        """
        Delete a repository by UUID

        Args:
            db: Database session
            uuid: Repository UUID

        Returns:
            True if deleted successfully, False otherwise
        """
        result = await db.execute(select(AnalyzeJobs).where(AnalyzeJobs.id == uuid))
        repo = result.scalar_one_or_none()

        if repo:
            await db.delete(repo)
            await db.commit()
            return True
        return False
