import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import datetime
import re
from Cardgame import cardgame_manager as cm
from Cardgame import database_manager as db_manager
from Cardgame.game_rules import GAME_RULES

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='?', intents=intents)

# Initialize database manager
db = db_manager.CardGameDB()

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is connected to {len(bot.guilds)} guilds')

    # Initialize card game manager with default channel
    global cardgame
    default_channel_id = None  # This will be set when a game is started
    cardgame = cm.CardGameManager(db, default_channel_id)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Fehlendes Argument. Bitte überprüfe die Syntax deines Befehls: {error}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Ungültiges Argument. Bitte überprüfe deine Eingabe: {error}")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"Ein Fehler ist aufgetreten: {error}")
        print(f"Fehler im Befehl {ctx.command}: {error}")

#cardgame commands (?c <command>)

@bot.group(name='c', invoke_without_command=True)
async def cardgame_group(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("❌ Ungültiger Unterbefehl. Verwende `?c helpme` für Hilfe.")

@cardgame_group.command(name='start', help='Startet ein neues Kartenspiel. Spieler mit @ erwähnen. Optional: Gewinnpunktzahl.')
async def start_game_command(ctx, *players: discord.Member):
    """Befehl zum Starten eines neuen Spiels."""
    channel_id = ctx.channel.id
    if channel_id not in cardgame.active_games:
        cardgame.active_games[channel_id] = cm.CardGameManager(db, channel_id)

    winning_score = 1000

    await cardgame.active_games[channel_id].start_new_game(ctx, list(players), winning_score=winning_score)

@cardgame_group.command(name='createplayer',
             help='Registriert einen neuen Spieler in der Datenbank. Beispiel: `?c createplayer @Anna`')
async def create_player_command(ctx, player_user: discord.Member):
    """Erstellt einen Spieler in der Datenbank."""
    player_name = player_user.name  # Den tatsächlichen Benutzernamen des Discord-Nutzers nutzen
    player_id = db.get_or_create_player(player_name)  # Nutze get_or_create_player
    if player_id:
        await ctx.send(f"Spieler **{player_name}** (ID: {player_id}) wurde registriert oder existiert bereits.")
    else:
        await ctx.send(f"Konnte Spieler **{player_name}** nicht registrieren.")

@cardgame_group.command(name='round',
             help='Fügt Daten für eine Runde hinzu. Format: `?round @Spieler1:Punkte[:Stil][:Fehler] ... [-ender @SpielerDerDieRundeBeendetHat]`. Stil: ungeöffnet, doppelt, normal.')
async def round_command(ctx, *, data_string_and_ender: str):
    channel_id = ctx.channel.id
    if channel_id not in cardgame.active_games or not cardgame.active_games[channel_id].game_started:
        await ctx.send("Es läuft kein aktives Spiel in diesem Kanal. Starte zuerst ein Spiel mit `?startgame`.")
        return

    parts = data_string_and_ender.split(' -ender ', 1)
    player_data_raw_str = parts[0].strip()

    round_ender_user = None
    if len(parts) > 1:
        # Hier ist bereits die Auflösung von @Mention zu discord.Member korrekt
        try:
            # Versuche, die Mention direkt in ein discord.Member-Objekt zu konvertieren
            converter = commands.MemberConverter()
            round_ender_user = await converter.convert(ctx, parts[1].strip())
        except commands.MemberNotFound:
            await ctx.send(
                f"Konnte den Spieler '{parts[1].strip()}' für den Rundenbeender nicht finden. Bitte @ erwähnen.")
            return
        except Exception as e:
            await ctx.send(f"Fehler beim Parsen des Rundenbeenders: {e}")
            return

    # NEUE PARSING LOGIK FÜR @MENTIONS IM !ROUND BEFEHL
    player_data_parsed = []
    # Regex, um Mentions wie <@123> oder <@!123> zu finden
    mention_pattern = re.compile(r"<@!?(\d+)>")

    player_entries = player_data_raw_str.split()  # Splitten nach Leerzeichen für jeden Spielerblock

    for entry in player_entries:
        match = mention_pattern.match(entry)
        if not match:
            await ctx.send(
                f"Fehler im Format: '{entry}'. Erwarte `@[Spieler]:Punkte[:Stil][:Fehler]`. Bitte @ erwähnen.")
            return  # Befehl abbrechen, da Formatfehler

        user_id = int(match.group(1))  # Die Discord-ID aus der Mention holen

        # Den Rest des Strings nach der Mention extrahieren (z.B. ":10:normal:0")
        remaining_string = entry[match.end():]

        sub_parts = remaining_string.split(':')
        if len(sub_parts) < 2:  # Erwarte mindestens :Punkte
            await ctx.send(f"Fehler im Format für {entry}. Erwarte mindestens `@[Spieler]:Punkte`.")
            return

        # Nun versuchen, den discord.Member für die gefundene ID zu bekommen
        try:
            # ctx.guild.get_member ist schneller, wenn der Member im Cache ist
            # Ansonsten bot.fetch_user für Member, die nicht im Cache sind
            player_discord_obj = ctx.guild.get_member(user_id) or await bot.fetch_user(user_id)
            if not isinstance(player_discord_obj, discord.Member):  # Sollte ein Member sein, wenn im Guild
                await ctx.send(
                    f"Konnte Discord-Benutzer für ID {user_id} nicht auflösen. Ist der Bot auf diesem Server?")
                return
        except Exception as e:
            await ctx.send(f"Fehler beim Auflösen von @Mention für {entry}: {e}")
            return

        try:
            score = int(sub_parts[1])
            style = "normal"
            errors = 0

            if len(sub_parts) > 2:
                style = sub_parts[2].lower()
            if len(sub_parts) > 3:
                errors = int(sub_parts[3])

            player_data_parsed.append({
                'player_obj': player_discord_obj,
                'score': score,
                'style': style,
                'errors': errors
            })

        except ValueError:
            await ctx.send(f"Ungültige Eingabe für Punkte oder Fehler in '{entry}'. Bitte gib ganze Zahlen ein.")
            return
        except Exception as e:
            await ctx.send(f"Ein unerwarteter Fehler ist beim Parsen von '{entry}' aufgetreten: {e}")
            return

    await cardgame.active_games[channel_id].enter_round_data(ctx, player_data_parsed, round_ender_user)

@cardgame_group.command(name='scores', help='Zeigt den aktuellen Punktestand des aktiven Spiels an.')
async def scores_command(ctx):
    channel_id = ctx.channel.id
    if channel_id not in cardgame.active_games or not cardgame.active_games[channel_id].game_started:
        await ctx.send("Es läuft kein aktives Spiel in diesem Kanal.")
        return
    await cardgame.active_games[channel_id].display_current_scores(ctx)

@cardgame_group.command(name='stats', help='Zeigt Statistiken für einen Spieler an. Beispiel: `?stats @Paul`')
async def stats_command(ctx, player_user: discord.Member):  # Typ-Hinting hilft Discord.py bei der Konvertierung
    await cm.CardGameManager(db, ctx.channel.id).show_player_stats(ctx, player_user)

@cardgame_group.command(name='end', help='Beendet das aktuelle Spiel vorzeitig in diesem Kanal.')
async def end_game_command(ctx):
    channel_id = ctx.channel.id
    if channel_id not in cardgame.active_games or not cardgame.active_games[channel_id].game_started:
        await ctx.send("Kein aktives Spiel in diesem Kanal, das beenden werden könnte.")
        return
    await cardgame.active_games[channel_id].end_current_game_early(ctx)

@cardgame_group.command(name='listgames', help='Zeigt eine Liste aller aktiven Spiele auf allen Kanälen an.')
async def list_active_games_command(ctx):
    embed = discord.Embed(
        title="🎮 Aktive Spiele Übersicht 🎮",
        description="Hier sind alle Spiele, die aktuell aktiv sind:",
        color=discord.Color.orange()  # Eine nette Farbe
    )

    if not cardgame.active_games:
        embed.description = "Momentan sind **keine aktiven Spiele** in irgendeinem Kanal."
    else:
        for channel_id, game_manager in cardgame.active_games.items():
            channel = bot.get_channel(channel_id)
            channel_name = channel.name if channel else f"Unbekannter Kanal (ID: {channel_id})"

            # Sammle Spieler und aktuelle Punktstände für die Zusammenfassung
            scores = game_manager.db.calculate_current_scores(game_manager.active_game_id)
            score_summary = ""
            if scores:
                # Sortieren nach Punkten
                sorted_scores = sorted(scores.items(), key=lambda item: item[1], reverse=True)
                for player_id, score in sorted_scores:
                    player_name = game_manager.current_players.get(player_id, f'Unbekannt {player_id}')
                    score_summary += f"  **{player_name}**: {score} Pkt.\n"
            else:
                score_summary = "  Noch keine Punkte.\n"

            # Fügen Sie ein Feld für jedes Spiel hinzu
            embed.add_field(
                name=f"➡️ Kanal: #{channel_name} (ID: {game_manager.active_game_id})",
                value=(
                    f"**Runde:** {game_manager.current_round_number}\n"
                    f"**Gewinnziel:** {game_manager.winning_score} Pkt.\n"
                    f"**Aktuelle Punkte:**\n{score_summary}"
                ),
                inline=False  # Jedes Spiel in einem eigenen Feld
            )

    embed.set_footer(text=f"Insgesamt {len(cardgame.active_games)} aktive Spiele")
    await ctx.send(embed=embed)

@cardgame_group.command(name='helpme', help='Zeigt eine ausführliche Liste aller Bot-Befehle und deren Anwendung.')
async def help_command_embed(ctx):
    embed = discord.Embed(
        title="🃏 KartenSpiel Bot Befehlsübersicht 🃏",
        description="Hier findest du alle Befehle, die ich verstehe, und wie du sie verwendest.",
        color=discord.Color.blue()
    )

    prefix = bot.command_prefix

    # Command: startgame
    embed.add_field(
        name=f"{prefix}startgame <@Spieler1> <@Spieler2> ...",
        value=(
            "Startet ein neues Kartenspiel in diesem Kanal.\n"
            "Du musst alle Spieler mit `@` erwähnen, die am Spiel teilnehmen sollen.\n"
            "Das Gewinnziel ist standardmäßig 1000 Punkte.\n"
            f"**Beispiel:** `{prefix}startgame @Alice @Bob @Charlie`"
        ),
        inline=False
    )

    # Command: round
    embed.add_field(
        name=f"{prefix}round @<Spieler1>:Punkte[:Stil][:Fehler] ... [-ender @SpielerDerDieRundeBeendetHat]",
        value=(
            "Fügt die Runden-Ergebnisse hinzu. Gib für jeden Spieler die Punkte an, optional den Stil und die Fehler.\n"
            "**Spielstil-Optionen:** `ungeöffnet`, `doppelt`, `normal` (Standard).\n"
            "**Fehler:** Eine ganze Zahl (Standard ist 0).\n"
            "Der Runden-Beender ist optional und muss ebenfalls mit `@` erwähnt werden.\n"
            f"**Beispiele:**\n"
            f"`{prefix}round @Alice:10 @Bob:5`\n"
            f"`{prefix}round @Charlie:15:ungeöffnet:1 @David:8:normal:0`\n"
            f"`{prefix}round @Eve:20 @Frank:12:doppelt -ender @Eve`"
        ),
        inline=False
    )

    # Command: scores
    embed.add_field(
        name=f"{prefix}scores",
        value=(
            "Zeigt den aktuellen Punktestand des laufenden Spiels in diesem Kanal an.\n"
            f"**Beispiel:** `{prefix}scores`"
        ),
        inline=False
    )

    # Command: stats
    embed.add_field(
        name=f"{prefix}stats @<Spielername>",
        value=(
            "Zeigt detaillierte Statistiken für einen bestimmten Spieler an (gespielte/gewonnene Spiele, Gesamtpunkte, Spielstil-Häufigkeit, Gesamtfehler).\n"
            "Du musst den Spieler mit `@` erwähnen.\n"
            f"**Beispiel:** `{prefix}stats @Paul`"
        ),
        inline=False
    )

    # Command: gamestats
    embed.add_field(
        name=f"{prefix}gamestats <Game-ID>",
        value=(
            "Zeigt detaillierte Statistiken für ein spezifisches Spiel an, inklusive aller Runden und Spielergebnisse.\n"
            "Die Game-ID wird beim Start eines Spiels ausgegeben.\n"
            f"**Beispiel:** `{prefix}gamestats 123`"
        ),
        inline=False
    )

    # Command: createplayer
    embed.add_field(
        name=f"{prefix}createplayer @<Spielername>",
        value=(
            "Registriert einen neuen Spieler manuell in der Datenbank oder gibt seine ID zurück, falls er schon existiert.\n"
            "Dies ist nur nötig, wenn ein Spieler noch nie an einem Spiel teilgenommen hat, das mit `?startgame` gestartet wurde.\n"
            "Du musst den Spieler mit `@` erwähnen.\n"
            f"**Beispiel:** `{prefix}createplayer @Gastspieler`"
        ),
        inline=False
    )

    # Command: listplayers
    embed.add_field(
        name=f"{prefix}listplayers",
        value=(
            "Zeigt eine Liste aller in der Datenbank registrierten Spieler an.\n"
            f"**Beispiel:** `{prefix}listplayers`"
        ),
        inline=False
    )

    # Command: endgame
    embed.add_field(
        name=f"{prefix}endgame",
        value=(
            "Beendet das aktuell in diesem Kanal laufende Spiel vorzeitig.\n"
            "Die aktuellen Punktstände werden gespeichert, aber kein Gewinner deklariert.\n"
            f"**Beispiel:** `{prefix}endgame`"
        ),
        inline=False
    )

    # Command: listgames
    embed.add_field(
        name=f"{prefix}listgames",
        value=(
            "Zeigt eine Übersicht aller aktuell aktiven Spiele auf allen Kanälen an.\n"
            "Nützlich, um den Überblick über laufende Spiele zu behalten.\n"
            f"**Beispiel:** `{prefix}listgames`"
        ),
        inline=False
    )

    # Command: listplayedgames
    embed.add_field(
        name=f"{prefix}listplayedgames [Start-Index]",
        value=(
            "Listet vergangene Spiele in einer paginierten Ansicht auf. Standardmäßig die letzten 10 Spiele (ab Index 0).\n"
            "Gib einen `Start-Index` an, um Spiele ab dieser Position anzuzeigen (z.B. `10` für Spiele 11-20).\n"
            f"**Beispiele:**\n"
            f"`{prefix}listplayedgames` (zeigt die letzten 10 Spiele)\n"
            f"`{prefix}listplayedgames 10` (zeigt die nächsten 10 Spiele ab Index 10)"
        ),
        inline=False
    )

    # Command: rules (NEU HINZUGEFÜGT)
    embed.add_field(
        name=f"{prefix}rules [Abschnitt]",
        value=(
            "Zeigt die detaillierten Spielregeln für Köy Kızı an.\n"
            "Ohne Angabe eines Abschnitts wird eine Übersicht angezeigt.\n"
            "**Verfügbare Abschnitte:** `übersicht`, `vorbereitung`, `spielstart_zugablauf`, `öffnen_paarbildung`, `ergänzung`, `ablage_ankerkarte`, `rundenende_wertung`, `fehlerspiel`, `partieende_punktetabelle`\n"
            f"**Beispiele:**\n"
            f"`{prefix}rules` (zeigt die Übersicht)\n"
            f"`{prefix}rules vorbereitung` (zeigt Regeln zur Spielvorbereitung)"
        ),
        inline=False
    )

    # Command: deletegame (bleibt wie es ist)
    embed.add_field(
        name=f"{prefix}deletegame <Game-ID>",
        value=(
            "**ACHTUNG: LÖSCHT ALLE DATEN** für ein Spiel und seine Runden aus der Datenbank. Dies kann nicht rückgängig gemacht werden!\n"
            "Nur verwenden, wenn du sicher bist, dass diese Daten dauerhaft entfernt werden sollen.\n"
            f"**Beispiel:** `{prefix}deletegame 42`"
        ),
        inline=False
    )

    # Command: backupdb
    embed.add_field(
        name=f"{prefix}backupdb",
        value=(
            "Erstellt eine Sicherungskopie der gesamten Datenbankdatei in einem 'backups'-Ordner.\n"
            "**WICHTIG:** Dieser Befehl kann nur von **Administratoren** ausgeführt werden, um Missbrauch zu verhindern.\n"
            f"**Beispiel:** `{prefix}backupdb`"
        ),
        inline=False
    )

    embed.set_footer(text="Viel Spaß beim Kartenspiel!")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)

    await ctx.send(embed=embed)

