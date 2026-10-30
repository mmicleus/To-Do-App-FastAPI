from sqlmodel import create_engine,Session
from dotenv import dotenv_values
from typing import Annotated
from fastapi import Depends
from config import settings
from sqlalchemy import event
from sqlalchemy.engine import make_url


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


database_url = settings.DATABASE_URL
url = make_url(database_url)

connect_args = (
    {"check_same_thread": False}
    if url.get_backend_name() == "sqlite"
    else {}
)


engine = create_engine(
        database_url, 
        connect_args=connect_args
        )


# if database_url.startswith("sqlite"):
#     #for sqlite
#     engine = create_engine(
#         database_url, 
#         connect_args={"check_same_thread": False}
#         )
# else:
#     #for PostregreSQL and other supported databases
#     engine = create_engine(database_url)




# The hook runs whenever SQLAlchemy opens a SQLite connection, enabling foreign-key checks and ON DELETE CASCADE for that connection.
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


#only if it's a sqlite connection
if url.get_backend_name() == "sqlite":
    event.listen(engine, "connect", enable_sqlite_foreign_keys)