import json
import logging
from datetime import datetime

import redis

from kusogaki_bot.data.redis_db import Database
from kusogaki_bot.models.food_counter import FoodCounter


class FoodCounterRepository:
    """Repository class for food counter persistence using Redis."""

    def __init__(self, key_prefix='food_counter:'):
        """Initialize Redis connection using Database singleton."""
        self.redis_client = Database.get_instance()
        self.key_prefix = key_prefix

    def get_counter(self, user_id: str) -> FoodCounter:
        """Get a user's food counter from Redis."""
        try:
            key = f'{self.key_prefix}{user_id}'
            data = self.redis_client.get(key)

            if data:
                try:
                    counter_data = json.loads(data)
                    return FoodCounter(
                        user_id=user_id,
                        count=counter_data['count'],
                        last_updated=datetime.fromisoformat(
                            counter_data['last_updated']
                        ),
                    )
                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(
                        f'Error decoding food counter for user {user_id}: {str(e)}'
                    )
                    return FoodCounter(user_id=user_id)
            return FoodCounter(user_id=user_id)

        except redis.RedisError as e:
            logging.error(f'Error loading food counter from Redis: {str(e)}')
            return FoodCounter(user_id=user_id)

    def save_counter(self, counter: FoodCounter) -> None:
        """Save a food counter to Redis."""
        try:
            key = f'{self.key_prefix}{counter.user_id}'
            data = {
                'count': counter.count,
                'last_updated': counter.last_updated.isoformat(),
            }

            if counter.count > 0:
                self.redis_client.set(key, json.dumps(data))
            else:
                self.redis_client.delete(key)

        except redis.RedisError as e:
            logging.error(f'Error saving food counter to Redis: {str(e)}')

    def clear_all(self) -> None:
        """Clear all food counters from Redis (useful for testing)."""
        try:
            keys = self.redis_client.keys(f'{self.key_prefix}*')
            if keys:
                self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logging.error(f'Error clearing food counters from Redis: {str(e)}')
