from flask import Flask, request, jsonify
import requests
import logging
from datetime import datetime
import os

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('webhook_bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ====== НАСТРОЙКИ ======
TG_BOT_TOKEN = "7794541820:AAHYZZn5Wo1ISS4pQe-kC5AuEOhDRJnGzbg"
TG_CHAT_ID = "5308270090"

# ====== ФУНКЦИИ ДЛЯ ФОРМАТИРОВАНИЯ ======

def format_students_list(students_text):
    """Форматирует список студентов с эмодзи"""
    if not students_text:
        return "Нет данных о студентах"
    
    lines = students_text.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Определяем статус студента
        if 'Болеет' in line:
            icon = "🤒"  # Болеет
        elif 'Отсутствует' in line:
            icon = "❌"  # Отсутствует
        elif 'Опоздал' in line:
            icon = "⏰"  # Опоздал
        else:
            icon = "✅"  # Присутствует
            
        formatted_lines.append(f"{icon} {line}")
    
    return '\n'.join(formatted_lines)

def create_beautiful_message(form_data):
    """Создает красивое сообщение из данных формы"""
    
    # Извлекаем данные из формы
    group = form_data.get('group', 'Не указана')
    date = form_data.get('date', 'Не указана')
    students_text = form_data.get('students', '')
    additional_info = form_data.get('additional_info', '')
    
    # Преобразуем дату в читаемый формат
    try:
        if date and date != 'Не указана':
            date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            formatted_date = date_obj.strftime('%d.%m.%Y')
            weekday = date_obj.strftime('%A')
            # Русские названия дней недели
            weekdays_ru = {
                'Monday': 'Понедельник',
                'Tuesday': 'Вторник',
                'Wednesday': 'Среда', 
                'Thursday': 'Четверг',
                'Friday': 'Пятница',
                'Saturday': 'Суббота',
                'Sunday': 'Воскресенье'
            }
            weekday_ru = weekdays_ru.get(weekday, weekday)
        else:
            formatted_date = datetime.now().strftime('%d.%m.%Y')
            weekday_ru = "Сегодня"
    except:
        formatted_date = "Неизвестная дата"
        weekday_ru = ""
    
    # Создаем сообщение
    message = f"📊 *ИТОГИ ДНЯ*\n\n"
    message += f"*Группа:* {group}\n"
    message += f"*Дата:* {formatted_date} ({weekday_ru})\n\n"
    
    # Добавляем разделитель
    message += "👥 *СТАТУС СТУДЕНТОВ:*\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    
    # Форматируем список студентов
    students_formatted = format_students_list(students_text)
    message += f"{students_formatted}\n\n"
    
    # Дополнительная информация
    if additional_info:
        message += "📝 *ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:*\n"
        message += "━━━━━━━━━━━━━━━━━━━━\n"
        message += f"{additional_info}\n\n"
    
    # Статистика
    total_students = len([line for line in students_text.split('\n') if line.strip()])
    sick_count = students_text.count('Болеет')
    absent_count = students_text.count('Отсутствует')
    late_count = students_text.count('Опоздал')
    present_count = total_students - sick_count - absent_count
    
    message += "📈 *СТАТИСТИКА:*\n"
    message += "━━━━━━━━━━━━━━━━━━━━\n"
    message += f"✅ Присутствуют: {present_count}\n"
    message += f"🤒 Болеют: {sick_count}\n"
    message += f"❌ Отсутствуют: {absent_count}\n"
    if late_count > 0:
        message += f"⏰ Опоздали: {late_count}\n"
    
    message += f"\n_Отправлено: {datetime.now().strftime('%H:%M')}_"
    
    return message

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    
    payload = {
        'chat_id': TG_CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response_data = response.json()
        
        if response_data.get('ok'):
            logger.info("✅ Сообщение успешно отправлено в Telegram")
            return True
        else:
            logger.error(f"❌ Ошибка Telegram API: {response_data.get('description')}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Ошибка при отправке в Telegram: {e}")
        return False

# ====== WEBHOOK РОУТЫ ======

@app.route('/', methods=['GET'])
def home():
    """Главная страница"""
    return jsonify({
        "status": "success",
        "message": "Webhook server is running!",
        "endpoints": {
            "webhook": "/webhook (POST)",
            "health": "/health (GET)"
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервера"""
    return jsonify({
        "status": "success",
        "message": "Server is healthy",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Обработчик вебхуков от Яндекс Форм"""
    try:
        logger.info("📨 Получен новый вебхук")
        
        # Получаем данные из запроса
        if request.is_json:
            form_data = request.get_json()
        else:
            form_data = request.form.to_dict()
        
        logger.info(f"📊 Данные формы: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        
        # Создаем красивое сообщение
        message = create_beautiful_message(form_data)
        logger.info(f"📝 Создано сообщение: {message}")
        
        # Отправляем в Telegram
        success = send_telegram_message(message)
        
        if success:
            return jsonify({
                "status": "success",
                "message": "Сообщение отправлено в Telegram"
            }), 200
        else:
            return jsonify({
                "status": "error", 
                "message": "Ошибка при отправке в Telegram"
            }), 500
            
    except Exception as e:
        logger.error(f"💥 Ошибка обработки вебхука: {e}")
        return jsonify({
            "status": "error",
            "message": f"Internal server error: {str(e)}"
        }), 500

@app.route('/test', methods=['GET'])
def test_handler():
    """Тестовый endpoint для проверки"""
    test_data = {
        "group": "1-ИКСС11-10",
        "date": "2024-10-14T15:56:00Z",
        "students": "Бежко Кристина Романовна ✅\nВолков Иван Вадимович 🤒 Болеет\nГрачев Дениз Германович 🤒 Болеет\nГренке Максим Александрович 🤒 Болеет",
        "additional_info": "Все отсутствующие уведомили заранее"
    }
    
    message = create_beautiful_message(test_data)
    
    # Отправляем тестовое сообщение
    success = send_telegram_message(message)
    
    return jsonify({
        "status": "success" if success else "error",
        "message": "Тестовое сообщение отправлено" if success else "Ошибка отправки",
        "test_message": message
    })

# ====== ЗАПУСК СЕРВЕРА ======
if __name__ == '__main__':
    logger.info("🚀 Запуск Flask сервера...")
    app.run(
        host='0.0.0.0',  # Доступ с других устройств в сети
        port=5000,
        debug=True  # В продакшене установить False
    )
