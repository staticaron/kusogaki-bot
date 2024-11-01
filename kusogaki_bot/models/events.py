from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class GameEvent:
    type: str
    data: Dict[str, Any]
