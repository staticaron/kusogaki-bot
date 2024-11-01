from dataclasses import dataclass


@dataclass
class GameConfig:
    STARTING_HP: int = 3
    GUESS_TIME: int = 15  # this value is in seconds
    CHOICES: int = 4
    COUNTDOWN_TIME: int = 15  # this value is in seconds
    ROUND_TIMEOUT: int = 15  # this value is in seconds
    CACHE_LIFETIME: int = 3600  # this value is in seconds
    MIN_CACHE_HITS: int = 100
