import os
import jwt
import time
import json
import urllib.request
from flask import Flask, request, jsonify

app = Flask(__name__)

CONTENT_KEY = "5c89dcdbd66d2a9783a7d8763a"
ADMIN_KEY = "69e2993d64d025041a09268d:81603c0315f3c5ed0974189ba9be81feed576ba4e646fde370e93ac5d16f8e06"
API_BASE = "https://mycovita.bio/ghost/api/admin"
PAGE_SLUG = "okuma-haritasi"

CATEGORIES = [
    {"id": "tur", "title": "Tur Ansiklopedileri", "emoji": "🍄", "tag": "Tur Ansiklopedileri"},
    {"id": "molekul", "title": "Molekul Ansiklopedisi", "emoji": "🔬", "tag": "Molekul Ansiklopedisi"},
    {"id": "gastro-bilim", "title": "Gastronomy Bilimi", "emoji": "🧪", "tag": "Gastronomy Bilimi"},
    {"id": "gastro", "title": "Gastronomy ve Tarifler", "emoji": "🍳", "tag": "Gastronomy"},
    {"id": "apothecary", "title": "Apothecary", "emoji": "⚗️", "tag": "Apothecary"},
    {"id": "kullanim", "title": "Kullanim Rehberleri", "emoji": "📋", "tag": "Kullanim Rehberleri"},
    {"id": "satin", "title": "Satin Alma Kilavuzu", "emoji": "🛒", "tag": "Satin Alma Kilavuzu"},
    {"id": "kutuphane", "title": "Kutuphane", "emoji": "📚", "tag": "Kutuphane"},
]

def get_token():
    key_id, secret = ADMIN_KEY.split(":")
    iat = int(time.time())
    payload = {"iat": iat, "exp": iat + 300, "aud": "/admin/"}
    return jwt.encode(payload, bytes.fromhex(secret), algorithm="HS256", headers={"kid": key_id})

