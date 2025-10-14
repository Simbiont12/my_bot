from http.server import BaseHTTPRequestHandler
import json
import requests
import re
from datetime import datetime
import os

class TelegramMessageProcessor:
    def __init__(self, bot_token):
        self.bot_token = bot_token
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def parse_group_and_students(self, text):
        """Улучшенный парсинг группы и студентов"""
        students = []
        group = None
        
        group_match = re.search(r'[А-ЯЁA-Z]{2,}-\d{2,}-\d', text)
        if group_match:
            group = group_match.group()
        
        name_pattern = r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)(?:\s+(Болеет|Прогул|Академ|ИГ|Заявление|Пришёл))?'
        
        matches = re.finditer(name_pattern, text)
        for match in matches:
            last_name, first_name, middle_name, status = match.groups()
            name = f"{last_name} {first_name} {middle_name}"
            status = status or "Пришёл"
            
            students.append({
                "name": name, 
                "status": status,
                "last_name": last_name
            })
        
        students.sort(key=lambda x: x['last_name'])
        return group, students
    
    def process_message(self, text):
        """Обработка сообщения и создание таблицы"""
        group, students = self.parse_group_and_students(text)
        
        if not students:
            return None
        
        result = "🎓 <b>ОТЧЕТ О ПОСЕЩАЕМОСТИ</b>\n\n"
        if group:
            result += f"🏫 <b>Группа:</b> <code>{group}</code>\n\n"
        
        result += "<code>"
        for idx, student in enumerate(students, 1):
            result += f"{idx:2}. {student['name']} - {student['status']}\n"
        result += "</code>"
        
        total = len(students)
        present = len([s for s in students if s['status'] == 'Пришёл'])
        
        result += f"\n📊 <b>Статистика:</b>\n"
        result += f"• Всего: {total}\n"
        result += f"• Присутствуют: {present}\n"
        result += f"• Отсутствуют: {total - present}\n"
        result += f"\n🕐 <i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
        
        return result
    
    def send_message(self, chat_id, text):
        """Отправляем сообщение через бота"""
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return False
    
    def check_and_process_messages(self):
        """Проверяет и обрабатывает новые сообщения (одноразово)"""
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok'] and data['result']:
                    latest_update = data['result'][-1]  # Берем последнее сообщение
                    
                    if 'message' in latest_update and 'text' in latest_update['message']:
                        message = latest_update['message']
                        text = message['text'].strip()
                        chat_id = message['chat']['id']
                        
                        if not text.startswith('/') and len(text) > 15:
                            processed_text = self.process_message(text)
                            if processed_text:
                                success = self.send_message(chat_id, processed_text)
                                return {"status": "processed" if success else "send_error"}
            
            return {"status": "no_messages"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/check_messages':
            bot_token = os.environ.get('BOT_TOKEN')
            
            if not bot_token:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "BOT_TOKEN not set"}).encode())
                return
            
            processor = TelegramMessageProcessor(bot_token)
            result = processor.check_and_process_messages()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        else:
            self.send_response(404)
