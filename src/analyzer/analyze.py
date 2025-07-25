import asyncio
import json
import os
import shutil
import zipfile
import requests

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import (
    upsert_auth_model,
    upsert_data_model,
    upsert_entry_points_model,
    upsert_overview_model,
    upsert_repo_model,
    get_models_by_analyze_job_id,
)
from src.ai.entry_points_agent import get_entry_points
from src.ai.auth_agent import get_auth_analysis
from src.ai.data_model_agent import get_data_model_analysis
from src.database.models import (
    AnalyzeJobs,
)
from src.analyzer.repo_analyzer import build_repo_model, find_readme
from src.ai.overview_agent import get_repo_overview


async def download_github_repo(github_url: str, destination_path: str, default_branch: str = "main"):
    """
    Download a GitHub repository as ZIP and extract it to the destination path
    
    Args:
        github_url: GitHub repository URL (e.g., https://github.com/owner/repo)
        destination_path: Local path where to extract the repository
        default_branch: The default branch to download (defaults to 'main')
    """
    # Extract owner and repo from GitHub URL
    # Handle both https://github.com/owner/repo and https://github.com/owner/repo.git
    github_url = github_url.rstrip('.git')
    parts = github_url.split('/')
    owner = parts[-2]
    repo = parts[-1]
    
    # GitHub's ZIP download URL
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{default_branch}.zip"
    
    try:
        # Download the ZIP file
        response = requests.get(zip_url, stream=True)
        response.raise_for_status()
        
        # Create a temporary ZIP file
        zip_path = f"/tmp/{repo}.zip"
        with open(zip_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Extract the ZIP file
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall("/tmp/")
        
        # GitHub creates a folder named "repo-branch", we need to rename it to just "repo"
        extracted_folder = f"/tmp/{repo}-{default_branch}"
        if os.path.exists(extracted_folder):
            if os.path.exists(destination_path):
                shutil.rmtree(destination_path)
            shutil.move(extracted_folder, destination_path)
        
        # Clean up the ZIP file
        os.remove(zip_path)
        
    except Exception as e:
        # If main branch fails, try master branch
        if default_branch == "main":
            try:
                download_github_repo(github_url, destination_path, "master")
            except Exception:
                raise Exception(f"Failed to download repository from {github_url}: {str(e)}")
        else:
            raise Exception(f"Failed to download repository from {github_url}: {str(e)}")


async def generate_analysis_stream(job: AnalyzeJobs, db: AsyncSession):
    """
    Generate SSE stream for repository analysis progress

    Args:
        repo_uuid: UUID of the repository being analyzed
        db: Database session

    Yields:
        SSE formatted messages with analysis progress
    """
    try:
        yield f"data: {json.dumps({'repo_id': str(job.id), 'name': job.repo_name, 'default_branch': job.default_branch, 'owner': job.owner, 'link': job.github_url, 'event_type': 'start'})}\n\n"

        # now check if we parsed this repo before
        models_result = await get_models_by_analyze_job_id(db, job.id)
        if models_result:
            repo_model, overview_model, auth_model, data_model, entry_points_model = (
                models_result
            )
            if (
                repo_model
                and overview_model
                and auth_model
                and data_model
                and entry_points_model
            ):

                yield f"data: {json.dumps({'event_type': 'overview', 'message': overview_model.overview_data})}\n\n"
                yield f"data: {json.dumps({'event_type': 'entry_points', 'message': entry_points_model.usage_data})}\n\n"
                yield f"data: {json.dumps({'event_type': 'auth_analysis', 'message': auth_model.auth_data})}\n\n"
                yield f"data: {json.dumps({'event_type': 'data_model_analysis', 'message': data_model.data_structure})}\n\n"

                readme_path = await find_readme("/tmp/repo/" + job.repo_name)
                if readme_path:
                    yield f"data: {json.dumps({'event_type': 'readme',  'message': {'has_readme': True, 'readme': readme_path}})}\n\n"
                else:
                    yield f"data: {json.dumps({'event_type': 'readme',  'message': {'has_readme': False, 'readme': None}})}\n\n"

                yield f"data: {json.dumps({'repo_id': str(job.id), 'event_type': 'completed'})}\n\n"

                return

        # check if we downloaded repo before
        if not os.path.exists("/tmp/repo/" + job.repo_name):
            # download repo as ZIP from GitHub (git plugin )
            await download_github_repo(job.github_url, "/tmp/repo/" + job.repo_name, job.default_branch or "main")

        # check if repo has readme to retrun early
        readme_path = await find_readme("/tmp/repo/" + job.repo_name)
        if readme_path:
            yield f"data: {json.dumps({'event_type': 'readme',  'message': {'has_readme': True, 'readme': readme_path}})}\n\n"
        else:
            yield f"data: {json.dumps({'event_type': 'readme',  'message': {'has_readme': False, 'readme': None}})}\n\n"

        # Build repo model if not exists
        repo_model = await build_repo_model("/tmp/repo/" + job.repo_name)
        await upsert_repo_model(db, job.id, repo_model.model_dump_json())

        # Generate overview
        overview = await get_repo_overview(repo_model)
        yield f"data: {json.dumps({'event_type': 'overview', 'message': overview.model_dump_json()})}\n\n"
        await upsert_overview_model(db, job.id, overview.model_dump_json())

        # Run analysis tasks in parallel
        print("Starting parallel analysis tasks...")

        # Define tasks to run in parallel
        tasks = [
            get_entry_points(repo_model, overview.summary),
            get_auth_analysis(repo_model, overview.summary),
            get_data_model_analysis(repo_model, overview.summary),
        ]

        # Run tasks in parallel
        results = await asyncio.gather(*tasks)

        # Process results and save to database
        task_names = [
            "entry_points",
            "auth_analysis",
            "data_model_analysis",
        ]

        for task_name, result in zip(task_names, results):
            print(f"Completed {task_name} analysis")

            if task_name == "entry_points":
                # Save to database
                await upsert_entry_points_model(db, job.id, result.model_dump_json())
                # Yield SSE message
                yield f"data: {json.dumps({'event_type': 'entry_points', 'message': result.model_dump_json()})}\n\n"

            elif task_name == "auth_analysis":
                await upsert_auth_model(db, job.id, result.model_dump_json())
                yield f"data: {json.dumps({'event_type': 'auth_analysis', 'message': result.model_dump_json()})}\n\n"

            elif task_name == "data_model_analysis":
                await upsert_data_model(db, job.id, result.model_dump_json())
                yield f"data: {json.dumps({'event_type': 'data_model_analysis', 'message': result.model_dump_json()})}\n\n"

        # Send completion event to signal the stream is finished
        yield f"data: {json.dumps({'repo_id': str(job.id), 'event_type': 'completed'})}\n\n"
        await db.commit()

    except Exception as e:
        yield f"data: {json.dumps({'event_type': 'error', 'repo_id': str(job.id), 'message': f'Analysis failed: {str(e)}'})}\n\n"
        return
