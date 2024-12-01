import logging
from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from kusogaki_bot.data.db import Database
from kusogaki_bot.data.models import FoodCounter


class FoodCounterRepository:
    """Repository class for food counter persistence using PostgreSQL."""

    def __init__(self):
        """Initialize database connection using Database singleton."""
        self.db = Database.get_instance()

    def get_counter(self, user_id: str) -> FoodCounter:
        """Get a user's food counter from the database."""
        try:
            counter = self.db.query(FoodCounter).filter_by(user_id=user_id).first()
            if not counter:
                counter = FoodCounter(user_id=user_id)
            return counter
        except SQLAlchemyError as e:
            logging.error(f'Error loading food counter from database: {str(e)}')
            return FoodCounter(user_id=user_id)

    def save_counter(self, counter: FoodCounter) -> None:
        """Save a food counter to the database."""
        try:
            if counter.count > 0:
                existing = (
                    self.db.query(FoodCounter)
                    .filter_by(user_id=counter.user_id)
                    .first()
                )
                if existing:
                    existing.count = counter.count
                    existing.last_updated = datetime.now()
                else:
                    self.db.add(counter)
            else:
                self.db.query(FoodCounter).filter_by(user_id=counter.user_id).delete()

            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error saving food counter to database: {str(e)}')
            self.db.rollback()

    def clear_all(self) -> None:
        """Clear all food counters from the database (useful for testing)."""
        try:
            self.db.query(FoodCounter).delete()
            self.db.commit()
        except SQLAlchemyError as e:
            logging.error(f'Error clearing food counters from database: {str(e)}')
            self.db.rollback()
