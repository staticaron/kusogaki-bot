from kusogaki_bot.features.food_tracker.data import FoodCounterRepository


class FoodCounterService:
    """Service layer for handling food counter business logic"""

    def __init__(self):
        self.repository = FoodCounterRepository()

    def increment_counter(self, user_id: str) -> int:
        """
        Increment food counter for a user and return new count

        Args:
            user_id (str): Discord user ID

        Returns:
            int: Updated count
        """
        counter = self.repository.get_counter(user_id)
        new_count = counter.increment()
        self.repository.save_counter(counter)
        return new_count

    def get_count(self, user_id: str) -> int:
        """
        Get current count for a user

        Args:
            user_id (str): Discord user ID

        Returns:
            int: Current count
        """
        counter = self.repository.get_counter(user_id)
        return counter.count
