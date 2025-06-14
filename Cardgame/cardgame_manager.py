import discord

import datetime

class CardGameManager:
    active_games = {}

    def __init__(self, db_manager, channel_id):
        self.db = db_manager
        self.channel_id = channel_id
        self.active_game_id = None
        self.current_players = {}
        self.current_discord_users = {}
        self.current_round_number = 0
        self.winning_score = 1000
        self.game_started = False
        CardGameManager.active_games[channel_id] = self

    async def start_new_game(self, ctx, discord_users, winning_score=1000, location="TableTop"):
        """
        starts a new game in the current text channel
        :param ctx: context of the command
        :param discord_users: discord users to select from
        :param winning_score: score that the winner needs to reach to win the game, defaults to 1000
        :param location: location of the game, defaults to "TableTop"
        """
        if not await self.selPlayers(ctx, discord_users):
            return

        self.winning_score = winning_score
        self.active_game_id = self.db.start_game(list(self.current_players.keys()), self.winning_score, location)
        self.current_round_number = 0
        self.game_started = True
        await ctx.send(f"\nEin neues Kartenspiel wurde gestartet! Game-ID: **{self.active_game_id}**")
        await self.display_current_scores(ctx)

    async def list_played_games_embed(self, ctx, offset: int = 0):
        """
        generates an embed with a list of played games
        :param ctx: context of the command
        :param offset: start index of the games to display, 0-based
        """
        games_per_page = 10  # Wir wollen 10 Spiele pro Nachricht

        # Offset anpassen, da der Benutzer vielleicht '10' eingibt, aber wir ab dem 10. Index (0-basiert) wollen
        # Wenn der Benutzer ?listplayedgames 10 eingibt, bedeutet das Spiel 11-20
        # Dann wäre der offset 10. Wenn er 0 oder nichts eingibt, ist es Spiel 1-10, also offset 0.
        # Wenn wir von 10-19 wollen, dann ist offset = start_index.
        # Beispiel: ?listplayedgames 1 (erste Seite) -> offset 0
        # Beispiel: ?listplayedgames 11 (zweite Seite) -> offset 10
        # Wir nehmen die Eingabe als Start-Index (1-basiert) und konvertieren sie zu 0-basiertem Offset
        calculated_offset = offset

        games, total_games = self.db.get_played_games_paginated(calculated_offset, games_per_page)

        if not games:
            if calculated_offset == 0:
                await ctx.send("Es wurden noch keine Spiele in der Datenbank aufgezeichnet.")
            else:
                await ctx.send(
                    f"Es gibt keine Spiele ab der Startposition {calculated_offset + 1}. Die letzten aufgezeichneten Spiele sind bis Spiel {total_games}.")
            return

        embed = discord.Embed(
            title="📜 Liste der gespielten Spiele 📜",
            description=f"Zeigt Spiele von **{calculated_offset + 1}** bis **{min(calculated_offset + games_per_page, total_games)}** von insgesamt **{total_games}** Spielen.",
            color=discord.Color.blue()
        )

        for game in games:
            game_id = game['game_id']
            start_time_str = datetime.datetime.fromisoformat(game['start_time']).strftime('%d.%m.%Y %H:%M')
            end_time_str = datetime.datetime.fromisoformat(game['end_time']).strftime('%H:%M') if game[
                'end_time'] else "Läuft noch ⏳"
            winner_str = f"👑 {game['winner_name']}" if game['winner_name'] else "Kein Gewinner"
            participants_str = game['participant_names'] if game['participant_names'] else "Keine Teilnehmer bekannt"

            game_info = (
                f"**Gestartet:** {start_time_str}\n"
                f"**Beendet:** {end_time_str}\n"
                f"**Teilnehmer:** {participants_str}\n"
                f"**Gewinner:** {winner_str}\n"
                f"**Gewinnziel:** {game['winning_score']} Punkte"
            )
            embed.add_field(name=f"Game-ID: {game_id}", value=game_info, inline=False)

        # Paginierungsinformationen im Footer
        total_pages = (total_games + games_per_page - 1) // games_per_page
        current_page_number = (calculated_offset // games_per_page) + 1

        footer_text = f"Seite {current_page_number} von {total_pages} | Zeige Spiele {calculated_offset + 1}-{min(calculated_offset + games_per_page, total_games)}"

        if calculated_offset + games_per_page < total_games:
            next_start_index = calculated_offset + games_per_page
            footer_text += f" | Nächste Seite: `?listplayedgames {next_start_index}`"

        embed.set_footer(text=footer_text)
        await ctx.send(embed=embed)

    async def selPlayers(self, ctx, discord_users):
        """
        interval function to select players for the game
        :param ctx: context of the command
        :param discord_users: discord users to select from
        :return: boolean indicating whether the selection was successful or not
        """
        if self.game_started:
            await ctx.send("Es läuft bereits ein Spiel in diesem Kanal. Bitte beende es zuerst oder starte ein neues.")
            return False

        if not discord_users:
            await ctx.send("Bitte nenne Spieler, die am Spiel teilnehmen sollen (z.B. ?startgame @Spieler1 @Spieler2).")
            return False

        self.current_players = {}
        self.current_discord_users = {}
        player_names_selected = []

        for user in discord_users:
            player_name = user.name
            player_id = self.db.get_or_create_player(player_name)

            self.current_players[player_id] = player_name
            self.current_discord_users[user.id] = player_id
            player_names_selected.append(player_name)

        if not self.current_players:
            await ctx.send("Keine Spieler ausgewählt. Spiel kann nicht gestartet werden.")
            return False

        await ctx.send(f"Spieler für das Spiel: {', '.join(player_names_selected)} ausgewählt.")
        return True

    async def display_current_scores(self, ctx):
        """
        displays the current scores of all players in the game
        :param ctx: context of the command
        :return: scores of all players in the game
        """
        if not self.active_game_id:
            await ctx.send("Kein aktives Spiel in diesem Kanal.")
            return

        scores = self.db.calculate_current_scores(self.active_game_id)
        score_message = f"\n--- Aktuelle Punktstände (Runde {self.current_round_number}) ---\n"
        if not scores:
            score_message += "Noch keine Punkte in diesem Spiel registriert."
        else:
            for player_id, score in scores.items():
                player_name = self.current_players.get(player_id, f'Unbekannter Spieler-ID {player_id}')
                score_message += f"**{player_name}**: {score} Punkte\n"
            score_message += "---------------------------------------"
            await ctx.send(score_message)
            return scores

    async def enter_round_data(self, ctx, player_data_list: list, round_ender_user: discord.Member = None):
        """
        takes the data of all players in the current round and stores it in the database
        :param ctx: context of the command
        :param player_data_list: list of dictionaries containing the data of all players in the round,
         each with the following keys: player_obj (discord.Member), score (int), style (str, optional),
          errors (int, optional)
        :param round_ender_user: round ender user, if specified, otherwise None
        """
        if not self.active_game_id:
            await ctx.send("Kein aktives Spiel in diesem Kanal. Bitte starte zuerst ein Spiel mit `?startgame`.")
            return

        self.current_round_number += 1
        await ctx.send(f"\n--- Runde **{self.current_round_number}** ---")

        player_round_data_to_db = []  # Liste für die Datenbank
        processed_player_ids = set()  # Zum Prüfen, ob alle aktiven Spieler Daten haben

        valid_play_styles = ["ungeöffnet", "doppelt", "normal"]

        for data_entry in player_data_list:
            user_obj = data_entry['player_obj']
            score = data_entry['score']
            style = data_entry.get('style', 'normal')
            errors = data_entry.get('errors', 0)

            player_name = user_obj.name  # Der tatsächliche Benutzername des Discord-Nutzers
            player_discord_id = user_obj.id  # Die Discord-ID des Benutzers

            # Stelle sicher, dass der Discord-Benutzer im aktiven Spiel registriert ist
            player_db_id = self.current_discord_users.get(player_discord_id)
            if player_db_id is None:
                await ctx.send(f"Fehler: **{player_name}** ist nicht Teil des aktiven Spiels in diesem Kanal.")
                self.current_round_number -= 1
                return  # Runde abbrechen, da ein nicht-Spieler Daten übermittelt

            if style not in valid_play_styles:
                await ctx.send(
                    f"Ungültiger Spielstil '{style}' für **{player_name}**. Erlaubt sind: {', '.join(valid_play_styles)}. Verwende 'normal'.")
                style = "normal"  # Setze auf Standard, aber lass die Runde weiterlaufen

            player_round_data_to_db.append({
                'player_id': player_db_id,
                'score': score,
                'style': style,
                'errors': errors
            })
            processed_player_ids.add(player_db_id)

        # Prüfen, ob alle aktiven Spieler Daten erhalten haben
        if len(processed_player_ids) != len(self.current_players):
            missing_players = [self.current_players[pid] for pid in self.current_players if
                               pid not in processed_player_ids]
            await ctx.send(
                f"Fehler: Daten für alle Spieler müssen angegeben werden. Es fehlen Daten für: {', '.join(missing_players)}")
            self.current_round_number -= 1
            return

        # Wer hat die Runde beendet?
        round_ender_id = None
        if round_ender_user:
            round_ender_id = self.current_discord_users.get(round_ender_user.id)
            if round_ender_id is None:
                await ctx.send(f"**{round_ender_user.name}** ist kein aktiver Spieler in diesem Spiel.")
        else:
            await ctx.send(
                "Runde ohne spezifischen Beender gespeichert. (Optional: Füge `-ender @User` zum Befehl hinzu)")

        self.db.add_round_data(self.active_game_id, self.current_round_number, round_ender_id, player_round_data_to_db)

        current_total_scores = await self.display_current_scores(ctx)

        winner_found = False
        winner_id = None

        for player_id, total_score in current_total_scores.items():
            if total_score >= self.winning_score:
                winner_found = True
                winner_id = player_id
                break

        if winner_found:
            await ctx.send(
                f"\n--- SPIEL BEENDET! **{self.current_players[winner_id]}** hat gewonnen mit **{current_total_scores[winner_id]}** Punkten! ---")
            self.db.end_game(self.active_game_id, winner_id)

            self.active_game_id = None
            self.current_players = {}
            self.current_discord_users = {}
            self.current_round_number = 0
            self.game_started = False
            del CardGameManager.active_games[self.channel_id]

    async def show_player_stats(self, ctx, player_discord_user: discord.Member):
        """
        shows the statistics of a player in an embed
        :param ctx: context of the command
        :param player_discord_user: discord user of the player to show the statistics for,
         must be registered in the database
        """
        player_name = player_discord_user.name
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT player_id FROM players WHERE name = ?", (player_name,))
        result = cursor.fetchone()

        if result:
            player_id = result['player_id']
            stats = self.db.get_player_statistics(player_id)

            embed = discord.Embed(
                title=f"📈 Statistiken für {player_name}",
                color=discord.Color.purple() # Eine nette Farbe
            )

            embed.add_field(name="Gespielte Spiele", value=stats['played_games'], inline=True)
            embed.add_field(name="Gewonnene Spiele", value=stats['won_games'], inline=True)
            embed.add_field(name="Gesamtpunkte", value=stats['total_points'], inline=True)

            # Spielstil-Häufigkeit
            style_freq_str = ""
            if stats['play_style_frequency']:
                for style, count in stats['play_style_frequency'].items():
                    style_freq_str += f"- {style.capitalize()}: {count} Mal\n"
            else:
                style_freq_str = "Keine Spielstil-Daten verfügbar."
            embed.add_field(name="Häufigkeit der Spielstile", value=style_freq_str, inline=False)

            embed.add_field(name="Gesamte Fehleranzahl", value=stats['total_errors'], inline=False)

            embed.set_footer(text=f"Statistiken generiert am {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
            # Optional: Spieler-Avatar als Thumbnail setzen
            # embed.set_thumbnail(url=player_discord_user.avatar.url if player_discord_user.avatar else None)

            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Spieler '**{player_name}**' nicht gefunden. Stelle sicher, dass der Spieler mit `?createplayer` registriert ist oder am Spiel teilgenommen hat.")

    async def end_current_game_early(self, ctx):
        """
        ends the current game early, if there is one
        :param ctx: context of the command
        """

        if not self.active_game_id:
            await ctx.send("Kein aktives Spiel in diesem Kanal, das beenden werden könnte.")
            return

        cursor = self.db.conn.cursor()
        end_time = datetime.datetime.now().isoformat()
        cursor.execute('''
                       UPDATE games
                       SET end_time         = ?,
                           winner_player_id = NULL
                       WHERE game_id = ?
                       ''', (end_time, self.active_game_id))
        self.db.conn.commit()

        current_scores = self.db.calculate_current_scores(self.active_game_id)
        for player_id, score in current_scores.items():
            cursor.execute('''
                           UPDATE player_games
                           SET final_score = ?,
                               has_won     = 0
                           WHERE game_id = ?
                             AND player_id = ?
                           ''', (score, self.active_game_id, player_id))
        self.db.commit()  # Korrektur: self.conn.commit()

        await ctx.send(f"Das Spiel mit Game-ID **{self.active_game_id}** wurde vorzeitig beendet.")
        self.active_game_id = None
        self.current_players = {}
        self.current_discord_users = {}
        self.current_round_number = 0
        self.game_started = False
        if self.channel_id in CardGameManager.active_games:  # Sicherheitsprüfung
            del CardGameManager.active_games[self.channel_id]

    async def show_game_stats_embed(self, ctx, game_id: int):
        """
        shows the statistics of a game in an embed
        :param ctx: context of the command
        :param game_id: game id
        """
        game_data = self.db.get_game_details(game_id)

        if not game_data:
            await ctx.send(f"Kein Spiel mit der Game-ID **{game_id}** in der Datenbank gefunden.")
            return

        embed = discord.Embed(
            title=f"📊 Spielstatistik: Game-ID {game_data['game_id']} 📊",
            description=f"Spiel gestartet: **{datetime.datetime.fromisoformat(game_data['start_time']).strftime('%d.%m.%Y %H:%M')}**",
            color=discord.Color.gold()
        )

        # Grundlegende Spielinformationen
        end_time_str = datetime.datetime.fromisoformat(game_data['end_time']).strftime('%d.%m.%Y %H:%M') if game_data[
            'end_time'] else "Läuft noch ⏳"
        winner_str = f"🏆 **{game_data['winner_name']}**" if game_data['winner_name'] else "Noch nicht beendet"

        embed.add_field(name="📍 Ort", value=game_data['location'] or "N/A", inline=True)
        embed.add_field(name="🎯 Gewinnziel", value=f"{game_data['winning_score']} Punkte", inline=True)
        embed.add_field(name="🏁 Beendet am", value=end_time_str, inline=True)
        embed.add_field(name="👑 Gewinner", value=winner_str, inline=True)

        # Auflistung der Spieler
        players_in_game = ", ".join([f"**{p}**" for p in game_data['players'].values()])
        embed.add_field(name="👥 Teilnehmer", value=players_in_game, inline=False)

        # Aktuelle/Endpunktstände
        final_scores_str = ""
        if game_data['final_scores']:
            # Sortieren nach Punkten (absteigend)
            sorted_scores = sorted(game_data['final_scores'].items(), key=lambda item: item[1], reverse=True)
            for player_name, score in sorted_scores:
                final_scores_str += f"**{player_name}**: {score} Punkte\n"
        else:
            final_scores_str = "Noch keine Punkte registriert."
        embed.add_field(name="💯 End-/Aktuelle Punktstände", value=final_scores_str, inline=False)

        # Runden-Details
        if game_data['rounds']:
            embed.add_field(name="\u200b", value="--- **Runden Details** ---",
                            inline=False)  # Leeres Feld für Trennlinie
            for r in game_data['rounds']:
                round_field_name = f"Round {r['round_number']}"
                if r['round_ender']:
                    round_field_name += f" (beendet von **{r['round_ender']}**)"

                round_value_str = ""
                for ps in r['player_scores']:
                    style_info = f" ({ps['style']})" if ps['style'] and ps['style'] != 'normal' else ""
                    errors_info = f", {ps['errors']} Fehler" if ps['errors'] > 0 else ""
                    round_value_str += f"**{ps['player_name']}**: {ps['score']} Punkte{style_info}{errors_info}\n"

                if not round_value_str:
                    round_value_str = "Keine Daten für diese Runde."

                embed.add_field(name=f"🔢 {round_field_name}", value=round_value_str, inline=False)
        else:
            embed.add_field(name="Runden", value="Keine Runden für dieses Spiel aufgezeichnet.", inline=False)

        embed.set_footer(
            text=f"Statistiken für Spiel {game_id} | Erzeugt am {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}")
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)  # Server-Icon, falls vorhanden

        await ctx.send(embed=embed)

    async def delete_game_data(self, ctx, game_id: int):
        """
        deletes the game data from the database and the manager
        :param ctx: context of the command
        :param game_id: game id to delete
        """
        # Überprüfen, ob das Spiel überhaupt existiert, bevor wir löschen
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT game_id FROM games WHERE game_id = ?", (game_id,))
        if not cursor.fetchone():
            await ctx.send(f"Es wurde kein Spiel mit der Game-ID **{game_id}** gefunden, das gelöscht werden könnte.")
            return

        # Wenn das zu löschende Spiel zufällig das aktuell aktive Spiel im Kanal ist,
        # dann müssen wir den aktiven Spielzustand im Manager zurücksetzen.
        if self.active_game_id == game_id:
            await ctx.send(
                f"⚠️ **Achtung:** Das zu löschende Spiel (ID: {game_id}) ist das aktuell aktive Spiel in diesem Kanal. Es wird beendet.")
            # Setze den Status dieses Managers zurück
            self.active_game_id = None
            self.current_players = {}
            self.current_discord_users = {}
            self.current_round_number = 0
            self.game_started = False
            # Entferne auch aus der globalen active_games Liste, falls es die letzte Referenz war
            if self.channel_id in CardGameManager.active_games:
                del CardGameManager.active_games[self.channel_id]

        if self.db.delete_game(game_id):
            await ctx.send(f"✅ Spiel mit Game-ID **{game_id}** und alle zugehörigen Daten wurden erfolgreich gelöscht.")
        else:
            await ctx.send(
                f"❌ Fehler beim Löschen von Spiel mit Game-ID **{game_id}**. Bitte überprüfe die Konsole für Details.")
