import feedparser
from bs4 import BeautifulSoup
import json
import re
import math
from datetime import datetime

DZEN_RSS_URL = "https://dzen.ru/rss/author/699c22fc64a8661012fa62ed"
OUTPUT_FILE = "trueform_blog_data.json"

CATEGORIES_MAP = {
    "ПП-рецепты": ["рецепт", "приготовить", "блюдо", "кухня", "завтрак"],
    "Похудение": ["похудение", "жиросжигатель", "диета", "калории", "вес", "перекус", "фигура"],
    "Набор массы": ["набор", "масса", "мышцы", "гейнер", "креатин", "рост", "протеин"],
    "Здоровье": ["витамины", "здоровье", "суставы", "омега", "сон", "восстановление", "коллаген", "opti-men"],
    "Бизнес": ["франшиза", "бизнес", "открытие", "маркетплейс", "ozon", "wildberries", "прибыль", "магазин"]
}

def transliterate(text):
    symbols = (u"абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ",
               u"abvgdeejzijklmnoprstufhzcss_y_euaABVGDEEJZIJKLMNOPRSTUFHZCSS_Y_EUA")
    tr = {ord(a): ord(b) for a, b in zip(*symbols)}
    text = text.translate(tr).lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    return re.sub(r'[\s-]+', '-', text).strip('-')

def detect_category(text, title):
    combined_text = (text + " " + title).lower()
    for category, keywords in CATEGORIES_MAP.items():
        if any(keyword in combined_text for keyword in keywords):
            return category
    return "Все"

def calculate_read_time(text):
    words = len(re.findall(r'\w+', text))
    minutes = math.ceil(words / 150)
    return f"{minutes} мин" if minutes > 0 else "1 мин"

def parse_dzen_feed():
    feed = feedparser.parse(DZEN_RSS_URL)
    blog_data = []
    
    for entry in feed.entries:
        try:
            title = entry.title
            slug = transliterate(title)
            dzen_url = entry.link
            
            parsed_date = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")
            formatted_date = parsed_date.strftime("%Y-%m-%d")
            
            soup = BeautifulSoup(entry.description, "html.parser")
            
            cover_url = "https://placehold.co/1200x600/222/B88655.webp?text=TRUEFORM+NEWS"
            img_tag = soup.find("img")
            if img_tag and img_tag.get("src"):
                cover_url = img_tag["src"]
                img_tag.decompose()
            
            raw_text = soup.get_text(separator=" ", strip=True)
            excerpt = raw_text[:160] + "..." if len(raw_text) > 160 else raw_text
            
            for tag in soup():
                for attribute in ["class", "id", "style", "data-v"]:
                    del tag[attribute]
            
            article = {
                "id": entry.id if hasattr(entry, 'id') else slug,
                "slug": slug,
                "title": title,
                "date": formatted_date,
                "readTime": calculate_read_time(raw_text),
                "category": detect_category(raw_text, title),
                "cover": cover_url,
                "excerpt": excerpt,
                "content": str(soup),
                "dzenUrl": dzen_url
            }
            blog_data.append(article)
        except Exception as e:
            pass

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(blog_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    parse_dzen_feed()
    