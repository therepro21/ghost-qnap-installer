import gzip, hmac, json, os, secrets, subprocess
from datetime import datetime
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
    <style>body{{font:16px system-ui;background:#f3f5f7;margin:0;color:#20242b}}main{{max-width:650px;margin:5vh auto;background:#fff;padding:32px;border-radius:18px;box-shadow:0 8px 30px #0002}}label{{display:block;font-weight:700;margin:18px 0 6px}}input{{width:100%;box-sizing:border-box;padding:12px;border:1px solid #bbc2cc;border-radius:9px;font-size:16px}}button{{margin:22px 8px 0 0;padding:13px 18px;border:0;border-radius:9px;background:#30cf82;font-weight:750;cursor:pointer}}small{{color:#647080}}</style><main>{body}</main></html>'''

@app.get("/")
def home():
    s = load()
    if not s: return redirect("/setup")
    return html(f'''<h1>Ghost QNAP Manager</h1><p>Ghost: <a href="{s['url']}">{s['url']}</a></p>
    <form method="post" action="/apply"><label>Ghost-Adresse</label><input name="url" value="{s['url']}" required>
    <label>Port</label><input name="port" type="number" value="{s['port']}" required><button>Änderung übernehmen</button></form>
    <form method="post" action="/update"><button>Backup und Ghost aktualisieren</button></form>''')

@app.route("/setup", methods=["GET", "POST"])
def setup():
    if load(): return redirect("/")
    if request.method == "POST":
        s = {"url": request.form["url"].rstrip("/"), "port": int(request.form["port"]),
             "manager_password": request.form["password"], "db_password": secrets.token_urlsafe(32),
             "root_password": secrets.token_urlsafe(32)}
        os.makedirs("/data", exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as f: json.dump(s, f)
        deploy(s); return redirect("/")
    return html('''<h1>Ghost auf QNAP einrichten</h1><p>Für den Start ohne Domain die interne QNAP-IP verwenden.</p>
    <form method="post"><label>Ghost-Adresse</label><input name="url" placeholder="http://192.168.1.100:2368" required>
    <label>Ghost-Port</label><input name="port" type="number" value="2368" required>
    <label>Manager-Kennwort</label><input name="password" type="password" minlength="12" required>
    <button>Ghost installieren</button></form>''')

@app.post("/apply")
def apply():
    s = load(); s["url"] = request.form["url"].rstrip("/"); s["port"] = int(request.form["port"])
    with open(STATE, "w", encoding="utf-8") as f: json.dump(s, f)
    deploy(s); return redirect("/")

@app.post("/update")
def update():
    s = load(); backup(s); run("pull", "ghost:6-alpine"); run("pull", "mysql:8.4"); deploy(s); return redirect("/")

app.run(host="0.0.0.0", port=2380)