@cardgame_group.command(name='gamestats', help='Zeigt detaillierte Statistiken für ein spezifisches Spiel anhand seiner Game-ID an. Beispiel: `?gamestats 123`')
async def game_stats_command(ctx, game_id: int):
    temp_game_manager = cm.CardGameManager(db, ctx.channel.id)
    await temp_game_manager.show_game_stats_embed(ctx, game_id)

@cardgame_group.command(name='deletegame', help='Löscht ein Spiel und alle zugehörigen Daten aus der Datenbank. ACHTUNG: Dies kann nicht rückgängig gemacht werden! Beispiel: `?deletegame 123`')
# Optional: commands.has_permissions(administrator=True) oder eine andere Rollenprüfung
# @commands.has_permissions(administrator=True)
async def delete_game_command(ctx, game_id: int):
    # Auch hier nutzen wir eine temporäre Manager-Instanz, da das Löschen unabhängig vom Kanalzustand ist.
    temp_game_manager = cm.CardGameManager(db, ctx.channel.id)
    await temp_game_manager.delete_game_data(ctx, game_id)

@cardgame_group.command(name='listplayers', help='Zeigt eine Liste aller in der Datenbank registrierten Spieler an.')
async def list_players_command(ctx):
    player_names = db.list_all_players()

    embed = discord.Embed(
        title="👥 Registrierte Spieler",
        color=discord.Color.teal() # Eine nette Farbe
    )

    if not player_names:
        embed.description = (
            "Momentan sind **keine Spieler in der Datenbank registriert**.\n"
            "Spieler werden automatisch hinzugefügt, wenn sie an einem Spiel teilnehmen, "
            "oder du kannst sie mit `?createplayer @Spielername` manuell registrieren."
        )
    else:
        # Teile die Spieler in mehrere Felder auf, wenn es zu viele sind
        # Discord Embed Field Value Limit ist 1024 Zeichen
        player_list_str = ""
        for i, player_name in enumerate(player_names):
            player_list_str += f"{i+1}. **{player_name}**\n"

        # Grundsätzlich passt die Spielerliste in ein Feld, aber bei sehr vielen Spielern wäre es gut, dies aufzuteilen.
        # Für eine einfache Liste ist ein Feld ausreichend, solange es unter 1024 Zeichen bleibt.
        # Wenn wir wirklich Tausende von Spielern hätten, müssten wir hier komplexere Logik anwenden.
        # Für eine typische Anzahl von Spielern ist das hier ausreichend.
        embed.description = player_list_str

    embed.set_footer(text=f"Gesamtanzahl Spieler: {len(player_names)}")
    await ctx.send(embed=embed)

