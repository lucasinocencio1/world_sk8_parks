from pydantic import BaseModel
from typing import Any, Dict, List


class GeoJSONPoint(BaseModel):
    type: str = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    properties: Dict[str, Any]
    geometry: GeoJSONPoint


class GeoJSONFeatureCollection(BaseModel):
    type: str = "FeatureCollection"
    features: List[GeoJSONFeature]