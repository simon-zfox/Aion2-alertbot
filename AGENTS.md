# Entwicklungsregeln für KI-Agenten

## Ziel und aktueller Stand

- Dieses Repository entwickelt einen Discord-Bot für AION 2 in Python 3.11+ mit `discord.py`.
- Einstiegspunkt ist [bot.py](bot.py), Abhängigkeiten stehen in [requirements.txt](requirements.txt), Einrichtung und Betrieb in [README.md](README.md).
- Aktuell existieren `/ping` → `pong` und `/timers` mit globaler Command-Synchronisierung beim Start. Weitere Funktionen sind nicht automatisch Teil eines Auftrags.
- Kommunikation und Projektdokumentation auf Deutsch; Code-Bezeichner auf Englisch.

## Rolle von template-bot

- [template-bot](template-bot/) enthält einen TypeScript-/discord.js-Bot als **funktionale Referenz**. Gewünschte Teile seines Verhaltens werden in diesem Python-Projekt nachgebildet, nicht pauschal vollständig portiert.
- Die Referenz bleibt unverändert: keine Änderungen, Formatierungen, generierten Dateien oder Dependency-Installationen innerhalb von `template-bot`, sofern nicht ausdrücklich beauftragt.
- `template-bot/` wird derzeit durch [.gitignore](.gitignore) ausgeschlossen und ist damit nicht automatisch in einem frischen Checkout verfügbar. Fehlt der Ordner, die Einschränkung melden und bei referenzabhängigen Aufgaben um Bereitstellung bitten; keine Funktionsdetails erfinden oder eigenmächtig externe Quellen herunterladen.
- Nutzeranforderungen und bewusst festgelegtes Verhalten des Python-Bots haben Vorrang. Widersprüche zur Referenz vor einer Verhaltensänderung klären; beispielsweise darf `/ping` nicht ungefragt von `pong` auf eine Latenzanzeige umgestellt werden.
- Die Referenz ist keine Laufzeitabhängigkeit: Python-Code darf keine Dateien aus `template-bot` zur Laufzeit benötigen und keine Node.js-Prozesse starten. Benötigte Daten gehören nach bewusster Übernahme in den Python-Projektbereich.
- Bei der Übernahme von Code oder Daten die Lizenzbedingungen und erforderlichen Hinweise aus [template-bot/LICENSE](template-bot/LICENSE) beachten.

## Referenz gezielt lesen

Zuerst die betroffenen Abschnitte der [Referenz-README](template-bot/README.md), danach Implementierung, Daten und passende Tests lesen. Die README allein ist kein Nachweis für das tatsächliche Verhalten.

| Funktion | Implementierung / Daten in der Referenz | Relevante Tests in der Referenz |
| --- | --- | --- |
| Commands und Einrichtung | [commands](template-bot/src/commands/) | [setup-ids](template-bot/tests/setup-ids.test.ts) |
| Events, Timer, Resets, Zeitzonen | [core](template-bot/src/core/), [data](template-bot/data/) | [schedule-engine](template-bot/tests/schedule-engine.test.ts) |
| Regionsauswahl und Guild-Einstellungen | [region-resolver](template-bot/src/core/region-resolver.ts), [guild-settings](template-bot/src/persistence/guild-settings.ts) | [region-resolver](template-bot/tests/region-resolver.test.ts), [guild-settings](template-bot/tests/guild-settings.test.ts) |
| Panels und Alerts | [services](template-bot/src/services/), [views](template-bot/src/discord/views/), [panels-alerts](template-bot/src/persistence/panels-alerts.ts) | [panel-render](template-bot/tests/panel-render.test.ts), [alert-display](template-bot/tests/alert-display.test.ts), [scheduler](template-bot/tests/scheduler.test.ts) |
| News und Duplikaterkennung | [news](template-bot/src/news/), [news-poller](template-bot/src/services/news-poller.ts), [news persistence](template-bot/src/persistence/news.ts) | [steam-news](template-bot/tests/steam-news.test.ts), [bbcode](template-bot/tests/bbcode.test.ts), [news-store](template-bot/tests/news-store.test.ts) |

## Ablauf einer Implementierung

1. Bestehende Änderungen prüfen und erhalten. Umfang und beobachtbares Zielverhalten des Auftrags bestimmen; bei relevanten Unklarheiten nachfragen.
2. Für Referenzfunktionen die betroffenen Dateien und Tests benennen. Optionen, Defaults, Berechtigungen, Fehlermeldungen, Zeitverhalten und Persistenz berücksichtigen; gewünschte Abweichungen explizit machen.
3. Verhalten idiomatisch mit Python und `discord.py` implementieren, nicht TypeScript-Struktur oder Bibliotheken mechanisch übertragen. Nur tatsächlich benötigte Module und Abhängigkeiten ergänzen.
4. Passende Referenz-Testfälle als eigenständige Python-Tests nachbilden, einschließlich relevanter Randfälle und Regressionen. Referenztests allein validieren die Python-Implementierung nicht.
5. Betroffene Prüfungen ausführen, direkt zugehörige Dokumentation aktualisieren und knapp berichten: Änderungen, geprüfte Fälle, bewusste Abweichungen und verbleibende Einschränkungen. Nicht ausgeführte Prüfungen ausdrücklich nennen.

