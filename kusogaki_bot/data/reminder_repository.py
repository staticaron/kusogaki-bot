import json
import logging
from typing import Dict


class ReminderRepository:
    """Repository class for reminder persistence."""

    def __init__(self, filename='reminders.json'):
        self.filename = filename

    def load(self) -> Dict:
        """Load reminders from file."""
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            logging.error(f'Error decoding {self.filename}: {str(e)}')
            return {}

    def save(self, data: Dict) -> None:
        """Save reminders to file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f)
        except IOError as e:
            logging.error(f'Error saving reminders: {str(e)}')
