# Metin & Resim Önerisi

Basit Flask uygulaması: solda metin yazarsın, butona basınca GPT-4o-mini metinden Google Görsel arama terimi çıkarır ve dönen ilk resmi sağda gösterir. Google başarısız olursa DuckDuckGo'ya düşer.

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
# .env içine OPENAI_API_KEY=... ekle
python app.py
```

Sonra tarayıcıdan `http://localhost:5001`.

`PORT` env var ile portu değiştirebilirsin (`PORT=8000 python app.py`).
`OPENAI_MODEL` ile modeli değiştirebilirsin (varsayılan `gpt-4o-mini`).

> macOS'te 5000 portunu AirPlay Receiver tutar; varsayılan 5001.
