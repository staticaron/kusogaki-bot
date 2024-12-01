import logging
from typing import Dict

from sqlalchemy.exc import SQLAlchemyError

from kusogaki_bot.data.db import Database
from kusogaki_bot.data.models import ScheduledThread


class ScheduledThreadRepository:
    """Repository class for scheduled thread persistence using PostgreSQL."""

    def __init__(self):
        """Initialize database connection using Database singleton."""
        self.db = Database.get_instance()

    def load(self) -> Dict:
        """Load all scheduled threads from database."""
        try:
            thread = self.db.query(ScheduledThread).first()
            return thread.data if thread else {}
        except SQLAlchemyError as e:
            logging.error(f'Error loading scheduled threads from database: {str(e)}')
            return {}

    def save(self, data: Dict) -> None:
        """Save scheduled threads to database."""
        try:
            thread = self.db.query(ScheduledThread).first()
            if data:
                if thread:
                    thread.data = data
                else:
                    self.db.add(ScheduledThread(data=data))
            elif thread:
                self.db.delete(thread)

            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error saving scheduled threads to database: {str(e)}')
            self.db.rollback()

    def clear_all(self) -> None:
        """Clear all scheduled threads from database."""
        try:
            self.db.query(ScheduledThread).delete()
            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error clearing scheduled threads from database: {str(e)}')
            self.db.rollback()
