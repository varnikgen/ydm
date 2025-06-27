# Yealink Device Management

Веб-приложение для управления IP-телефонами Yealink через Action URL API.

## Основные возможности

- 📱 Управление устройствами Yealink (добавление, редактирование, удаление)
- 🧾 Работа с конфигурациями устройств (XML-формат)
- ⚙️ Отправка команд на устройства:
  - Перезагрузка
  - Запрос статуса
  - Применение конфигураций (будет реализовано)
- 🔄 Автоматический сбор статусов устройств
- 📁 Управление моделями устройств

## Технологии

- **Backend**: Python 3.12, FastAPI
- **Frontend**: Jinja2, HTML5, CSS3, JavaScript
- **База данных**: SQLite (легко переключается на PostgreSQL)
- **Другие компоненты**:
  - SQLAlchemy (ORM)
  - HTTpx (HTTP-клиент)
  - APScheduler (планировщик задач)
  - Pydantic (валидация данных)
  - UV (менеджер пакетов)

## Установка и запуск

1. **Клонировать репозиторий**:
```bash
git clone https://github.com/varnikgen/ydm.git
cd ydm
```
2. **Создать виртуальное окружение и установить зависимости**:
```bash
uv venv .venv
source .venv/bin/activate  # Для Linux/MacOS
# .\.venv\Scripts\activate  # Для Windows
uv pip install -r requirements.txt
```
3. **Запустить приложение**:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
