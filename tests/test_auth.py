from fastapi.testclient import TestClient

from src.auth.jwt import decode_access_token
from src.main import app

client = TestClient(app)

INVALID = "Invalid email or password"


def test_login(test_user):
    """Correct credentials return 200 with a bearer token whose sub is the user id."""
    response = client.post("/login", data={"username": "louise@test.com", "password": "louise_pass_1"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert decode_access_token(body["access_token"])["sub"] == test_user["id"]


def test_login_admin(admin_user):
    """The admin logs in like any user and the token carries the admin id."""
    response = client.post("/login", data={"username": "ada@test.com", "password": "ada_pass_123"})
    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"])["sub"] == admin_user["id"]


def test_login_email_case_insensitive(test_user):
    """An email in different capitals logs in the same user."""
    response = client.post("/login", data={"username": "Louise@Test.com", "password": "louise_pass_1"})
    assert response.status_code == 200
    assert decode_access_token(response.json()["access_token"])["sub"] == test_user["id"]


def test_login_wrong_password():
    """A wrong password returns 401 with the generic detail and the Bearer header."""
    response = client.post("/login", data={"username": "louise@test.com", "password": "wrong_pass_1"})
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_login_unknown_email():
    """An unknown email returns the same 401 detail and header as a wrong password."""
    response = client.post("/login", data={"username": "nobody@test.com", "password": "louise_pass_1"})
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_login_missing_username():
    """Login without a username returns 422."""
    response = client.post("/login", data={"password": "louise_pass_1"})
    assert response.status_code == 422


def test_login_missing_password():
    """Login without a password returns 422."""
    response = client.post("/login", data={"username": "louise@test.com"})
    assert response.status_code == 422


def test_login_response_has_only_token_fields():
    """The login response has only access_token and token_type."""
    response = client.post("/login", data={"username": "louise@test.com", "password": "louise_pass_1"})
    assert set(response.json()) == {"access_token", "token_type"}
    assert "hashed_password" not in response.text
    assert "password" not in response.json()


def test_login_rejects_json_body():
    """Login expects form data, so a JSON body returns 422."""
    response = client.post("/login", json={"username": "louise@test.com", "password": "louise_pass_1"})
    assert response.status_code == 422


def test_openapi_login_takes_form_data():
    """POST /login in the OpenAPI schema takes form data with required username and password."""
    schema = app.openapi()
    content = schema["paths"]["/login"]["post"]["requestBody"]["content"]
    assert list(content) == ["application/x-www-form-urlencoded"]
    ref = content["application/x-www-form-urlencoded"]["schema"]["$ref"]
    form_schema = schema["components"]["schemas"][ref.split("/")[-1]]
    assert {"username", "password"} <= set(form_schema["properties"])
    assert {"username", "password"} <= set(form_schema["required"])
