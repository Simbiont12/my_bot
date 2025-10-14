from http.server import BaseHTTPRequestHandler
import json
import requests
from datetime import datetime
import os
from urllib.parse import urlparse, parse_qs

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_IDS = os.environ.get('CHAT_ID', '').split(',')

def format_students_table(text):
    students = []
    group = None
    
    clean_text = text.replace('Итоги дня', '').replace('0:27', '').strip()
    words = clean_text.split()
    
    i = 0
    while i < len(words):
        if group is None and '-' in words[i] and any(char.isdigit() for char in words[i]):
            group = words[i]
            i += 1
            continue
            
        if (i + 2 < len(words) and 
            words[i][0].isupper() and 
            words[i+1][0].isupper() and 
            words[i+2][0].isupper()):
            
            name = f"{words[i]} {words[i+1]} {words[i+2]}"
            status = "Пришёл"
            
            if i + 3 < len(words) and words[i+3] in ['Болеет', 'Прогул', 'Академ', 'ИГ', 'Заявление', 'Пришёл']:
                status = words[i+3]
                i += 4
            else:
                i += 3
                
            students.append({"name": name, "status": status})
        else:
            i += 1
    
    if not students:
        return "Не удалось распознать данные формы"
    
    result = "🎓 ОТЧЕТ О ПОСЕЩАЕМОСТИ\n\n"
    
    if group:
        result += f"🏫 Группа: {group}\n\n"
    
    for idx, student in enumerate(students, 1):
        status_icon = "✅" if student['status'] == 'Пришёл' else "❌"
        result += f"{idx:2}. {student['name']} - {status_icon} {student['status']}\n"
    
    total = len(students)
    present = len([s for s in students if s['status'] == 'Пришёл'])
    absent = total - present
    
    result += f"\n📊 Статистика:\n"
    result += f"• Всего: {total}\n"
    result += f"• Присутствуют: {present}\n"
    result += f"• Отсутствуют: {absent}\n"
    
    result += f"\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
    return result

def send_to_telegram(message_text):
    success_count = 0
    
    for chat_id in CHAT_IDS:
        chat_id = chat_id.strip()
        if not chat_id:
            continue
            
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message_text
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            
            if response.status_code == 200:
                success_count += 1
                
        except Exception:
            pass
    
    return success_count > 0

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            
            if parsed_path.path == '/process_form' or parsed_path.path.startswith('/process_form'):
                params = parse_qs(parsed_path.query)
                text = params.get('text', [''])[0]
                
                if not text:
                    self.send_json_response(400, {"error": "No text provided"})
                    return
                
                formatted_message = format_students_table(text)
                success = send_to_telegram(formatted_message)
                
                if success:
                    self.send_json_response(200, {"status": "success"})
                else:
                    self.send_json_response(500, {"error": "Failed to send message"})
                    
            else:
                self.send_html_response("""
                <!DOCTYPE html>
                <html>
                <head>
                    <title>Form Processor</title>
                    <meta charset="utf-8">
                </head>
                <body>
                    <h1>Form Processor</h1>
                    <p>Server is running</p>
                </body>
                </html>
                """)
                
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})
    
    def do_POST(self):
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
                
                formatted_message = format_students_table(text)
                success = send_to_telegram(formatted_message)
                
                if success:
                    self.send_json_response(200, {"status": "success"})
                else:
                    self.send_json_response(500, {"error": "Failed to send message"})
                    
            else:
                self.send_error(404)
                
        except Exception as e:
            self.send_json_response(500, {"error": str(e)})
    
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        response = json.dumps(data, ensure_ascii=False)
        self.wfile.write(response.encode())
    
    def send_html_response(self, html_content):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_content.encode())
