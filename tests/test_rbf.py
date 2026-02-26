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
