def get_headers():
    """Ghost Admin API için JWT token üretir ve 403 hatalarını önlemek için header ekler."""
    id, secret = GHOST_ADMIN_KEY.split(':')
    # Saat farkı sorunlarını önlemek için 30 saniye geri aldık
    iat = int(dt.now().timestamp()) - 30 
    header = {'alg': 'HS256', 'typ': 'JWT', 'kid': id}
    payload = {
        'iat': iat,
        'exp': iat + 5 * 60,
        'aud': '/admin/'
    }
    
    token = jwt.encode(payload, bytes.fromhex(secret), algorithm='HS256', headers=header)
    # PyJWT sürüm farkı için string kontrolü
    if isinstance(token, bytes):
        token = token.decode('utf-8')
        
    return {
        'Authorization': f'Ghost {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def purge_cloudflare_cache():
    """Cloudflare cache temizleme (403 engeline karşı User-Agent eklendi)."""
    url = f"https://api.cloudflare.com/client/v4/zones/{CF_ZONE_ID}/purge_cache"
    data = json.dumps({"files": [f"{SITE_URL}/{PAGE_SLUG}/"]}).encode("utf-8")
    
    headers = {
        "Authorization": f"Bearer {CF_PURGE_TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "MycovitaBot/1.0" # Cloudflare için özel bir isim
    }
    
    try:
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"Cloudflare Purge Hatası: {str(e)}")
        return None
