# --- SPIELREGELN FÜR KÖY KIZI (IN MEHRERE SEKTIONEN UNTERTEILT) ---
GAME_RULES = {
    "übersicht": {
        "title": "🃏 Köy Kızı Spielregeln: Übersicht",
        "description": "Hier findest du eine Zusammenfassung der Spielregeln für Köy Kızı. Nutze `?rules <Abschnitt>` für Details (z.B. `?rules vorbereitung`).",
        "fields": [
            {"name": "Ziel des Spiels", "value": "Als erster Spieler 1.000 Punkte erreichen, indem man Runden gewinnt und Punkte durch das Legen von Kartenpaaren sammelt. "},
            {"name": "Grundlegender Ablauf", "value": "Karten ziehen, Paare bilden, auf den Ablagestapel legen und Runden gewinnen. Spieler müssen sich für Dreier-/Straßen- oder Doppelpaare entscheiden. "},
            {"name": "Wichtige Begriffe", "value": "`Ankerkarte`, `Öffnen`, `Ablagestapel`, `Fehlerspiel`"}
        ]
    },
    "vorbereitung": {
        "title": "📚 Köy Kızı Spielregeln: Vorbereitung des Spiels",
        "description": "Details zur Einrichtung einer Partie.",
        "fields": [
            {"name": "Benötigtes Material", "value": "2 Kartendecks (Zahlen 2-König plus Ass) und 2 Joker. "},
            {"name": "Mischen & Teilen", "value": "Ein Spieler mischt, der nächste Gegenspieler teilt an beliebiger Stelle. "},
            {"name": "Ankerkarte", "value": "Die letzte Karte des geteilten Stapels wird aufgedeckt und als Ankerkarte in die Mitte des Spielfelds gelegt. "},
            {"name": "Joker als Ankerkarte", "value": "Sollte die Ankerkarte ein Joker sein, bekommt der Teiler diesen Joker, und die nächste Karte wird zur Ankerkarte. "},
            {"name": "Zusammenfügen der Decks", "value": "Beide Decks werden wieder zusammengefügt und auf die Ankerkarte gelegt. "},
            {"name": "Kartenverteilung", "value": "Jeder Spieler erhält 13 Karten; der Teiler erhält 14 Karten. "},
            {"name": "Teilerwechsel", "value": "Der Spieler mit den 14 Karten wechselt nach jeder Runde im Uhrzeigersinn. "}
        ]
    },
    "spielstart_zugablauf": {
        "title": "▶️ Köy Kızı Spielregeln: Spielstart & Zugablauf",
        "description": "Wie eine Runde beginnt und Züge ausgeführt werden.",
        "fields": [
            {"name": "Erster Zug", "value": "Der Spieler mit den 14 Karten beginnt, indem er eine Karte in die Mitte auf den Ablagestapel legt. "},
            {"name": "Zugrichtung", "value": "Danach wird im Uhrzeigersinn weitergespielt. "},
            {"name": "Karten ziehen", "value": "Zu Beginn jedes weiteren Zuges muss jeder Spieler eine Karte ziehen: entweder aus der Mitte vom Ablagestapel (wenn er bereits 'geöffnet' hat) oder vom Kartenstapel. "},
            {"name": "Zug beenden", "value": "Ein Spieler beendet seinen Zug, indem er eine Karte aus seiner Hand in die Mitte legt. "}
        ]
    },
    "öffnen_paarbildung": {
        "title": "🤝 Köy Kızı Spielregeln: Öffnen & Paarbildung",
        "description": "Wie man seine Hand öffnet und Paare bildet.",
        "fields": [
            {"name": "Ziel des Öffnens", "value": "Zu Beginn ist es das Ziel eines jeden Spielers, seine Hand zu öffnen. "},
            {"name": "Möglichkeiten zum Öffnen", "value": "Dies geschieht, indem ein Spieler Dreier-, Straßen- oder Doppelpaare vor sich auf den Tisch legt. "},
            {"name": "Entscheidung der Spielweise", "value": "Jeder Spieler muss, bevor er öffnet, entscheiden, ob er mit Dreier-/Straßenpaaren oder mit Doppelpaaren spielt. "},
            {"name": "Regel: Doppelpaare", "value": "Legt man einmal Doppelpaare (z.B. ♠ 7 und ♠ 7), muss man den Rest des Spiels damit fortsetzen. "},
            {"name": "Ausnahme: Dreier-/Straßenpaare", "value": "Man darf trotzdem ein einziges Dreier-/Straßenpaar (♣ 3 und ♦ 3 und ♥ 3 bzw. ♥ 8 und ♥ 9 und ♥ 10) legen. "},
            {"name": "Regel: Dreier-/Straßenpaare", "value": "Gleiches gilt auch für Dreier-/Straßenpaare. Legt man einmal Dreier-/Straßenpaare, kann man nicht mehr Doppelpaare legen! "},
            {"name": "Voraussetzung zum Öffnen", "value": "Um als erster Spieler seine Hand zu öffnen, muss man zwei Dreier-/Straßenpaare legen bzw. drei Doppelpaare (dazu gehörend die Ausnahme!). "}
        ]
    },
    "ergänzung": {
        "title": "➕ Köy Kızı Spielregeln: Ergänzung während des Spiels",
        "description": "Wie man bestehende Paare ergänzt und davon profitiert.",
        "fields": [
            {"name": "Ergänzen erlaubt", "value": "Jeder Spieler darf Dreier-/Straßenpaare mit eigenen Karten ergänzen. "},
            {"name": "Kein Dazwischenlegen", "value": "Dabei ist es wichtig, dass man nur ergänzen, aber nicht dazwischenlegen darf! "},
            {"name": "Beispiel: Erlaubte Ergänzung", "value": "Ergänzung von ♥ 6 an das Straßenpaar ♥ 7, ♥ 8, ♥ 9 ist erlaubt. "},
            {"name": "Beispiel: Verbotenes Dazwischenlegen", "value": "Ein Dazwischenlegen von ♣ 10 an die Reihe ♣ 9, ♣ B, ♣ D ist nicht erlaubt! "},
            {"name": "Karten erhalten durch Ergänzung", "value": "Durch Ergänzung mit seinen eigenen Karten erhält der Spieler eine Karte dieses Straßenpaares, je nach Punktewert seiner gelegten Karte. "},
            {"name": "Beispiel: Karten-Tausch", "value": "♠ 4 ist 5 Punkte wert. Wenn man diese an das Straßenpaar ♠ 5, ♠ 6, ♠ 7 legt, dann darf man sich die ♠ 5 wegnehmen, da diese auch 5 Punkte wert ist. "},
            {"name": "Entstehung einer Lücke", "value": "Dabei entsteht eine Lücke, in die nicht dazwischengelegt werden darf! "}
        ]
    },
    "ablage_ankerkarte": {
        "title": "♻️ Köy Kızı Spielregeln: Ablagestapel & Ankerkarte",
        "description": "Regeln für den Ablagestapel und die Nutzung der Ankerkarte.",
        "fields": [
            {"name": "Ziehen vom Ablagestapel", "value": "Sobald ein Spieler geöffnet hat, darf er vom Ablagestapel in der Mitte ziehen. "},
            {"name": "Regel nach Ablagestapel-Zug", "value": "Wenn ein Spieler eine Karte vom Ablagestapel nimmt, muss er mit dieser Karte ein *neues* Dreier-/Straßen- oder Doppelpaar bilden! "},
            {"name": "Mehrere Karten nehmen", "value": "Wenn ein Spieler eine Karte nimmt, die vor vielen anderen Karten abgelegt wurde, muss er *alle* Karten nehmen, die nach seiner gewünschten Karte auf den Ablagestapel gelegt wurden! "},
            {"name": "Ankerkarte aufnehmen", "value": "Die Ankerkarte in der Mitte unter den Kartendecks kann von einem Spieler aufgenommen werden, wenn er sie in der *gleichen Runde* benutzen kann, um das Spiel zu beenden. "},
            {"name": "Ankerkarte Nutzungsvorsicht", "value": "Dabei ist gemeint, ein Dreier-/Straßen- oder Doppelpaar zu bilden bzw. zu ergänzen und nicht die Karte zu nehmen, um sie danach auf den Ablagestapel zu werfen! "}
        ]
    },
    "rundenende_wertung": {
        "title": "🏆 Köy Kızı Spielregeln: Rundenende & Wertung",
        "description": "Wie eine Runde endet und Punkte gezählt werden.",
        "fields": [
            {"name": "Runde gewinnen", "value": "Der Spieler, der mit seiner letzten Karte auf der Hand seinen Zug beendet, gewinnt das Spiel (die Runde). "},
            {"name": "Bonuspunkte für Gewinner", "value": "Er bekommt 25 Bonuspunkte. "},
            {"name": "Punktzählung für andere Spieler", "value": "Alle anderen Spieler zählen nun ihre Karten: Karten auf der Hand sind Minuspunkte, abgelegte Karten (Paare oder Tauschkarten) sind Pluspunkte. "},
            {"name": "Gewinn mit Joker", "value": "Beendet ein Spieler mit einem Joker, bekommt er 50 Bonuspunkte.  Alle anderen Spieler bekommen doppelte Minuspunkte. "},
            {"name": "Doppelpaare-Spieler gewinnt", "value": "Beendet ein Spieler, der die Runde mit Doppelpaaren gespielt hat, bekommt dieser ebenfalls 50 Bonuspunkte und alle seine Punkte werden doppelt gewertet. "},
            {"name": "Doppelpaare-Spieler verliert", "value": "Achtung: Verliert ein Spieler, der Doppelpaare gespielt hat, werden seine Minuspunkte doppelt gewertet! "},
            {"name": "Sonderausnahme: Vervierfachte Minuspunkte", "value": "Die doppelten Minuspunkte bei Doppelpaaren erhöhen sich, wenn ein Spieler, der Doppelpaare gespielt hat, gewinnt (vervierfachte Minuspunkte). "}
        ]
    },
    "fehlerspiel": {
        "title": "⛔ Köy Kızı Spielregeln: Fehlerspiel",
        "description": "Was als Fehler zählt und wie er bestraft wird.",
        "fields": [
            {"name": "Ablegen einer Karte", "value": "Sollte ein Spieler eine Karte ablegen, obwohl er sie an ein anderes Paar anhängen könnte oder einen Joker damit austauschen könnte, gilt dies als Fehler. "},
            {"name": "Falsche Zugreihenfolge", "value": "Auch das Ziehen einer Karte, obwohl der Spieler nicht an der Reihe ist, gilt als Fehler. "},
            {"name": "Gravierender Fehler", "value": "Sollte ein Spieler aus dem Ablagestapel in der Mitte ziehen, dabei die Reihenfolge der Karten vergessen und dann nicht nach Regel spielen können, gilt dies als gravierender Fehler. "},
            {"name": "Strafen", "value": "Fehler werden mit 25 Minuspunkten bestraft, wobei gravierende Fehler mit 50 Minuspunkten bestraft werden. "}
        ]
    },
    "partieende_punktetabelle": {
        "title": "🏁 Köy Kızı Spielregeln: Partieende & Punktetabelle",
        "description": "Wann die Partie endet und die Punktwerte der Karten.",
        "fields": [
            {"name": "Partieende", "value": "Hat ein Spieler am Ende nach Zählung aller Runden 1000 Punkte oder mehr, gewinnt er die Partie. "},
            {"name": "Karte: 2 bis 9", "value": "Punkte: 5 Punkte, Negativpunkte: -5 Punkte "},
            {"name": "Karte: 10", "value": "Punkte: 10 Punkte, Negativpunkte: -10 Punkte "},
            {"name": "Karte: Bube, Dame, König", "value": "Punkte: 10 Punkte, Negativpunkte: -10 Punkte "},
            {"name": "Karte: Ass (als 1)", "value": "Punkte: 5 Punkte, Negativpunkte: Bleibt ein Ass auf der Hand hat der Spieler -25 Punkte "},
            {"name": "Karte: Ass (als 14 nach König)", "value": "Punkte: 10 Punkte "},
            {"name": "Karte: Ass (In einem Dreierpaar)", "value": "Punkte: 25 Punkte "},
            {"name": "Karte: Joker", "value": "Kann jede beliebige Karte ersetzen und erhält somit ihren Punktwert, Negativpunkte: -50 Punkte "}
        ]
    }
}