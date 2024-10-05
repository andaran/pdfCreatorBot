# СоздайPDF (pdfCreatorBot)

**pdfCreatorBot** — это Telegram-бот, который принимает несколько изображений от пользователя и склеивает их в один PDF документ.

## Установка и запуск

1. **Клонировать репозиторий:**

   ```bash
   git clone https://github.com/andaran/pdfCreatorBot
   cd pdfCreatorBot
   ```

2. **Установка зависимостей:**

   Установите необходимые библиотеки через `pip`:

   ```bash
   pip install pillow aiogram
   ```

3. **Создание бота в Telegram:**

   - Создайте бота через [BotFather](https://t.me/BotFather) и получите токен.
   - Добавьте токен в `configs/bot_config.py`:

     ```python
     TOKEN = "токен бота"
     ```

4. **Запуск бота:**

   После установки всех зависимостей и получения токена, запустите бота:

   ```bash
   python bot.py
   ```