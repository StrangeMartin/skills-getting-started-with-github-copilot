"""
Tests for the FastAPI application
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    activities.clear()
    activities.update(original_activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_root_redirect():
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert "Gym Class" in data
    assert len(data) == 3


def test_get_activities_has_required_fields(reset_activities):
    """Test that activities have required fields"""
    response = client.get("/activities")
    data = response.json()
    activity = data["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity
    assert isinstance(activity["participants"], list)


def test_signup_for_activity(reset_activities):
    """Test signing up a student for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]

    # Verify the student was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(reset_activities):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Club/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_remove_participant(reset_activities):
    """Test removing a participant from an activity"""
    response = client.post(
        "/activities/Chess%20Club/remove?email=michael@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "michael@mergington.edu" in data["message"]
    assert "Chess Club" in data["message"]

    # Verify the participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]


def test_remove_nonexistent_participant(reset_activities):
    """Test removing a participant that doesn't exist in an activity"""
    response = client.post(
        "/activities/Chess%20Club/remove?email=nonexistent@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Participant not found" in data["detail"]


def test_remove_from_nonexistent_activity(reset_activities):
    """Test removing a participant from an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Club/remove?email=student@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert "Activity not found" in data["detail"]


def test_participant_count_updates(reset_activities):
    """Test that participant counts update correctly"""
    # Get initial count
    response = client.get("/activities")
    initial_count = len(response.json()["Chess Club"]["participants"])

    # Add a participant
    client.post("/activities/Chess%20Club/signup?email=test1@mergington.edu")

    # Check count increased
    response = client.get("/activities")
    new_count = len(response.json()["Chess Club"]["participants"])
    assert new_count == initial_count + 1

    # Remove a participant
    client.post("/activities/Chess%20Club/remove?email=test1@mergington.edu")

    # Check count decreased
    response = client.get("/activities")
    final_count = len(response.json()["Chess Club"]["participants"])
    assert final_count == initial_count
