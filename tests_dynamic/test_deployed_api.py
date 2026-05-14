import requests

BASE_URL = "http://127.0.0.1:5001"

def test_api_is_running():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200

def test_unauthenticated_user_cannot_access_profile():
    response = requests.get(f"{BASE_URL}/students/1001/profile")
    assert response.status_code in (401, 403)

def test_student_cannot_access_another_student_profile():
    session = requests.Session()
    login_response = requests.session.post(
    f"{BASE_URL}/login",
    data={"username": "alice", "password": "alicepw"},
    )
    assert login_response.status_code == 200
    response = requests.session.get(f"{BASE_URL}/students/1002/profile")
    assert response.status_code == 403

def test_student_cannot_update_grades():
    session = requests.Session()
    login_response = session.post(
    f"{BASE_URL}/login",

    data={"username": "alice", "password": "alicepw"},
    )
    
    assert login_response.status_code == 200
    response = session.post(
    f"{BASE_URL}/grades/update",
    json={"student_id": 1001, "course_id": "SRS", "grade": 20},
    )
    assert response.status_code in (401, 403)


def test_malicious_file_path_rejected():
    
    response = requests.get(
        f"{BASE_URL}/files",
        params={"path": "../../etc/passwd"},
    )
    assert response.status_code in (400, 401, 403, 404)