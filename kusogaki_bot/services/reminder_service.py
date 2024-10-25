from datetime import datetime
from typing import Dict, List, Tuple


class ReminderError(Exception):
    """Base exception for reminder-related errors."""

    pass


class ReminderService:
    """Service class for managing reminders."""

    def __init__(self):
        self.reminders: Dict[str, List[Dict]] = {}

    def parse_time(self, time_str: str) -> int:
        """
        Parse time string into seconds.

        Args:
            time_str: Time string in format like 1h30m, 2d, 30m

        Returns:
            int: Total seconds

        Raises:
            ValueError: If time format is invalid
        """
        seconds = 0
        time_str = time_str.lower()

        if 'd' in time_str:
            days, time_str = time_str.split('d')
            seconds += int(days) * 86400
        if 'h' in time_str:
            hours, time_str = time_str.split('h')
            seconds += int(hours) * 3600
        if 'm' in time_str:
            minutes, time_str = time_str.split('m')
            seconds += int(minutes) * 60

        if seconds == 0:
            raise ValueError('Invalid time format')

        return seconds

    def create_reminder(self, message: str, seconds: int, channel_id: int) -> Dict:
        """Create reminder data dictionary."""
        current_time = datetime.now().timestamp()
        return {
            'message': message,
            'time': current_time + seconds,
            'created_at': current_time,
            'channel_id': channel_id,
        }

    def add_reminder(self, user_id: str, reminder_data: Dict) -> None:
        """Add a reminder for a user."""
        if user_id not in self.reminders:
            self.reminders[user_id] = []
        self.reminders[user_id].append(reminder_data)

    def get_user_reminders(self, user_id: str) -> List[Dict]:
        """Get all reminders for a user."""
        return self.reminders.get(user_id, [])

    def delete_reminder(self, user_id: str, index: int) -> None:
        """
        Delete a reminder by index.

        Args:
            user_id: User ID
            index: Reminder index

        Raises:
            ReminderError: If reminder not found
        """
        user_reminders = self.reminders.get(user_id, [])
        if not user_reminders:
            raise ReminderError('You have no active reminders!')

        if 0 <= index < len(user_reminders):
            user_reminders.pop(index)
            if not user_reminders:
                del self.reminders[user_id]
        else:
            raise ReminderError('Invalid reminder index!')

    def get_due_reminders(self, current_time: float) -> List[Tuple[str, Dict]]:
        """Get all due reminders."""
        due_reminders = []
        for user_id, reminders in self.reminders.items():
            for reminder in reminders:
                if current_time >= reminder['time']:
                    due_reminders.append((user_id, reminder))
        return due_reminders
