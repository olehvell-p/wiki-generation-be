from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.future import select

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
    Upsert a RepoModel in the database

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        model_data: JSON string representation of repo data

    Returns:
        Created or updated RepoModel or None if operation failed
    """
    try:
        # Try to find existing record
        result = await db.execute(
            select(RepoModel).where(RepoModel.analyze_job_id == analyze_job_id)
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            # Update existing record
            existing_model.model_data = model_data
            await db.commit()
            await db.refresh(existing_model)
            return existing_model
        else:
            # Create new record
            repo_model = RepoModel(analyze_job_id=analyze_job_id, model_data=model_data)
            db.add(repo_model)
            await db.commit()
            await db.refresh(repo_model)
            return repo_model
    except Exception as e:
        await db.rollback()
        print(f"Error upserting RepoModel: {e}")
        return None



async def upsert_overview_model(
    db: AsyncSession, analyze_job_id: str, overview_data: str
) -> Optional[OverviewModel]:
    """
    Upsert an OverviewModel in the database

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        overview_data: JSON string representation of overview data

    Returns:
        Created or updated OverviewModel or None if operation failed
    """
    try:
        # Try to find existing record
        result = await db.execute(
            select(OverviewModel).where(OverviewModel.analyze_job_id == analyze_job_id)
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            # Update existing record
            existing_model.overview_data = overview_data
            await db.commit()
            await db.refresh(existing_model)
            return existing_model
        else:
            # Create new record
            overview_model = OverviewModel(
                analyze_job_id=analyze_job_id,
                overview_data=overview_data,
            )
            db.add(overview_model)
            await db.commit()
            await db.refresh(overview_model)
            return overview_model
    except Exception as e:
        await db.rollback()
        print(f"Error upserting OverviewModel: {e}")
        return None



# ============ AuthModel Functions ============


async def upsert_auth_model(
    db: AsyncSession, analyze_job_id: str, auth_data: Optional[str] = None
) -> Optional[AuthModel]:
    """
    Upsert an AuthModel in the database

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        auth_data: JSON string representation of authentication analysis

    Returns:
        Created or updated AuthModel or None if operation failed
    """
    try:
        # Try to find existing record
        result = await db.execute(
            select(AuthModel).where(AuthModel.analyze_job_id == analyze_job_id)
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            # Update existing record
            existing_model.auth_data = auth_data
            await db.commit()
            await db.refresh(existing_model)
            return existing_model
        else:
            # Create new record
            auth_model = AuthModel(
                analyze_job_id=analyze_job_id,
                auth_data=auth_data,
            )
            db.add(auth_model)
            await db.commit()
            await db.refresh(auth_model)
            return auth_model
    except Exception as e:
        await db.rollback()
        print(f"Error upserting AuthModel: {e}")
        return None




# ============ DataModel Functions ============


async def upsert_data_model(
    db: AsyncSession, analyze_job_id: str, data_structure: Optional[str] = None
) -> Optional[DataModel]:
    """
    Upsert a DataModel in the database

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        data_structure: JSON string representation of data model analysis

    Returns:
        Created or updated DataModel or None if operation failed
    """
    try:
        # Try to find existing record
        result = await db.execute(
            select(DataModel).where(DataModel.analyze_job_id == analyze_job_id)
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            # Update existing record
            existing_model.data_structure = data_structure
            await db.commit()
            await db.refresh(existing_model)
            return existing_model
        else:
            # Create new record
            data_model = DataModel(
                analyze_job_id=analyze_job_id,
                data_structure=data_structure,
            )
            db.add(data_model)
            await db.commit()
            await db.refresh(data_model)
            return data_model
    except Exception as e:
        await db.rollback()
        print(f"Error upserting DataModel: {e}")
        return None


# ============ HowToUseModel Functions ============


async def upsert_entry_points_model(
    db: AsyncSession, analyze_job_id: str, usage_data: Optional[str] = None
) -> Optional[EntryPointsModel]:
    """
    Upsert an EntryPointsModel in the database

    Args:
        db: Database session
        analyze_job_id: ID of the associated AnalyzeJob
        usage_data: JSON string representation of how-to-use analysis

    Returns:
        Created or updated EntryPointsModel or None if operation failed
    """
    try:
        # Try to find existing record
        result = await db.execute(
            select(EntryPointsModel).where(EntryPointsModel.analyze_job_id == analyze_job_id)
        )
        existing_model = result.scalar_one_or_none()
        
        if existing_model:
            # Update existing record
            existing_model.usage_data = usage_data
            await db.commit()
            await db.refresh(existing_model)
            return existing_model
        else:
            # Create new record
            entry_points_model = EntryPointsModel(
                analyze_job_id=analyze_job_id,
                usage_data=usage_data,
            )
            db.add(entry_points_model)
            await db.commit()
            await db.refresh(entry_points_model)
            return entry_points_model
    except Exception as e:
        await db.rollback()
        print(f"Error upserting EntryPointsModel: {e}")
        return None


# ============ Backward Compatibility Aliases ============

# Keep old function names for backward compatibility
add_repo_model = upsert_repo_model
add_overview_model = upsert_overview_model
add_auth_model = upsert_auth_model
add_data_model = upsert_data_model
add_entry_points_model = upsert_entry_points_model
