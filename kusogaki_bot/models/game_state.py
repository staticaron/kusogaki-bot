from dataclasses import dataclass
from typing import Dict


@dataclass
class Player:
    hp: int


@dataclass
class GameState:
    channel_id: int
    players: Dict[int, Player]
    is_active: bool = False
