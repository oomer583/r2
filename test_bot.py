
#!/usr/bin/env python3
"""
============================================================
  BOT TEST ARACI — Terminalden Test Et
============================================================
Kullanım:
  1. Önce bot.py'yi çalıştır:  python bot.py
  2. Başka bir terminalde:     python test_bot.py
============================================================
"""

import requests
import json
import sys
import uuid

BASE_URL = "http://localhost:8000"
SESSION_ID = str(uuid.uuid4())

def check_bot():
    """Botun çalışıp çalışmadığını kontrol et."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        data = r.json()
        print(f"✅ Bot aktif! Site: {data['site']} | SSS: {data['faq_count']}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Bot çalışmıyor! Önce 'python bot.py' çalıştır.")
        return False
    except Exception as e:
        print(f"❌ Hata: {e}")
        return False

def send_message(message: str):
    """Bota mesaj gönder ve yanıtı göster."""
    try:
        payload = {
            "message": message,
            "session_id": SESSION_ID
        }
        r = requests.post(
            f"{BASE_URL}/chat",
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        data = r.json()
        return data.get("response", "Yanıt alınamadı.")
    except Exception as e:
        return f"Hata: {e}"

def main():
    print("=" * 60)
    print("  🤖 BOT TEST ARACI")
    print("=" * 60)
    
    if not check_bot():
        sys.exit(1)
    
    print(f"\n📌 Session ID: {SESSION_ID}")
    print("Komutlar: /quit (çık), /clear (temizle), /faq (SSS listesi)\n")
    
    while True:
        try:
            user_input = input("👤 Siz: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == "/quit":
                print("👋 Görüşmek üzere!")
                break
            
            if user_input.lower() == "/clear":
                print("\n" * 50)
                continue
            
            if user_input.lower() == "/faq":
                try:
                    r = requests.get(f"{BASE_URL}/faq")
                    data = r.json()
                    print("\n📋 Sıkça Sorulan Sorular:")
                    for i, item in enumerate(data["faq"], 1):
                        print(f"  {i}. {item['question']}")
                    print()
                except Exception as e:
                    print(f"SSS alınamadı: {e}")
                continue
            
            print("🤖 Bot yazıyor...", end="\r")
            response = send_message(user_input)
            print(" " * 30, end="\r")  # Temizle
            print(f"🤖 Bot: {response}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Görüşmek üzere!")
            break

if __name__ == "__main__":
    main()