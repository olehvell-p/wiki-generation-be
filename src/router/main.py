import uuid
import re
import json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any, Optional, List, Tuple
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
import requests

from src.analyzer.analyze import generate_analysis_stream
from src.ai.question_master_agent import answer_question, Message, QuestionResponse
from src.types.files import Repo

from ..database.config import init_db, get_db
from ..database.repo_service import AnalyzeJobService
from ..database.db import get_models_by_analyze_job_id

import git


def extract_github_repo_info(url: str) -> Tuple[str, str]:
    """
    Extract owner and repository name from a GitHub URL.

    Args:
        url: GitHub repository URL (e.g., https://github.com/phosphor-icons/react)

    Returns:
        Tuple of (owner, repo_name)

    Raises:
        ValueError: If the URL is not a valid GitHub repository URL
    """
    # Remove trailing slash and .git extension if present
    url = url.rstrip("/")

    # Regular expression to match GitHub repository URLs
    pattern = r"https?://github\.com/([^/]+)/([^/]+)"
    match = re.match(pattern, url)

    if not match:
        raise HTTPException(status_code=400, detail="Invalid GitHub repository URL")

    owner = match.group(1)
    repo_name = match.group(2)

    return owner, repo_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database on startup
    await init_db()
    yield


app = FastAPI(
    title="GitHub Repo Analyzer API",
    description="A FastAPI application for analyzing GitHub repository URLs",
    version="1.0.0",
    lifespan=lifespan,
)


class AnalyzeRequest(BaseModel):
    url: HttpUrl


class AnalyzeResponse(BaseModel):
    repo_id: uuid.UUID


class RepoListResponse(BaseModel):
    repos: List[Dict[str, Any]]
    total: int
    limit: int
    offset: int


class AskQuestionRequest(BaseModel):
    messages: List[Message]


class AskQuestionResponse(BaseModel):
    response: str


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_url(
    request: AnalyzeRequest, db: AsyncSession = Depends(get_db)
) -> AnalyzeResponse:
    """
    Analyze a GitHub repository URL and save to database

    Args:
        request: AnalyzeRequest containing the GitHub repo URL to analyze
        db: Database session dependency

    Returns:
        AnalyzeResponse with analysis results and UUID if repo is public
    """
    url_str = str(request.url)

    # Extract owner and repo name from GitHub URL
    owner, repo_name = extract_github_repo_info(url_str)

    # Check if repo is public
    response = requests.get(f"https://api.github.com/repos/{owner}/{repo_name}")
    print(response.status_code)
    print(owner, repo_name)
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Repository is not public")

    repo_metadata = response.json()

    print(repo_metadata)

    # quickly save essentail info so we can return early
    saved_job = await AnalyzeJobService.create_analyze_job(
        db=db,
        github_url=repo_metadata["html_url"],
        owner=repo_metadata["owner"]["login"],
        repo_name=repo_metadata["name"],
        description=repo_metadata["description"],
        default_branch=repo_metadata["default_branch"],
    )


    if not saved_job:
        raise HTTPException(
            status_code=500, detail="Failed to save repository to database"
        )

    return AnalyzeResponse(
        repo_id=saved_job.id,
    )


@app.get("/analyze/{uuid}")
async def analyze_repo_stream(
    uuid: str, db: AsyncSession = Depends(get_db)
) -> StreamingResponse:
    """
    Start repository analysis with SSE communication

    Args:
        uuid: Repository UUID to analyze
        db: Database session dependency

    Returns:
        StreamingResponse with SSE for real-time analysis updates
    """
    # Check if repository exists in database
    job = await AnalyzeJobService.get_repo_by_uuid(db, uuid)
    if not job:
        raise HTTPException(
            status_code=404, detail=f"Repository with UUID {uuid} not found in database"
        )

    # Return SSE stream with timeout protection

    
    return StreamingResponse(
        generate_analysis_stream(job, db),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        },
    )


@app.post("/repo/{uuid}/ask", response_model=AskQuestionResponse)
async def ask_question(
    uuid: str, 
    request: AskQuestionRequest, 
    db: AsyncSession = Depends(get_db)
) -> AskQuestionResponse:
    """
    Answer questions about a repository using AI
    
    Args:
        uuid: Repository UUID
        request: AskQuestionRequest containing the conversation messages
        db: Database session dependency
    
    Returns:
        AskQuestionResponse with the AI's answer
    """
    # Check if repository exists in database
    job = await AnalyzeJobService.get_repo_by_uuid(db, uuid)
    if not job:
        raise HTTPException(
            status_code=404, detail=f"Repository with UUID {uuid} not found in database"
        )
    
    # Get the repository model data
    models = await get_models_by_analyze_job_id(db, job.id)
    if not models or not models[0] or not models[0].model_data:
        raise HTTPException(
            status_code=404, detail=f"Repository model data not found for UUID {uuid}. Please ensure the repository has been analyzed."
        )
    
    # Deserialize the repository model data
    try:
        repo_data = json.loads(models[0].model_data)
        repo = Repo(**repo_data)
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to parse repository model data: {str(e)}"
        )
    
    # Use the Question Master agent to answer the question
    try:
        response = await answer_question(repo, request.messages)
        return AskQuestionResponse(response=response.response)
    except Exception as e:
        print(f"Error in Question Master agent: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate response: {str(e)}"
        )
