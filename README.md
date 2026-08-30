# Ghost QNAP Installer

Ein-Befehl-Installation von Ghost 6 mit MySQL 8 für QNAP Container Station. Unterstützt Intel/AMD64 und ARM64, speichert alle Nutzdaten dauerhaft auf dem NAS und enthält einen browserbasierten Konfigurationsmanager.

## Installation ohne SSH über QNAP App Templates

In Container Station 3 unter **Preferences → App Templates** den benutzerdefinierten Katalog aktivieren und diese URL eintragen:

```text
https://raw.githubusercontent.com/therepro21/ghost-qnap-installer/main/qnap-template.json
```

Danach unter **App Templates → Custom Templates** den **Ghost QNAP Installer** bereitstellen. Anschließend `http://QNAP-IP:2380` öffnen und Ghost vollständig per Browser einrichten. Der Manager erzeugt zufällige Datenbankkennwörter und persistente Docker-Volumes automatisch.

> **Datensicherheit:** Updates ersetzen ausschließlich Container. Beiträge und Einstellungen liegen in `ghost-qnap-mysql`, Bilder und Themes in `ghost-qnap-content`, Manager-Konfiguration und Update-Backups in `ghost-qnap-manager-data`. Diese drei Volumes in Container Station niemals löschen oder bei einer Bereinigung auswählen.

## Installation

Das Repository ist privat. Deshalb zuerst mit einem GitHub Personal Access Token anmelden oder das Repository auf die QNAP klonen. Danach:

```sh
cd /share/Container/ghost-qnap-installer
chmod +x install.sh ghostctl
./install.sh
```

Ghost ist anschließend unter der beim Setup eingegebenen internen Adresse erreichbar. Ghost Admin liegt unter `/ghost`.

## Konfiguration mit Klicks

Der Manager lauscht standardmäßig nur auf `127.0.0.1:2380`. Um ihn von einem Gerät im LAN zu öffnen, in `.env` `MANAGER_BIND` auf die LAN-IP der QNAP setzen und `docker compose up -d manager` ausführen. Danach `http://QNAP-IP:2380` öffnen und das bei der Installation ausgegebene Kennwort verwenden.

Eine Domain kann jederzeit eingetragen werden. Für HTTPS zusätzlich in QTS unter **Systemsteuerung → Netzwerk & Dateidienste → Reverse Proxy** die Domain auf `http://127.0.0.1:2368` weiterleiten und ein Zertifikat zuweisen.

## Sicher aktualisieren

Nicht nur „Rebuild“ in Container Station anklicken: Das lädt je nach QNAP-Version nicht zuverlässig ein neues Image. Stattdessen:

```sh
./ghostctl update
```

Der Befehl erstellt zuerst ein Datenbank- und Inhaltsbackup, lädt Images und erstellt Container neu. Persistente Daten liegen unter `/share/Container/ghost-qnap` und werden nicht im Container gespeichert.

Weitere Befehle: `./ghostctl status`, `./ghostctl logs`, `./ghostctl backup`, `./ghostctl restore SQL CONTENT`, `./ghostctl domain URL`.

## Beiträge per Ghost Admin API

In Ghost unter **Settings → Integrations → Add custom integration** eine Integration anlegen. Den Admin API Key ausschließlich lokal als Secret aufbewahren, nie committen. Damit können Bilder hochgeladen und Beiträge samt Tags, Metadaten und Veröffentlichungszeit angelegt werden. Automatisierte Beiträge sollten standardmäßig als Entwurf erstellt werden.

`GHOST_ADMIN_URL` und `GHOST_ADMIN_KEY` in `.env` eintragen, Bilder und JSON nach `stories/` kopieren und `./publish-story stories/beitrag.json` ausführen. Das Format zeigt `stories/example.json`. Nur `"status": "published"` veröffentlicht sofort; sonst entsteht ein Entwurf.

## Architekturhinweis

Unterstützt werden `x86_64/amd64` und `aarch64/arm64`. Alte 32-Bit-ARM-QNAPs werden bewusst abgelehnt, da der aktuelle produktive MySQL/Ghost-Stack dafür nicht verlässlich verfügbar ist.
