import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import SupabaseUser, get_supabase_user
from ferreus_rbf import RBFInterpolator
from ferreus_rbf.interpolant_config import InterpolantSettings, RBFKernelType

app = FastAPI(
    title="geology-engine",
    version="0.1.0",
    description="FastAPI service for geological data processing and RBF interpolation",
)


class RootResponse(BaseModel):
    """Response model for root endpoint."""

    service: str = Field(..., description="Name of the service")
    docs: str = Field(..., description="URL path to interactive API documentation")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str = Field(..., description="Health status of the service")
    service: str = Field(..., description="Name of the service")


class UserResponse(BaseModel):
    """Response model for authenticated user endpoint."""

    user_id: str = Field(..., description="Unique identifier for the authenticated user")
    email: str | None = Field(None, description="Email address of the authenticated user")
    role: str | None = Field(None, description="Role of the authenticated user")


class RBFRequest(BaseModel):
    """Request model for RBF interpolation."""

    training_points: list[list[float]] = Field(
        ...,
        description="N x D array of training point coordinates (e.g., [[x1, y1], [x2, y2], ...])",
    )
    training_values: list[float] = Field(
        ...,
        description="N values corresponding to each training point",
    )
    test_points: list[list[float]] = Field(
        ...,
        description="M x D array of test point coordinates where values should be interpolated",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "training_points": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
                "training_values": [0.0, 1.0, 1.0, 2.0],
                "test_points": [[0.5, 0.5]],
            }
        }
    )


class RBFResponse(BaseModel):
    """Response model for RBF interpolation."""

    interpolated_values: list[float] = Field(
        ...,
        description="M interpolated values at the test point locations",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "interpolated_values": [1.0],
            }
        }
    )


@app.get("/", response_model=RootResponse)
async def root():
    """Root endpoint returning service information and documentation link."""
    return {"service": "geology-engine", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health():
    """Health check endpoint to verify service is running."""
    return {"status": "ok", "service": "geology-engine"}


@app.get("/me", response_model=UserResponse)
async def me(user: SupabaseUser = Depends(get_supabase_user)):
    """Return the authenticated user's identity (requires valid Supabase JWT)."""
    return {"user_id": user.id, "email": user.email, "role": user.role}


@app.post("/rbf/interpolate", response_model=RBFResponse)
async def rbf_interpolate(request: RBFRequest):
    """
    Perform RBF interpolation on scattered data.

    Takes training points with known values and returns interpolated values
    at test points using Linear RBF kernel.

    Example:
        Training: points=[[0,0], [1,0], [0,1], [1,1]], values=[0, 1, 1, 2]
        Test: [[0.5, 0.5]]
        Result: Interpolated value at (0.5, 0.5)
    """
    # Convert to numpy arrays
    training_points = np.array(request.training_points, dtype=np.float64)
    test_points = np.array(request.test_points, dtype=np.float64)

    # Validate input dimensions (before reshaping values)
    if training_points.shape[0] != len(request.training_values):
        raise HTTPException(
            status_code=422,
            detail="Number of training points must match number of training values"
        )

    if training_points.shape[1] != test_points.shape[1]:
        raise HTTPException(
            status_code=422,
            detail="Training and test points must have same dimensionality"
        )

    # Reshape training values to 2D (required by ferreus_rbf)
    training_values = np.array(request.training_values, dtype=np.float64).reshape(-1, 1)

    # Configure RBF interpolator with Linear kernel
    settings = InterpolantSettings(RBFKernelType.Linear)

    # Create and train interpolator
    rbf = RBFInterpolator(training_points, training_values, settings)

    # Evaluate at test points
    interpolated = rbf.evaluate(test_points)

    # Extract values (interpolated is N x 1, we want just the values)
    if interpolated.ndim == 2:
        values = interpolated[:, 0].tolist()
    else:
        values = interpolated.tolist()

    return RBFResponse(interpolated_values=values)
