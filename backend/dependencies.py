from typing import Any

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import Request

from notifications.notifier import Notifications
from peeweare.peeweare_api import PeeweareAPI


class BackgroundAssetRegistry:
    """Manages active third-party connections across HTTP and background worker context lines."""

    def __init__(self):
        self._monitoring_collection: Any | None = None
        self._peeweare_api: PeeweareAPI | None = None
        self._notifier: Notifications | None = None
        self._scheduler: AsyncIOScheduler | None = None

    async def initialize(
        self,
        monitoring_collection: Any,
        peeweare_api: PeeweareAPI,
        notifier: Notifications,
        scheduler: AsyncIOScheduler,
    ) -> None:
        """Bind live initialized lifespan assets to the container."""
        self._monitoring_collection = monitoring_collection
        self._peeweare_api = peeweare_api
        self._notifier = notifier
        self._scheduler = scheduler

    @property
    async def monitoring_collection(self) -> Any:
        if self._monitoring_collection is None:
            raise RuntimeError(
                "BackgroundAssetRegistry: monitoring_collection is not initialized"
            )
        return self._monitoring_collection

    @property
    async def peeweare_api(self) -> PeeweareAPI:
        if self._peeweare_api is None:
            raise RuntimeError(
                "BackgroundAssetRegistry: peeweare_api is not initialized"
            )
        return self._peeweare_api

    @property
    async def notifier(self) -> Notifications:
        if self._notifier is None:
            raise RuntimeError("BackgroundAssetRegistry: notifier is not initialized")
        return self._notifier

    @property
    async def scheduler(self) -> AsyncIOScheduler:
        if self._scheduler is None:
            raise RuntimeError("BackgroundAssetRegistry: scheduler is not initialized")
        return self._scheduler


bg_assets = BackgroundAssetRegistry()


async def get_monitoring_collection(request: Request) -> Any:
    return request.app.state.monitoring_collection


async def get_jobsstore_collection(request: Request) -> Any:
    return request.app.state.jobsstore_collection


async def get_peeweare_api(request: Request) -> PeeweareAPI:
    return request.app.state.peeweare_api


async def get_notifier(request: Request) -> Notifications:
    return request.app.state.notifier


async def get_scheduler(request: Request) -> AsyncIOScheduler:
    return request.app.state.scheduler
