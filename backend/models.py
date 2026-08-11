from datetime import datetime, timedelta
from enum import Enum, StrEnum
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, model_validator
from pydantic.alias_generators import to_snake


class Theater(StrEnum):
    M534 = "PVR GLOBAL MALL"
    M519 = "PVR GT WORLD MALL"
    M533 = "PVR SUPERPLEX FORUM MALL"
    M511 = "PVR ORION MALL"
    M391 = "PVR VAISHNAVI SAPPHIRE MALL"
    M148 = "INOX MANTRI SQUARE"
    M127 = "INOX SHREE GARUDA SWAGATH MALL"
    M150 = "INOX CENTRAL"
    M520 = "PVR VEGA CITY"
    M507 = "PVR NEXUS"
    M529 = "PVR DIRECTORS CUT FORUM REX WALK"
    M110 = "INOX GARUDA MALL"
    M14 = "INOX LIDO MALL"
    M309 = "INOX MEGAPLEX MALL OF ASIA"
    M261 = "INOX GARUDA YELAHANKA"
    M385 = "PVR MSR ELEMENTS MALL"
    M231 = "INOX GALLERIA MALL"
    M510 = "PVR CENTRAL SPIRIT MALL"
    M583 = "INOX M5 ECITY"
    M531 = "PVR BHARTIYA MALL OF BENGALURU"
    M390 = "PVR VR BENGALURU"
    M512 = "PVR PHOENIX MARKETCITY MALL"
    M208 = "INOX BROOKEFIELD MALL"
    M522 = "PVR AURA PARK SQUARE WHITEFIELD"
    M24 = "INOX NEXUS WHITEFIELD"
    M282 = "INOX SBR HORIZON"
    M528 = "PVR ORION UPTOWN"
    # PVR_GLOBAL_MALL = "534"
    # PVR_GT_WORLD_MALL = "519"
    # PVR_SUPERPLEX_FORUM_MALL = "533"
    # PVR_ORION_MALL = "511"
    # PVR_VAISHNAVI_SAPPHIRE_MALL = "391"
    # INOX_MANTRI_SQUARE = "148"
    # INOX_SHREE_GARUDA_SWAGATH_MALL = "127"
    # INOX_CENTRAL = "150"
    # PVR_VEGA_CITY = "520"
    # PVR_NEXUS = "507"
    # PVR_DIRECTORS_CUT_FORUM_REX_WALK = "529"
    # INOX_GARUDA_MALL = "110"
    # INOX_LIDO_MALL = "14"
    # INOX_MEGAPLEX_MALL_OF_ASIA = "309"
    # INOX_GARUDA_YELAHANKA = "261"
    # PVR_MSR_ELEMENTS_MALL = "385"
    # INOX_GALLERIA_MALL = "231"
    # PVR_CENTRAL_SPIRIT_MALL = "510"
    # INOX_M5_ECITY = "583"
    # PVR_BHARTIYA_MALL_OF_BENGALURU = "531"
    # PVR_VR_BENGALURU = "390"
    # PVR_PHOENIX_MARKETCITY_MALL = "512"
    # INOX_BROOKEFIELD_MALL = "208"
    # PVR_AURA_PARK_SQUARE_WHITEFIELD = "522"
    # INOX_NEXUS_WHITEFIELD = "24"
    # INOX_SBR_HORIZON = "282"
    # PVR_ORION_UPTOWN = "528"

    @classmethod
    def get_default_theater(cls):
        return cls.PVR_SUPERPLEX_FORUM_MALL


class Tags(Enum):
    users = "users"
    movies = "movies"
    monitoring = "monitoring"
    scheduler = "scheduler"


class FormData(BaseModel):
    username: str
    password: str
    model_config = ConfigDict(extra="forbid")


class ShowingType(str, Enum):
    nowshowing = "nowshowing"
    comingsoon = "comingsoon"


class MonitoringDetails(BaseModel):
    movie_id: str
    name: str | None = None
    theater_id: str
    release_date: datetime = datetime.now(tz=ZoneInfo("Asia/Kolkata"))
    expiry_date: datetime | None = None
    imax: bool = False
    job_id: str | None = None
    showtimes: dict | None = {}
    updates: int = 5
    model_config = ConfigDict(alias_generator=to_snake, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def set_expiry_date(cls, values: dict) -> dict:
        """
        Set the expiry date to 1 day after the release date.
        """
        if "expiry_date" not in values or values["expiry_date"] is None:
            values["expiry_date"] = datetime.fromisoformat(
                values["release_date"]
            ) + timedelta(days=1)
        return values


class NotificationPayload(BaseModel):
    payload: dict[str, str]
