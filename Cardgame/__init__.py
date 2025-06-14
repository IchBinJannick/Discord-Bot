"""
Cardgame package for Discord bot.

This package provides functionality for managing card games in a Discord bot,
including game state management and database operations.
"""

from .cardgame_manager import CardGameManager
from .database_manager import CardGameDB
from .game_rules import GAME_RULES

__all__ = ['CardGameManager', 'CardGameDB', 'GAME_RULES']