@cardgame_group.command(name='backupdb', help='Erstellt ein Backup der Datenbank. Nur für Administratoren.')
@commands.has_permissions(administrator=True) # NUR FÜR SERVER-ADMINS!
async def backup_db_command(ctx):
    """
    Erstellt ein Backup der aktuellen Datenbankdatei.
    Nur für Benutzer mit Administratorrechten.
    """
    await ctx.send("Starte Datenbank-Backup...")
    backup_path = db.backup_database() # Ruft die Methode aus der db_manager Instanz auf

    if backup_path:
        await ctx.send(f"✅ Datenbank-Backup erfolgreich erstellt unter: `{backup_path}`")
        # Optional: Wenn Backup an Discord senden (VORSICHT BEI GROSSEN DATEIEN!)
        # try:
        #     await ctx.send(file=discord.File(backup_path))
        #     await ctx.send("Backup-Datei wurde gesendet.")
        # except discord.HTTPException as e:
        #     await ctx.send(f"Fehler beim Senden des Backups: Datei ist zu groß oder ein anderer HTTP-Fehler: {e}")
        # except Exception as e:
        #     await ctx.send(f"Ein unbekannter Fehler ist beim Senden des Backups aufgetreten: {e}")

    else:
        await ctx.send("❌ Datenbank-Backup fehlgeschlagen. Überprüfe die Bot-Konsole für Details.")

