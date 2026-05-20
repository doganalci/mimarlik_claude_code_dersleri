import os
import re
from urllib.parse import quote, unquote

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()
# Kullanıcı .env yerine .env.example'a key yazarsa da çalışsın
if not os.environ.get("OPENAI_API_KEY") and os.path.exists(".env.example"):
    load_dotenv(".env.example")

app = Flask(__name__)

if not os.environ.get("OPENAI_API_KEY"):
    print(
        "[uyarı] OPENAI_API_KEY bulunamadı. .env dosyasına ekle "
        "(cp .env.example .env, sonra düzenle)."
    )

SEARCH_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
}

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
_openai_client: OpenAI | None = None


def get_openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError(
                "OPENAI_API_KEY tanımlı değil. .env dosyasına ekle."
            )
        _openai_client = OpenAI()
    return _openai_client


KEYWORD_PROMPT = (
    "Aşağıdaki metni özetleyen, Google Görseller'de iyi sonuç verecek "
    "kısa bir arama terimi üret. Sadece terimi döndür, başka hiçbir şey yazma. "
    "2-5 kelime, tırnaksız, noktasız."
)


def extract_search_query(text: str) -> str:
    client = get_openai()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": KEYWORD_PROMPT},
            {"role": "user", "content": text},
        ],
        temperature=0.2,
        max_tokens=30,
    )
    raw = (resp.choices[0].message.content or "").strip()
    # tek satır, tırnak/nokta temizliği
    raw = raw.splitlines()[0] if raw else ""
    return raw.strip().strip('"').strip("'").rstrip(".")


def _first_image_from_google(query: str) -> str | None:
    url = f"https://www.google.com/search?tbm=isch&q={quote(query)}"
    r = requests.get(url, headers=SEARCH_HEADERS, timeout=10)
    r.raise_for_status()
    html = r.text

    candidates = re.findall(
        r'\["(https?://[^"]+?\.(?:jpg|jpeg|png|gif|webp))",\s*\d+,\s*\d+\]',
        html,
        flags=re.IGNORECASE,
    )
    for c in candidates:
        if "gstatic.com" in c or "google.com" in c:
            continue
        return c

    for m in re.findall(r"/imgres\?imgurl=([^&]+)&", html):
        decoded = unquote(m)
        if decoded.startswith("http"):
            return decoded

    return None


def _first_image_from_duckduckgo(query: str) -> str | None:
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
    text = (payload.get("query") or "").strip()
    if not text:
        return jsonify({"error": "Metin boş olamaz."}), 400

    try:
        search_query = extract_search_query(text)
    except Exception as e:
        return jsonify({"error": f"Anahtar kelime çıkarılamadı: {e}"}), 500

    if not search_query:
        return jsonify({"error": "Anahtar kelime üretilemedi."}), 500

    image = find_first_image(search_query)
    if not image:
        return jsonify(
            {"error": "Resim bulunamadı.", "search_query": search_query}
        ), 404
    return jsonify({"image": image, "search_query": search_query})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
