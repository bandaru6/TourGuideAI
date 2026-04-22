from pydantic import BaseModel


class SpotifyProfile(BaseModel):
    user_id: str = ""
    display_name: str = ""
    access_token: str = ""
    refresh_token: str = ""
    top_genres: list[str] = []
