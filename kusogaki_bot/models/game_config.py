from dataclasses import dataclass


@dataclass
class GameConfig:
    STARTING_HP: int = 3
    GUESS_TIME: int = 15
    CHOICES: int = 4
    COUNTDOWN_TIME: int = 15
    ROUND_TIMEOUT: int = 15
