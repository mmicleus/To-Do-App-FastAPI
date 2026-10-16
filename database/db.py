from sqlmodel import create_engine,Session
from dotenv import dotenv_values
from typing import Annotated
from fastapi import Depends


config = dotenv_values(".env")

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


engine = create_engine(config["SQLITE_URL"], connect_args={"check_same_thread": False})