## Coding-Stil

- Schlanken, direkten Python-Code schreiben: kein unnötiger Boilerplate, keine spekulativen Abstraktionen oder ungenutzten Funktionen. Discord-Callbacks und dekorierte Tasks gelten als verwendet.
- Keine redundanten Checks oder unerreichbaren Zweige. Prüfungen nur behalten, wenn sie einen konkreten Fehler verhindern oder gewünschtes Verhalten sichern; Berechtigungen, externe Daten und atomare Persistenz nicht blind vereinfachen.
- Externe Daten beim Einlesen validieren, nicht dieselben unveränderten Daten bei jedem Zugriff erneut prüfen. Unnötige Datei-/API-Zugriffe und Berechnungen vermeiden.
- Bei fehleranfälligen I/O-Operationen im Zweifel `try`/`except` statt vorgeschalteter Existenzprüfungen verwenden. Fehler an der zuständigen Grenze abfangen und mit Kontext in der Konsole protokollieren; bei unerwarteten Fehlern `logger.exception` verwenden. Fehler nicht still verschlucken oder Erfolg vortäuschen.
- Nur tatsächlich benötigte Hilfsfunktionen behalten; abstrahieren, wenn es reale Wiederholung oder Komplexität reduziert. Lesbarkeit hat Vorrang vor möglichst wenigen Zeilen.
- Optimierungen müssen bestehendes Verhalten erhalten und durch passende Regressionstests belegt sein.

## Technische Leitplanken

- Discord-I/O asynchron halten; den Event-Loop nicht mit synchronen Netzwerkaufrufen, langen Berechnungen oder `sleep` blockieren. Fachlogik möglichst unabhängig von Discord und Netzwerk testbar halten.
- Keine zusätzlichen privilegierten Intents oder weitreichenden Berechtigungen ohne konkreten Funktionsbedarf. Administrationsbefehle mit passenden Berechtigungsprüfungen versehen.
- Bei Zeitplanfunktionen zeitzonenbewusste Datumswerte und explizite IANA-Zeitzonen verwenden; Tages-/Wochenwechsel und Sommerzeit testen. Die lokale Rechnerzeitzone darf nicht stillschweigend das Ergebnis bestimmen.
- Zeitplandaten sind nicht automatisch offiziell oder aktuell. Den dokumentierten Global-Zeitzonenkonflikt der Referenz nicht durch eine unbelegte Annahme auflösen. Zeitpläne aus versionierten Daten laden, keine Runtime-Scraper für Eventzeiten einführen.
- Bei Übernahme der Regionsauflösung die Reihenfolge beachten: explizite Option → Rollen-Zuordnung → Guild-Standard → interaktive Auswahl, sofern nicht anders beauftragt.
- Für Alerts, Panels und News bei entsprechender Implementierung Wiederanlauf, Duplikaterkennung, entfernte Channels/Nachrichten und API-Fehler berücksichtigen.
- `.env`, Tokens und produktive Nutzerdaten nicht lesen, ausgeben, in Tests verwenden oder committen. Konfiguration über Umgebungsvariablen beziehungsweise lokale `.env`; nur wertfreie Beispiele dokumentieren.

## Validierung und Seiteneffekte

- Die Python-Umgebung `.venv` verwenden. Abhängigkeiten nur bei einer Manifeständerung oder nachgewiesen fehlenden Paketen installieren: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.
- Vorhandene Tests unter [tests](tests/) verwenden `unittest`; Linter und Build sind nicht konfiguriert. Keine erfolgreichen Prüfungen behaupten, die nicht eingerichtet oder ausgeführt wurden.
- Bei neuen Python-Tests ohne zusätzlichen Framework-Bedarf `unittest` mit einem `tests`-Verzeichnis nutzen. Vorhandenes Testwerkzeug hat Vorrang; zunächst nur betroffene Tests ausführen, z. B. `.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_<feature>.py"`. Ein Lauf ohne gefundene Tests ist kein Funktionsnachweis.
- Discord und externe APIs in automatisierten Tests mocken; Zeit für Scheduler-Tests kontrollierbar machen. Tests dürfen ohne Token und ohne Zugriff auf einen echten Discord-Server laufen.
- Den Bot nicht als beiläufigen Test starten: `bot.py` verbindet sich mit Discord und synchronisiert globale Commands. Live-Tests, Command-Deployments und externe Schreibaktionen nur nach ausdrücklicher Freigabe auf einem Testserver.
- Für reine Dokumentations-/Instruktionsänderungen sind keine Bot-Starts oder Dependency-Installationen nötig.
