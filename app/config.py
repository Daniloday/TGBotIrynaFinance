import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    DB_PATH: str


def _must(v: str | None, name: str) -> str:
    if not v:
        raise RuntimeError(f"{name} not set")
    return v


def get_settings() -> Settings:
    load_dotenv()

    return Settings(
        BOT_TOKEN=_must(os.getenv("BOT_TOKEN"), "BOT_TOKEN"),
        DB_PATH=os.getenv("DB_PATH", "data/iryna.db"),
    )

