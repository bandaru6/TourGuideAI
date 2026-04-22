from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    google_maps_api_key: str = ""
    gemini_api_key: str = ""
    spotify_client_id: str = ""
    spotify_client_secret: str = ""
    frontend_url: str = "http://localhost:5173"
    database_url: str = "sqlite:///./tourguide.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
