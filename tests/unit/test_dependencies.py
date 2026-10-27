from datetime import timedelta

import jwt
import pytest
from fastapi import HTTPException
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from auth import create_access_token
from config import settings
from dependencies import (
    Pagination,
    check_todo_data,
    find_todo_by_id,
    get_current_active_user,
    get_current_user,
    get_userTodo_by_id,
    getUserToDosWithPagination,
)
from models.loginModels import UserInDB
from models.todoModels import ToDoCreate, ToDoItem


@pytest.fixture
def test_session():
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
    test_engine.dispose()


def add_user(
    session: Session,
    username: str = "Marik77",
    disabled: bool = False,
) -> UserInDB:
    user = UserInDB(
        username=username,
        full_name="Test User",
        email=f"{username}@example.com",
        disabled=disabled,
        hashed_password="not-used-by-these-tests",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def add_todo(
    session: Session,
    user: UserInDB,
    title: str = "Write tests",
) -> ToDoItem:
    todo = ToDoItem(title=title, user_id=user.id)
    session.add(todo)
    session.commit()
    session.refresh(todo)
    return todo


def test_check_todo_data_accepts_allowed_task():
    todo = ToDoCreate(title="Read a book")

    assert check_todo_data(todo) is todo


@pytest.mark.parametrize("title", ["drink", "SMOKE", "Gamble", "DRUGS"])
def test_check_todo_data_rejects_forbidden_task(title: str):
    with pytest.raises(HTTPException) as exc_info:
        check_todo_data(ToDoCreate(title=title))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == f"Task '{title}' is not allowed."


def test_pagination_defaults_and_custom_values():
    default_pagination = Pagination()
    custom_pagination = Pagination(limit=10, skip=5)

    assert (default_pagination.limit, default_pagination.skip) == (5, 0)
    assert (custom_pagination.limit, custom_pagination.skip) == (10, 5)


def test_find_todo_by_id_returns_existing_todo(test_session: Session):
    user = add_user(test_session)
    todo = add_todo(test_session, user)

    result = find_todo_by_id(todo.id, test_session)

    assert result.id == todo.id
    assert result.title == "Write tests"


def test_find_todo_by_id_raises_404_for_missing_todo(test_session: Session):
    with pytest.raises(HTTPException) as exc_info:
        find_todo_by_id(999, test_session)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "To-do item not found"


def test_get_current_user_returns_user_for_valid_token(test_session: Session):
    user = add_user(test_session)
    token = create_access_token({"sub": user.username})

    result = get_current_user(token, test_session)

    assert result.id == user.id
    assert result.username == user.username


@pytest.mark.parametrize(
    "token",
    [
        "not-a-valid-token",
        create_access_token({"scope": "todos"}),
        create_access_token({"sub": "unknown-user"}),
        create_access_token(
            {"sub": "Marik77"},
            expires_delta=timedelta(seconds=-1),
        ),
    ],
)
def test_get_current_user_rejects_invalid_tokens(
    test_session: Session,
    token: str,
):
    add_user(test_session)

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, test_session)

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"


def test_get_current_user_rejects_token_signed_with_wrong_secret(
    test_session: Session,
):
    token = jwt.encode(
        {"sub": "Marik77"},
        "incorrect-secret-that-is-at-least-32-bytes-long",
        algorithm=settings.algorithm,
    )

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token, test_session)

    assert exc_info.value.status_code == 401


def test_get_current_active_user_returns_enabled_user(test_session: Session):
    user = add_user(test_session)

    assert get_current_active_user(user) is user


def test_get_current_active_user_rejects_disabled_user(test_session: Session):
    disabled_user = add_user(test_session, disabled=True)

    with pytest.raises(HTTPException) as exc_info:
        get_current_active_user(disabled_user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user"


def test_get_user_todo_by_id_returns_owned_todo(test_session: Session):
    user = add_user(test_session)
    todo = add_todo(test_session, user)

    assert get_userTodo_by_id(user, todo) is todo


def test_get_user_todo_by_id_rejects_another_users_todo(
    test_session: Session,
):
    owner = add_user(test_session, "TaskOwner")
    other_user = add_user(test_session, "OtherUser")
    todo = add_todo(test_session, owner)

    with pytest.raises(HTTPException) as exc_info:
        get_userTodo_by_id(other_user, todo)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Forbidden from accessing this item!"


def test_get_user_todos_with_pagination_filters_user_and_applies_page(
    test_session: Session,
):
    user = add_user(test_session, "TaskOwner")
    other_user = add_user(test_session, "OtherUser")
    first_todo = add_todo(test_session, user, "First task")
    second_todo = add_todo(test_session, user, "Second task")
    add_todo(test_session, other_user, "Other user's task")

    results = getUserToDosWithPagination(
        user,
        Pagination(limit=1, skip=1),
        test_session,
    )

    assert [todo.id for todo in results] == [second_todo.id]
    assert first_todo.id not in [todo.id for todo in results]
