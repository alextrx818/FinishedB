"""
Telegram notification package initialization
Makes the telegram module importable from anywhere in the project
"""

from .notifier import send_message, send_alert, send_match_alert, send_system_alert

__all__ = ['send_message', 'send_alert', 'send_match_alert', 'send_system_alert']
