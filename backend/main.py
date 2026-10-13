import json
import logging
import os
from contextlib import AsyncExitStack, asynccontextmanager

from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from pymongo import AsyncMongoClient, MongoClient

from backend.dependencies import bg_assets
from backend.exceptions import PeeweareAppException
from mcp_server.server import mcp
from notifications.notifier import Notifications
from peeweare.peeweare_api import PeeweareAPI

from .routers import lists, monitoring

load_dotenv()


@asynccontextmanager
async def api_lifespan(app: FastAPI):
    # Initialze Logger
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
    )

    # Initialize PeeweareAPI
    peeweare_api = PeeweareAPI(
        url=os.environ["URL"], headers=json.loads(os.environ["HEADERS"])
    )
    app.state.peeweare_api = peeweare_api

    # Initialize Notifier
    notifier = Notifications()
    app.state.notifier = notifier

    # Initialize MongoDB client and database
    mongodb_client = AsyncMongoClient(
        os.environ["MONGODB_HOST"],
        username=os.environ["MONGODB_INITDB_ROOT_USERNAME"],
        password=os.environ["MONGODB_INITDB_ROOT_PASSWORD"],
        authMechanism="SCRAM-SHA-256",
    )
    database = mongodb_client.peeweare
    monitoring_collection = database.get_collection("monitoring_jobs")
    jobstore_collection = database.get_collection("jobstore")
    app.state.monitoring_collection = monitoring_collection
    app.state.jobstore_collection = jobstore_collection
    ping_response = await database.command("ping")
    if int(ping_response["ok"]) != 1:
        logger.error("Problem connecting to database cluster.")
        raise PeeweareAppException("Problem connecting to database cluster.")
    else:
        logger.info("Connected to database cluster.")

    # Create an index on the expiry_date field to automatically delete expired documents
    await monitoring_collection.create_index("expiry_date", expireAfterSeconds=0)

    # Initialize the scheduler and add the MongoDB job store
    scheduler = AsyncIOScheduler()
    jobstore = MongoDBJobStore(
        client=MongoClient(
            os.environ["MONGODB_HOST"],
            username=os.environ["MONGODB_INITDB_ROOT_USERNAME"],
            password=os.environ["MONGODB_INITDB_ROOT_PASSWORD"],
            authMechanism="SCRAM-SHA-256",
        ),
        database="peeweare",
        collection="jobstore",
    )
    scheduler.add_jobstore(jobstore)
    scheduler.start()
    app.state.scheduler = scheduler

    # Initialize background assets
    await bg_assets.initialize(monitoring_collection, peeweare_api, notifier, scheduler)
    yield

    # Shutdown the scheduler and close the MongoDB client
    scheduler.shutdown()
    await mongodb_client.close()


@asynccontextmanager
async def mcp_lifespan(app: FastAPI):
    async with mcp.session_manager.run():
        yield


@asynccontextmanager
async def combined_lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        await stack.enter_async_context(api_lifespan(app))
        await stack.enter_async_context(mcp_lifespan(app))
        yield


app = FastAPI(
    title="Peeweare Showtime Notifier API with MCP", lifespan=combined_lifespan
)
app.include_router(monitoring.router)
app.include_router(lists.router)

mcp_app = mcp.streamable_http_app()
app.mount("/", mcp_app)
