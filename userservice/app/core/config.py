from pathlib import Path
from tomllib import load
from typing import Literal

from joserfc.jwk import OctKey
from pydantic import PostgresDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    SECRET_KEY: str
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = "development"

    JWT_ALGORITHM: str
    JWT_SECRET: OctKey
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str

    @field_validator("JWT_SECRET", mode="before")
    @classmethod
    def convert_secret_to_octkey(cls, v: str) -> OctKey:
        return OctKey.import_key(v)


    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> str:
        if self.ENVIRONMENT == "testing":
            return "sqlite:///:memory:"

        database_dsn = PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )
        return str(database_dsn)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VERSION(self) -> str:
        # Get the version from the pyproject.toml file
        project_dir = Path(__file__).parent.parent.parent
        with open(project_dir / "pyproject.toml", "rb") as f:
            pyproject = load(f)
        app_version = pyproject["project"]["version"]

        if not isinstance(app_version, str):
            raise ValueError(
                "Application version not found. Please check `pyproject.toml` file."
            )

        if self.ENVIRONMENT == "development":
            app_version += "-dev"

        return app_version


settings = Settings()  # ty:ignore[missing-argument]
