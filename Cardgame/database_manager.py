import sqlite3
import datetime
import os
import shutil

class CardGameDB:
    def __init__(self, db_path=None):
        # 1. Pfad-Korrektur mit os.path
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, 'databases', 'cardgame.db')

        # 2. Verzeichnis automatisch erstellen
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        self.db_path = db_path
        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            print(f"Datenbank erfolgreich geöffnet: {db_path}")
        except sqlite3.Error as e:
            print(f"KRITISCHER FEHLER: {e}")
            raise

    #game controls
    def start_game(self, player_ids, winning_score=1000, location=None):
        """
        start a new game
        :param player_ids: list of player ids that participate in the game
        :param winning_score: score that the winner needs to reach to win the game
        :param location: location of the game
        :return: game id of the new game
        """
        cursor = self.conn.cursor()
        start_time = datetime.datetime.now().isoformat()
        cursor.execute("INSERT INTO games (start_time, location, winning_score) VALUES (?, ?, ?)",
                       (start_time, location, winning_score))
        game_id = cursor.lastrowid

        for player_id in player_ids:
            cursor.execute("INSERT INTO player_games (player_id, game_id, final_score) VALUES (?, ?, 0)",
                           (player_id, game_id))

        self.conn.commit()
        return game_id

    def add_round_data(self, game_id, round_number, round_ender_player_id, player_round_data):
        """
        add round data to the database
        :param game_id: game id of the game to add round data to
        :param round_number: number of the round
        :param round_ender_player_id: player id of the player that ended the round
        :param player_round_data: data of each player in the round
        :return: round id
        """
        cursor = self.conn.cursor()

        # Sicherstellen, dass die Runde nicht doppelt hinzugefügt wird
        cursor.execute("SELECT round_id FROM rounds WHERE game_id = ? AND round_number = ?", (game_id, round_number))
        existing_round = cursor.fetchone()

        if existing_round:
            round_id = existing_round['round_id']
            # Optional: Hier könnte man auch einen Fehler werfen oder die bestehenden Daten aktualisieren
            print(
                f"Warnung: Runde {round_number} für Spiel {game_id} existiert bereits. Daten werden überschrieben/aktualisiert.")
            # Lösche alte Daten für diese Runde, falls sie aktualisiert werden sollen
            cursor.execute("DELETE FROM round_player_data WHERE round_id = ?", (round_id,))
        else:
            cursor.execute("INSERT INTO rounds (game_id, round_number, round_ender_player_id) VALUES (?, ?, ?)",
                           (game_id, round_number, round_ender_player_id))
            round_id = cursor.lastrowid

        for data in player_round_data:
            player_id = data['player_id']
            score = data['score']
            style = data.get('style', 'normal')
            errors = data.get('errors', 0)
            cursor.execute('''
                           INSERT INTO round_player_data (round_id, player_id, score_in_round, play_style, errors_in_round)
                           VALUES (?, ?, ?, ?, ?)
                           ''', (round_id, player_id, score, style, errors))
        self.conn.commit()
        return round_id

    def calculate_current_scores(self, game_id):
        """
        calculates the current scores of all players in the game
        :param game_id: game id
        :return: total scores of all players
        """

        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT p.player_id,
                              p.name,
                              SUM(rpd.score_in_round) AS total_score
                       FROM players p
                                JOIN player_games pg ON p.player_id = pg.player_id
                                JOIN rounds r ON pg.game_id = r.game_id
                                JOIN round_player_data rpd ON r.round_id = rpd.round_id AND p.player_id = rpd.player_id
                       WHERE pg.game_id = ?
                       GROUP BY p.player_id, p.name
                       ''', (game_id,))
        return {row['player_id']: row['total_score'] for row in cursor.fetchall()}

    def end_game(self, game_id, winner_id):
        """
        end a game and update the database
        :param game_id: game id
        :param winner_id: player id of the winner
        """
        cursor = self.conn.cursor()
        end_time = datetime.datetime.now().isoformat()
        cursor.execute('''
                       UPDATE games
                       SET end_time         = ?,
                           winner_player_id = ?
                       WHERE game_id = ?
                       ''', (end_time, winner_id, game_id))

        current_scores = self.calculate_current_scores(game_id)
        for player_id, score in current_scores.items():
            has_won = 1 if player_id == winner_id else 0
            cursor.execute('''
                           UPDATE player_games
                           SET final_score = ?,
                               has_won     = ?
                           WHERE game_id = ?
                             AND player_id = ?
                           ''', (score, has_won, game_id, player_id))
        self.conn.commit()

    def delete_game(self, game_id):
        """
        deletes a game and all its data from the database
        :param game_id: game id
        :return: boolean indicating whether the deletion was successful or not
        """
        cursor = self.conn.cursor()

        try:
            # Starte eine Transaktion für atomares Löschen
            self.conn.execute("BEGIN TRANSACTION")

            # 1. Runde die IDs aller Runden dieses Spiels ab, um deren Daten zu löschen
            cursor.execute("SELECT round_id FROM rounds WHERE game_id = ?", (game_id,))
            round_ids = [row['round_id'] for row in cursor.fetchall()]

            # 2. Lösche Daten aus round_player_data für alle Runden dieses Spiels
            if round_ids:  # Nur ausführen, wenn es Runden gibt
                # Hier können wir IN verwenden, um alle auf einmal zu löschen
                placeholders = ','.join('?' for _ in round_ids)
                cursor.execute(f"DELETE FROM round_player_data WHERE round_id IN ({placeholders})", round_ids)

            # 3. Lösche Runden dieses Spiels
            cursor.execute("DELETE FROM rounds WHERE game_id = ?", (game_id,))

            # 4. Lösche Einträge aus player_games für dieses Spiel
            cursor.execute("DELETE FROM player_games WHERE game_id = ?", (game_id,))

            # 5. Lösche das Spiel selbst
            cursor.execute("DELETE FROM games WHERE game_id = ?", (game_id,))

            self.conn.commit()
            return True  # Erfolgreich gelöscht
        except Exception as e:
            self.conn.rollback()  # Bei Fehlern Transaktion zurückrollen
            print(f"Fehler beim Löschen des Spiels {game_id}: {e}")
            return False

    #statistics
    def get_played_games_paginated(self, offset, limit):
        """
        Retrieves a paginated list of played games.
        :param offset: starting index of the games to retrieve
        :param limit: number of games to retrieve
        :return: list of total games and list of games
        """
        cursor = self.conn.cursor()
        cursor.execute('''
                       SELECT g.game_id,
                              g.start_time,
                              g.end_time,
                              g.location,
                              g.winning_score,
                              p.name                                AS winner_name,
                              GROUP_CONCAT(player_names.name, ', ') AS participant_names
                       FROM games g
                                LEFT JOIN players p ON g.winner_player_id = p.player_id
                                LEFT JOIN player_games pg ON g.game_id = pg.game_id
                                LEFT JOIN players player_names ON pg.player_id = player_names.player_id
                       GROUP BY g.game_id, g.start_time, g.end_time, g.location, g.winning_score, p.name
                       ORDER BY g.start_time DESC
                       LIMIT ? OFFSET ?
                       ''', (limit, offset))

        games = cursor.fetchall()

        # Holen Sie die Gesamtzahl der Spiele für die Paginierungsinformation
        cursor.execute("SELECT COUNT(*) FROM games")
        total_games = cursor.fetchone()[0]

        return games, total_games

    def get_player_statistics(self, player_id):
        """
        retrieves statistics for a player
        :param player_id: player id
        :return: statistics
        """
        cursor = self.conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM player_games WHERE player_id = ?", (player_id,))
        stats['played_games'] = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM player_games WHERE player_id = ? AND has_won = 1", (player_id,))
        stats['won_games'] = cursor.fetchone()[0]

        cursor.execute('''
                       SELECT SUM(final_score)
                       FROM player_games
                       WHERE player_id = ?
                       ''', (player_id,))
        stats['total_points'] = cursor.fetchone()[0] or 0

        cursor.execute('''
                       SELECT rpd.play_style,
                              COUNT(rpd.play_style) AS style_count
                       FROM round_player_data rpd
                                JOIN rounds r ON rpd.round_id = r.round_id
                                JOIN player_games pg ON r.game_id = pg.game_id AND rpd.player_id = pg.player_id
                       WHERE rpd.player_id = ?
                       GROUP BY rpd.play_style
                       ''', (player_id,))
        stats['play_style_frequency'] = {row['play_style']: row['style_count'] for row in cursor.fetchall()}

        cursor.execute('''
                       SELECT SUM(rpd.errors_in_round)
                       FROM round_player_data rpd
                                JOIN rounds r ON rpd.round_id = r.round_id
                                JOIN player_games pg ON r.game_id = pg.game_id AND rpd.player_id = pg.player_id
                       WHERE rpd.player_id = ?
                       ''', (player_id,))
        stats['total_errors'] = cursor.fetchone()[0] or 0

        return stats

    def get_game_details(self, game_id):
        """
        retrieves details of a game
        :param game_id: game id
        :return: statistics
        """
        cursor = self.conn.cursor()
        game_details = {}

        # 1. Game-Details
        cursor.execute('''
                       SELECT g.game_id,
                              g.start_time,
                              g.end_time,
                              g.location,
                              g.winning_score,
                              p.name AS winner_name
                       FROM games g
                                LEFT JOIN players p ON g.winner_player_id = p.player_id
                       WHERE g.game_id = ?
                       ''', (game_id,))
        game_row = cursor.fetchone()

        if not game_row:
            return None  # Spiel nicht gefunden

        game_details['game_id'] = game_row['game_id']
        game_details['start_time'] = game_row['start_time']
        game_details['end_time'] = game_row['end_time']
        game_details['location'] = game_row['location']
        game_details['winning_score'] = game_row['winning_score']
        game_details['winner_name'] = game_row['winner_name']

        # 2. Spieler im Spiel
        cursor.execute('''
                       SELECT p.player_id, p.name
                       FROM players p
                                JOIN player_games pg ON p.player_id = pg.player_id
                       WHERE pg.game_id = ?
                       ''', (game_id,))
        game_players = {row['player_id']: row['name'] for row in cursor.fetchall()}
        game_details['players'] = game_players

        # 3. Runden-Details und Spielerdaten pro Runde
        rounds_data = []
        cursor.execute('''
                       SELECT r.round_id, r.round_number, p.name AS round_ender_name
                       FROM rounds r
                                LEFT JOIN players p ON r.round_ender_player_id = p.player_id
                       WHERE r.game_id = ?
                       ORDER BY r.round_number ASC
                       ''', (game_id,))
        round_rows = cursor.fetchall()

        for r_row in round_rows:
            round_info = {
                'round_id': r_row['round_id'],
                'round_number': r_row['round_number'],
                'round_ender': r_row['round_ender_name'],
                'player_scores': []
            }

            cursor.execute('''
                           SELECT p.name AS player_name, rpd.score_in_round, rpd.play_style, rpd.errors_in_round
                           FROM round_player_data rpd
                                    JOIN players p ON rpd.player_id = p.player_id
                           WHERE rpd.round_id = ?
                           ''', (r_row['round_id'],))
            player_round_rows = cursor.fetchall()

            for pr_row in player_round_rows:
                round_info['player_scores'].append({
                    'player_name': pr_row['player_name'],
                    'score': pr_row['score_in_round'],
                    'style': pr_row['play_style'],
                    'errors': pr_row['errors_in_round']
                })
            rounds_data.append(round_info)

        game_details['rounds'] = rounds_data

        # 4. Final Scores
        final_scores = self.calculate_current_scores(game_id)  # Diese Methode haben wir schon
        game_details['final_scores'] = {game_players.get(pid, f"Unbekannt {pid}"): score for pid, score in
                                        final_scores.items()}

        return game_details

    #player controls
    def add_player(self, name):
        """
        add a player to the database
        :param name: player name
        :return: name of the player
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Falls Spieler schon existiert, dessen ID zurückgeben
            cursor.execute("SELECT player_id FROM players WHERE name = ?", (name,))
            return cursor.fetchone()[0]

    def get_or_create_player(self, name: str):
        """
        get or create a player by name
        :param name: player name
        :return: player id
        """
        cursor = self.conn.cursor()
        # Suche den Spieler über den Namen
        cursor.execute("SELECT player_id FROM players WHERE name = ?", (name,))
        player_data = cursor.fetchone()

        if player_data:
            # Spieler gefunden
            return player_data['player_id']
        else:
            # Spieler nicht gefunden, neu erstellen
            cursor.execute("INSERT INTO players (name) VALUES (?)", (name,))
            self.conn.commit()
            return cursor.lastrowid

    def get_player_name_by_id(self, player_id: int):
        """
        get player name by id
        :param player_id: player id
        :return: player name
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM players WHERE player_id = ?", (player_id,))
        result = cursor.fetchone()
        return result['name'] if result else "Unbekannter Spieler"

    def get_player_by_name(self, name: str):
        """
        get player by name
        :param name: player name
        :return: player id and name
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT player_id, name FROM players WHERE name = ?", (name,))
        return cursor.fetchone()

    def list_all_players(self):
        """
        lists all players in the database
        :return: player names
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM players ORDER BY name ASC")
        player_names = [row['name'] for row in cursor.fetchall()]
        return player_names

    #databse controls
    def backup_database(self, backup_dir='..\\backups\\'):
        """
        Creates a backup of the database.
        :param backup_dir: directory to save the backup file
        """

        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{self.db_path.replace('.db', '')}_backup_{timestamp}.db"
        backup_path = os.path.join(backup_dir, backup_filename)

        try:
            # Schließe die Verbindung temporär, um sicherzustellen, dass die Datei nicht gesperrt ist
            # Dies ist wichtig für ein konsistentes Backup bei SQLite
            self.conn.close()

            shutil.copy2(self.db_path, backup_path)

            # Verbindung wieder öffnen
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row

            print(f"Datenbank-Backup erfolgreich erstellt: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Fehler beim Erstellen des Datenbank-Backups: {e}")
            try:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.row_factory = sqlite3.Row
            except Exception as reconnect_e:
                print(
                    f"Kritischer Fehler: Verbindung zur Datenbank konnte nicht wiederhergestellt werden nach Backup-Versuch: {reconnect_e}")
            return None

    def close(self):
        self.conn.close()