import logging
import uuid
from datetime import datetime
from typing import Dict, List


class ThreadError(Exception):
    """Base exception for thread-related errors."""

    pass


class ScheduledThreadService:
    """Service class for managing scheduled threads."""

    def __init__(self):
        self.scheduled_threads: Dict[str, Dict] = {}

    def parse_time(self, time_str: str) -> int:
        """Parse time string into seconds."""
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

    def create_thread_data(
        self,
        name: str,
        channel_id: int,
        role_id: int,
        seconds: int,
        message: str = None,
    ) -> Dict:
        """Create thread data dictionary."""
        current_time = datetime.now().timestamp()
        return {
            'id': str(uuid.uuid4()),
            'name': name,
            'channel_id': channel_id,
            'role_id': role_id,
            'time': current_time + seconds,
            'created_at': current_time,
            'message': message,
        }

    def add_thread(self, thread_data: Dict) -> None:
        """Add a scheduled thread."""
        self.scheduled_threads[thread_data['id']] = thread_data

    def get_all_threads(self) -> Dict:
        """Get all scheduled threads."""
        return self.scheduled_threads

    def delete_thread(self, thread_id: str) -> None:
        """Delete a scheduled thread by ID."""
        if thread_id in self.scheduled_threads:
            del self.scheduled_threads[thread_id]
        else:
            logging.warning(f'Attempted to delete non-existent thread: {thread_id}')
            raise ThreadError('Thread not found!')

    def get_due_threads(self, current_time: float) -> List[Dict]:
        """Get all due threads."""
        due_threads = []
        for thread_id, thread in list(self.scheduled_threads.items()):
            if current_time >= thread['time']:
                thread_copy = thread.copy()
                due_threads.append(thread_copy)
                del self.scheduled_threads[thread_id]
        return due_threads
