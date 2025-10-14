from http.server import BaseHTTPRequestHandler
import json
import requests
import re
from datetime import datetime
import os

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

def process_request(self, method):
    try:
        # ДОБАВЬТЕ ЭТОТ КОД ДЛЯ ЛОГИРОВАНИЯ
        print("🚀 Функция запущена!")
        print(f"📋 BOT_TOKEN: {'установлен' if BOT_TOKEN else 'НЕ УСТАНОВЛЕН'}")
        print(f"📋 CHAT_ID: {'установлен' if CHAT_ID else 'НЕ УСТАНОВЛЕН'}")
        
        # остальной ваш код...
def format_students_table(text):
    """Форматирует сырые данные в красивую таблицу"""
    students = []
    group = None
    
    # Очищаем текст
    clean_text = text.replace('Итоги дня', '').replace('0:27', '').strip()
    words = clean_text.split()
    
    i = 0
    while i < len(words):
        # Ищем группу
        if group is None and '-' in words[i] and any(char.isdigit() for char in words[i]):
            group = words[i]
            i += 1
            continue
            
        # Ищем ФИО (три слова с заглавных)
        if (i + 2 < len(words) and 
            words[i][0].isupper() and 
            words[i+1][0].isupper() and 
            words[i+2][0].isupper()):
            
            name = f"{words[i]} {words[i+1]} {words[i+2]}"
            status = "Пришёл"  # по умолчанию
            
            # Ищем статус
            if i + 3 < len(words) and words[i+3] in ['Болеет', 'Прогул', 'Академ', 'ИГ', 'Заявление', 'Пришёл']:
                status = words[i+3]
                i += 4
            else:
                i += 3
                
            students.append({"name": name, "status": status})
        else:
            i += 1
    
    if not students:
        return "❌ Не удалось распознать данные формы"
    
    # Создаем таблицу
    result = "🎓 <b>ОТЧЕТ О ПОСЕЩАЕМОСТИ</b>\n\n"
    
    if group:
        result += f"🏫 <b>Группа:</b> <code>{group}</code>\n\n"
    
    result += "<code>"
    for idx, student in enumerate(students, 1):
        result += f"{idx:2}. {student['name']} - {student['status']}\n"
    result += "</code>"
    
    # Статистика
    total = len(students)
    present = len([s for s in students if s['status'] == 'Пришёл'])
    absent = total - present
    
    result += f"\n📊 <b>Статистика:</b>\n"
    result += f"• Всего: {total}\n"
    result += f"• Присутствуют: {present}\n"
    result += f"• Отсутствуют: {absent}\n"
    
    result += f"\n🕐 <i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
    
    return result

def send_telegram_message(text):
    """Отправляет сообщение в Telegram"""
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN или CHAT_ID не установлены")
        return False
        
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        print(f"📤 Статус отправки: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обрабатывает GET запросы"""
        try:
            if self.path == '/process_form' or self.path.startswith('/process_form?'):
                # Обрабатываем запрос от Яндекс Форм
                from urllib.parse import urlparse, parse_qs
                parsed_path = urlparse(self.path)
                params = parse_qs(parsed_path.query)
                text = params.get('text', [''])[0]
                
                if not text:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No text provided"}).encode())
                    return
                
                print(f"📨 Получены данные: {text[:100]}...")
                
                # Форматируем в таблицу
                formatted_text = format_students_table(text)
                
                # Отправляем в Telegram
                success = send_telegram_message(formatted_text)
                
                if success:
                    print("✅ Сообщение отправлено в Telegram")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode())
                else:
                    print("❌ Ошибка отправки в Telegram")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Failed to send message to Telegram"}).encode())
                    
            else:
                # Главная страница
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                html_content = """
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Форматтер Яндекс Форм</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
                        code { background: #f4f4f4; padding: 10px; display: block; margin: 10px 0; }
                    </style>
                </head>
                <body>
                    <h1>🎓 Форматтер Яндекс Форм</h1>
                    <p>Сервер готов обрабатывать данные от Яндекс Форм и отправлять в Telegram</p>
                    
                    <h2>📝 Использование:</h2>
                    <p>Отправьте GET запрос на <code>/process_form</code> с данными формы:</p>
                    <code>https://ваш-домен.vercel.app/process_form?text=ДАННЫЕ_ФОРМЫ</code>
                    
                    <h2>✅ Статус: Сервер работает</h2>
                </body>
                </html>
                """
                self.wfile.write(html_content.encode())
                
        except Exception as e:
            print(f"❌ Ошибка обработки GET: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
    
    def do_POST(self):
        """Обрабатывает POST запросы"""
        try:
            if self.path == '/process_form':
                # Обрабатываем POST запрос от Яндекс Форм
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    
                    if self.headers.get('Content-Type') == 'application/json':
                        data = json.loads(body)
                        text = data.get('text', '')
                    else:
                        from urllib.parse import parse_qs
                        data = parse_qs(body)
                        text = data.get('text', [''])[0]
                else:
                    text = ''
                
                if not text:
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "No text provided"}).encode())
                    return
                
                print(f"📨 Получены POST данные: {text[:100]}...")
                
                # Форматируем в таблицу
                formatted_text = format_students_table(text)
                
                # Отправляем в Telegram
                success = send_telegram_message(formatted_text)
                
                if success:
                    print("✅ Сообщение отправлено в Telegram")
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "success"}).encode())
                else:
                    print("❌ Ошибка отправки")
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "Failed to send message"}).encode())
                    
            else:
                self.send_error(404)
                
        except Exception as e:
            print(f"❌ Ошибка обработки POST: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
