from pydantic import BaseModel


class NotificationsResult(BaseModel):
    id: str
    time: int
    expires: int
    event: str
    topic: str
    message: str
