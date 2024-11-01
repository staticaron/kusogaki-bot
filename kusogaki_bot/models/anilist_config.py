from dataclasses import dataclass


@dataclass
class AniListConfig:
    """Configuration settings for AniList service."""

    base_url: str = 'https://graphql.anilist.co'
    max_page: int = 500
    cache_timeout: int = 3600  # this value is in seconds
    request_timeout: int = 10  # this value is in seconds
    max_retries: int = 3
    batch_size: int = 50
    cache_pages: int = 3
