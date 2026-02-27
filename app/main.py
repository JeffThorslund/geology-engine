import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.auth import SupabaseUser, get_supabase_user
from app.rbf_models import (
    RBFCoefficientsRequest,
    RBFCoefficientsResponse,
    RBFEvaluateRequest,
    RBFEvaluateResponse,
)
from app.rbf_service import (
    evaluate_at_query_points,
    extract_coefficients,
    fit_rbf_from_intervals,
)
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


@app.get("/health/auth", response_model=HealthResponse)
async def health_auth(user: SupabaseUser = Depends(get_supabase_user)):
    """
    Authenticated health check endpoint.

    Verifies that both the service is running AND authentication is working.
    Requires a valid Supabase JWT. Useful for testing that auth is configured correctly.
    """
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


@app.post("/rbf/coefficients", response_model=RBFCoefficientsResponse)
async def rbf_coefficients(
    request: RBFCoefficientsRequest,
    user: SupabaseUser = Depends(get_supabase_user),
):
    """
    Fit RBF model from spatial intervals and return coefficients.

    Returns the RBF function coefficients for client-side evaluation.
    This is more compact than sending pre-rendered geometry and allows
    the client to evaluate the function at arbitrary points locally.

    Requires authentication via Supabase JWT.

    Example:
        Input: 3D spatial intervals with commodity values
        Output: Model coefficients, source points, kernel config, extents
    """
    try:
        # Fit RBF model from intervals
        rbf_interpolator, extents = fit_rbf_from_intervals(
            request.intervals,
            request.fitting_accuracy,
        )

        # Extract coefficients from the fitted model
        model_data = extract_coefficients(rbf_interpolator)

        # Build response from extracted model data
        # Note: ferreus_rbf saves arrays as dicts with 'data' field (flat array)
        def extract_array(array_dict):
            """Extract and reshape list from ferreus_rbf array dict format."""
            if isinstance(array_dict, dict) and "data" in array_dict:
                nrows = array_dict.get("nrows", 1)
                ncols = array_dict.get("ncols", 1)
                data = array_dict["data"]

                # Reshape flat array to 2D (always return 2D structure)
                reshaped = []
                for i in range(nrows):
                    row = data[i * ncols : (i + 1) * ncols]
                    reshaped.append(row)
                return reshaped
            return array_dict

        coefficients_data = model_data.get("coefficients", {})

        response_data = {
            "source_points": extract_array(model_data.get("points", [])),
            "point_coefficients": extract_array(
                coefficients_data.get("point_coefficients", [])
            ),
            "poly_coefficients": extract_array(
                coefficients_data.get("poly_coefficients", None)
            ),
            "kernel_type": "linear",
            "polynomial_degree": model_data.get("interpolant_settings", {}).get(
                "polynomial_degree", 0
            ),
            "nugget": model_data.get("interpolant_settings", {}).get("nugget", 0.0),
            "translation_factor": extract_array(
                model_data.get("translation_factor", [0.0, 0.0, 0.0])
            ),
            "scale_factor": extract_array(
                model_data.get("scale_factor", [1.0, 1.0, 1.0])
            ),
            "extents": extents.tolist(),
        }

        return RBFCoefficientsResponse(**response_data)

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RBF fitting failed: {str(e)}")


@app.post("/rbf/evaluate", response_model=RBFEvaluateResponse)
async def rbf_evaluate(
    request: RBFEvaluateRequest,
    user: SupabaseUser = Depends(get_supabase_user),
):
    """
    Fit RBF model from spatial intervals and evaluate at query points.

    Performs server-side RBF evaluation. The client sends training data
    (spatial intervals) and query points, and receives interpolated values.

    Requires authentication via Supabase JWT.

    Example:
        Input: 3D spatial intervals + query points
        Output: Interpolated commodity values at query points
    """
    try:
        # Fit RBF and evaluate at query points
        values, extents = evaluate_at_query_points(
            request.intervals,
            request.query_points,
            request.fitting_accuracy,
        )

        return RBFEvaluateResponse(
            values=values,
            extents=extents.tolist(),
        )

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RBF evaluation failed: {str(e)}")
