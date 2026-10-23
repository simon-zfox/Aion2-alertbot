# Aion2-alertbot

Minimale Discord-Bot-Boilerplate mit Python und discord.py. Der Slash-Command
`/ping` antwortet mit `pong`. Keine Nachrichtenverarbeitung oder
Aion-spezifischen Funktionen.

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
`applications.commands` erstellen und den Bot auf einen Testserver einladen. Zusätzliche Berechtigungen
und privilegierte Gateway-Intents sind für diese Boilerplate nicht erforderlich.

## Starten

```powershell
.\.venv\Scripts\python.exe bot.py
```

Nach erfolgreicher Anmeldung erscheint eine Logmeldung. Beenden mit `Strg+C`.
Ohne Token beendet sich der Bot mit einer verständlichen Fehlermeldung.

Beim Start werden die Slash-Commands global mit Discord synchronisiert.
Danach `/ping` auf dem Server aufrufen; der Bot antwortet mit `pong`.
Neue oder geänderte Commands können mit Verzögerung in Discord erscheinen.

## Entwicklung mit KI-Agenten

[AGENTS.md](AGENTS.md) enthält die projektweiten Entwicklungsregeln für
KI-Agenten, die dieses Format unterstützen. Bei anderen Werkzeugen die Datei
explizit als Kontext einbinden.

Der vorhandene [template-bot](template-bot/) dient als **funktionale Referenz**:
Ausgewählte Funktionen des TypeScript-Bots werden nach Bedarf in Python
nachgebildet. Der Referenzordner bleibt unverändert und wird nicht zur Laufzeit
verwendet. Es ist keine vollständige Portierung vorgesehen; der aktuelle
Funktionsumfang des Python-Bots bleibt zunächst `/ping` → `pong`.

Die Regeln enthalten eine Übersicht relevanter Referenzdateien und Tests sowie
Vorgaben für Implementierung, Validierung und den sicheren Umgang mit Discord.
Bei Entwicklungsaufträgen die gewünschte Funktion und bewusste Abweichungen von
der Referenz angeben.

**Hinweis:** [template-bot/](template-bot/) wird derzeit über
[.gitignore](.gitignore) ausgeschlossen. Für referenzbasierte Entwicklung muss
der Ordner lokal bereitgestellt werden; ein frischer Checkout enthält ihn nicht
automatisch.

