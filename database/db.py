from sqlmodel import create_engine,Session
from dotenv import dotenv_values
from typing import Annotated
from fastapi import Depends
from config import settings
from sqlalchemy import event


todos = {}

fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
        "disabled": False,
    }
}



def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]


engine = create_engine(settings.SQLITE_URL, connect_args={"check_same_thread": False})


# The hook runs whenever SQLAlchemy opens a SQLite connection, enabling foreign-key checks and ON DELETE CASCADE for that connection.
@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(connection, _):
    cursor = connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()