"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)

@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        key: {
            "description": value["description"],
            "schedule": value["schedule"],
            "max_participants": value["max_participants"],
            "participants": value["participants"].copy()
        }
        for key, value in activities.items()
    }
    yield
    # Restore original state after test
    for key, value in original_activities.items():
        activities[key]["participants"] = value["participants"]


def test_root_redirect(client):
    """Test that root path redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client, reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Basketball" in data
    assert "Soccer" in data
    assert "Chess Club" in data
    assert "Gym Class" in data
    
    # Verify activity structure
    basketball = data["Basketball"]
    assert "description" in basketball
    assert "schedule" in basketball
    assert "max_participants" in basketball
    assert "participants" in basketball
    assert isinstance(basketball["participants"], list)


def test_signup_for_activity(client, reset_activities):
    """Test signing up a student for an activity"""
    response = client.post(
        "/activities/Basketball/signup?email=newstudent@mergington.edu"
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    
    # Verify the student was added
    assert "newstudent@mergington.edu" in activities["Basketball"]["participants"]


def test_signup_for_nonexistent_activity(client, reset_activities):
    """Test signing up for an activity that doesn't exist"""
    response = client.post(
        "/activities/NonexistentActivity/signup?email=student@mergington.edu"
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_duplicate_student(client, reset_activities):
    """Test that a student can't sign up twice for the same activity"""
    # First signup
    response1 = client.post(
        "/activities/Basketball/signup?email=duplicate@mergington.edu"
    )
    assert response1.status_code == 200
    
    # Try to sign up again
    response2 = client.post(
        "/activities/Basketball/signup?email=duplicate@mergington.edu"
    )
    assert response2.status_code == 400
    assert "already signed up" in response2.json()["detail"].lower()


def test_unregister_from_activity(client, reset_activities):
    """Test unregistering a student from an activity"""
    # First, add a student
    client.post("/activities/Soccer/signup?email=temp@mergington.edu")
    
    # Then remove them
    response = client.delete(
        "/activities/Soccer/unregister?email=temp@mergington.edu"
    )
    assert response.status_code == 200
    assert "temp@mergington.edu" in response.json()["message"]
    
    # Verify they were removed
    assert "temp@mergington.edu" not in activities["Soccer"]["participants"]


def test_unregister_nonexistent_activity(client, reset_activities):
    """Test unregistering from an activity that doesn't exist"""
    response = client.delete(
        "/activities/NonexistentActivity/unregister?email=student@mergington.edu"
    )
    assert response.status_code == 404


def test_unregister_nonexistent_student(client, reset_activities):
    """Test unregistering a student who isn't signed up"""
    response = client.delete(
        "/activities/Basketball/unregister?email=notstudent@mergington.edu"
    )
    assert response.status_code == 400
    assert "not signed up" in response.json()["detail"].lower()


def test_unregister_existing_participant(client, reset_activities):
    """Test unregistering an existing participant"""
    # Basketball has alex@mergington.edu as a participant
    response = client.delete(
        "/activities/Basketball/unregister?email=alex@mergington.edu"
    )
    assert response.status_code == 200
    assert "alex@mergington.edu" not in activities["Basketball"]["participants"]
