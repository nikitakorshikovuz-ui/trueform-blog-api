import requests
from bs4 import BeautifulSoup
import json
import os
import re

CHANNEL_URL = "https://t.me/s/sportpittrueform"
OUTPUT_FILE = "telegram_blog_data.json"
IMAGES_DIR = "images"
# Ваша постоянная ссылка на картинки в GitHub
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/nikitakorshikovuz-ui/trueform-blog-api/main/images/"

def parse_telegram():
    existing_data = []
    # 1. Загружаем старые посты
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception:
            pass
            
    existing_ids = {post.get('id') for post in existing_data if post.get('id')}
    
    # 2. Создаем папку для картинок, если её нет
    if not os.path.exists(IMAGES_DIR):
        os.makedirs(IMAGES_DIR)
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
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
        msg_el = msg.find("div", class_="tgme_widget_message")
        post_id = msg_el["data-post"] if msg_el and "data-post" in msg_el.attrs else ""
        if not post_id: continue
            
        # Защита: Если пост уже есть — пропускаем!
        if post_id in existing_ids:
            continue

        text_el = msg.find("div", class_="tgme_widget_message_text")
        if not text_el: continue
        clean_text = text_el.decode_contents()
        
        # 3. НАХОДИМ И СКАЧИВАЕМ КАРТИНКУ НАВЕЧНО
        img_el = msg.find("a", class_="tgme_widget_message_photo_wrap")
        final_image_url = ""
        
        if img_el and "style" in img_el.attrs:
            match = re.search(r"url\(['\"]?([^'\"]+)['\"]?\)", img_el["style"])
            if match: 
                temp_url = match.group(1)
                img_filename = f"post_{post_id.replace('/', '_')}.jpg"
                img_path = os.path.join(IMAGES_DIR, img_filename)
                
                try:
                    # Скачиваем фото в папку
                    img_response = requests.get(temp_url, headers=headers, timeout=10)
                    if img_response.status_code == 200:
                        with open(img_path, 'wb') as f:
                            f.write(img_response.content)
                        # Сохраняем в базу постоянную ссылку на GitHub
                        final_image_url = GITHUB_RAW_BASE + img_filename
                    else:
                        final_image_url = temp_url
                except Exception:
                    final_image_url = temp_url
                
        time_el = msg.find("time", class_="time")
        post_date = time_el["datetime"] if time_el and "datetime" in time_el.attrs else ""
        post_link = f"https://t.me/{post_id}"
            
        new_posts.append({
            "id": post_id,
            "cleanText": clean_text,
            "imageUrl": final_image_url,
            "postDate": post_date,
            "postLink": post_link
        })
            
    if new_posts:
        all_posts = new_posts + existing_data
        all_posts.sort(key=lambda x: x.get('postDate', ''), reverse=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_posts, f, ensure_ascii=False, indent=2)
        print(f"Добавлено новых постов: {len(new_posts)}. Картинки скачаны.")
    else:
        print("Новых постов нет. Старые не трогаем.")

if __name__ == "__main__":
    parse_telegram()
