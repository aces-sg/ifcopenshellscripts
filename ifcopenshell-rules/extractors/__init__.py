"""
IFC element extractors for rule checking.

Provides consistent extraction of IFC elements with their properties
and geometry, optimized for rule checking operations.
"""

from .spaces import SpaceExtractor, SpaceData
from .doors import DoorExtractor, DoorData
from .walls import WallExtractor, WallData
from .stairs import StairExtractor, StairData

__all__ = [
    "SpaceExtractor",
    "SpaceData",
    "DoorExtractor",
    "DoorData",
    "WallExtractor",
    "WallData",
    "StairExtractor",
    "StairData",
]
