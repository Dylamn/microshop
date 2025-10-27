from pathlib import Path
from typing import Literal

from pydantic import PostgresDsn, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    SECRET_KEY: str
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    DB_NAME: str
    DB_HOST: str
    DB_PORT: int = 5432
    DB_USER: str
    DB_PASSWORD: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def VERSION(self) -> str | None:
        # Get the version from the pyproject.toml file
        from tomllib import load
        project_dir = Path(__file__).parent.parent.parent
        with open(project_dir / "pyproject.toml", "rb") as f:
            pyproject = load(f)
        app_version = pyproject["project"]["version"]

        return app_version if isinstance(app_version, str) else None


settings = Settings()
