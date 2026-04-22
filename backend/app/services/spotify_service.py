class SpotifyService:
    """Spotify integration — Phase 6 implementation."""

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret

    async def generate_playlist(self, trip_id: str) -> str | None:
        """Generate a playlist for a trip. Stubbed for MVP."""
        return None
