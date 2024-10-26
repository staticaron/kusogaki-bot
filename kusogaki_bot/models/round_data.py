from dataclasses import dataclass
from typing import Dict, List

from kusogaki_bot.models.game_state import Player


@dataclass
class RoundData:
    correct_title: str
    image_url: str
    choices: List[str]
    players: Dict[int, Player]
