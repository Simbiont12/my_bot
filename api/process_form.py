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
    
    print(f"🔧 Начало обработки текста: {text[:50]}...")
    
    # Очищаем текст
    clean_text = text.replace('Итоги дня', '').replace('0:27', '').strip()
    words = clean_text.split()
    
    i = 0
    while i < len(words):
        # Ищем группу
        if group is None and '-' in words[i] and any(char.isdigit() for char in words[i]):
            group = words[i]
            print(f"📋 Найдена группа: {group}")
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
            print(f"👤 Найден студент: {name} - {status}")
        else:
            i += 1
    
    if not students:
        print("❌ Студенты не найдены")
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
    
    print(f"✅ Таблица сформирована: {total} студентов")
    return result

def send_to_telegram(message_text):
    """Отправляет сообщение в Telegram через API бота"""
    print(f"📤 Начало отправки в Telegram...")
    print(f"🔑 BOT_TOKEN: {'установлен' if BOT_TOKEN else 'НЕТ'}")
    print(f"💬 CHAT_IDS: {CHAT_IDS}")
    
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
            print(f"📤 Ответ Telegram: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Успешно отправлено в {chat_id}")
                success_count += 1
            else:
                print(f"❌ Ошибка {response.status_code} для {chat_id}: {response.text}")
                
        except Exception as e:
            print(f"❌ Исключение при отправке в {chat_id}: {e}")
    
    print(f"📊 Итог: отправлено в {success_count} из {len(CHAT_IDS)} чатов")
    return success_count > 0

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обрабатывает GET запросы (для тестирования)"""
        try:
            print(f"📍 GET запрос: {self.path}")
            
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/process_form' or parsed_path.path.startswith('/process_form'):
                # Обработка данных формы
                params = parse_qs(parsed_path.query)
                text = params.get('text', [''])[0]
                
                if not text:
                    print("❌ Пустой текст")
                    return self.send_json_response(400, {"error": "No text provided"})
                
                print(f"📨 Получен текст: {text[:100]}...")
                
                # Форматируем в таблицу
                formatted_message = format_students_table(text)
                
                # Отправляем в Telegram
                success = send_to_telegram(formatted_message)
                
                if success:
                    print("✅ Успех: сообщение отправлено в Telegram")
                    return self.send_json_response(200, {
                        "status": "success", 
                        "message": "Сообщение отправлено в Telegram",
                        "chats_count": len(CHAT_IDS)
                    })
                else:
                    print("❌ Ошибка: не удалось отправить в Telegram")
                    return self.send_json_response(500, {
                        "error": "Failed to send message to any chat",
                        "chats_tried": len(CHAT_IDS)
                    })
                    
            else:
                # Главная страница
                return self.send_html_response("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Telegram Form Processor</title>
                    <meta charset="utf-8">
                </head>
                <body>
                    <h1>🤖 Telegram Form Processor</h1>
                    <p>Сервер работает. Используйте /process_form?text=...</p>
                </body>
                </html>
                """)
                
        except Exception as e:
            print(f"❌ Ошибка в do_GET: {e}")
            return self.send_json_response(500, {"error": str(e)})
    
    def do_POST(self):
        """Обрабатывает POST запросы от Яндекс Форм"""
        try:
            print(f"📍 POST запрос: {self.path}")
            
            if self.path == '/process_form':
                content_length = int(self.headers.get('Content-Length', 0))
                print(f"📏 Длина контента: {content_length}")
                
                if content_length > 0:
                    body = self.rfile.read(content_length).decode('utf-8')
                    print(f"📦 Тело запроса: {body[:200]}...")
                    
                    # Пробуем разные форматы данных
                    text = ""
                    if self.headers.get('Content-Type') == 'application/json':
                        try:
                            data = json.loads(body)
                            text = data.get('text', '')
                            print(f"📋 JSON текст: {text}")
                        except:
                            print("❌ Ошибка парсинга JSON")
                    else:
                        # Формат form-data или x-www-form-urlencoded
                        try:
                            data = parse_qs(body)
                            text = data.get('text', [''])[0]
                            if not text:
                                # Пробуем получить первый параметр
                                text = list(data.values())[0][0] if data else ''
                            print(f"📋 Form текст: {text}")
                        except:
                            print("❌ Ошибка парсинга form-data")
                else:
                    text = ''
                    print("⚠️ Пустое тело запроса")
                
                if not text:
                    print("❌ Текст не найден в запросе")
                    return self.send_json_response(400, {"error": "No text provided"})
                
                print(f"📨 Получен текст для обработки: {text[:100]}...")
                
                # Форматируем в таблицу
                formatted_message = format_students_table(text)
                
                # Отправляем в Telegram
                success = send_to_telegram(formatted_message)
                
                if success:
                    print("🎉 УСПЕХ: Сообщение отправлено в Telegram!")
                    # Важно: Яндекс Формы ждут простой ответ
                    return self.send_json_response(200, {
                        "status": "success",
                        "message": "Данные обработаны и отправлены"
                    })
                else:
                    print("💥 ОШИБКА: Не удалось отправить в Telegram")
                    return self.send_json_response(500, {
                        "error": "Не удалось отправить сообщение"
                    })
                    
            else:
                print(f"❌ Неизвестный путь: {self.path}")
                return self.send_error(404)
                
        except Exception as e:
            print(f"💥 Критическая ошибка в do_POST: {e}")
            return self.send_json_response(500, {"error": str(e)})
    
    def send_json_response(self, status_code, data):
        """Отправляет JSON ответ"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode())
        print(f"📤 Отправлен ответ: {status_code} - {response}")
    
    def send_html_response(self, html_content):
        """Отправляет HTML ответ"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
