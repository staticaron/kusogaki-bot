from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class Player:
    hp: int
    last_answer_time: Optional[datetime] = None
    correct_guesses: int = 0


@dataclass
class GameState:
    channel_id: int
    players: Dict[int, Player]
    is_active: bool = False
    current_round: Optional[int] = None
    start_time: Optional[datetime] = None
