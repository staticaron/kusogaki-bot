import json
import logging

import redis

from kusogaki_bot.data.redis_db import Database


class ReminderRepository:
    """Repository class for reminder persistence using Redis."""

    def __init__(self, key_prefix='reminder:'):
        """Initialize Redis connection using Database singleton."""
        self.redis_client = Database.get_instance()
        self.key_prefix = key_prefix

    def load(self) -> dict:
        """Load all reminders from Redis."""
        try:
            all_keys = self.redis_client.keys(f'{self.key_prefix}*')
            if not all_keys:
                return {}

            all_values = self.redis_client.mget(all_keys)

            reminders = {}
            for key, value in zip(all_keys, all_values):
                if value is None:
                    continue
                user_id = key.replace(self.key_prefix, '')
                try:
                    reminders[user_id] = json.loads(value)
                except json.JSONDecodeError as e:
                    logging.error(
                        f'Error decoding reminders for user {user_id}: {str(e)}'
                    )
                    continue

            return reminders
        except redis.RedisError as e:
            logging.error(f'Error loading reminders from Redis: {str(e)}')
            return {}

    def save(self, data: dict) -> None:
        """Save reminders to Redis."""
        try:
            existing_keys = self.redis_client.keys(f'{self.key_prefix}*')

            current_user_keys = {
                f'{self.key_prefix}{user_id}' for user_id in data.keys()
            }
            keys_to_delete = set(existing_keys) - current_user_keys
            if keys_to_delete:
                self.redis_client.delete(*keys_to_delete)

            for user_id, reminders in data.items():
                key = f'{self.key_prefix}{user_id}'
                if reminders:
                    self.redis_client.set(key, json.dumps(reminders))
                else:
                    self.redis_client.delete(key)

        except redis.RedisError as e:
            logging.error(f'Error saving reminders to Redis: {str(e)}')

    def clear_all(self) -> None:
        """Clear all reminders from Redis (useful for testing)."""
        try:
            keys = self.redis_client.keys(f'{self.key_prefix}*')
            if keys:
                self.redis_client.delete(*keys)
        except redis.RedisError as e:
            logging.error(f'Error clearing reminders from Redis: {str(e)}')
