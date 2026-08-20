import logging
import os
from typing import Annotated, Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import APIRouter, Body, Depends, Query, status

from backend.exceptions import PeeweareAppException
from notifications.models import NotificationsResult

from ..dependencies import (
    bg_assets,
    get_monitoring_collection,
    get_scheduler,
)
from ..models import MonitoringDetails, Tags

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/movies/monitoring", tags=[Tags.monitoring])


# helper functions
async def push_notification(document: dict) -> NotificationsResult:
    date_obj = document["release_date"]
    release_date = date_obj.strftime("%d-%m-%Y")
    payload = {
        "title": f"Shows updated for {document['name']} on {release_date}",
        "message": "",
    }
    for experience, shows in document["showtimes"].items():
        payload["message"] += f"{experience}: "
        for show in shows:
            payload["message"] += f"{show}, "
        payload["message"] = payload["message"].rstrip(", ") + "\n"
    try:
        notifier = await bg_assets.notifier
        response = await notifier.push(payload)
        logger.info(
            f"Notification sent successfully for movie_id {document['movie_id']} in theater_id {document['theater_id']} on {document['release_date']} with message: {response.message}"
        )
        return response
    except Exception as e:
        logger.error(
            f"Error trying to push notification for movie_id {document['movie_id']} in theater_id {document['theater_id']} on {document['release_date']}: {e}"
        )
        raise PeeweareAppException(f"Error trying to push notification: {e}")


async def save_showtimes_to_database(
    movie_id: str, showtimes: dict, monitoring_collection: Any
):
    try:
        document = await monitoring_collection.find_one({"movie_id": movie_id})
        if document and document["showtimes"] != showtimes:
            document["showtimes"] = showtimes
            document["updates"] = document["updates"] - 1
            result = await monitoring_collection.update_one(
                {"movie_id": movie_id}, {"$set": document}
            )
            logger.info(
                f"Showtimes for movie_id {movie_id} in theater_id {document['theater_id']} on {document['release_date']} with id {result.upserted_id} updated in db"
            )
            await push_notification(document)
    except Exception as e:
        logger.error(f"Error trying to find document with movie_id {movie_id}: {e}")
        raise PeeweareAppException(
            f"Error trying to find document with movie_id {movie_id}: {e}"
        )


async def get_movie_showtimes(
    movie_id: str,
    theater_id: str,
    release_date: str,
    imax: bool,
) -> None:
    """
    Get the showtimes for a specific movie at a specific theater on a specific date.

    Args:
        movie_id (str): The ID of the movie.
        theater_id (str): The ID of the theater.
        release_date (str): The date of the release.
        imax (bool, optional): Whether the movie is being shown in IMAX. Defaults to False.

    Returns:
        None: If the showtimes could not be fetched.
    """
    peeweare_api = await bg_assets.peeweare_api
    monitoring_collection = await bg_assets.monitoring_collection
    response = await peeweare_api.showtimes(movie_id, theater_id, release_date)
    if response is None:
        logger.warning(
            f"Failed to fetch showtimes for movie_id {movie_id} in theater_id {theater_id} on {release_date}"
        )
        return
    if imax:
        shows = {k: v for k, v in response.shows.items() if "IMAX" in k}
        await save_showtimes_to_database(movie_id, shows, monitoring_collection)
        return
    await save_showtimes_to_database(movie_id, response.shows, monitoring_collection)
    return


