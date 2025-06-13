import sqlite3
import datetime
import os
import shutil

class CardGameDB:
    def __init__(self, db_path='..\\databases\\cardgames.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def get_played_games_paginated(self, offset, limit):
        pass

    def backup_database(self, backup_dir='..\\backups\\'):
        pass

    def add_player(self, name):
        pass

    def start_game(self, player_ids, winning_score=1000, location=None):
        pass

    def get_or_create_player(self, name: str):
        pass

    def get_player_name_by_id(self, player_id: int):
        pass

    def add_round_data(self, game_id, round_number, round_ender_player_id, player_round_data):
        pass

    def calculate_current_scores(self, game_id):
        pass

    def end_game(self, game_id, winner_id):
        pass

    def get_player_statistics(self, player_id):
        pass

    def get_game_details(self, game_id):
        pass

    def delete_game(self, game_id):
        pass

    def list_all_players(self):
        pass