from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


# init constructor not required for pydantic models, as they automatically generate one based on the defined fields.
class Result(BaseModel):
    status_code: int
    message: str
    data: dict | None


class MoviesShowing(BaseModel):
    id: str
    n: str
    releaseDate: datetime
    imax: bool
    model_config = ConfigDict(extra="ignore")  # Ignore extra fields in the model

    @field_validator("releaseDate", mode="before")
    @classmethod
    def parse_release_date(cls, value):
        if isinstance(value, str):
            return datetime.strptime(value, "%b %d, %Y")
        return value


class MovieRe(BaseModel):
    id: int
    n: str
    model_config = ConfigDict(extra="ignore")  # Ignore extra fields in the model


class Show(BaseModel):
    theatreId: int
    movieId: int
    showDate: datetime
    showTime: str
    endTime: str
    language: str
    model_config = ConfigDict(extra="ignore")  # Ignore extra fields in the model


class ExperienceSession(BaseModel):
    experience: str
    shows: list[Show]
    model_config = ConfigDict(extra="ignore")  # Ignore extra fields in the model

    @field_validator("experience", mode="before")
    @classmethod
    def replace_empty_experience(cls, value):
        if not value:
            return "Classic"  # Replace empty string with "Classic"
        return value


class CinemaMovieSession(BaseModel):
    movieRe: MovieRe
    showCount: int
    experienceSessions: list[ExperienceSession]
    model_config = ConfigDict(extra="ignore")  # Ignore extra fields in the model


class Showtime(BaseModel):
    shows: dict[str, list[str]]
