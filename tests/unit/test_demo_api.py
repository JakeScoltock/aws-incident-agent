from unittest.mock import patch

from services.demo_api.handler import lambda_handler


def test_health_path():
    event = {"rawPath": "/health"}
    result = lambda_handler(event, None)
    assert result["statusCode"] == 200
    assert "ok" in result["body"]


def test_default_path():
    event = {"rawPath": "/"}
    result = lambda_handler(event, None)
    assert result["statusCode"] == 200


def test_slow_path_sleeps():
    event = {"rawPath": "/slow"}
    with patch("services.demo_api.handler.time.sleep") as mock_sleep:
        result = lambda_handler(event, None)
    mock_sleep.assert_called_once_with(28)
    assert result["statusCode"] == 200
