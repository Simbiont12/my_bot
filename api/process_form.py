def process_request(self, method):
    try:
        # Получаем текст из формы
        if method == 'GET':
            from urllib.parse import urlparse, parse_qs
            parsed_path = urlparse(self.path)
            params = parse_qs(parsed_path.query)
            text = params.get('text', [''])[0]
        else:
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

        # Форматируем в таблицу
        formatted_text = format_students_table(text)
        
        # Кодируем текст для URL
        encoded_text = requests.utils.quote(formatted_text)
        
        # Создаем готовый URL для Telegram
        telegram_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage?chat_id={CHAT_ID.split(',')[0]}&text={encoded_text}&parse_mode=HTML"
        
        # Возвращаем URL вместо отправки
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "success", 
            "telegram_url": telegram_url,
            "message": "Use this URL to send to Telegram"
        }).encode())
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": str(e)}).encode())
