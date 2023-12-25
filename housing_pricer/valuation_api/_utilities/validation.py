from pydantic import BaseModel


class ApartmentData(BaseModel):
    construction_year: int
    living_area: float
    latitude: float
    longitude: float
