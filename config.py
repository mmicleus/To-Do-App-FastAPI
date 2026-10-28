from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
# config = dotenv_values(".env")

# SECRET_KEY = config["SECRET_KEY"]
# ALGORITHM = config["ALGORITHM"]
# SQLITE_URL = config["SQLITE_URL"]


from typing import Literal

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class Settings(BaseSettings):

    SECRET_KEY: str
    ALGORITHM: str
    SQLITE_URL: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("SECRET_KEY")
    @classmethod
    def require_long_secret(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value


settings = Settings()


# class Settings(BaseSettings):
#     model_config = ConfigDict(frozen=True, extra="ignore")

#     secret_key: SecretStr = Field(validation_alias="SECRET_KEY")
#     algorithm: Literal["HS256"] = Field(validation_alias="ALGORITHM")
#     sqlite_url: str = Field(validation_alias="SQLITE_URL", min_length=1)

#     @field_validator("secret_key")
#     @classmethod
#     def require_long_secret(cls, value: SecretStr) -> SecretStr:
#         if len(value.get_secret_value()) < 32:
#             raise ValueError("SECRET_KEY must be at least 32 characters")
#         return value


# settings = Settings.model_validate(dotenv_values(".env"))