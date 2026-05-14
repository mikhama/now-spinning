from pydantic import BaseModel


class Track(BaseModel):
    title: str
    artist: str | None = None
    duration: str


class Side(BaseModel):
    id: str
    tracks: list[Track]


class Record(BaseModel):
    id: str
    release_id: str
    master_id: str
    title: str
    artist: str
    cover_image: str
    linked: bool
    sides: list[Side]


class Stylus(BaseModel):
    id: str
    name: str
    hours: float
    capacity_min: float
    capacity_max: float
