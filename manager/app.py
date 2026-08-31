import hmac, os, re, subprocess
from flask import Flask, request, Response, redirect

app = Flask(__name__)
ENV_FILE = os.environ.get("ENV_FILE", "/project/.env")
PROJECT_DIR = os.environ.get("PROJECT_DIR", "/project")

def auth_ok():
    auth = request.authorization
    expected = os.environ.get("MANAGER_PASSWORD", "")
    return bool(auth and expected and hmac.compare_digest(auth.password, expected))

@app.before_request
def require_auth():
    if not auth_ok():
        return Response("Anmeldung erforderlich", 401, {"WWW-Authenticate": 'Basic realm="Ghost QNAP Manager"'})

def read_env():
    values = {}
    with open(ENV_FILE, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                k, v = line.rstrip("\n").split("=", 1)
                values[k] = v
    return values

def update_env(changes):
    lines = open(ENV_FILE, encoding="utf-8").read().splitlines()
    seen, out = set(), []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0]
            if key in changes:
                out.append(f"{key}={changes[key]}"); seen.add(key); continue
        out.append(line)
    out.extend(f"{k}={v}" for k, v in changes.items() if k not in seen)
    with open(ENV_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")

def page(message=""):
    env = read_env()
    url = env.get("GHOST_URL", "")
    https = "checked" if url.startswith("https://") else ""
    esc = lambda s: str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
    def help_label(title, de, en):
        return f'''<div class="field-label"><label>{title}</label><details class="help"><summary aria-label="Hilfe / Help">?</summary><div><p><strong>Deutsch:</strong> {de}</p><p><strong>English:</strong> {en}</p></div></details></div>'''
    return f'''<!doctype html><html lang="de"><meta name="viewport" content="width=device-width"><title>Ghost QNAP Manager</title>
    <style>body{{font:16px system-ui;background:#f4f5f7;color:#20242b;margin:0}}main{{max-width:680px;margin:6vh auto;background:white;padding:32px;border-radius:18px;box-shadow:0 8px 32px #0002}}.field-label{{display:flex;align-items:center;gap:8px;margin:18px 0 7px;font-weight:650}}input{{box-sizing:border-box;width:100%;padding:12px;border:1px solid #bbc2cc;border-radius:9px;font-size:16px}}button{{margin-top:24px;padding:13px 20px;border:0;border-radius:9px;background:#30cf82;color:#10251a;font-weight:750;font-size:16px;cursor:pointer}}small{{color:#647080}}.ok{{background:#e4f8ed;padding:12px;border-radius:8px}}details.help{{position:relative;display:inline-block}}details.help summary{{display:grid;place-items:center;width:21px;height:21px;border-radius:50%;background:#e7ebef;cursor:pointer;list-style:none;font-size:13px}}details.help summary::-webkit-details-marker{{display:none}}details.help div{{position:absolute;z-index:10;left:28px;top:-8px;width:min(420px,70vw);padding:14px;background:#17212b;color:white;border-radius:10px;box-shadow:0 8px 24px #0004;font-weight:400;line-height:1.4}}details.help p{{margin:0 0 9px}}details.help p:last-child{{margin:0}}@media(max-width:600px){{main{{margin:0;padding:22px;border-radius:0;min-height:100vh}}details.help div{{position:fixed;left:5vw;right:5vw;top:15vh;width:auto}}}}</style>
    <main><h1>Ghost QNAP Manager</h1>{f'<p class="ok">{esc(message)}</p>' if message else ''}
    <p>Interne IP oder öffentliche Domain eintragen. Klicke auf <strong>?</strong> für Erklärungen auf Deutsch und Englisch. Inhalte und Datenbank bleiben beim Übernehmen erhalten.</p>
    <form method="post" action="/save">{help_label('Ghost-Adresse / Ghost URL', 'Ohne Domain meistens <code>http://QNAP-IP:2368</code>. Die IP steht in QTS unter Systemsteuerung → Netzwerk & virtueller Switch oder in Qfinder Pro. Mit eingerichtetem Reverse Proxy und Zertifikat meistens <code>https://blog.example.de</code>. Immer mit <code>http://</code> oder <code>https://</code>, ohne Schrägstrich am Ende.', 'Without a domain this is usually <code>http://QNAP-IP:2368</code>. Find the IP in QTS under Control Panel → Network & Virtual Switch or in Qfinder Pro. With a configured reverse proxy and certificate use something like <code>https://blog.example.com</code>. Always include <code>http://</code> or <code>https://</code> and omit the trailing slash.')}
    <input name="url" value="{esc(url)}" placeholder="http://192.168.1.100:2368" required>
    {help_label('Ghost-Port im LAN / LAN port', 'Standard und meistens richtig: <code>2368</code>. Nur ändern, wenn der Port bereits belegt ist. Bei interner IP dieselbe Nummer auch hinter dem Doppelpunkt in der Ghost-Adresse verwenden.', 'The standard and usually correct value is <code>2368</code>. Change it only if already occupied. When using a local IP, put the same number after the colon in the Ghost URL.')}
    <input name="port" type="number" min="1" max="65535" value="{esc(env.get('GHOST_PORT','2368'))}" required>
    <button>Speichern und Ghost neu erstellen / Save and recreate</button></form>
    <p><small>Hinweis: Für HTTPS muss der QNAP-Reverse-Proxy samt Zertifikat ebenfalls auf die Domain eingerichtet sein.</small></p></main></html>'''

@app.get("/")
def home(): return page(request.args.get("message", ""))

@app.post("/save")
def save():
    url = request.form.get("url", "").strip().rstrip("/")
    port = request.form.get("port", "2368").strip()
    if not re.match(r"^https?://[^\s/]+(?::\d+)?$", url) or not port.isdigit() or not 1 <= int(port) <= 65535:
        return page("Ungültige URL oder Port."), 400
    update_env({"GHOST_URL": url, "GHOST_PORT": port})
    result = subprocess.run(["docker", "compose", "--project-directory", PROJECT_DIR, "up", "-d", "--force-recreate", "ghost"], cwd=PROJECT_DIR, text=True, capture_output=True)
    if result.returncode:
        return page("Gespeichert, aber der Neustart schlug fehl: " + result.stderr[-400:]), 500
    return redirect("/?message=Konfiguration+übernommen.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2380)
