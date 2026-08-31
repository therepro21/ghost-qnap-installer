import gzip, hmac, json, os, re, secrets, subprocess
from datetime import datetime
from html import escape
from flask import Flask, request, Response, redirect

app = Flask(__name__)
STATE = "/data/settings.json"

def load():
    try:
        with open(STATE, encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return {}

def run(*args, check=True):
    return subprocess.run(["docker", *args], text=True, capture_output=True, check=check)

def ensure(name, *args):
    run("rm", "-f", name, check=False)
    run("run", "-d", "--name", name, "--restart", "unless-stopped", *args)

def deploy(s):
    run("network", "create", "ghost-qnap", check=False)
    run("volume", "create", "ghost-qnap-mysql")
    run("volume", "create", "ghost-qnap-content")
    ensure("ghost-qnap-db", "--network", "ghost-qnap", "-e", "MYSQL_DATABASE=ghost", "-e", "MYSQL_USER=ghost",
           "-e", f"MYSQL_PASSWORD={s['db_password']}", "-e", f"MYSQL_ROOT_PASSWORD={s['root_password']}",
           "-v", "ghost-qnap-mysql:/var/lib/mysql", "mysql:8.4")
    ensure("ghost-qnap-app", "--network", "ghost-qnap", "-p", f"{s['port']}:2368",
           "-e", "database__client=mysql", "-e", "database__connection__host=ghost-qnap-db",
           "-e", "database__connection__user=ghost", "-e", f"database__connection__password={s['db_password']}",
           "-e", "database__connection__database=ghost", "-e", f"url={s['url']}",
           "-v", "ghost-qnap-content:/var/lib/ghost/content", "ghost:6-alpine")

def backup(s):
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.makedirs("/data/backups", exist_ok=True)
    dump = run("exec", "ghost-qnap-db", "mysqldump", "-uroot", f"-p{s['root_password']}", "--single-transaction", "ghost").stdout.encode()
    with gzip.open(f"/data/backups/ghost-{stamp}.sql.gz", "wb") as f: f.write(dump)
    run("run", "--rm", "-v", "ghost-qnap-content:/source:ro", "-v", "ghost-qnap-manager-data:/backup",
        "alpine:3.22", "tar", "-czf", f"/backup/backups/content-{stamp}.tar.gz", "-C", "/source", ".")

@app.before_request
def auth():
    s = load()
    if not s or request.path == "/setup": return None
    a = request.authorization
    if not a or not hmac.compare_digest(a.password, s["manager_password"]):
        return Response("Anmeldung erforderlich", 401, {"WWW-Authenticate": 'Basic realm="Ghost QNAP Manager"'})

def html(body):
    return f'''<!doctype html><html lang="de"><meta name="viewport" content="width=device-width"><title>Ghost QNAP Setup</title>
    <style>body{{font:16px system-ui;background:#f3f5f7;margin:0;color:#20242b}}main{{max-width:680px;margin:5vh auto;background:#fff;padding:32px;border-radius:18px;box-shadow:0 8px 30px #0002}}.field-label{{display:flex;align-items:center;gap:8px;font-weight:700;margin:18px 0 6px}}input{{width:100%;box-sizing:border-box;padding:12px;border:1px solid #bbc2cc;border-radius:9px;font-size:16px}}button{{margin:22px 8px 0 0;padding:13px 18px;border:0;border-radius:9px;background:#30cf82;font-weight:750;cursor:pointer}}small{{color:#647080}}details.help{{position:relative;display:inline-block}}details.help summary{{display:grid;place-items:center;width:21px;height:21px;border-radius:50%;background:#e7ebef;color:#34404c;cursor:pointer;list-style:none;font-size:13px}}details.help summary::-webkit-details-marker{{display:none}}details.help div{{position:absolute;z-index:10;left:28px;top:-8px;width:min(420px,70vw);padding:14px;background:#17212b;color:white;border-radius:10px;box-shadow:0 8px 24px #0004;font-weight:400;line-height:1.4}}details.help p{{margin:0 0 9px}}details.help p:last-child{{margin:0}}code{{overflow-wrap:anywhere}}@media(max-width:600px){{main{{margin:0;padding:22px;border-radius:0;min-height:100vh}}details.help div{{position:fixed;left:5vw;right:5vw;top:15vh;width:auto}}}}</style><main>{body}</main></html>'''

def label(text, de, en):
    return f'''<div class="field-label"><label>{text}</label><details class="help"><summary aria-label="Hilfe / Help">?</summary><div><p><strong>Deutsch:</strong> {de}</p><p><strong>English:</strong> {en}</p></div></details></div>'''

def values(form):
    url = form.get("url", "").strip().rstrip("/")
    port = form.get("port", "").strip()
    if not re.match(r"^https?://[^\s/]+(?::\d+)?$", url) or not port.isdigit() or not 1 <= int(port) <= 65535:
        raise ValueError("Ungültige Ghost-Adresse oder Port / Invalid Ghost URL or port")
    return url, int(port)

@app.get("/")
def home():
    s = load()
    if not s: return redirect("/setup")
    url = escape(str(s["url"]), quote=True); port = escape(str(s["port"]), quote=True)
    return html(f'''<h1>Ghost QNAP Manager</h1><p>Ghost: <a href="{url}">{url}</a></p>
    <p><strong>Deine Inhalte bleiben in getrennten Docker-Volumes erhalten.</strong> In Container Station niemals die Volumes <code>ghost-qnap-mysql</code>, <code>ghost-qnap-content</code> oder <code>ghost-qnap-manager-data</code> löschen.</p>
    <form method="post" action="/apply">{label('Ghost-Adresse / Ghost URL', 'Die vollständige Adresse, unter der Leser Ghost öffnen. Ohne Domain meistens <code>http://QNAP-IP:2368</code>. Die QNAP-IP steht in QTS unter Systemsteuerung → Netzwerk & virtueller Switch. Mit Domain meistens <code>https://blog.example.de</code>. Kein Schrägstrich am Ende.', 'The complete address readers use to open Ghost. Without a domain this is usually <code>http://QNAP-IP:2368</code>. Find the QNAP IP in QTS under Control Panel → Network & Virtual Switch. With a domain use something like <code>https://blog.example.com</code>. Do not add a trailing slash.')}
    <input name="url" value="{url}" placeholder="http://192.168.1.100:2368" required>
    {label('Ghost-Port', 'Der freie Netzwerk-Port auf der QNAP. Standard und meistens richtig: <code>2368</code>. Nur ändern, wenn dieser Port bereits belegt ist. Bei einer Änderung muss dieselbe Portnummer auch in der Ghost-Adresse stehen.', 'The free network port on the QNAP. The standard and usually correct value is <code>2368</code>. Change it only if that port is already in use. If changed, the Ghost URL must contain the same port.')}
    <input name="port" type="number" min="1" max="65535" value="{port}" required><button>Änderung übernehmen / Apply changes</button></form>
    <form method="post" action="/update"><button>Backup und Ghost aktualisieren</button></form><p><small>Das Update löscht und ersetzt nur Container, niemals die persistenten Volumes.</small></p>''')

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if load(): return redirect("/")
    if request.method == "POST":
        try: url, port = values(request.form)
        except ValueError as e: return html(f"<h1>Fehler / Error</h1><p>{escape(str(e))}</p><p><a href='/setup'>Zurück / Back</a></p>"), 400
        s = {"url": url, "port": port,
             "manager_password": request.form["password"], "db_password": secrets.token_urlsafe(32),
             "root_password": secrets.token_urlsafe(32)}
        os.makedirs("/data", exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f: json.dump(s, f)
        deploy(s); return redirect("/")
    return html(f'''<h1>Ghost auf QNAP einrichten</h1><p>Für den Start ohne Domain die interne QNAP-IP verwenden. Klicke auf <strong>?</strong> für eine Erklärung auf Deutsch und Englisch.</p>
    <form method="post">{label('Ghost-Adresse / Ghost URL', 'Die Adresse, die du später im Browser eingibst. Meistens zuerst <code>http://DEINE-QNAP-IP:2368</code>, zum Beispiel <code>http://192.168.1.100:2368</code>. Deine QNAP-IP findest du in QTS unter Systemsteuerung → Netzwerk & virtueller Switch oder in Qfinder Pro. Wenn bereits Domain, Zertifikat und Reverse Proxy eingerichtet sind, verwende <code>https://deine-domain.de</code>.', 'The address you will enter in your browser. Initially this is usually <code>http://YOUR-QNAP-IP:2368</code>, for example <code>http://192.168.1.100:2368</code>. Find the QNAP IP in QTS under Control Panel → Network & Virtual Switch or in Qfinder Pro. If domain, certificate and reverse proxy are already configured, use <code>https://your-domain.com</code>.')}
    <input name="url" placeholder="http://192.168.1.100:2368" required>
    {label('Ghost-Port', 'Standard: <code>2368</code>. Dies ist die Türnummer, über die Ghost im Heimnetz erreichbar ist. Lass den Wert unverändert, solange Container Station keinen Portkonflikt meldet.', 'Default: <code>2368</code>. This is the network door used to reach Ghost on your local network. Leave it unchanged unless Container Station reports a port conflict.')}
    <input name="port" type="number" min="1" max="65535" value="2368" required>
    {label('Manager-Kennwort / Manager password', 'Ein neues Kennwort nur für diesen Installationshelfer. Es ist nicht das spätere Ghost-Admin-Kennwort. Mindestens 12 Zeichen; am besten 16 oder mehr mit mehreren zufälligen Wörtern. Sicher im Passwortmanager speichern.', 'A new password used only for this setup manager. It is not the later Ghost Admin password. Use at least 12 characters, preferably 16 or more with several random words, and store it in a password manager.')}
    <input name="password" type="password" minlength="12" autocomplete="new-password" required>
    <button>Ghost installieren / Install Ghost</button></form>''')

@app.post("/apply")
def apply():
    try: url, port = values(request.form)
    except ValueError as e: return html(f"<h1>Fehler / Error</h1><p>{escape(str(e))}</p><p><a href='/'>Zurück / Back</a></p>"), 400
    s = load(); s["url"] = url; s["port"] = port
    with open(STATE, "w", encoding="utf-8") as f: json.dump(s, f)
    deploy(s); return redirect("/")

@app.post("/update")
def update():
    s = load(); backup(s); run("pull", "ghost:6-alpine"); run("pull", "mysql:8.4"); deploy(s); return redirect("/")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2380)
