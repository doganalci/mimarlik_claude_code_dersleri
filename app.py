import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from openai import OpenAI

load_dotenv()
if not os.environ.get("OPENAI_API_KEY") and os.path.exists(".env.example"):
    load_dotenv(".env.example")

app = Flask(__name__)

if not os.environ.get("OPENAI_API_KEY"):
    print(
        "[uyarı] OPENAI_API_KEY bulunamadı. .env dosyasına ekle "
        "(cp .env.example .env, sonra düzenle)."
    )

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "dall-e-3")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")

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


PROMPT_SYSTEM = (
    "Aşağıdaki metni, bir görsel üretim modeline (DALL·E) verilecek "
    "kısa ve net bir İngilizce görsel açıklamasına çevir. "
    "Metnin ana fikrini ve atmosferini yakala. "
    "Sadece açıklamayı döndür, başka hiçbir şey yazma. "
    "1-2 cümle, tırnaksız."
)


def build_image_prompt(text: str) -> str:
    client = get_openai()
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=0.4,
        max_tokens=120,
    )
    raw = (resp.choices[0].message.content or "").strip()
    return raw.strip('"').strip("'")


def generate_image(prompt: str) -> str:
    client = get_openai()
    result = client.images.generate(
        model=IMAGE_MODEL,
        prompt=prompt,
        size=IMAGE_SIZE,
        n=1,
    )
    return result.data[0].url


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
        prompt = build_image_prompt(text)
    except Exception as e:
        return jsonify({"error": f"Prompt üretilemedi: {e}"}), 500

    if not prompt:
        return jsonify({"error": "Prompt boş döndü."}), 500

    try:
        image_url = generate_image(prompt)
    except Exception as e:
        return jsonify(
            {"error": f"Resim üretilemedi: {e}", "prompt": prompt}
        ), 500

    return jsonify({"image": image_url, "prompt": prompt})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=True)
