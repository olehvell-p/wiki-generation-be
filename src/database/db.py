from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func

from src.database.models import (
    EntryPointsModel,
    RepoModel,
    OverviewModel,
    AuthModel,
    DataModel,
    OverviewModel,
)


async def get_models_by_analyze_job_id(
    db: AsyncSession, analyze_job_id: int
) -> Optional[Tuple[RepoModel, OverviewModel, AuthModel, DataModel, EntryPointsModel]]:
    """
    Get all models by analyze_job_id
    """
    result = await db.execute(
        select(RepoModel, OverviewModel, AuthModel, DataModel, EntryPointsModel)
        .outerjoin(
            OverviewModel, RepoModel.analyze_job_id == OverviewModel.analyze_job_id
        )
        .outerjoin(AuthModel, RepoModel.analyze_job_id == AuthModel.analyze_job_id)
        .outerjoin(DataModel, RepoModel.analyze_job_id == DataModel.analyze_job_id)
        .outerjoin(
            EntryPointsModel,
            RepoModel.analyze_job_id == EntryPointsModel.analyze_job_id,
        )
        .where(RepoModel.analyze_job_id == analyze_job_id)
    )
    return result.first()


async def upsert_repo_model(
    db: AsyncSession, analyze_job_id: str, model_data: Optional[str] = None
) -> Optional[RepoModel]:
    """
    Upsert a RepoModel in the database using INSERT...ON CONFLICT

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        model_data: JSON string representation of repo data

    Returns:
        Created or updated RepoModel or None if operation failed
    """
    try:
        insert_stmt = insert(RepoModel).values(
            analyze_job_id=analyze_job_id,
            model_data=model_data
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["analyze_job_id"],
            set_={
                "model_data": insert_stmt.excluded.model_data,
                "updated_at": func.now()
            }
        )
        
        result = await db.execute(upsert_stmt.returning(RepoModel))
        await db.commit()
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        print(f"Error upserting RepoModel: {e}")
        return None


async def upsert_overview_model(
    db: AsyncSession, analyze_job_id: str, overview_data: str
) -> Optional[OverviewModel]:
    """
    Upsert an OverviewModel in the database using INSERT...ON CONFLICT

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        overview_data: JSON string representation of overview data

    Returns:
        Created or updated OverviewModel or None if operation failed
    """
    try:
        insert_stmt = insert(OverviewModel).values(
            analyze_job_id=analyze_job_id,
            overview_data=overview_data
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["analyze_job_id"],
            set_={
                "overview_data": insert_stmt.excluded.overview_data,
                "updated_at": func.now()
            }
        )
        
        result = await db.execute(upsert_stmt.returning(OverviewModel))
        await db.commit()
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        print(f"Error upserting OverviewModel: {e}")
        return None




async def upsert_auth_model(
    db: AsyncSession, analyze_job_id: str, auth_data: Optional[str] = None
) -> Optional[AuthModel]:
    """
    Upsert an AuthModel in the database using INSERT...ON CONFLICT

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        auth_data: JSON string representation of authentication analysis

    Returns:
        Created or updated AuthModel or None if operation failed
    """
    try:
        insert_stmt = insert(AuthModel).values(
            analyze_job_id=analyze_job_id,
            auth_data=auth_data
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["analyze_job_id"],
            set_={
                "auth_data": insert_stmt.excluded.auth_data,
                "updated_at": func.now()
            }
        )
        
        result = await db.execute(upsert_stmt.returning(AuthModel))
        await db.commit()
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        print(f"Error upserting AuthModel: {e}")
        return None


# ============ DataModel Functions ============


async def upsert_data_model(
    db: AsyncSession, analyze_job_id: str, data_structure: Optional[str] = None
) -> Optional[DataModel]:
    """
    Upsert a DataModel in the database using INSERT...ON CONFLICT

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        data_structure: JSON string representation of data model analysis

    Returns:
        Created or updated DataModel or None if operation failed
    """
    try:
        insert_stmt = insert(DataModel).values(
            analyze_job_id=analyze_job_id,
            data_structure=data_structure
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["analyze_job_id"],
            set_={
                "data_structure": insert_stmt.excluded.data_structure,
                "updated_at": func.now()
            }
        )
        
        result = await db.execute(upsert_stmt.returning(DataModel))
        await db.commit()
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        print(f"Error upserting DataModel: {e}")
        return None




async def upsert_entry_points_model(
    db: AsyncSession, analyze_job_id: str, usage_data: Optional[str] = None
) -> Optional[EntryPointsModel]:
    """
    Upsert an EntryPointsModel in the database using INSERT...ON CONFLICT

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        usage_data: JSON string representation of how-to-use analysis

    Returns:
        Created or updated EntryPointsModel or None if operation failed
    """
    try:
        insert_stmt = insert(EntryPointsModel).values(
            analyze_job_id=analyze_job_id,
            usage_data=usage_data
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            index_elements=["analyze_job_id"],
            set_={
                "usage_data": insert_stmt.excluded.usage_data,
                "updated_at": func.now()
            }
        )
        
        # Execute and return the upserted row
        result = await db.execute(upsert_stmt.returning(EntryPointsModel))
        await db.commit()
        return result.scalar_one()
        
    except Exception as e:
        await db.rollback()
        print(f"Error upserting EntryPointsModel: {e}")
        return None

