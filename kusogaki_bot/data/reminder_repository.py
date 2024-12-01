import logging
from typing import Dict

from sqlalchemy.exc import SQLAlchemyError

from kusogaki_bot.data.db import Database
from kusogaki_bot.data.models import Reminder


class ReminderRepository:
    """Repository class for reminder persistence using PostgreSQL."""

    def __init__(self):
        """Initialize database connection using Database singleton."""
        self.db = Database.get_instance()

    def load(self) -> Dict:
        """Load all reminders from database."""
        try:
            reminders = {}
            results = self.db.query(Reminder).all()
            for reminder in results:
                reminders[reminder.user_id] = reminder.data
            return reminders
        except SQLAlchemyError as e:
            logging.error(f'Error loading reminders from database: {str(e)}')
            return {}

    def save(self, data: Dict) -> None:
        """Save reminders to database."""
        try:
            existing_user_ids = {r.user_id for r in self.db.query(Reminder).all()}
            users_to_delete = existing_user_ids - set(data.keys())
            if users_to_delete:
                self.db.query(Reminder).filter(
                    Reminder.user_id.in_(users_to_delete)
                ).delete(synchronize_session=False)

            for user_id, reminders in data.items():
                if reminders:
                    existing = (
                        self.db.query(Reminder).filter_by(user_id=user_id).first()
                    )
                    if existing:
                        existing.data = reminders
                    else:
                        self.db.add(Reminder(user_id=user_id, data=reminders))
                else:
                    self.db.query(Reminder).filter_by(user_id=user_id).delete()

            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error saving reminders to database: {str(e)}')
            self.db.rollback()

    def clear_all(self) -> None:
        """Clear all reminders from database (useful for testing)."""
        try:
            self.db.query(Reminder).delete()
            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error clearing reminders from database: {str(e)}')
            self.db.rollback()
