from http.server import BaseHTTPRequestHandler
import json
import requests
import re
from datetime import datetime
import os
from urllib.parse import urlparse, parse_qs

# Конфигурация
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8210361140:AAHMafEoPS4ugu2spU6Ut4CTzrVgzhVxuJQ')
CHAT_IDS = os.environ.get('CHAT_ID', '5308270090,533483177,1513163562').split(',')

def format_students_table(text):
    """Форматирует сырые данные в красивую таблицу для Telegram"""
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

def send_to_telegram(message_text):
    """Отправляет сообщение в Telegram через API бота"""
    success_count = 0
    
    for chat_id in CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
            
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        
        try:
            print(f"📤 Отправка в чат {chat_id}...")
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Успешно отправлено в {chat_id}")
                success_count += 1
            else:
                print(f"❌ Ошибка {response.status_code} для {chat_id}: {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение при отправке в {chat_id}: {e}")
    
    return success_count > 0

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обрабатывает GET запросы"""
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/process_form' or parsed_path.path.startswith('/process_form'):
                # Обработка данных формы
                params = parse_qs(parsed_path.query)
                text = params.get('text', [''])[0]
                
                if not text:
                    self.send_json_response(400, {"error": "No text provided"})
                    return
                
                print(f"📨 Получен текст: {text[:100]}...")
                
                # Форматируем в таблицу
                formatted_message = format_students_table(text)
                print(f"📊 Форматированное сообщение: {formatted_message[:100]}...")
                
                # Отправляем в Telegram
                success = send_to_telegram(formatted_message)
                
                if success:
                    print("✅ Сообщение отправлено в Telegram")
                    self.send_json_response(200, {
                        "status": "success", 
                        "message": "Сообщение отправлено в Telegram",
                        "chats_count": len(CHAT_IDS)
                    })
                else:
                    print("❌ Не удалось отправить ни в один чат")
                    self.send_json_response(500, {
                        "error": "Failed to send message to any chat",
                        "chats_tried": len(CHAT_IDS)
                    })
                    
            else:
                # Главная страница
                self.send_html_response("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Telegram Form Processor</title>
                    <meta charset="utf-8">
                    <style>
                        body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; }
                        code { background: #f4f4f4; padding: 10px; display: block; margin: 10px 0; }
                        .success { color: green; }
                        .error { color: red; }
                    </style>
                </head>
                <body>
                    <h1>🤖 Telegram Form Processor</h1>
                    <p>Сервер для обработки данных и отправки в Telegram</p>
                    
                    <h2>📝 Использование:</h2>
                    <p>GET запрос:</p>
                    <code>https://my-pair136pq-sims-projects-10ecc07f.vercel.app/process_form?text=Ваши_данные</code>
                    
                    <h2>🔧 Конфигурация:</h2>
                    <ul>
                        <li>Бот: <code>{}</code></li>
                        <li>Чаты: <code>{}</code></li>
                    </ul>
                    
                    <h2>✅ Статус: Сервер работает</h2>
                    <p>Сообщения будут отправляться в указанные Telegram чаты</p>
                </body>
                </html>
                """.format(BOT_TOKEN[:10] + '...' if BOT_TOKEN else 'Не установлен', 
                          len(CHAT_IDS)))
                
        except Exception as e:
            print(f"❌ Ошибка в do_GET: {e}")
            self.send_json_response(500, {"error": str(e)})
    
    def do_POST(self):
        """Обрабатывает POST запросы"""
        try:
            if self.path == '/process_form':
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    
                    if self.headers.get('Content-Type') == 'application/json':
                        data = json.loads(body)
                        text = data.get('text', '')
                    else:
                        data = parse_qs(body)
                        text = data.get('text', [''])[0]
                else:
                    text = ''
                
                if not text:
                    self.send_json_response(400, {"error": "No text provided"})
                    return
                
                print(f"📨 Получен POST текст: {text[:100]}...")
                
                # Форматируем и отправляем
                formatted_message = format_students_table(text)
                success = send_to_telegram(formatted_message)
                
                if success:
                    self.send_json_response(200, {"status": "success"})
                else:
                    self.send_json_response(500, {"error": "Failed to send message"})
                    
            else:
                self.send_error(404)
                
        except Exception as e:
            print(f"❌ Ошибка в do_POST: {e}")
            self.send_json_response(500, {"error": str(e)})
    
    def send_json_response(self, status_code, data):
        """Отправляет JSON ответ"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
    
    def send_html_response(self, html_content):
        """Отправляет HTML ответ"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())

# Для локального тестирования
if __name__ == '__main__':
    from http.server import HTTPServer
    print("🚀 Сервер запущен на http://localhost:8000")
    server = HTTPServer(('localhost', 8000), handler)
    server.serve_forever()
    #1
