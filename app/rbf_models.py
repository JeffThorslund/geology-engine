"""
Pydantic models for RBF interpolation endpoints.

These models define the request/response schemas for geological RBF operations
using 3D spatial coordinates (x, y, z) and commodity values.
"""

from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class SpatialInterval(BaseModel):
    """A 3D spatial point with an associated commodity value (signed distance)."""

    x: float = Field(..., description="UTM easting in meters")
    y: float = Field(..., description="UTM northing in meters")
    z: float = Field(..., description="Elevation in meters above sea level")
    value: float = Field(..., description="Commodity value (signed distance)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "x": 500000.0,
                "y": 4500000.0,
                "z": 100.0,
                "value": 1.5,
            }
        }
    )


class QueryPoint(BaseModel):
    """A 3D point where RBF interpolation should be evaluated."""

    x: float = Field(..., description="UTM easting in meters")
    y: float = Field(..., description="UTM northing in meters")
    z: float = Field(..., description="Elevation in meters above sea level")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "x": 500500.0,
                "y": 4500500.0,
                "z": 150.0,
            }
        }
    )


class RBFCoefficientsRequest(BaseModel):
    """Request to fit RBF model and return coefficients for client-side evaluation."""

    intervals: list[SpatialInterval] = Field(
        ...,
        description="Training data: 3D spatial points with commodity values",
        min_length=1,
    )
    fitting_accuracy: Optional[float] = Field(
        default=0.01,
        description="Desired absolute fitting accuracy for RBF approximation",
        gt=0.0,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intervals": [
                    {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
                    {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0},
                    {"x": 500000.0, "y": 4501000.0, "z": 100.0, "value": 1.0},
                    {"x": 501000.0, "y": 4501000.0, "z": 100.0, "value": 2.0},
                ],
                "fitting_accuracy": 0.01,
            }
        }
    )


class RBFCoefficientsResponse(BaseModel):
    """RBF model coefficients for client-side evaluation.

    The client can use these coefficients to reconstruct the RBF function
    without needing to send evaluation requests to the server.
    """

    source_points: list[list[float]] = Field(
        ..., description="N x 3 array of source point coordinates (after transformation)"
    )
    point_coefficients: list[list[float]] = Field(
        ..., description="N x 1 array of RBF coefficients for each source point"
    )
    poly_coefficients: Optional[list[list[float]]] = Field(
        None, description="Polynomial coefficients (if polynomial augmentation is used)"
    )
    kernel_type: str = Field(..., description="RBF kernel type (e.g., 'linear')")
    polynomial_degree: int = Field(..., description="Degree of polynomial augmentation")
    nugget: float = Field(..., description="Nugget value for regularization")
    translation_factor: list[float] = Field(
        ..., description="Translation applied to input points before fitting"
    )
    scale_factor: list[float] = Field(
        ..., description="Scaling applied to input points before fitting"
    )
    extents: list[float] = Field(
        ...,
        description="Axis-aligned bounding box of source points [min_x, min_y, min_z, max_x, max_y, max_z]",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source_points": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                "point_coefficients": [[0.5], [0.5]],
                "poly_coefficients": None,
                "kernel_type": "linear",
                "polynomial_degree": 0,
                "nugget": 0.0,
                "translation_factor": [0.0, 0.0, 0.0],
                "scale_factor": [1.0, 1.0, 1.0],
                "extents": [0.0, 0.0, 0.0, 1.0, 1.0, 1.0],
            }
        }
    )


class RBFEvaluateRequest(BaseModel):
    """Request to fit RBF model and evaluate at query points."""

    intervals: list[SpatialInterval] = Field(
        ...,
        description="Training data: 3D spatial points with commodity values",
        min_length=1,
    )
    query_points: list[QueryPoint] = Field(
        ...,
        description="3D points where RBF should be evaluated",
        min_length=1,
    )
    fitting_accuracy: Optional[float] = Field(
        default=0.01,
        description="Desired absolute fitting accuracy for RBF approximation",
        gt=0.0,
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "intervals": [
                    {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
                    {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0},
                    {"x": 500000.0, "y": 4501000.0, "z": 100.0, "value": 1.0},
                    {"x": 501000.0, "y": 4501000.0, "z": 100.0, "value": 2.0},
                ],
                "query_points": [
                    {"x": 500500.0, "y": 4500500.0, "z": 100.0},
                    {"x": 500250.0, "y": 4500250.0, "z": 100.0},
                ],
                "fitting_accuracy": 0.01,
            }
        }
    )


class RBFEvaluateResponse(BaseModel):
    """RBF evaluation results at query points."""

    values: list[float] = Field(
        ..., description="Interpolated commodity values at each query point"
    )
    extents: list[float] = Field(
        ...,
        description="Axis-aligned bounding box of training points [min_x, min_y, min_z, max_x, max_y, max_z]",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "values": [1.0, 0.5],
                "extents": [500000.0, 4500000.0, 100.0, 501000.0, 4501000.0, 100.0],
            }
        }
    )
