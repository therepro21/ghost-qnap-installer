# Ghost QNAP Installer

[Deutsch](#deutsch) · [English](#english)

Ghost 6 mit MySQL 8 für QNAP Container Station 3 – klickbare Installation ohne SSH, für Intel/AMD64 und ARM64. Beiträge, Datenbank, Bilder und Einstellungen liegen dauerhaft in getrennten Docker-Volumes.

> **Inoffizielles Community-Projekt:** Nicht mit Ghost Foundation, QNAP Systems, Docker oder Oracle verbunden oder von ihnen unterstützt. Produktnamen werden ausschließlich beschreibend verwendet.

---

# Deutsch

## Was du vorab brauchst

- Eine QNAP mit **Container Station 3**.
- Eine Intel/AMD-64-Bit- oder ARM-64-Bit-CPU. Alte 32-Bit-ARM-Geräte werden nicht unterstützt.
- Internetzugang der QNAP zum Herunterladen der Container-Images.
- Die interne IP-Adresse deiner QNAP, meistens ähnlich wie `192.168.1.100`.

### Wo finde ich meine QNAP-IP?

Am einfachsten steht sie in der Browser-Adresszeile, während QTS geöffnet ist. Alternativ:

1. In QTS **Systemsteuerung → Netzwerk & virtueller Switch → Schnittstellen** öffnen.
2. Die IPv4-Adresse des verbundenen Netzwerkanschlusses notieren.
3. Oder auf einem Computer **Qfinder Pro** öffnen; dort erscheint die NAS-IP in der Geräteliste.

Typisch ist eine Adresse wie `192.168.0.20`, `192.168.1.100` oder `10.0.0.20`. Nicht `127.0.0.1` verwenden.

## Schritt 1: Template-URL in Container Station eintragen

Diese URL vollständig kopieren:

```text
https://raw.githubusercontent.com/therepro21/ghost-qnap-installer/main/qnap-template.json
```

Dann:

1. QTS im Browser öffnen und **Container Station** starten.
2. Links bzw. oben **Einstellungen / Preferences** öffnen.
3. **App Templates / Anwendungsvorlagen** auswählen.
4. **Benutzerdefinierte Vorlage aktivieren / Enable custom template** einschalten.
5. Die kopierte URL in das Feld für die benutzerdefinierte Template-URL einfügen.
6. **Übernehmen / Apply** anklicken.
7. Links **App Templates** und danach **Custom Templates / Benutzerdefinierte Vorlagen** öffnen.

Falls keine Vorlage erscheint, die URL in einem normalen Browser öffnen. Es muss lesbarer JSON-Text erscheinen. Danach Container Station neu öffnen oder die Template-Einstellung erneut übernehmen.

## Schritt 2: Richtige Prozessorversion auswählen

- Bei den meisten QNAP-Modellen mit Intel Celeron, Intel Core, Intel Xeon oder AMD Ryzen: **Ghost QNAP Installer (Intel/AMD64)**.
- Bei QNAP-Modellen mit 64-Bit-ARM-Prozessor: **Ghost QNAP Installer (ARM64)**.

Die Architektur findest du in QTS unter **Systemsteuerung → Systemstatus → Systeminformationen** oder auf der QNAP-Produktseite deines Modellnamens. Im Zweifel nicht raten: Eine falsche Architektur startet nicht, beschädigt aber keine Ghost-Daten.

Beim passenden Template **Deploy / Bereitstellen** anklicken. Die Vorgaben normalerweise unverändert lassen:

| Wert | Standard | Bedeutung |
|---|---:|---|
| Manager-Port | `2380` | Nur für den Installations- und Verwaltungshelfer |
| Neustartrichtlinie | `unless-stopped` | Startet nach einem NAS-Neustart automatisch |
| Manager-Datenvolume | `ghost-qnap-manager-data` | Enthält Konfiguration und Update-Backups |

Nach dem Bereitstellen ein bis zwei Minuten warten. Der Manager wird unter `http://QNAP-IP:2380` geöffnet, beispielsweise:

```text
http://192.168.1.100:2380
```

Port `2380` niemals im Router ins Internet weiterleiten. Der Manager darf nur im vertrauenswürdigen Heim- oder Firmennetz erreichbar sein.

## Schritt 3: Werte im Installationshelfer

Neben jedem Eingabewert befindet sich ein kleines **?**. Anklicken oder mit der Tastatur fokussieren, um eine Erklärung auf Deutsch und Englisch zu öffnen.

### Ghost-Adresse

Ohne eigene Domain ist meistens dieser Wert richtig:

```text
http://DEINE-QNAP-IP:2368
```

Beispiel:

```text
http://192.168.1.100:2368
```

Regeln:

- Immer `http://` oder `https://` angeben.
- Bei interner IP den Ghost-Port anhängen.
- Keinen `/` am Ende eintragen.
- Nicht die Manager-Adresse mit Port `2380` verwenden.

Wenn später eine Domain eingerichtet ist, kann die Adresse im Manager beispielsweise auf `https://blog.example.de` geändert werden.

### Ghost-Port

Standard und meistens richtig: `2368`. Nur ändern, wenn Container Station meldet, dass der Port bereits belegt ist. Bei einer Änderung muss dieselbe Nummer auch in der internen Ghost-Adresse stehen, zum Beispiel `http://192.168.1.100:12368`.

### Manager-Kennwort

Ein neues Kennwort mit mindestens 12, besser 16 oder mehr Zeichen verwenden und in einem Passwortmanager speichern. Dieses Kennwort schützt den QNAP-Manager. Es ist **nicht** das spätere Ghost-Admin-Kennwort.

Danach **Ghost installieren** anklicken. Der Helfer erzeugt Datenbankkennwörter automatisch; sie müssen nicht selbst gewählt oder kopiert werden. Der erste Start von MySQL und Ghost kann mehrere Minuten dauern.

## Schritt 4: Ghost-Administratorkonto anlegen

1. `http://QNAP-IP:2368/ghost` öffnen.
2. Den Ghost-Assistenten durchlaufen.
3. Namen, E-Mail-Adresse und ein neues Ghost-Admin-Kennwort festlegen.

Das Ghost-Admin-Kennwort ist unabhängig vom Manager-Kennwort.

## Später eine Domain verwenden

Eine Domain benötigt zusätzlich DNS, ein TLS-Zertifikat und einen Reverse Proxy. Typischer Ablauf:

1. Beim Domainanbieter einen DNS-Eintrag auf den Internetanschluss bzw. den verwendeten Proxy setzen.
2. In QTS den **Reverse Proxy** öffnen. Die genaue Position unterscheidet sich je nach QTS-Version; häufig liegt er unter **Systemsteuerung → Netzwerk & Dateidienste → Netzwerkzugriff → Reverse Proxy**.
3. Quelle: `HTTPS`, gewünschte Domain, Port `443`.
4. Ziel: `HTTP`, QNAP-IP oder `127.0.0.1`, Port `2368`.
5. Ein gültiges Zertifikat für die Domain zuweisen.
6. `http://QNAP-IP:2380` öffnen und im Ghost QNAP Manager die Ghost-Adresse auf `https://deine-domain.de` ändern.

Nur die Ghost-Seite über den Reverse Proxy veröffentlichen. Den Manager-Port `2380` nicht veröffentlichen.

## Updates und Datensicherheit

Im Manager **Backup und Ghost aktualisieren** verwenden. Der Ablauf:

1. SQL-Backup der Ghost-Datenbank erstellen.
2. Inhaltsbackup erstellen.
3. neue kompatible Images laden;
4. nur die Container ersetzen;
5. vorhandene Volumes wieder einbinden.

Niemals diese Volumes löschen oder bei **Prune/Bereinigen/Remove volumes** auswählen:

| Volume | Inhalt |
|---|---|
| `ghost-qnap-mysql` | Beiträge, Benutzer, Tags und Einstellungen |
| `ghost-qnap-content` | Bilder, Themes und hochgeladene Dateien |
| `ghost-qnap-manager-data` | Manager-Konfiguration und Update-Backups |

Ein „Rebuild“ oder Löschen eines Containers ist nicht dasselbe wie das Löschen eines Volumes. Container sind austauschbar; die drei genannten Volumes sind deine dauerhaften Daten. Zusätzlich regelmäßig ein externes NAS-Backup bzw. einen Snapshot einrichten.

## Beiträge per Ghost Admin API

In Ghost unter **Settings → Integrations → Add custom integration** eine Integration anlegen. Den Admin API Key nur lokal speichern und niemals auf GitHub veröffentlichen. Der optionale Publisher kann Bilder hochladen und Beiträge mit Tags und Metadaten standardmäßig als Entwurf erstellen. Details stehen in `stories/example.json`.

---

# English

## What you need

- A QNAP running **Container Station 3**.
- An Intel/AMD 64-bit or ARM 64-bit processor. Old 32-bit ARM systems are unsupported.
- Internet access from the QNAP to download container images.
- The QNAP's local IP address, usually similar to `192.168.1.100`.

### Finding the QNAP IP address

It is usually visible in the browser address bar while QTS is open. Alternatively:

1. Open **Control Panel → Network & Virtual Switch → Interfaces** in QTS.
2. Note the IPv4 address of the connected network adapter.
3. Or open **Qfinder Pro** on a computer and read the NAS IP from the device list.

Typical addresses are `192.168.0.20`, `192.168.1.100`, or `10.0.0.20`. Do not use `127.0.0.1`.

## Step 1: Add the template URL

Copy this complete URL:

```text
https://raw.githubusercontent.com/therepro21/ghost-qnap-installer/main/qnap-template.json
```

Then:

1. Open QTS and start **Container Station**.
2. Open **Preferences**.
3. Select **App Templates**.
4. Enable **Custom template**.
5. Paste the URL into the custom template URL field.
6. Click **Apply**.
7. Open **App Templates → Custom Templates**.

If no template appears, open the URL in a normal browser. It should display readable JSON text. Reopen Container Station or apply the template setting again.

## Step 2: Select the processor version

- For most QNAP systems using Intel Celeron, Core, Xeon, or AMD Ryzen: **Ghost QNAP Installer (Intel/AMD64)**.
- For QNAP systems with a 64-bit ARM processor: **Ghost QNAP Installer (ARM64)**.

Find the architecture under **Control Panel → System Status → System Information** or on the QNAP product page for your model. Choosing the wrong architecture will prevent startup but does not damage Ghost data.

Click **Deploy** and normally keep these defaults:

| Value | Default | Purpose |
|---|---:|---|
| Manager port | `2380` | Setup and management interface only |
| Restart policy | `unless-stopped` | Automatically starts after a NAS restart |
| Manager volume | `ghost-qnap-manager-data` | Configuration and update backups |

Wait one or two minutes, then open `http://QNAP-IP:2380`, for example:

```text
http://192.168.1.100:2380
```

Never forward port `2380` through your router. The manager must remain accessible only on a trusted local network.

## Step 3: Setup values

Every configurable value has a small **?** button. Click or focus it to see beginner-friendly explanations in German and English.

### Ghost URL

Without a domain, this is usually correct:

```text
http://YOUR-QNAP-IP:2368
```

Example: `http://192.168.1.100:2368`.

Always include `http://` or `https://`, include the Ghost port when using a local IP, and omit the trailing slash. Do not use the manager URL on port `2380`.

### Ghost port

The default and usually correct value is `2368`. Change it only if Container Station reports that it is already occupied. If changed, use the same number in the local Ghost URL.

### Manager password

Create a new password of at least 12 characters, preferably 16 or more, and save it in a password manager. It protects the QNAP manager and is separate from the Ghost Admin password.

Click **Install Ghost**. Database passwords are generated automatically. The initial MySQL and Ghost startup can take several minutes.

## Step 4: Create the Ghost administrator

1. Open `http://QNAP-IP:2368/ghost`.
2. Follow the Ghost setup wizard.
3. Set the administrator name, email, and a new Ghost Admin password.

## Adding a domain later

A domain also requires DNS, a TLS certificate, and a reverse proxy:

1. Point the domain's DNS record at the connection or proxy being used.
2. Open the QTS **Reverse Proxy** settings. The exact location varies; it is commonly under **Control Panel → Network & File Services → Network Access → Reverse Proxy**.
3. Source: `HTTPS`, your domain, port `443`.
4. Destination: `HTTP`, QNAP IP or `127.0.0.1`, port `2368`.
5. Assign a valid certificate for the domain.
6. Open `http://QNAP-IP:2380` and change the Ghost URL to `https://your-domain.com`.

Expose only Ghost through the reverse proxy. Never expose manager port `2380`.

## Updates and persistent data

Use **Backup and update Ghost** in the manager. It creates database and content backups, pulls compatible images, replaces only containers, and reconnects the existing volumes.

Never delete or select these volumes during **Prune/Cleanup/Remove volumes**:

| Volume | Contents |
|---|---|
| `ghost-qnap-mysql` | Posts, users, tags, and settings |
| `ghost-qnap-content` | Images, themes, and uploaded files |
| `ghost-qnap-manager-data` | Manager configuration and update backups |

Containers are replaceable; these volumes contain the permanent data. Configure an additional external NAS backup or snapshot as well.

## License and liability

The installer code is available under the [MIT License](LICENSE). Third-party licenses and trademark notices are listed in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). The software is provided without warranty. The integrated update backup does not replace a separate backup strategy.
