from dataclasses import dataclass
from datetime import datetime


@dataclass
class FoodCounter:
    user_id: str
    count: int = 0
    last_updated: datetime = datetime.now()

    def increment(self) -> int:
        self.count += 1
        self.last_updated = datetime.now()
        return self.count
