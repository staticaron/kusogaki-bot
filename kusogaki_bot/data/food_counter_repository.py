import json
from datetime import datetime
from pathlib import Path
from typing import Dict

from kusogaki_bot.models.food_counter import FoodCounter


class FoodCounterRepository:
    def __init__(self, file_path: str = 'data/food_counter.json'):
        self.file_path = Path(file_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Ensure the data file and directory exist"""
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.file_path.exists():
            self._save_data({})

    def _load_data(self) -> Dict:
        """Load raw data from JSON file"""
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _save_data(self, data: Dict):
        """Save raw data to JSON file"""
        with open(self.file_path, 'w') as f:
            json.dump(data, f)

    def get_counter(self, user_id: str) -> FoodCounter:
        """Get a user's food counter"""
        data = self._load_data()
        if user_id in data:
            return FoodCounter(
                user_id=user_id,
                count=data[user_id]['count'],
                last_updated=datetime.fromisoformat(data[user_id]['last_updated']),
            )
        return FoodCounter(user_id=user_id)

    def save_counter(self, counter: FoodCounter):
        """Save a food counter"""
        data = self._load_data()
        data[counter.user_id] = {
            'count': counter.count,
            'last_updated': counter.last_updated.isoformat(),
        }
        self._save_data(data)
