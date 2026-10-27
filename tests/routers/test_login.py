import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlalchemy.pool import StaticPool

from database.db import get_session
from main import app
from models.loginModels import Activity, ActivityLog, UserInDB


@pytest.fixture
def test_client():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)

    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    try:
        yield TestClient(app), test_engine
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


def signup_payload(username: str = "Marik77") -> dict[str, str]:
    return {
        "username": username,
        "password": "secret123",
        "full_name": "Test User",
        "email": f"{username}@example.com",
    }


def create_user(client: TestClient, username: str = "Marik77") -> None:
    response = client.post("/sign-up", json=signup_payload(username))
    assert response.status_code == 201


def test_sign_up_creates_user_and_activity_log(test_client):
    client, test_engine = test_client

    response = client.post("/sign-up", json=signup_payload())

    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "Marik77"
    assert body["full_name"] == "Test User"
    assert "id" in body
    assert "password" not in body
    assert "hashed_password" not in body

    with Session(test_engine) as session:
        user = session.exec(
            select(UserInDB).where(UserInDB.username == "Marik77")
        ).one()
        activity_log = session.exec(
            select(ActivityLog).where(ActivityLog.user_id == user.id)
        ).one()

        assert user.hashed_password != "secret123"
        assert activity_log.activity == Activity.SignUp
        assert activity_log.occured_at is not None


def test_sign_up_rejects_duplicate_username(test_client):
    client, _ = test_client
    create_user(client)

    response = client.post("/sign-up", json=signup_payload())

    assert response.status_code == 409
    assert response.json()["detail"] == "username already registered"


def test_sign_up_rejects_invalid_payload(test_client):
    client, _ = test_client

    response = client.post(
        "/sign-up",
        json={**signup_payload(), "username": "abc"},
    )

    assert response.status_code == 422


def test_sign_in_returns_token_and_activity_log(test_client):
    client, test_engine = test_client
    create_user(client)

    response = client.post(
        "/token",
        data={"username": "Marik77", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]

    with Session(test_engine) as session:
        user = session.exec(
            select(UserInDB).where(UserInDB.username == "Marik77")
        ).one()
        activity_log = session.exec(
            select(ActivityLog).where(ActivityLog.user_id == user.id)
        ).all()

        assert [log.activity for log in activity_log] == [
            Activity.SignUp,
            Activity.SignIn,
        ]


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("Marik77", "wrong-password"),
        ("unknown-user", "secret123"),
    ],
)
def test_sign_in_rejects_invalid_credentials(test_client, username, password):
    client, test_engine = test_client
    create_user(client)

    response = client.post(
        "/token",
        data={"username": username, "password": password},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
    assert response.headers["www-authenticate"] == "Bearer"

    with Session(test_engine) as session:
        logs = session.exec(select(ActivityLog)).all()
        assert [log.activity for log in logs] == [Activity.SignUp]


def test_read_users_me_requires_and_accepts_bearer_token(test_client):
    client, _ = test_client
    create_user(client)

    unauthenticated_response = client.get("/users/me/")
    assert unauthenticated_response.status_code == 401

    login_response = client.post(
        "/token",
        data={"username": "Marik77", "password": "secret123"},
    )
    token = login_response.json()["access_token"]

    response = client.get(
        "/users/me/",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["username"] == "Marik77"
    assert "hashed_password" not in response.json()
