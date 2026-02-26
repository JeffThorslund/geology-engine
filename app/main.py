import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel

from app.auth import SupabaseUser, get_supabase_user
from ferreus_rbf import RBFInterpolator
from ferreus_rbf.interpolant_config import InterpolantSettings, RBFKernelType

app = FastAPI(title="geology-engine")


class RBFRequest(BaseModel):
    """Request model for RBF interpolation."""

    training_points: list[list[float]]  # N x 2 array of [x, y] coordinates
    training_values: list[float]  # N values corresponding to each point
    test_points: list[list[float]]  # M x 2 array of points to interpolate


class RBFResponse(BaseModel):
    """Response model for RBF interpolation."""

    interpolated_values: list[float]  # M interpolated values


@app.get("/")
async def root():
    return {"service": "geology-engine", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "geology-engine"}


@app.get("/me")
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