def get_headers():
    return {
        "Authorization": "Ghost " + get_token(),
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

def fetch_all_posts():
    all_posts = []
    page = 1
    while True:
        url = ("https://mycovita.bio/ghost/api/content/posts/"
               "?key=" + CONTENT_KEY +
               "&limit=50&page=" + str(page) +
               "&include=tags&fields=title,slug")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
        posts = data["posts"]
        if not posts:
            break
        all_posts.extend(posts)
        if len(posts) < 50:
            break
        page += 1
    return all_posts

def build_html(all_posts):
    for cat in CATEGORIES:
        cat["posts"] = []
        for post in all_posts:
            post_tags = [t["name"] for t in post.get("tags", [])]
            if cat["tag"] in post_tags:
                slug = post["slug"]
                title = post["title"]
                cat["posts"].append({
                    "title": title,
                    "url": "https://mycovita.bio/" + slug + "/"
                })

    total = len(all_posts)

    lines = []
    lines.append('<div id="oh">')
    lines.append('<style>')
    lines.append('#oh{font-family:inherit;color:#3d2b1f;max-width:100%;box-sizing:border-box;}')
    lines.append('.oh-header{display:flex;align-items:center;justify-content:space-between;padding:20px 0 18px;border-bottom:2px solid #e8ddd3;margin-bottom:22px;flex-wrap:wrap;gap:12px;}')
    lines.append('.oh-title{font-size:1.25em;font-weight:700;color:#3d2b1f;margin:0;}')
    lines.append('.oh-stats{display:flex;gap:20px;}')
    lines.append('.oh-stat{text-align:center;background:#f5efe8;border-radius:8px;padding:6px 16px;}')
    lines.append('.oh-stat b{display:block;font-size:1.1em;font-weight:700;color:#6b4c35;}')
    lines.append('.oh-stat span{font-size:0.72em;color:#a07850;text-transform:uppercase;letter-spacing:.06em;}')
    lines.append('.oh-filters{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:24px;}')
    lines.append('@media(max-width:600px){.oh-filters{grid-template-columns:repeat(2,1fr);}}')
    lines.append('.oh-fb{display:flex;align-items:center;justify-content:center;gap:6px;padding:9px 10px;border-radius:8px;border:1.5px solid #e8ddd3;background:#fdf8f3;color:#6b4c35;font-size:0.82em;font-weight:500;cursor:pointer;font-family:inherit;transition:all .15s;text-align:center;line-height:1.3;}')
    lines.append('.oh-fb:hover{background:#f0e6d8;border-color:#a07850;}')
    lines.append('.oh-fb.on{background:#3d2b1f;color:#fdf8f3;border-color:#3d2b1f;}')
    lines.append('.oh-count{border-radius:10px;padding:1px 7px;font-size:0.85em;font-weight:600;background:#e8ddd3;color:#6b4c35;}')
    lines.append('.oh-fb.on .oh-count{background:rgba(255,255,255,0.2);color:#fdf8f3;}')
    lines.append('.oh-section{margin-bottom:16px;border:1px solid #e8ddd3;border-radius:10px;overflow:hidden;}')
    lines.append('.oh-sh{display:flex;align-items:center;justify-content:space-between;padding:13px 18px;cursor:pointer;background:#3d2b1f;transition:background .15s;}')
    lines.append('.oh-sh:hover{background:#4e3828;}')
    lines.append('.oh-sh-left{display:flex;align-items:center;gap:10px;}')
    lines.append('.oh-sh-title{font-size:0.95em;font-weight:600;color:#fdf8f3;margin:0;}')
    lines.append('.oh-sh-right{display:flex;align-items:center;gap:8px;}')
    lines.append('.oh-sh-badge{background:rgba(255,255,255,0.15);color:#f5efe8;border-radius:12px;padding:2px 10px;font-size:0.78em;font-weight:600;}')
    lines.append('.oh-sh-arrow{color:#a07850;font-size:0.9em;transition:transform .2s;}')
    lines.append('.oh-collapsed .oh-sh-arrow{transform:rotate(-90deg);}')
    lines.append('.oh-body{padding:14px 18px 16px;background:#fdf8f3;}')
    lines.append('.oh-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:7px;}')
    lines.append('@media(max-width:480px){.oh-grid{grid-template-columns:1fr;}}')
    lines.append('.oh-link{display:block;padding:9px 13px;background:white;border:1px solid #e8ddd3;border-radius:7px;color:#3d2b1f;text-decoration:none;font-size:0.84em;line-height:1.45;transition:all .12s;}')
    lines.append('.oh-link:hover{border-color:#a07850;background:#f5efe8;box-shadow:0 2px 6px rgba(61,43,31,.08);}')
    lines.append('.oh-collapsed .oh-body{display:none;}')
    lines.append('.oh-footer{text-align:center;padding:14px 0 4px;font-size:0.78em;color:#a07850;}')
    lines.append('</style>')

    lines.append('<div class="oh-header">')
    lines.append('<p class="oh-title">🗺️ Okuma Haritasi</p>')
    lines.append('<div class="oh-stats">')
    lines.append('<div class="oh-stat"><b>' + str(total) + '</b><span>Icerik</span></div>')
    lines.append('<div class="oh-stat"><b>8</b><span>Kategori</span></div>')
    lines.append('</div></div>')

    lines.append('<div class="oh-filters">')
    lines.append('<button class="oh-fb on" onclick="ohAll(this)">Tumu <span class="oh-count">' + str(total) + '</span></button>')
    for cat in CATEGORIES:
        lines.append('<button class="oh-fb" onclick="ohFilter(this,'' + cat["id"] + '')">' + cat["emoji"] + ' ' + cat["title"] + ' <span class="oh-count">' + str(len(cat["posts"])) + '</span></button>')
    lines.append('</div>')

    for cat in CATEGORIES:
        lines.append('<div class="oh-section" id="s-' + cat["id"] + '">')
        lines.append('<div class="oh-sh" onclick="ohToggle(this)">')
        lines.append('<div class="oh-sh-left"><span>' + cat["emoji"] + '</span><p class="oh-sh-title">' + cat["title"] + '</p></div>')
        lines.append('<div class="oh-sh-right"><span class="oh-sh-badge">' + str(len(cat["posts"])) + ' icerik</span><span class="oh-sh-arrow">&#9662;</span></div>')
        lines.append('</div>')
        lines.append('<div class="oh-body"><div class="oh-grid">')
        for p in cat["posts"]:
            t = p["title"].replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
            lines.append('<a class="oh-link" href="' + p["url"] + '">' + t + '</a>')
        lines.append('</div></div></div>')

    lines.append('<div class="oh-footer">Son guncelleme: <span id="oh-d"></span> - Mycovita</div>')
    lines.append('<script>')
    lines.append("document.getElementById('oh-d').textContent=new Date().toLocaleDateString('tr-TR',{day:'numeric',month:'long',year:'numeric'});")
    lines.append("function ohToggle(h){h.closest('.oh-section').classList.toggle('oh-collapsed');}")
    lines.append("function ohAll(b){document.querySelectorAll('.oh-fb').forEach(x=>x.classList.remove('on'));b.classList.add('on');document.querySelectorAll('.oh-section').forEach(s=>s.style.display='');}")
    lines.append("function ohFilter(b,id){document.querySelectorAll('.oh-fb').forEach(x=>x.classList.remove('on'));b.classList.add('on');document.querySelectorAll('.oh-section').forEach(s=>s.style.display=s.id==='s-'+id?'':'none');}")
    lines.append('</script>')
    lines.append('</div>')

    return "
".join(lines)

def get_page_info():
    url = API_BASE + "/pages/?filter=slug:" + PAGE_SLUG
    req = urllib.request.Request(url, headers=get_headers())
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    page = data["pages"][0]
    return page["id"], page["updated_at"]

def update_ghost_page(html_content):
    page_id, updated_at = get_page_info()
    lexical = json.dumps({
        "root": {
            "children": [{"type": "html", "html": html_content, "version": 1}],
            "direction": None, "format": "", "indent": 0, "type": "root", "version": 1
        }
    })
    payload = json.dumps({"pages": [{"lexical": lexical, "updated_at": updated_at}]}).encode("utf-8")
    update_url = API_BASE + "/pages/" + page_id + "/"
    req = urllib.request.Request(update_url, data=payload, headers=get_headers(), method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    try:
        posts = fetch_all_posts()
        html = build_html(posts)
        update_ghost_page(html)
        return jsonify({"status": "ok", "posts": len(posts)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "running", "service": "Mycovita Okuma Haritasi"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
