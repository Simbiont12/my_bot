from http.server import BaseHTTPRequestHandler
import json
import requests
from datetime import datetime
import os
import re
from urllib.parse import urlparse, parse_qs, unquote

BOT_TOKEN = os.environ.get('BOT_TOKEN')
CHAT_IDS = os.environ.get('CHAT_ID', '').split(',')

def format_students_table(text):
    students = []
    group = None
    
    try:
        
        decoded_text = unquote(text)
        
        
        group_match = re.search(r'(\d-ИКСС\d{2}-\d{2})', decoded_text)
        if group_match:
            group = group_match.group(1)
        
        
        pattern = r'"([^"]+)"\s*:\s*([А-Яа-яёЁ]+)'
        matches = re.findall(pattern, decoded_text)
        
        for name, status in matches:
           
            valid_statuses = ['Болеет', 'Прогул', 'Академ', 'ИГ', 'Заявление', 'Пришёл', 'Пришёд']
            if status not in valid_statuses:
                status = "Пришёл"
            
            students.append({"name": name, "status": status})
    
    except Exception as e:
        print(f"Ошибка: {e}")
        return "❌ Ошибка обработки данных"
    
    if not students:
        return "❌ Не удалось распознать данные формы"
    
    
    students.sort(key=lambda x: x['name'])
    
   
    result = "ОТЧЕТ О ПОСЕЩАЕМОСТИ\n\n"
    
    if group:
        result += f"Группа: {group}\n\n"
    
    for idx, student in enumerate(students, 1):
        result += f" {idx}. {student['name']} - {student['status']}\n"
    
    total = len(students)
    present = len([s for s in students if s['status'] == 'Пришёл'])
    absent = total - present
    
    result += f"\nСтатистика:\n"
    result += f"• Всего: {total}\n"
    result += f"• Присутствуют: {present}\n"
    result += f"• Отсутствуют: {absent}\n"
    
    result += f"\n{datetime.now().strftime('%d.%m.%Y %H:%M')}"
    
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
