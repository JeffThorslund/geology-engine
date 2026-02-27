"""
Service layer for RBF interpolation operations.

Handles the business logic for fitting RBF models, extracting coefficients,
and evaluating at query points. Implements proper file management with
context managers for temporary files.
"""

import json
import logging
import os
import tempfile
from typing import Any

import numpy as np
from ferreus_rbf import RBFInterpolator
from ferreus_rbf.interpolant_config import (
    FittingAccuracy,
    FittingAccuracyType,
    InterpolantSettings,
    RBFKernelType,
)

from app.rbf_models import QueryPoint, SpatialInterval

logger = logging.getLogger(__name__)


def fit_rbf_from_intervals(
    intervals: list[SpatialInterval],
    fitting_accuracy: float = 0.01,
) -> tuple[RBFInterpolator, np.ndarray]:
    """
    Fit an RBF model from spatial intervals.

    Args:
        intervals: List of 3D spatial points with commodity values
        fitting_accuracy: Desired absolute fitting accuracy

    Returns:
        Tuple of (fitted RBFInterpolator, extents array)
        extents: [min_x, min_y, min_z, max_x, max_y, max_z]

    Raises:
        ValueError: If intervals list is empty
    """
    if not intervals:
        raise ValueError("At least one interval is required")

    # Extract source points and values from intervals
    source_points = np.array(
        [[interval.x, interval.y, interval.z] for interval in intervals],
        dtype=np.float64,
    )
    source_values = np.array(
        [[interval.value] for interval in intervals],
        dtype=np.float64,
    )

    # Calculate axis-aligned bounding box extents
    extents = np.concatenate(
        (
            np.floor(np.min(source_points, axis=0)),
            np.ceil(np.max(source_points, axis=0)),
        )
    )

    # Use Linear kernel (as specified in example code)
    kernel_type = RBFKernelType.Linear

    # Configure fitting accuracy
    accuracy = FittingAccuracy(fitting_accuracy, FittingAccuracyType.Absolute)

    # Initialize interpolant settings
    settings = InterpolantSettings(kernel_type, fitting_accuracy=accuracy)

    # Fit the RBF model
    logger.info(
        f"Fitting RBF with {len(intervals)} intervals, "
        f"fitting_accuracy={fitting_accuracy}"
    )
    rbf_interpolator = RBFInterpolator(source_points, source_values, settings)

    return rbf_interpolator, extents


def extract_coefficients(rbf_interpolator: RBFInterpolator) -> dict[str, Any]:
    """
    Extract RBF model coefficients by saving to temporary file and parsing JSON.

    Uses proper file management with try/finally to ensure cleanup.

    Args:
        rbf_interpolator: Fitted RBF interpolator instance

    Returns:
        Dictionary containing model coefficients and metadata

    Raises:
        RuntimeError: If model save/load fails
    """
    # Create temporary file (delete=False so we can read it after closing)
    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".json",
        delete=False,
    )
    temp_path = temp_file.name

    try:
        # Close the file so ferreus_rbf can write to it
        temp_file.close()

        # Save the RBF model to JSON
        logger.debug(f"Saving RBF model to temporary file: {temp_path}")
        rbf_interpolator.save_model(temp_path)

        # Read and parse the JSON file
        with open(temp_path, "r") as f:
            model_data = json.load(f)

        logger.debug("Successfully extracted coefficients from RBF model")
        return model_data

    finally:
        # Guaranteed cleanup - remove temp file even if errors occur
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug(f"Cleaned up temporary file: {temp_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temporary file {temp_path}: {e}")


def evaluate_at_query_points(
    intervals: list[SpatialInterval],
    query_points: list[QueryPoint],
    fitting_accuracy: float = 0.01,
) -> tuple[list[float], np.ndarray]:
    """
    Fit RBF model from intervals and evaluate at query points.

    Args:
        intervals: Training data (3D spatial points with commodity values)
        query_points: Points where RBF should be evaluated
        fitting_accuracy: Desired absolute fitting accuracy

    Returns:
        Tuple of (evaluated values list, extents array)

    Raises:
        ValueError: If intervals or query_points are empty
    """
    if not intervals:
        raise ValueError("At least one interval is required")
    if not query_points:
        raise ValueError("At least one query point is required")

    # Fit the RBF model
    rbf_interpolator, extents = fit_rbf_from_intervals(intervals, fitting_accuracy)

    # Convert query points to numpy array
    query_array = np.array(
        [[point.x, point.y, point.z] for point in query_points],
        dtype=np.float64,
    )

    # Evaluate RBF at query points
    logger.info(f"Evaluating RBF at {len(query_points)} query points")
    interpolated = rbf_interpolator.evaluate(query_array)

    # Extract values from 2D array (N x 1) to 1D list
    if interpolated.ndim == 2:
        values = interpolated[:, 0].tolist()
    else:
        values = interpolated.tolist()

    return values, extents
