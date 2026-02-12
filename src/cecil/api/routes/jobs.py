"""Job history API routes.

Provides endpoints for listing, retrieving, and deleting persistent
job records.  Jobs are stored as individual JSON files under
``~/.cecil/jobs/``.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from cecil.api.schemas import ErrorResponse, JobRecord


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


def _get_jobs_dir() -> Path:
    """Get the directory for storing job JSON files.

    Returns:
        Path to ``~/.cecil/jobs/`` directory (created if it does not exist).
    """
    jobs_dir = Path("~/.cecil/jobs").expanduser()
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir


def _persist_job(job: dict[str, object]) -> None:
    """Write a job record to disk as JSON.

    Args:
        job: Serialisable dictionary representing the job record.
    """
    jobs_dir = _get_jobs_dir()
    job_path = jobs_dir / f"{job['job_id']}.json"
    try:
        with job_path.open("w", encoding="utf-8") as f:
            json.dump(job, f, indent=2, default=str)
        logger.info(
            "Job persisted to disk",
            extra={"job_id": job["job_id"], "path": str(job_path)},
        )
    except OSError as err:
        logger.error(
            "Failed to persist job",
            extra={"job_id": job["job_id"], "error": str(err)},
        )


def _load_all_jobs() -> list[dict[str, object]]:
    """Read all job JSON files from disk.

    Returns:
        List of job dictionaries sorted by ``created_at`` descending.
        Malformed files are logged and skipped.
    """
    jobs_dir = _get_jobs_dir()
    jobs: list[dict[str, object]] = []

    for json_file in jobs_dir.glob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                jobs.append(data)
        except (json.JSONDecodeError, OSError) as err:
            logger.warning(
                "Skipping malformed job file",
                extra={"path": str(json_file), "error": str(err)},
            )
            continue

    # Sort by created_at descending (most recent first).
    jobs.sort(key=lambda j: str(j.get("created_at", "")), reverse=True)
    return jobs


@router.get(
    "/",
    response_model=list[JobRecord],
)
async def list_jobs() -> list[dict[str, object]]:
    """List all persisted job records.

    Returns:
        A list of job records sorted by ``created_at`` descending.
    """
    return _load_all_jobs()


@router.get(
    "/{job_id}",
    response_model=JobRecord,
    responses={404: {"model": ErrorResponse}},
)
async def get_job(job_id: str) -> dict[str, object] | JSONResponse:
    """Retrieve a single job record by ID.

    Args:
        job_id: The unique job identifier.

    Returns:
        The job record, or 404 if not found.
    """
    job_path = _get_jobs_dir() / f"{job_id}.json"
    if not job_path.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="job_not_found",
                message="No job found with the given ID",
            ).model_dump(),
        )

    try:
        with job_path.open("r", encoding="utf-8") as f:
            data: dict[str, object] = json.load(f)
        return data
    except (json.JSONDecodeError, OSError) as err:
        logger.error(
            "Failed to read job file",
            extra={"job_id": job_id, "error": str(err)},
        )
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="job_not_found",
                message="Job file is unreadable",
            ).model_dump(),
        )


@router.delete(
    "/{job_id}",
    status_code=204,
    response_model=None,
    responses={404: {"model": ErrorResponse}},
)
async def delete_job(job_id: str) -> JSONResponse | None:
    """Delete a job record from disk.

    Args:
        job_id: The unique job identifier.

    Returns:
        204 No Content on success, or 404 if not found.
    """
    job_path = _get_jobs_dir() / f"{job_id}.json"
    if not job_path.is_file():
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="job_not_found",
                message="No job found with the given ID",
            ).model_dump(),
        )

    try:
        job_path.unlink()
        logger.info("Job deleted", extra={"job_id": job_id})
    except OSError as err:
        logger.error(
            "Failed to delete job file",
            extra={"job_id": job_id, "error": str(err)},
        )
        return JSONResponse(
            status_code=404,
            content=ErrorResponse(
                error="job_delete_failed",
                message="Failed to delete job file",
            ).model_dump(),
        )

    return None
