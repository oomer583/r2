import os
import sys
import re
import time
import threading
from typing import Optional, List
from dataclasses import dataclass

from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("google-genai eksik. Kur: pip install google-genai python-dotenv")
    sys.exit(1)

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
SITE_NAME = os.getenv("SITE_NAME", "Vireon Systems")
SYSTEM_PROMPT_TEMPLATE = os.getenv("SYSTEM_PROMPT", "")
FAQ_RAW = os.getenv("FAQ_DATA", "")

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY .env dosyasında yok.")
    sys.exit(1)


@dataclass
class FAQItem:
    question: str
    answer: str


def parse_faq(data: str) -> List[FAQItem]:
    items = []
    data = data.replace("\\n", "\n")

    for line in data.strip().split("\n"):
        if "|" in line:
            q, a = line.split("|", 1)
            items.append(FAQItem(q.strip(), a.strip()))

    return items


FAQ_LIST = parse_faq(FAQ_RAW)
client = genai.Client(api_key=GEMINI_API_KEY)


def build_system_prompt() -> str:
    prompt = SYSTEM_PROMPT_TEMPLATE.replace("{site_name}", SITE_NAME)

    if FAQ_LIST:
        prompt += "\n\nSİTE SSS BİLGİLERİ:\n"
        for i, faq in enumerate(FAQ_LIST, 1):
            prompt += f"{i}. Soru: {faq.question}\nCevap: {faq.answer}\n"

    return prompt


def find_faq_answer(user_message: str) -> Optional[str]:
    user_words = set(re.findall(r"\w+", user_message.lower()))

    for faq in FAQ_LIST:
        faq_words = set(re.findall(r"\w+", faq.question.lower()))
        if faq_words and len(user_words & faq_words) / len(faq_words) > 0.5:
            return faq.answer

    return None


# 🔄 Spinner
def spinner(stop_event):
    frames = ["|", "/", "-", "\\"]
    i = 0

    while not stop_event.is_set():
        print(f"\rBot düşünüyor... {frames[i % len(frames)]}", end="", flush=True)
        i += 1
        time.sleep(0.12)


# ⌨️ Yazma efekti
def typing_effect(text, delay=0.015):
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


# 🤖 Gemini çağırma + retry
def ask_gemini(user_message: str, history: list, retries=2) -> str:
    try:
        system_text = build_system_prompt()
        faq_answer = find_faq_answer(user_message)

        if faq_answer:
            system_text += f"\n\nBu soru SSS ile benzer. İlgili cevap: {faq_answer}"

        contents = []

        for msg in history[-10:]:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part(text=msg["content"])]
                )
            )

        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(text=user_message)]
            )
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_text,
                temperature=0.7,
                max_output_tokens=2048,
            )
        )

        return response.text or "Yanıt oluşturulamadı."

    except Exception as e:
        error_text = str(e)

        # 🔥 QUOTA / RATE LIMIT
        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            if retries > 0:
                time.sleep(5)  # kısa bekleme
                return ask_gemini(user_message, history, retries - 1)

            return "AI kodu hatası. Lütfen biraz bekleyin ve yeniden deneyin."

        return "Şu anda bir sorun oluştu. Lütfen daha sonra tekrar deneyin."


def main():
    print("=" * 55)
    print(f"{SITE_NAME} Terminal Destek Botu")
    print("Model: Gemini 2.5 Flash")
    print("Çıkmak için: exit / quit / çık")
    print("=" * 55)

    print(f"\nBot: Merhaba! {SITE_NAME} destek hattına hoş geldiniz, size nasıl yardımcı olabilirim?")

    history = []

    while True:
        user_message = input("\nSen: ").strip()

        if user_message.lower() in ["exit", "quit", "çık", "cik"]:
            print("Bot kapatılıyor...")
            break

        if not user_message:
            continue

        stop_event = threading.Event()
        loading_thread = threading.Thread(target=spinner, args=(stop_event,))
        loading_thread.start()

        answer = ask_gemini(user_message, history)

        stop_event.set()
        loading_thread.join()

        print("\r" + " " * 80, end="\r")

        print("Bot: ", end="")
        typing_effect(answer)

        history.append({"role": "user", "content": user_message})
        history.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()