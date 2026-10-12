from fastapi import APIRouter

from backend.models import ShowingType, Tags
from peeweare.models import MoviesShowing

from ..dependencies import bg_assets

router = APIRouter(prefix="/movies/lists", tags=[Tags.lists])


# list
@router.get("/{showing_type}", summary="Lists Movies Showing")
async def get_movies_showing(showing_type: ShowingType) -> list[MoviesShowing]:
    """
    Get a list of movies based on their showing type.

    Args:
        showing_type (ShowingType): The type of showing (nowshowing or comingsoon).

    Returns:
        list[MoviesShowing]: A list of movies based on their showing type.
    """
    peeweare_api = await bg_assets.peeweare_api
    if showing_type == ShowingType.nowshowing:
        result = await peeweare_api.nowshowing()
        return result
    elif showing_type == ShowingType.comingsoon:
        result = await peeweare_api.comingsoon()
        return result
