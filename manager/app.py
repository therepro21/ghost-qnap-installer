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
    return f'''<!doctype html><html lang="de"><meta name="viewport" content="width=device-width"><title>Ghost QNAP Manager</title>
    <style>body{{font:16px system-ui;background:#f4f5f7;color:#20242b;margin:0}}main{{max-width:650px;margin:6vh auto;background:white;padding:32px;border-radius:18px;box-shadow:0 8px 32px #0002}}label{{display:block;margin:18px 0 7px;font-weight:650}}input{{box-sizing:border-box;width:100%;padding:12px;border:1px solid #bbc2cc;border-radius:9px;font-size:16px}}button{{margin-top:24px;padding:13px 20px;border:0;border-radius:9px;background:#30cf82;color:#10251a;font-weight:750;font-size:16px;cursor:pointer}}small{{color:#647080}}.ok{{background:#e4f8ed;padding:12px;border-radius:8px}}</style>
    <main><h1>Ghost QNAP Manager</h1>{f'<p class="ok">{esc(message)}</p>' if message else ''}
    <p>Interne IP oder öffentliche Domain eintragen. Ghost wird beim Übernehmen kontrolliert neu erstellt; Inhalte und Datenbank bleiben erhalten.</p>
    <form method="post" action="/save"><label>Ghost-Adresse</label><input name="url" value="{esc(url)}" placeholder="http://192.168.1.100:2368" required>
    <small>Mit Protokoll, ohne abschließenden Schrägstrich. Für eine Domain z. B. https://blog.example.de</small>
    <label>Ghost-Port im LAN</label><input name="port" type="number" min="1" max="65535" value="{esc(env.get('GHOST_PORT','2368'))}" required>
    <button>Speichern und Ghost neu erstellen</button></form>
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

app.run(host="0.0.0.0", port=2380)