@cardgame_group.command(name='listplayedgames', help='Listet vergangene Spiele, standardmäßig die letzten 10. Nutze `?listplayedgames <Start-Index>` für weitere Seiten (z.B. `?listplayedgames 10` für Spiele ab Index 10).')
async def list_played_games_command(ctx, start_index: int = 0):
    """
    Listet die zuletzt gespielten Spiele in paginierter Form auf.
    Standardmäßig die ersten 10 Spiele (Index 0-9).
    """
    # Eine temporäre Manager-Instanz ist hier ebenfalls in Ordnung,
    # da wir nur Daten abrufen und keinen aktiven Spielstatus beeinflussen.
    temp_game_manager = cm.CardGameManager(db, ctx.channel.id)
    await temp_game_manager.list_played_games_embed(ctx, start_index)

@cardgame_group.command(name='rules',
             help='Zeigt die Spielregeln von Köy Kızı an. Nutze `?rules <Abschnitt>` für spezifische Details.')
async def show_rules_command(ctx, section: str = None):
    """
    Zeigt die Spielregeln von Köy Kızı in Embed-Nachrichten an.
    Optional kann ein spezifischer Abschnitt angefordert werden.
    """
    if section:
        section = section.lower()  # Sektion in Kleinbuchstaben umwandeln für den Vergleich
        if section in GAME_RULES:
            rule_section = GAME_RULES[section]
            embed = discord.Embed(
                title=rule_section["title"],
                description=rule_section.get("description", ""),  # description ist optional
                color=discord.Color.dark_red()
            )
            for field in rule_section["fields"]:
                embed.add_field(name=field["name"], value=field["value"], inline=False)

            embed.set_footer(text=f"Regelabschnitt: {section} | Für alle Abschnitte: ?rules")
            await ctx.send(embed=embed)
        else:
            await ctx.send(
                f"❌ Der Abschnitt '{section}' wurde nicht gefunden. Verfügbare Abschnitte sind: {', '.join(GAME_RULES.keys())}.")
    else:
        # Standard: Übersicht der Regeln senden und auf spezifische Abschnitte verweisen
        overview_section = GAME_RULES["übersicht"]
        embed = discord.Embed(
            title=overview_section["title"],
            description=overview_section["description"],
            color=discord.Color.dark_red()
        )
        for field in overview_section["fields"]:
            embed.add_field(name=field["name"], value=field["value"], inline=False)

        # Liste aller verfügbaren Abschnitte im Footer
        available_sections = ", ".join([f"`{key}`" for key in GAME_RULES.keys() if key != "übersicht"])
        embed.set_footer(text=f"Für Details, nutze `?rules <Abschnitt>`. Verfügbare Abschnitte: {available_sections}")
        await ctx.send(embed=embed)

# Starte den Bot
if __name__ == "__main__":
    try:
        # db_manager.create_tables() # Diesen Aufruf lassen wir hier, er schadet nicht
        bot.run(TOKEN)
    except Exception as e:
        print(f"Fehler beim Starten des Bots: {e}")
    finally:
        pass
