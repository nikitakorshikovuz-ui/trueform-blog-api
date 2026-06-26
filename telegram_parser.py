import requests
from bs4 import BeautifulSoup
import json
import os
import re

CHANNEL_URL = "https://t.me/s/sportpittrueform"
OUTPUT_FILE = "telegram_blog_data.json"

def parse_telegram():
    existing_data = []
    # 1. Загружаем уже существующие посты
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    # Собираем ID существующих постов, чтобы их не трогать
    existing_ids = {post.get('id') for post in existing_data if post.get('id')}
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers, timeout=10)
        response.raise_for_status()
    except Exception as e:
        print(f"Ошибка загрузки Telegram: {e}")
        return
        
    soup = BeautifulSoup(response.text, "html.parser")
    messages = soup.find_all("div", class_="tgme_widget_message_wrap")
    
    new_posts = []
    for msg in messages:
        # Получаем ID поста
        msg_el = msg.find("div", class_="tgme_widget_message")
        post_id = msg_el["data-post"] if msg_el and "data-post" in msg_el.attrs else ""
        if not post_id: continue
            
        # 2. ГЛАВНАЯ ЗАЩИТА: Если пост уже есть в базе — пропускаем его (не меняем)
        if post_id in existing_ids:
            continue

        # Парсим текст
        text_el = msg.find("div", class_="tgme_widget_message_text")
        if not text_el: continue
        clean_text = text_el.decode_contents()
        
        # Парсим картинку (улучшенное регулярное выражение)
        img_el = msg.find("a", class_="tgme_widget_message_photo_wrap")
        image_url = ""
        if img_el and "style" in img_el.attrs:
            match = re.search(r"url\(['\"]?([^'\"]+)['\"]?\)", img_el["style"])
            if match: image_url = match.group(1)
                
        # Парсим дату
        time_el = msg.find("time", class_="time")
        post_date = time_el["datetime"] if time_el and "datetime" in time_el.attrs else ""
        
        post_link = f"https://t.me/{post_id}"
            
        new_posts.append({
            "id": post_id,
            "cleanText": clean_text,
            "imageUrl": image_url,
            "postDate": post_date,
            "postLink": post_link
        })
            
    if new_posts:
        # 3. Добавляем ТОЛЬКО новые посты в начало списка
        all_posts = new_posts + existing_data
        # Сортируем по дате для надежности
        all_posts.sort(key=lambda x: x.get('postDate', ''), reverse=True)
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
        print(f"Добавлено новых постов: {len(new_posts)}. Всего в базе: {len(all_posts)}")
    else:
        print(f"Новых постов нет. В базе сохранено {len(existing_data)} постов.")

if __name__ == "__main__":
    parse_telegram()
