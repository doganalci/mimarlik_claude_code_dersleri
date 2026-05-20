# Metin & Resim Önerisi

Flask uygulaması: solda metin yazarsın, butona basınca GPT-4o-mini metinden bir görsel açıklaması (prompt) üretir, DALL·E o prompt'tan resmi oluşturur. Üretilen prompt arayüzde ayrı bir kutuda gösterilir.

## Kurulum

```bash
pip install -r requirements.txt
cp .env.example .env
# .env içinde OPENAI_API_KEY=sk-... ayarla
python app.py
```

Sonra `http://localhost:5001`.

## Ayarlar (.env)

| Anahtar | Varsayılan | Açıklama |
|--|--|--|
| `OPENAI_API_KEY` | — | OpenAI API anahtarı (zorunlu) |
| `OPENAI_MODEL` | `gpt-4o-mini` | Prompt üreten chat modeli |
| `IMAGE_MODEL` | `dall-e-3` | Resim üretim modeli (`dall-e-2` daha ucuz) |
| `IMAGE_SIZE` | `1024x1024` | dall-e-3: 1024x1024, 1024x1792, 1792x1024 |
| `PORT` | `5001` | Sunucu portu |

> macOS'te 5000 portunu AirPlay tutar; varsayılan 5001.
> DALL·E 3 resim üretim maliyeti standart kalitede ~$0.04/resim.
