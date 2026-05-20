import re
from urllib.parse import quote, unquote

import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}


def _first_image_from_google(query: str) -> str | None:
    url = f"https://www.google.com/search?tbm=isch&q={quote(query)}"
    r = requests.get(url, headers=SEARCH_HEADERS, timeout=10)
    r.raise_for_status()
    html = r.text

    # Google embeds candidate image URLs inside arrays like ["https://...jpg",123,456]
    candidates = re.findall(
        r'\["(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))",\s*\d+,\s*\d+\]',
        html,
        flags=re.IGNORECASE,
    )
    for c in candidates:
        if "gstatic.com" in c or "google.com" in c:
            continue
        return c

    # Fallback: imgres?imgurl=... links in the HTML
    for m in re.findall(r"/imgres\?imgurl=([^&]+)&", html):
        decoded = unquote(m)
        if decoded.startswith("http"):
            return decoded

    return None


def _first_image_from_duckduckgo(query: str) -> str | None:
    # vqd token
    token_resp = requests.post(
        "https://duckduckgo.com/",
        data={"q": query},
        headers=SEARCH_HEADERS,
        timeout=10,
    )
    m = re.search(r"vqd=([\d-]+)\&", token_resp.text) or re.search(
        r'vqd="([\d-]+)"', token_resp.text
    )
    if not m:
        return None
    vqd = m.group(1)

    api = (
        "https://duckduckgo.com/i.js"
        f"?l=tr-tr&o=json&q={quote(query)}&vqd={vqd}&f=,,,,,&p=1"
    )
    headers = {**SEARCH_HEADERS, "Referer": "https://duckduckgo.com/"}
    data = requests.get(api, headers=headers, timeout=10).json()
    results = data.get("results") or []
    if results:
        return results[0].get("image") or results[0].get("thumbnail")
    return None


def find_first_image(query: str) -> str | None:
    try:
        img = _first_image_from_google(query)
        if img:
            return img
    except Exception:
        pass
    try:
        return _first_image_from_duckduckgo(query)
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/suggest")
def suggest():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Metin boş olamaz."}), 400

    image = find_first_image(query)
    if not image:
        return jsonify({"error": "Resim bulunamadı."}), 404
    return jsonify({"image": image, "query": query})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
