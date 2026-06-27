import os
import json
import re
import requests
from bs4 import BeautifulSoup

# --- Конфигурация ---
CHANNEL_URL = 'https://t.me/s/sportpittrueform'
JSON_FILE = 'telegram_blog_data.json'
IMAGES_DIR = 'images'
GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/nikitakorshikovuz-ui/trueform-blog-api/main/images/'

def main():
    os.makedirs(IMAGES_DIR, exist_ok=True)

    existing_posts = []
    existing_ids = set()
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, 'r', encoding='utf-8') as f:
                existing_posts = json.load(f)
                existing_ids = {post['id'] for post in existing_posts}
        except json.JSONDecodeError:
            pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(CHANNEL_URL, headers=headers)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Ошибка сети: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    messages = soup.find_all('div', class_='tgme_widget_message')

    new_posts = []

    for msg in messages:
        post_path = msg.get('data-post', '')
        if not post_path:
            continue
        
        try:
            post_id = int(post_path.split('/')[-1])
        except ValueError:
            continue

        # ЗАЩИТА: Если пост уже есть в базе - мы его не трогаем.
        if post_id in existing_ids:
            continue

        # Получаем текст
        text_elem = msg.find('div', class_='tgme_widget_message_text')
        html_text = ""
        if text_elem:
            raw_text = text_elem.get_text(separator='\n', strip=True)
            paragraphs = raw_text.split('\n')
            html_text = ''.join(f'<p>{p.strip()}</p>' for p in paragraphs if p.strip())

        if not html_text:
            continue

        date_elem = msg.find('time', class_='datetime')
        post_date = date_elem.get('datetime', '') if date_elem else ''
        post_link = f"https://t.me/{post_path}"

        image_url = ""
        tg_img_url = ""
        
        # === АГРЕССИВНЫЙ ПОИСК КАРТИНОК ===
        # 1. Ищем любые элементы со стилем background-image
        elements_with_style = msg.find_all(style=True)
        for el in elements_with_style:
            style_attr = el['style']
            if 'background-image' in style_attr:
                urls = re.findall(r"url\(['\"]?([^'\")]+)['\"]?\)", style_attr)
                if urls:
                    tg_img_url = urls[0]
                    break # Нашли картинку - выходим из цикла
        
        # 2. Если не нашли в стилях, ищем обычный тег img
        if not tg_img_url:
            img_tag = msg.find('img')
            if img_tag and img_tag.get('src'):
                tg_img_url = img_tag['src']

        # Если картинка найдена - скачиваем её
        if tg_img_url:
            img_filename = f"post_{post_id}.jpg"
            img_filepath = os.path.join(IMAGES_DIR, img_filename)
            
            try:
                img_response = requests.get(tg_img_url, headers=headers)
                img_response.raise_for_status()
                with open(img_filepath, 'wb') as img_file:
                    img_file.write(img_response.content)
                image_url = f"{GITHUB_RAW_BASE}{img_filename}" # Ссылка для сайта
            except Exception:
                pass

        post_data = {
            'id': post_id,
            'date': post_date,
            'link': post_link,
            'text_html': html_text,
            'image': image_url
        }
        new_posts.append(post_data)

    if new_posts:
        new_posts.reverse() # Свежие сверху
        final_posts = new_posts + existing_posts
        
        with open(JSON_FILE, 'w', encoding='utf-8') as f:
            json.dump(final_posts, f, ensure_ascii=False, indent=4)
        print(f"Добавлено {len(new_posts)} новых постов.")

if __name__ == '__main__':
    main()
