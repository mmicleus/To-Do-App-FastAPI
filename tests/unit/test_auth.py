from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine, select

from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_user,
    log_activity,
    verify_password,
)
from config import settings
from models.loginModels import Activity, ActivityLog, UserInDB
from models.todoModels import ToDoItem


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


def add_user(session: Session, username: str = "Marik77") -> UserInDB:
    user = UserInDB(
        username=username,
        full_name="Test User",
        email=f"{username}@example.com",
        hashed_password=get_password_hash("secret123"),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_get_user_returns_matching_user(test_session: Session):
    user = add_user(test_session)

    result = get_user("Marik77", test_session)

    assert result is not None
    assert result.id == user.id
    assert result.username == "Marik77"


def test_get_user_returns_none_for_unknown_username(test_session: Session):
    assert get_user("unknown-user", test_session) is None


def test_password_hash_verifies_password_without_storing_plaintext():
    hashed_password = get_password_hash("secret123")

    assert hashed_password != "secret123"
    assert verify_password("secret123", hashed_password) is True
    assert verify_password("wrong-password", hashed_password) is False


def test_authenticate_user_returns_user_for_valid_credentials(
    test_session: Session,
):
    user = add_user(test_session)

    result = authenticate_user("Marik77", "secret123", test_session)

    assert result is not False
    assert result.id == user.id


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("Marik77", "wrong-password"),
        ("unknown-user", "secret123"),
    ],
)
def test_authenticate_user_returns_false_for_invalid_credentials(
    test_session: Session,
    username: str,
    password: str,
):
    add_user(test_session)

    assert authenticate_user(username, password, test_session) is False


def test_create_access_token_encodes_data_and_expiry():
    before_creation = datetime.now(timezone.utc)
    token = create_access_token(
        {"sub": "Marik77", "scope": "todos"},
        expires_delta=timedelta(minutes=5),
    )

    payload = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )
    expiry = datetime.fromtimestamp(payload["exp"], timezone.utc)

    assert payload["sub"] == "Marik77"
    assert payload["scope"] == "todos"
    assert expiry > before_creation
    assert expiry <= before_creation + timedelta(minutes=5, seconds=1)


def test_create_access_token_uses_default_expiry():
    before_creation = datetime.now(timezone.utc)
    token = create_access_token({"sub": "Marik77"})

    payload = jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )
    expiry = datetime.fromtimestamp(payload["exp"], timezone.utc)

    assert expiry > before_creation
    assert expiry <= before_creation + timedelta(minutes=15, seconds=1)


@pytest.mark.parametrize("activity", [Activity.SignUp, Activity.SignIn])
def test_log_activity_persists_user_activity(
    test_session: Session,
    activity: Activity,
):
    user = add_user(test_session)

    log_activity(user, activity, test_session)

    activity_log = test_session.exec(
        select(ActivityLog).where(
            ActivityLog.user_id == user.id,
            ActivityLog.activity == activity,
        )
    ).one()
    assert activity_log.id is not None
    assert activity_log.occured_at is not None
