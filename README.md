# Aion2-alertbot

Discord-Bot für AION 2 mit Python und discord.py:

- `/ping` antwortet unverändert mit `pong`.
- `/timers` postet ein selbstaktualisierendes Timer-Board für **Global (UTC+9)**.

## Einrichtung

Voraussetzung: Python 3.11 oder neuer.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Im [Discord Developer Portal](https://discord.com/developers/applications) eine
Anwendung mit Bot anlegen. Den Bot-Token lokal in `.env` als `DISCORD_TOKEN`
eintragen. Den Token niemals veröffentlichen oder committen; `.env` wird von Git
ignoriert. Alternativ kann `DISCORD_TOKEN` als Umgebungsvariable gesetzt werden;
diese hat Vorrang vor `.env`.

Unter **Installation** einen Server-Installationslink mit den Scopes `bot` und
`applications.commands` erstellen und den Bot auf einen Testserver einladen.
Für Timer-Boards benötigt der Bot im Zielkanal **Kanal ansehen**, **Nachrichten
senden** und **Nachrichtenverlauf anzeigen**. **Links einbetten** ist nicht nötig. Weder
Administratorrechte noch privilegierte Gateway-Intents sind erforderlich.

## Starten

```powershell
.\.venv\Scripts\python.exe bot.py
```

Nach erfolgreicher Anmeldung erscheint eine Logmeldung. Beenden mit `Strg+C`.
Ohne Token beendet sich der Bot mit einer verständlichen Fehlermeldung.

Beim Start werden die Slash-Commands global mit Discord synchronisiert.
Danach `/ping` auf dem Server aufrufen; der Bot antwortet mit `pong`.
Neue oder geänderte Commands können mit Verzögerung in Discord erscheinen.

## Timer-Board

`/timers` in einem Server-Textkanal aufrufen. Dafür ist **Server verwalten**
erforderlich (Command-Default und Laufzeitprüfung). Threads und DMs werden nicht
unterstützt. Das Board ist öffentlich; die Bestätigung des Befehls ist nur für
den Aufrufenden sichtbar. Ein erneuter Aufruf aktualisiert dieselbe Nachricht,
auch nach einem Bot-Neustart. Pro Kanal wird ein Board verwaltet.
Vorhandene Embed-Boards werden beim nächsten Update oder mit `/timers` in
derselben Nachricht auf Components v2 umgestellt; alte Embeds werden entfernt.

Das Board verwendet **Discord Components v2** statt Embeds: eine Überschrift
pro Kategorie und eine Textzeile pro Event, einschließlich Status, Termin und
gegebenenfalls Portalphase. Auf schmalen Displays kann Discord Zeilen umbrechen.
Jeder vorhandene Event-Typ erscheint genau einmal mit dem laufenden oder
nächsten Termin, chronologisch innerhalb dieser Gruppen:

| Gruppe | Inhalt |
| --- | --- |
| Events | Spacetime Rift, Shugo Festival, Dimensional Invasion, Artifact Siege, Arena of Tactics |
| Weltbosse | Watcher Kaira, Siege Bosses (zusammengefasste Bossgruppe), Guardian Lord Nahma |
| Resets | Täglicher und wöchentlicher Reset |

Aktive Events zeigen das erwartete Ende; beim Rift wird zusätzlich zwischen
offenem und geschlossenem Eintrittsportal unterschieden. Boss-Zeitfenster sind
Planwerte, keine Erkennung von tatsächlich lebenden Bossen oder individuellen
Respawns. Die Daten enthalten nicht automatisch alle Bosse des Spiels.

### Zeitmodell und Datenstand

- **Einzige Online-Quelle:** <https://shugo.gg/timers.json>. Der Bot lädt die Daten
  beim Start und anschließend stündlich asynchron mit 15 Sekunden Timeout.
  Namen, Symbole, Gruppen, Zeiten, Dauer, Portalphase und Zeitzonen vorhandener
  Shugo-Events stammen ausschließlich daraus; es gibt keine weiteren Abfragen
  oder HTML-Scraper.
- Die Region bleibt **Global/Asia (`global-as`)**, derzeit `Asia/Seoul` (UTC+9).
  Regions- und explizite Event-Zeitzonen stammen aus Shugo. Aktuell liegen die
  Resets bei **07:00 UTC** (16:00 UTC+9), wöchentlich mittwochs; sie haben keine
  aktive Dauer. Discord zeigt Termine in der Zeitzone des Betrachters an.
- Jede geänderte, gültige Antwort wird vollständig und atomar in
  [data/shugo-timers.json](data/shugo-timers.json) gespeichert. Die mitgelieferte
  Startkopie hat den Datenstand **2026-10-09**. Bei Netzwerk-, HTTP-, JSON- oder
  Schemafehlern bleiben die letzte gültige Kopie und die laufenden Boards aktiv.
  Eine fehlerhafte Antwort überschreibt niemals den Cache. Ohne gültige Daten
  sowohl online als auch lokal bricht der Start verständlich ab.
- [data/local.json](data/local.json) enthält ausschließlich die Guild-, Kanal-
  und Nachrichten-IDs aktiver Boards (`boards`). Die Datei wird bei Bedarf mit
  einer leeren Board-Liste angelegt und ist von Git ausgeschlossen. Beim Start
  werden alte Regionseinstellungen und lokale Event-Ergänzungen entfernt;
  vorhandene Board-IDs bleiben erhalten.
- Es gibt keine lokalen Event-Ergänzungen. Events stammen ausschließlich aus
  Shugo beziehungsweise dessen letzter gültiger Kopie. Neue Shugo-Events werden
  automatisch übernommen; die **Arena of Tactics** erscheint nur, wenn Shugo
  sie liefert.
- Community-Daten sind keine offizielle NC-API und keine Aktualitätsgarantie.
  Nach Patches mit dem Spiel abgleichen. Lokale Referenzdaten unterliegen dem
  MIT-Hinweis in [data/LICENSE](data/LICENSE); die Referenz bleibt unverändert
  und ist keine Laufzeitabhängigkeit.

### Aktualisierung und Betrieb

Discord aktualisiert relative Countdowns selbst. Solange der Bot läuft, prüft
er alle **60 Sekunden** den Status und bearbeitet das Board nur bei Änderungen
(z. B. Start, Portalende oder nächster Termin). Statuswechsel können daher bis
zu etwa einer Minute verzögert erscheinen, bei API-Problemen auch länger.
Jede erfolgreiche Board-Aktualisierung wird auf INFO-Level in der Konsole
protokolliert, mit Kanal- und Nachrichten-ID sowie dem Auslöser (`/timers` oder
automatisch). Prüfläufe ohne Änderungen erzeugen keine Aktualisierungsmeldung.

Es wird **keine Datenbank** verwendet. Ausschließlich Board-IDs liegen in
[data/local.json](data/local.json). Schreibvorgänge ersetzen die Datei atomar.
Das Datenverzeichnis muss
beschreibbar und bei Deployments persistent sein. Nur **eine Bot-Instanz pro
Datenverzeichnis** betreiben. Nach Neustarts werden vorhandene Boards fortgesetzt.

**Einmaliger Wechsel von SQLite:** Die alte Datenbank wird weder gelesen noch
verändert und nicht mehr benötigt. Wie vereinbart alte Board-Nachrichten selbst
löschen und `/timers` erneut ausführen; es findet keine automatische Migration
statt. Die unbenutzte Datenbank kann anschließend manuell entfernt werden.

Zum Entfernen die Board-Nachricht in Discord löschen; der nächste Prüflauf
entfernt den gespeicherten Eintrag. Gelöschte Kanäle werden ebenso bereinigt.
Ein erneutes `/timers` legt bei gelöschter Nachricht ein neues Board an.
Fehlende Berechtigungen und vorübergehende API-Fehler löschen die Konfiguration
nicht: Der Bot protokolliert sie und versucht es beim nächsten Prüflauf erneut.
Im Offline-Zustand laufen Discord-Countdowns weiter, aber Eventstatus und
nächste Termine werden erst nach dem Wiederanlauf erneuert.

### Struktur und Tests

- [bot.py](bot.py): Client, Command-Registrierung und Lebenszyklus.
- [timers/command.py](timers/command.py): `/timers`, Rechte und Rückmeldungen.
- [timers/schedule.py](timers/schedule.py): Shugo-Laden, Validierung und netzwerkfreie Terminberechnung.
- [timers/view.py](timers/view.py): kompakte Components-v2-Darstellung mit drei Kategorien.
- [timers/board_service.py](timers/board_service.py): ein gemeinsamer HTTP-Client, stündlicher Datenabruf und Board-Aktualisierung.
- [timers/board_store.py](timers/board_store.py): Board-IDs in der lokalen JSON-Datei.
- [timers/json_file.py](timers/json_file.py): gemeinsames Lesen und atomisches Schreiben von JSON.
- [tests/](tests/): `unittest`-Tests mit kontrollierter Zeit, temporären JSON-Dateien
  und gemocktem HTTP/Discord; kein Token und keine Netzwerkverbindung nötig.
  Die produktive lokale Konfiguration und alte Datenbanken werden nicht gelesen.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_timers*.py"
```

Die Tests decken Tages-/Wochenwechsel, Sommerzeit des Betrachters, aktive
Zeitfenster, Portalgrenzen, UTC-Resets, vollständige Gruppierung, Discord-Limits,
Neustarts, parallele Aufrufe, Duplikatvermeidung und API-/Persistenzfehler ab.
Zusätzlich werden ausschließlich aus Shugo übernommene Events, neue Shugo-Events,
stündliche Downloads, Online-Ausfälle, ungültige Antworten, Offline-Neustarts,
Cache-Schreibfehler und atomare JSON-Persistenz geprüft. Unveränderte Antworten
werden nicht erneut geparst; die Terminsuche endet beim ersten passenden Tag.
Board-IDs werden beim Start validiert, nicht bei jedem internen Zugriff erneut.
Referenzfälle: `schedule-engine.test.ts`, `panel-render.test.ts` und
`scheduler.test.ts`; die Python-Tests validieren die eigenständige Implementierung.
Live-Tests und Command-Synchronisierung erfolgen nur beim ausdrücklich gestarteten Bot.

## Entwicklung mit KI-Agenten

[AGENTS.md](AGENTS.md) enthält die projektweiten Entwicklungsregeln für
KI-Agenten, die dieses Format unterstützen. Bei anderen Werkzeugen die Datei
explizit als Kontext einbinden.

Der vorhandene [template-bot](template-bot/) dient als **funktionale Referenz**:
Ausgewählte Funktionen des TypeScript-Bots werden nach Bedarf in Python
nachgebildet. Der Referenzordner bleibt unverändert und wird nicht zur Laufzeit
verwendet. Es ist keine vollständige Portierung vorgesehen; aktuell unterstützt
der Python-Bot `/ping` → `pong` und das oben beschriebene `/timers`-Board.

Die Regeln enthalten eine Übersicht relevanter Referenzdateien und Tests sowie
Vorgaben für Implementierung, Validierung und den sicheren Umgang mit Discord.
Bei Entwicklungsaufträgen die gewünschte Funktion und bewusste Abweichungen von
der Referenz angeben.

**Hinweis:** [template-bot/](template-bot/) wird derzeit über
[.gitignore](.gitignore) ausgeschlossen. Für referenzbasierte Entwicklung muss
der Ordner lokal bereitgestellt werden; ein frischer Checkout enthält ihn nicht
automatisch.

