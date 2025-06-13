import sqlite3
import os


if not os.path.exists("..\\databases"):
    os.mkdir("..\\databases")
conn = sqlite3.connect("..\\databases\\cardgame.db")

# Cursor-Objekt erstellen, um SQL-Befehle auszuführen
cursor = conn.cursor()

# --- 1. players Tabelle ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS players (
        player_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
''')

# --- 2. games Tabelle ---
cursor.execute('''
    CREATE TABLE IF NOT EXISTS games (
        game_id INTEGER PRIMARY KEY AUTOINCREMENT,
        start_time TEXT NOT NULL,
        end_time TEXT, -- NULL, solange das Spiel läuft
        location TEXT,
        winning_score INTEGER NOT NULL,
        winner_player_id INTEGER, -- NULL, solange das Spiel läuft (der Gewinner, der das Spiel beendet hat)
        FOREIGN KEY (winner_player_id) REFERENCES players(player_id)
    )
''')

# --- 3. player_games Verknüpfungstabelle ---
# Verbindet Spieler mit Spielen, speichert finale Scores und ob jemand gewonnen hat
cursor.execute('''
    CREATE TABLE IF NOT EXISTS player_games (
        player_id INTEGER,
        game_id INTEGER,
        final_score INTEGER, -- Finaler Score des Spielers in diesem Spiel
        has_won INTEGER DEFAULT 0, -- 0 für False, 1 für True
        PRIMARY KEY (player_id, game_id), -- Kombinierter Primärschlüssel
        FOREIGN KEY (player_id) REFERENCES players(player_id),
        FOREIGN KEY (game_id) REFERENCES games(game_id)
    )
''')

# --- 4. rounds Tabelle ---
# Speichert Informationen über jede einzelne Runde eines Spiels
cursor.execute('''
    CREATE TABLE IF NOT EXISTS rounds (
        round_id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id INTEGER NOT NULL,
        round_number INTEGER NOT NULL,
        round_ender_player_id INTEGER, -- Wer die Runde beendet hat
        FOREIGN KEY (game_id) REFERENCES games(game_id),
        FOREIGN KEY (round_ender_player_id) REFERENCES players(player_id),
        UNIQUE (game_id, round_number) -- Stellt sicher, dass jede Runde innerhalb eines Spiels eine eindeutige Nummer hat
    )
''')

# --- 5. round_player_data Verknüpfungstabelle ---
# Speichert die Details pro Spieler und pro Runde (Punkte, Stil, Fehler)
cursor.execute('''
    CREATE TABLE IF NOT EXISTS round_player_data (
        round_id INTEGER,
        player_id INTEGER,
        score_in_round INTEGER NOT NULL,
        play_style TEXT, -- z.B. 'doppel' oder 'normal' oder 'ungeöffnet
        errors_in_round INTEGER DEFAULT 0,
        PRIMARY KEY (round_id, player_id), -- Kombinierter Primärschlüssel
        FOREIGN KEY (round_id) REFERENCES rounds(round_id),
        FOREIGN KEY (player_id) REFERENCES players(player_id)
    )
''')

# Änderungen speichern und Verbindung schließen
conn.commit()
conn.close()

print("Datenbank 'kartenspiel.db' und alle Tabellen erfolgreich erstellt/aktualisiert.")