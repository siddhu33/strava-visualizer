import io

from unittest.mock import patch

import pytest
from PIL import Image

from main import (
    _elapsed_str,
    auto_text_color,
    get_activities,
    heart_rate_chart,
    image_from_activity_data,
    metres_per_beat_chart,
    pace_chart,
    select_random_color_palette,
)


@pytest.fixture
def mock_requests_get():
    with patch("requests.get") as mock:
        yield mock


@pytest.fixture
def mock_image_new():
    with patch("src.main.Image.new") as mock:
        yield mock


@pytest.fixture
def mock_image_from_activity_data():
    with patch("src.main.image_from_activity_data") as mock:
        yield mock


def test_get_activities(mock_requests_get):
    # Replace with sample data for testing
    mock_response = [{"start_date": "2022-01-01", "average_heartrate": 150}]
    mock_requests_get.return_value.json.return_value = mock_response

    # Mocking the token data
    token_data = {"access_token": "mock_access_token"}

    result = get_activities(token_data)

    assert result == mock_response


def test_heart_rate_chart():
    # Replace with sample data for testing
    activity_data = [
        {"start_date": "2022-01-01", "distance": 5000, "average_heartrate": 150}
    ]
    chart_shape = (800, 480)
    colors = ("#2d1b64", "#ffff00")

    result = heart_rate_chart(activity_data, chart_shape, colors, 1)

    assert isinstance(result, Image.Image)


def test_pace_chart():
    # Replace with sample data for testing
    activity_data = [{"start_date": "2022-01-01", "distance": 5000, "average_speed": 5}]
    chart_shape = (800, 480)
    colors = ("#2d1b64", "#ffff00")

    result = pace_chart(activity_data, chart_shape, colors, 2)

    assert isinstance(result, Image.Image)


def test_metres_per_beat_chart():
    # Replace with sample data for testing
    activity_data = [
        {
            "start_date": "2022-01-01",
            "distance": 5000,
            "average_speed": 5,
            "average_heartrate": 180,
        }
    ]
    chart_shape = (800, 480)
    colors = ("#2d1b64", "#ffff00")

    result = metres_per_beat_chart(activity_data, chart_shape, colors, 3)

    assert isinstance(result, Image.Image)


def test__elapsed_str():
    num_seconds = 3660  # 1 hour and 1 minute

    result = _elapsed_str(num_seconds)

    assert result == "1 hour and 1 minute"


def test_auto_text_color():
    primary_color = "#2d1b64"

    result = auto_text_color(primary_color)

    assert result == "#ffffff"


def test_select_random_color_palette():
    p, s = select_random_color_palette()
    assert isinstance(p, str)
    assert isinstance(s, str)


def test_image_from_activity_data():
    open_file = io.BytesIO()
    image_from_activity_data(
        [
            {
                "start_date": "2022-01-01",
                "start_date_local": "2022-01-01",
                "name": "Test Run",
                "elapsed_time": 1800,
                "distance": 5000,
                "average_speed": 5,
                "average_heartrate": 180,
            }
        ],
        1,
        open_file,
        (800, 480),
        ("#ff0000", "#0000ff"),
    )
    assert open_file.getbuffer().nbytes > 0
