from kusogaki_bot.features.food_tracker.data import (
    FoodCounterRepository,
    FoodMentionRepository,
)


class FoodCounterService:
    """Service layer for handling food counter business logic"""

    def __init__(self):
        self.counter_repository = FoodCounterRepository()
        self.mention_repository = FoodMentionRepository()
        self._food_items = None

    @property
    def food_items(self) -> list[str]:
        """Cached list of food items to check"""
        if self._food_items is None:
            self._food_items = self.mention_repository.get_all_food_items()
        return self._food_items

    def check_message_for_food(self, content: str) -> bool:
        """
        Check if a message contains any tracked food items

        Args:
            content (str): Message content to check

        Returns:
            bool: True if message contains food mention
        """
        message_words = content.lower().split()
        return any(food_item in message_words for food_item in self.food_items)

    def increment_counter(self, user_id: str) -> int:
        """
        Increment food counter for a user and return new count

        Args:
            user_id (str): Discord user ID

        Returns:
            int: Updated count
        """
        counter = self.counter_repository.get_counter(user_id)
        new_count = counter.increment()
        self.counter_repository.save_counter(counter)
        return new_count

    def get_count(self, user_id: str) -> int:
        """
        Get current count for a user

        Args:
            user_id (str): Discord user ID

        Returns:
            int: Current count
        """
        counter = self.counter_repository.get_counter(user_id)
        return counter.count
