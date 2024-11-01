import json
import logging
from typing import Dict

import redis

from kusogaki_bot.database.redis_db import Database


class ScheduledThreadRepository:
    """Repository class for scheduled thread persistence using Redis."""

    def __init__(self, key_prefix='scheduled_thread:'):
        """Initialize Redis connection using Database singleton."""
        self.redis_client = Database.get_instance()
        self.key_prefix = key_prefix

    def load(self) -> Dict:
        """Load all scheduled threads from Redis."""
        try:
            key = f'{self.key_prefix}all'
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return {}
        except redis.RedisError as e:
            logging.error(f'Error loading scheduled threads from Redis: {str(e)}')
            return {}

    def save(self, data: Dict) -> None:
        """Save scheduled threads to Redis."""
        try:
            key = f'{self.key_prefix}all'
            if data:
                self.redis_client.set(key, json.dumps(data))
            else:
                self.redis_client.delete(key)
        except redis.RedisError as e:
            logging.error(f'Error saving scheduled threads to Redis: {str(e)}')

    def clear_all(self) -> None:
        """Clear all scheduled threads from Redis."""
        try:
            key = f'{self.key_prefix}all'
            self.redis_client.delete(key)
        except redis.RedisError as e:
            logging.error(f'Error clearing scheduled threads from Redis: {str(e)}')