# dependencies
async def add_job_to_scheduler(
    body: Annotated[MonitoringDetails, Body()],
    scheduler: Annotated[AsyncIOScheduler, Depends(get_scheduler)],
) -> MonitoringDetails:
    """
    Add a job to the scheduler to fetch showtimes for a specific movie at a specific theater on a specific date.

    Args:
        body (MonitoringDetails): The details of the monitoring job, including movie_id, theater_id, release_date, and imax.

    Returns:
        MonitoringDetails: The details of the monitoring job, including the job ID.
    """
    seconds = int(os.environ["JOB_INTERVAL_SECONDS"])
    movie_id, theater_id, release_date, imax, expiry_date = (
        body.movie_id,
        body.theater_id,
        str(body.release_date.date()),
        body.imax,
        body.expiry_date,
    )
    result = scheduler.add_job(
        get_movie_showtimes,
        "interval",
        seconds=seconds,
        args=[movie_id, theater_id, release_date, imax],
        end_date=expiry_date,
    )
    logger.info(
        f"Scheduler job with interval {seconds} for movie_id {body.movie_id} with id {result.id} added"
    )
    body.job_id = result.id
    return body


async def add_job_to_database(
    body: Annotated[MonitoringDetails, Depends(add_job_to_scheduler)],
    monitoring_collection=Depends(get_monitoring_collection),
) -> MonitoringDetails:
    """
    Add a job to the database.

    Args:
        body (MonitoringDetails): The details of the monitoring job, including movie_id, theater_id, release_date, and imax.

    Returns:
        MonitoringDetails: The details of the monitoring job, including the job ID.
    """
    result = await monitoring_collection.insert_one(body.model_dump())
    logger.info(
        f"Monitoring job for movie_id {body.movie_id} in theater_id {body.theater_id} on {body.release_date} with id {result.inserted_id} added to db"
    )
    return body


async def remove_job_from_database(
    movie_id: Annotated[str, Query()],
    monitoring_collection=Depends(get_monitoring_collection),
) -> str | None:
    """
    Remove a job from the database based on the movie ID.

    Args:
        movie_id (str): The ID of the movie for which the monitoring job should be deleted.

    Returns:
        str: scheduler job ID if the job was found and removed, None otherwise.
    """
    if await monitoring_collection.find_one({"movie_id": movie_id}):
        result = await monitoring_collection.find_one({"movie_id": movie_id})
        job_id = result.get("job_id")
        await monitoring_collection.delete_one({"movie_id": movie_id})
        logger.info(f"Monitoring job for movie_id {movie_id} removed from db")
        return job_id
    logger.warning(f"Monitoring job for movie_id {movie_id} not found in db")
    return None


async def remove_job_from_scheduler(
    job_id: Annotated[str, Depends(remove_job_from_database)],
    scheduler: Annotated[AsyncIOScheduler, Depends(get_scheduler)],
) -> None:
    """
    Remove a job from the scheduler based on the job ID.

    Args:
        job_id (str): The ID of the job to be removed.

    Returns:
        None
    """
    if job_id is not None:
        scheduler.remove_job(job_id=job_id)
        logger.info(f"Scheduler job with id {job_id} removed")


# monitoring
@router.post(
    "/create",
    summary="Create Monitoring Job",
    status_code=status.HTTP_201_CREATED,
)
async def create_monitorting_job(
    body: Annotated[MonitoringDetails, Depends(add_job_to_database)],
) -> MonitoringDetails:
    """
    Create a new monitoring job with all the information:

    Args:
        body (MonitoringDetails): The details of the monitoring job, including movie_id, theater_id, release_date, and imax.

    Returns:
        MonitoringDetails: The details of the monitoring job, including the job ID.
    """
    return body


@router.delete(
    "/delete",
    summary="Delete Monitoring Job",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_monitoring_job(
    movie_id: Annotated[str, Depends(remove_job_from_scheduler)],
) -> None:
    """
    Delete a monitoring job based on the movie ID.

    Args:
        movie_id (str): The ID of the movie for which to delete the monitoring job.

    Returns:
        None
    """
    return


@router.get(
    "/list",
    summary="List Monitoring Jobs",
)
async def list_monitoring_jobs(
    monitoring_collection=Depends(get_monitoring_collection),
) -> Any:
    """
    List all monitoring jobs.
    """
    return await monitoring_collection.find().to_list(length=100)
