"""
RBF interpolation endpoint tests.

Tests basic RBF interpolation functionality using the ferreus_rbf package.
"""

import pytest


class TestRBFInterpolation:
    """Tests for /rbf/interpolate endpoint."""

    def test_simple_2d_interpolation(self, client):
        """Test basic 2D RBF interpolation with 4 corner points forming a plane."""
        # Create a simple plane: z = x + y
        # Corner points: (0,0)=0, (1,0)=1, (0,1)=1, (1,1)=2
        request_data = {
            "training_points": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
            "training_values": [0.0, 1.0, 1.0, 2.0],
            "test_points": [[0.5, 0.5]],
        }

        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert "interpolated_values" in data
        assert len(data["interpolated_values"]) == 1

        # For a plane z = x + y, the value at (0.5, 0.5) should be close to 1.0
        interpolated_value = data["interpolated_values"][0]
        assert abs(interpolated_value - 1.0) < 0.1, f"Expected ~1.0, got {interpolated_value}"

    def test_multiple_test_points(self, client):
        """Test interpolation at multiple test points simultaneously."""
        request_data = {
            "training_points": [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
            "training_values": [0.0, 1.0, 1.0, 2.0],
            "test_points": [[0.5, 0.5], [0.25, 0.25], [0.75, 0.75]],
        }

        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert len(data["interpolated_values"]) == 3

        # All values should be reasonable for z = x + y
        for value in data["interpolated_values"]:
            assert 0.0 <= value <= 2.0

    def test_exact_interpolation_at_training_points(self, client):
        """RBF should exactly reproduce training values at training point locations."""
        training_points = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        training_values = [0.0, 1.0, 1.0, 2.0]

        request_data = {
            "training_points": training_points,
            "training_values": training_values,
            "test_points": training_points,  # Test at same locations
        }

        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 200

        data = response.json()
        interpolated = data["interpolated_values"]

        # Should match training values closely (within numerical precision)
        for i, expected in enumerate(training_values):
            assert abs(interpolated[i] - expected) < 1e-6, \
                f"Point {i}: expected {expected}, got {interpolated[i]}"

    def test_mismatched_training_dimensions_returns_error(self, client):
        """Training points and values must have matching counts."""
        request_data = {
            "training_points": [[0.0, 0.0], [1.0, 0.0]],
            "training_values": [0.0, 1.0, 2.0],  # Too many values
            "test_points": [[0.5, 0.5]],
        }

        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 422 or response.status_code == 500

    def test_dimensional_mismatch_returns_error(self, client):
        """Training and test points must have same dimensionality."""
        request_data = {
            "training_points": [[0.0, 0.0], [1.0, 0.0]],  # 2D
            "training_values": [0.0, 1.0],
            "test_points": [[0.5, 0.5, 0.5]],  # 3D - wrong!
        }

        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 422 or response.status_code == 500

    def test_endpoint_accessible_without_auth(self, client):
        """RBF endpoint should be public (no authentication required)."""
        request_data = {
            "training_points": [[0.0, 0.0], [1.0, 1.0]],
            "training_values": [0.0, 1.0],
            "test_points": [[0.5, 0.5]],
        }

        # No Authorization header
        response = client.post("/rbf/interpolate", json=request_data)
        assert response.status_code == 200


class TestRBFCoefficientsEndpoint:
    """Tests for /rbf/coefficients endpoint (authenticated)."""

    def test_coefficients_requires_auth(self, client):
        """Endpoint should return 401 when no JWT is provided."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            ],
            "fitting_accuracy": 0.01,
        }

        # No Authorization header
        response = client.post("/rbf/coefficients", json=request_data)
        assert response.status_code == 401

    def test_coefficients_rejects_expired_token(self, client, expired_jwt):
        """Endpoint should return 401 for expired JWT."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            ],
        }

        response = client.post(
            "/rbf/coefficients",
            json=request_data,
            headers={"Authorization": f"Bearer {expired_jwt}"},
        )
        assert response.status_code == 401

    def test_coefficients_with_valid_auth(self, client, valid_jwt):
        """Returns coefficients when valid JWT is provided."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
                {"x": 0.0, "y": 1.0, "z": 0.0, "value": 1.0},
                {"x": 1.0, "y": 1.0, "z": 0.0, "value": 2.0},
            ],
            "fitting_accuracy": 0.01,
        }

        response = client.post(
            "/rbf/coefficients",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        # Verify response structure
        assert "source_points" in data
        assert "point_coefficients" in data
        assert "kernel_type" in data
        assert "extents" in data

        # Verify kernel type
        assert data["kernel_type"] == "linear"

        # Verify we have coefficients for each source point
        assert len(data["source_points"]) == len(data["point_coefficients"])

        # Verify extents is [min_x, min_y, min_z, max_x, max_y, max_z]
        assert len(data["extents"]) == 6

    def test_coefficients_with_3d_spatial_data(self, client, valid_jwt):
        """Test with realistic 3D geological coordinates."""
        request_data = {
            "intervals": [
                {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
                {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0},
                {"x": 500000.0, "y": 4501000.0, "z": 150.0, "value": 1.0},
                {"x": 501000.0, "y": 4501000.0, "z": 150.0, "value": 2.0},
            ],
            "fitting_accuracy": 0.01,
        }

        response = client.post(
            "/rbf/coefficients",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["source_points"]) == 4
        assert len(data["extents"]) == 6

        # Check extents match input bounds
        assert data["extents"][0] == 500000.0  # min_x
        assert data["extents"][3] == 501000.0  # max_x

    def test_coefficients_rejects_empty_intervals(self, client, valid_jwt):
        """Endpoint should return 422 for empty intervals."""
        request_data = {
            "intervals": [],
            "fitting_accuracy": 0.01,
        }

        response = client.post(
            "/rbf/coefficients",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        # Pydantic validation error for min_length=1
        assert response.status_code == 422

    def test_coefficients_with_custom_fitting_accuracy(self, client, valid_jwt):
        """Test custom fitting_accuracy parameter."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
                {"x": 0.0, "y": 1.0, "z": 0.0, "value": 1.0},
            ],
            "fitting_accuracy": 0.001,  # Higher accuracy
        }

        response = client.post(
            "/rbf/coefficients",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200


class TestRBFEvaluateEndpoint:
    """Tests for /rbf/evaluate endpoint (authenticated)."""

    def test_evaluate_requires_auth(self, client):
        """Endpoint should return 401 when no JWT is provided."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            ],
            "query_points": [
                {"x": 0.5, "y": 0.0, "z": 0.0},
            ],
        }

        # No Authorization header
        response = client.post("/rbf/evaluate", json=request_data)
        assert response.status_code == 401

    def test_evaluate_rejects_expired_token(self, client, expired_jwt):
        """Endpoint should return 401 for expired JWT."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            ],
            "query_points": [
                {"x": 0.5, "y": 0.0, "z": 0.0},
            ],
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {expired_jwt}"},
        )
        assert response.status_code == 401

    def test_evaluate_with_valid_auth(self, client, valid_jwt):
        """Returns interpolated values when valid JWT is provided."""
        # Create a simple plane: value = x + y
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
                {"x": 0.0, "y": 1.0, "z": 0.0, "value": 1.0},
                {"x": 1.0, "y": 1.0, "z": 0.0, "value": 2.0},
            ],
            "query_points": [
                {"x": 0.5, "y": 0.5, "z": 0.0},
            ],
            "fitting_accuracy": 0.01,
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert "values" in data
        assert "extents" in data

        # Should have one value for one query point
        assert len(data["values"]) == 1

        # For plane value = x + y, at (0.5, 0.5) should be close to 1.0
        interpolated_value = data["values"][0]
        assert abs(interpolated_value - 1.0) < 0.1

    def test_evaluate_multiple_query_points(self, client, valid_jwt):
        """Test evaluation at multiple query points."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
                {"x": 0.0, "y": 1.0, "z": 0.0, "value": 1.0},
                {"x": 1.0, "y": 1.0, "z": 0.0, "value": 2.0},
            ],
            "query_points": [
                {"x": 0.5, "y": 0.5, "z": 0.0},
                {"x": 0.25, "y": 0.25, "z": 0.0},
                {"x": 0.75, "y": 0.75, "z": 0.0},
            ],
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["values"]) == 3

        # All values should be reasonable for value = x + y
        for value in data["values"]:
            assert 0.0 <= value <= 2.0

    def test_evaluate_with_3d_spatial_data(self, client, valid_jwt):
        """Test with realistic 3D geological coordinates."""
        request_data = {
            "intervals": [
                {"x": 500000.0, "y": 4500000.0, "z": 100.0, "value": 0.0},
                {"x": 501000.0, "y": 4500000.0, "z": 100.0, "value": 1.0},
                {"x": 500000.0, "y": 4501000.0, "z": 150.0, "value": 1.0},
                {"x": 501000.0, "y": 4501000.0, "z": 150.0, "value": 2.0},
            ],
            "query_points": [
                {"x": 500500.0, "y": 4500500.0, "z": 125.0},
            ],
            "fitting_accuracy": 0.01,
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert len(data["values"]) == 1
        assert len(data["extents"]) == 6

    def test_evaluate_rejects_empty_intervals(self, client, valid_jwt):
        """Endpoint should return 422 for empty intervals."""
        request_data = {
            "intervals": [],
            "query_points": [
                {"x": 0.5, "y": 0.5, "z": 0.0},
            ],
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 422

    def test_evaluate_rejects_empty_query_points(self, client, valid_jwt):
        """Endpoint should return 422 for empty query points."""
        request_data = {
            "intervals": [
                {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
                {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            ],
            "query_points": [],
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 422

    def test_evaluate_exact_at_training_points(self, client, valid_jwt):
        """RBF should exactly reproduce training values at training point locations."""
        intervals = [
            {"x": 0.0, "y": 0.0, "z": 0.0, "value": 0.0},
            {"x": 1.0, "y": 0.0, "z": 0.0, "value": 1.0},
            {"x": 0.0, "y": 1.0, "z": 0.0, "value": 1.0},
            {"x": 1.0, "y": 1.0, "z": 0.0, "value": 2.0},
        ]

        # Query at the same locations as training data
        query_points = [
            {"x": interval["x"], "y": interval["y"], "z": interval["z"]}
            for interval in intervals
        ]

        request_data = {
            "intervals": intervals,
            "query_points": query_points,
        }

        response = client.post(
            "/rbf/evaluate",
            json=request_data,
            headers={"Authorization": f"Bearer {valid_jwt}"},
        )
        assert response.status_code == 200

        data = response.json()
        interpolated = data["values"]

        # Should match training values closely (within numerical precision)
        for i, interval in enumerate(intervals):
            expected = interval["value"]
            assert abs(interpolated[i] - expected) < 1e-6, \
                f"Point {i}: expected {expected}, got {interpolated[i]}"
