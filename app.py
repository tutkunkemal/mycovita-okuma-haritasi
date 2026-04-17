import os
import jwt
import time
import json
import threading
import urllib.request
from datetime import datetime as dt
from flask import Flask, request, jsonify

app = Flask(__name__)
_lock = threading.Lock()
_is_running = False
_last_run = 0
COOLDOWN = 10 

# --- GÜNCEL KİMLİK BİLGİLERİ ---
GHOST_ADMIN_KEY = "69e2af5d64d025041a0926d4:f7fda60b647910a1ca48a3e3e2d85d4d0a0fb809053d440d1c8504c5834497c6"
CF_PURGE_TOKEN = "cfut_2NSq4j7YAHlLf8et14ZsIqOzJY7Or5sivknqFKcN0c1a282a"
CF_ZONE_ID = "fc8d8c7fb7e28e12ff78e2db466c4674"
API_BASE = "https://mycovita.bio/ghost/api/admin"
PAGE_SLUG = "okuma-haritasi"
SITE_URL = "https://mycovita.bio"

def get_headers():
    """Ghost Admin API için güncel JWT üretir."""
    id, secret = GHOST_ADMIN_KEY.split(':')
    iat = int(dt.now().timestamp())
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/admin/'
    }
    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json'
    }

def purge_cloudflare_cache():
    """Cloudflare üzerindeki ilgili sayfanın önbelleğini temizler."""
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/purge_cache"
    # Sadece okuma-haritasi sayfasını temizleyerek sistemi yormuyoruz
    data = json.dumps({
        "files": [f"{SITE_URL}/{PAGE_SLUG}/"]
    }).encode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {CF_PURGE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Cloudflare Purge Hatası: {str(e)}")
        return None

def fetch_all_posts():
    """Ghost'tan tüm yayınlanmış yazıları çeker."""
    url = f"{API_BASE}/posts/?limit=all&fields=title,slug,status"
    req = urllib.request.Request(url, headers=get_headers())
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())['posts']

def build_html(posts):
    """Yazıları liste formatında HTML'e döker."""
    html = '<div class="gh-content gh-canvas"><h2>📖 Mycovita Okuma Haritası</h2><ul>'
    count = 0
    for post in posts:
        if post['status'] == 'published':
            html += f'<li><a href="/{post["slug"]}/">{post["title"]}</a></li>'
            count += 1
    html += '</ul>'
    html += f'<p style="font-size: 0.8em; color: gray;">Son Otomatik Güncelleme: {dt.now().strftime("%d/%m/%Y %H:%M")} ({count} Yazı)</p></div>'
    return html

def get_page_info():
    """Sayfanın ID ve updated_at bilgisini Conflict'i önlemek için taze çeker."""
    url = f"{API_BASE}/pages/?filter=slug:{PAGE_SLUG}&fields=id,updated_at"
    req = urllib.request.Request(url, headers=get_headers())
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if not data["pages"]:
        raise Exception(f"Ghost üzerinde '{PAGE_SLUG}' sluglı bir sayfa bulunamadı!")
    return data["pages"][0]["id"], data["pages"][0]["updated_at"]

def update_ghost_page(html_content):
    """Ghost sayfasını Lexical formatında günceller ve ardından Cache temizler."""
    lexical = json.dumps({
        "root": {
            "children": [{"type": "html", "html": html_content, "version": 1}],
            "direction": None, "format": "", "indent": 0, "type": "root", "version": 1
        }
    })
    
    # 409 Conflict Hatası için Retry Mekanizması
    for attempt in range(3):
        try:
            p_id, updated_at = get_page_info()
            payload = json.dumps({
                "pages": [{"lexical": lexical, "updated_at": updated_at}]
            }).encode("utf-8")
            
            req = urllib.request.Request(f"{API_BASE}/pages/{p_id}/", data=payload, headers=get_headers(), method="PUT")
            with urllib.request.urlopen(req) as resp:
                # Ghost başarıyla güncellendi, şimdi Cloudflare'i temizle
                purge_cloudflare_cache()
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code == 409 and attempt < 2:
                time.sleep(2) # Ghost'un veritabanını senkronize etmesi için kısa bekleme
                continue
            raise e

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    global _is_running, _last_run
    now = time.time()
    
    with _lock:
        if now - _last_run < COOLDOWN:
            return jsonify({"status": "skipped", "msg": "Sakin ol şampiyon, cooldown aktif."}), 200
        if _is_running:
            return jsonify({"status": "skipped", "msg": "İşlem zaten devam ediyor."}), 200
        _is_running, _last_run = True, now
    
    try:
        posts = fetch_all_posts()
        update_ghost_page(build_html(posts))
        return jsonify({"status": "ok", "message": "Okuma haritası güncellendi ve cache temizlendi."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        _is_running = False

if __name__ == "__main__":
    # Render'ın dinamik port atamasına uyum sağlar
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
