import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from database.db import get_session
from main import app
from models.todoModels import ToDoItem


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


def create_authenticated_user(
    client: TestClient,
    username: str = "Marik77",
) -> tuple[dict[str, str], int]:
    signup_response = client.post(
        "/sign-up",
        json={
            "username": username,
            "password": "secret123",
            "full_name": "Test User",
            "email": f"{username}@example.com",
        },
    )
    assert signup_response.status_code == 201

    token_response = client.post(
        "/token",
        data={"username": username, "password": "secret123"},
    )
    assert token_response.status_code == 200

    return (
        {"Authorization": f"Bearer {token_response.json()['access_token']}"},
        signup_response.json()["id"],
    )


def create_todo(
    client: TestClient,
    headers: dict[str, str],
    title: str = "Write tests",
) -> dict:
    response = client.post(
        "/todos/",
        json={"title": title},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


def test_create_todo_returns_created_item_and_location(test_client):
    client, test_engine = test_client
    headers, user_id = create_authenticated_user(client)

    response = client.post(
        "/todos/",
        json={
            "title": "Write tests",
            "description": "Cover the API",
            "completed": True,
            "urgency": "high",
        },
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "title": "Write tests",
        "description": "Cover the API",
        "completed": True,
        "urgency": "high",
    }
    assert response.headers["location"] == f"/todos/{body['id']}"

    with Session(test_engine) as session:
        todo = session.get(ToDoItem, body["id"])
        assert todo is not None
        assert todo.user_id == user_id


def test_create_todo_rejects_invalid_and_forbidden_titles(test_client):
    client, _ = test_client
    headers, _ = create_authenticated_user(client)

    invalid_title_response = client.post(
        "/todos/",
        json={"title": ""},
        headers=headers,
    )
    forbidden_title_response = client.post(
        "/todos/",
        json={"title": "DRINK"},
        headers=headers,
    )

    assert invalid_title_response.status_code == 422
    assert forbidden_title_response.status_code == 422
    assert forbidden_title_response.json()["detail"] == (
        "Task 'DRINK' is not allowed."
    )


def test_create_todo_requires_authentication(test_client):
    client, _ = test_client

    response = client.post("/todos/", json={"title": "Write tests"})

    assert response.status_code == 401


def test_list_todos_only_returns_current_users_items_and_supports_pagination(
    test_client,
):
    client, _ = test_client
    first_user_headers, _ = create_authenticated_user(client, "Marik77")
    second_user_headers, _ = create_authenticated_user(client, "OtherUser")
    first_todo = create_todo(client, first_user_headers, "First task")
    second_todo = create_todo(client, first_user_headers, "Second task")
    create_todo(client, second_user_headers, "Private task")

    response = client.get("/todos/", headers=first_user_headers)
    paginated_response = client.get(
        "/todos/?skip=1&limit=1",
        headers=first_user_headers,
    )

    assert response.status_code == 200
    assert [todo["id"] for todo in response.json()] == [
        first_todo["id"],
        second_todo["id"],
    ]
    assert paginated_response.status_code == 200
    assert [todo["id"] for todo in paginated_response.json()] == [
        second_todo["id"]
    ]


def test_get_todo_returns_own_item_and_hides_other_users_item(test_client):
    client, _ = test_client
    owner_headers, _ = create_authenticated_user(client, "Marik77")
    other_headers, _ = create_authenticated_user(client, "OtherUser")
    todo = create_todo(client, owner_headers)

    own_response = client.get(f"/todos/{todo['id']}", headers=owner_headers)
    other_response = client.get(f"/todos/{todo['id']}", headers=other_headers)
    missing_response = client.get("/todos/9999", headers=owner_headers)

    assert own_response.status_code == 200
    assert own_response.json()["id"] == todo["id"]
    assert other_response.status_code == 403
    assert missing_response.status_code == 404


def test_update_todo_changes_only_supplied_fields(test_client):
    client, test_engine = test_client
    headers, _ = create_authenticated_user(client)
    todo = create_todo(client, headers)

    response = client.patch(
        f"/todos/{todo['id']}",
        json={"completed": True, "urgency": "high"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Write tests"
    assert response.json()["completed"] is True
    assert response.json()["urgency"] == "high"

    with Session(test_engine) as session:
        updated_todo = session.get(ToDoItem, todo["id"])
        assert updated_todo is not None
        assert updated_todo.completed is True
        assert updated_todo.urgency.value == "high"


@pytest.mark.parametrize("field", ["title", "completed", "urgency"])
def test_update_todo_rejects_null_required_fields(test_client, field):
    client, _ = test_client
    headers, _ = create_authenticated_user(client)
    todo = create_todo(client, headers)

    response = client.patch(
        f"/todos/{todo['id']}",
        json={field: None},
        headers=headers,
    )

    assert response.status_code == 422


def test_update_todo_allows_clearing_description(test_client):
    client, _ = test_client
    headers, _ = create_authenticated_user(client)
    todo_response = client.post(
        "/todos/",
        json={"title": "Write tests", "description": "Temporary note"},
        headers=headers,
    )
    todo = todo_response.json()

    response = client.patch(
        f"/todos/{todo['id']}",
        json={"description": None},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_update_todo_rejects_access_by_another_user(test_client):
    client, _ = test_client
    owner_headers, _ = create_authenticated_user(client, "Marik77")
    other_headers, _ = create_authenticated_user(client, "OtherUser")
    todo = create_todo(client, owner_headers)

    response = client.patch(
        f"/todos/{todo['id']}",
        json={"completed": True},
        headers=other_headers,
    )

    assert response.status_code == 403


def test_delete_todo_removes_item_and_rejects_other_user(test_client):
    client, test_engine = test_client
    owner_headers, _ = create_authenticated_user(client, "Marik77")
    other_headers, _ = create_authenticated_user(client, "OtherUser")
    todo = create_todo(client, owner_headers)

    forbidden_response = client.delete(
        f"/todos/{todo['id']}",
        headers=other_headers,
    )
    delete_response = client.delete(
        f"/todos/{todo['id']}",
        headers=owner_headers,
    )
    missing_response = client.delete(
        f"/todos/{todo['id']}",
        headers=owner_headers,
    )

    assert forbidden_response.status_code == 403
    assert delete_response.status_code == 204
    assert delete_response.content == b""
    assert missing_response.status_code == 404

    with Session(test_engine) as session:
        assert session.get(ToDoItem, todo["id"]) is None


def test_list_todos_requires_authentication(test_client):
    client, _ = test_client

    response = client.get("/todos/")

    assert response.status_code == 401