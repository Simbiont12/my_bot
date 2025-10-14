def format_students_table(text):
    students = []
    group = None
    
    print("=== ИСХОДНЫЕ ДАННЫЕ ===")
    print(repr(text))
    print("=======================")
    
    try:
        # Декодируем URL-encoded текст
        decoded_text = unquote(text)
        print(f"Декодированный текст: {repr(decoded_text)}")
        
        # Убираем "Итоги дня" и лишние символы
        clean_text = decoded_text.replace('Итоги дня', '').replace('\u2028', '\n').replace('\\n', '\n')
        print(f"Очищенный текст: {repr(clean_text)}")
        
        # Разбиваем на строки
        lines = clean_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            print(f"Обрабатываем строку: {repr(line)}")
            
            # Ищем группу (формат: 1-ИКСС11-10:)
            if not group and re.search(r'\d-ИКСС\d{2}-\d{2}', line):
                group_match = re.search(r'(\d-ИКСС\d{2}-\d{2})', line)
                if group_match:
                    group = group_match.group(1)
                    print(f"Найдена группа: {group}")
                continue
            
            # Ищем студента в формате: "Фамилия Имя Отчество": Статус
            match = re.search(r'"([^"]+)"\s*:\s*([^\s]+)', line)
            if match:
                name, status = match.groups()
                name = name.strip()
                status = status.strip()
                
                # Проверяем валидность статуса
                valid_statuses = ['Болеет', 'Прогул', 'Академ', 'ИГ', 'Заявление', 'Пришёл', 'Пришёд']
                if status not in valid_statuses:
                    status = "Пришёл"  # Статус по умолчанию
                
                students.append({"name": name, "status": status})
                print(f"Найден студент: {name} - {status}")
            
            # Альтернативный поиск: три слова с заглавных + статус
            else:
                pattern = r'([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\s+([А-ЯЁ][а-яё]+)\s+([А-ЯЁа-яё]+)'
                match = re.search(pattern, line)
                if match:
                    last_name, first_name, middle_name, status = match.groups()
                    name = f"{last_name} {first_name} {middle_name}"
                    
                    valid_statuses = ['Болеет', 'Прогул', 'Академ', 'ИГ', 'Заявление', 'Пришёл', 'Пришёд']
                    if status not in valid_statuses:
                        status = "Пришёл"
                    
                    students.append({"name": name, "status": status})
                    print(f"Найден студент (альт): {name} - {status}")
        
    except Exception as e:
        print(f"❌ Ошибка обработки: {e}")
        return f"❌ Ошибка обработки данных: {e}"
    
    if not students:
        return "❌ Не удалось распознать данные формы"
    
    print(f"✅ Найдено студентов: {len(students)}")
    
    # Сортируем студентов по фамилии
    students.sort(key=lambda x: x['name'])
    
    # Форматируем результат
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
