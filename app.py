import os, json, threading, time, base64, requests
from flask import Flask, request, jsonify, send_from_directory, Response

TOKEN = os.environ["BOT_TOKEN"]
ALLOWED = {int(x) for x in os.environ.get("ALLOWED_IDS", "").split(",") if x.strip()}
PASSWORD = os.environ.get("APP_PASSWORD", "")
FILE = os.environ.get("DATA_FILE", "/data/db.json")
API = f"https://api.telegram.org/bot{TOKEN}"
lock = threading.Lock()
wait = {}  # chat_id -> {"img":..., "ids": None | [yuk id lar]}
app = Flask(__name__, static_folder="static")

def load():
    try:
        return json.load(open(FILE))
    except Exception:
        return {"data": [], "rate": 11980, "v": 0}

def save(db):
    os.makedirs(os.path.dirname(FILE), exist_ok=True)
    db["v"] = db.get("v", 0) + 1
    json.dump(db, open(FILE + ".tmp", "w"))
    os.replace(FILE + ".tmp", FILE)

@app.before_request
def auth():
    if not PASSWORD:
        return
    a = request.authorization
    if not a or a.password != PASSWORD:
        return Response("Parol kerak", 401, {"WWW-Authenticate": 'Basic realm="yuk"'})

@app.get("/")
def index():
    return send_from_directory("static", "index.html")

@app.get("/api/data")
def get_data():
    with lock:
        return jsonify(load())

@app.post("/api/data")
def put_data():
    j = request.get_json()
    with lock:
        db = load()
        if j.get("v") != db.get("v"):
            return jsonify(error="stale"), 409
        db["data"], db["rate"] = j["data"], j["rate"]
        save(db)
        return jsonify(v=db["v"])

# ---------- Telegram bot ----------
def tg(method, **kw):
    return requests.post(f"{API}/{method}", json=kw, timeout=60).json()

def say(chat, text):
    tg("sendMessage", chat_id=chat, text=text)

def digits(s):
    return "".join(c for c in str(s) if c.isdigit())

def photo_data(m):
    ps = [p for p in m["photo"] if p["width"] <= 900] or m["photo"][:1]
    path = tg("getFile", file_id=ps[-1]["file_id"])["result"]["file_path"]
    r = requests.get(f"https://api.telegram.org/file/bot{TOKEN}/{path}", timeout=60)
    return "data:image/jpeg;base64," + base64.b64encode(r.content).decode()

def finish(db, x, img, chat):
    x["chk"], x["paid"] = img, True
    save(db)
    say(chat, f"✅ {x.get('nm') or 'Ismsiz'} — {x['kg']} kg to'langan deb belgilandi.")

def attach(chat, img, last4):
    with lock:
        db = load()
        hits = [x for x in db["data"] if not x.get("paid") and digits(x.get("ph", "")).endswith(last4)]
        if not hits:
            say(chat, f"…{last4} bilan tugaydigan to'lanmagan yuk topilmadi.")
        elif len(hits) == 1:
            finish(db, hits[0], img, chat)
        else:
            wait[chat] = {"img": img, "ids": [x["id"] for x in hits]}
            lst = "\n".join(f"{i+1}) {x.get('nm') or 'Ismsiz'} — {x['kg']} kg — {x.get('d','')}" for i, x in enumerate(hits))
            say(chat, f"Bir nechta topildi:\n{lst}\nQaysi biri? Raqamini yozing.")

def handle(m):
    chat, uid = m["chat"]["id"], m["from"]["id"]
    if uid not in ALLOWED:
        say(chat, f"Ruxsat yo'q. Sizning ID: {uid}")
        return
    text = (m.get("text") or m.get("caption") or "").strip()
    d = digits(text)
    if "photo" in m:
        img = photo_data(m)
        if len(d) >= 4:
            attach(chat, img, d[-4:])
        else:
            wait[chat] = {"img": img, "ids": None}
            say(chat, "Telefonning oxirgi 4 raqamini yozing.")
        return
    w = wait.get(chat)
    if not w:
        say(chat, "Chek rasmini yuboring, izohga telefonning oxirgi 4 raqamini yozing.")
    elif w["ids"] is None and len(d) == 4:
        wait.pop(chat)
        attach(chat, w["img"], d)
    elif w["ids"] and d and 1 <= int(d) <= len(w["ids"]):
        wait.pop(chat)
        with lock:
            db = load()
            x = next((y for y in db["data"] if y["id"] == w["ids"][int(d) - 1]), None)
            if x:
                finish(db, x, w["img"], chat)
    else:
        say(chat, "Tushunmadim. 4 ta raqam (yoki ro'yxatdagi raqam) yozing.")

def poll():
    off = 0
    while True:
        try:
            r = requests.post(f"{API}/getUpdates", json={"offset": off, "timeout": 30}, timeout=40).json()
            for u in r.get("result", []):
                off = u["update_id"] + 1
                if "message" in u:
                    try:
                        handle(u["message"])
                    except Exception as e:
                        print("xato:", e)
        except Exception as e:
            print("poll xato:", e)
            time.sleep(5)

threading.Thread(target=poll, daemon=True).start()
