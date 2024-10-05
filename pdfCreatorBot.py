from src.pdfCreator import PdfCreator
from configs.bot_config import TOKEN, HELLO_STICKERS, HELLO_MESSAGE_1, HELLO_MESSAGE_2, SETTINGS_PARAMS_TYPES

from aiogram import Bot, Dispatcher, executor, types
import random
import os
import pickle
import json
import re
import shutil
import time
import threading
import asyncio


class TelegramBot:
    def __init__(self, token, temp_dir):

        # Initialize bot and dispatcher
        self._bot = Bot(token=token)
        self._dp = Dispatcher(self._bot)

        # Initialize main temp directory
        self._temp_dir = temp_dir

        # Initialize creator
        self._creator = PdfCreator()

        # Initialize deleting queue
        self._deleting_queue = []

        #   ---==== Registering handlers ====---   #

        # Commands
        self._dp.register_message_handler(
            self.handle_start, commands=['start'])
        self._dp.register_message_handler(
            self.handle_pdf, commands=['pdf'])
        self._dp.register_message_handler(
            self.handle_settings, commands=['settings'])
        self._dp.register_message_handler(
            self.handle_clear, commands=['clear'])

        # Settings message
        self._dp.register_message_handler(
            self.handle_message, content_types=['text'])

        # Photos
        self._dp.register_message_handler(
            self.handle_photo, content_types=['photo'])
        self._dp.register_message_handler(
            self.handle_document, content_types=['document'])

    def start(self):
        # Deleting queue loop
        threading.Thread(target=self.deleting_queue_loop).start()

        # Bot loop
        executor.start_polling(self._dp)

    #   ---==== Handlers ====---   #

    async def handle_start(self, message: types.Message):
        await message.answer_sticker(random.choice(HELLO_STICKERS))
        await asyncio.sleep(0.5)
        await message.answer(HELLO_MESSAGE_1)
        await asyncio.sleep(0.5)
        await message.answer(HELLO_MESSAGE_2, parse_mode="MarkdownV2")

    async def handle_message(self, message: types.Message):
        # Delete comments from JSON
        message.text = str(message.text)
        message.text = re.sub(r'//.*', '', message.text)

        # Parse message as JSON
        try:
            settings = json.loads(message.text)
        except json.JSONDecodeError:
            return await message.answer("Неверный формат JSON")

        # Filter settings params
        try:
            settings = {key: value for key,
                        value in settings.items() if key in SETTINGS_PARAMS_TYPES}
        except:
            return await message.answer("Неверный формат JSON")

        # Filter params types
        try:
            for key, value in settings.items():
                if settings[key] != SETTINGS_PARAMS_TYPES[key](value):
                    return await message.answer(f"Неверный тип параметра {key}")
        except:
            return await message.answer("Неверный формат JSON")

        # Save settings
        self.save_user_settings(message.from_user.id, settings)
        await message.answer("Настройки сохранены")

    async def handle_photo(self, message):
        # Delete temp dir after 20 minutes
        self.add_to_deleting_queue(message.from_user.id)

        # Save photo to temp dir
        path = os.path.join(self._temp_dir, str(message.from_user.id))
        name = os.path.join(path, f"{message.photo[-1].file_unique_id}.jpg")
        await message.photo[-1].download(destination_file=name)

    async def handle_document(self, message):
        # Check if file is image
        if message.document.mime_type != "image/jpeg":
            return

        # Delete temp dir after 20 minutes
        self.add_to_deleting_queue(message.from_user.id)

        # Save file to temp dir
        path = os.path.join(self._temp_dir, str(message.from_user.id))
        name = os.path.join(path, message.document.file_name)
        await message.document.download(destination_file=name)

    async def handle_settings(self, message):
        # Get settings from pickle
        settings = self.get_user_settings(message.from_user.id) or {}
        mes = f"`{json.dumps(settings, indent=4)}`"
        await message.answer(mes, parse_mode="MarkdownV2")

    async def handle_pdf(self, message):
        await message.answer("Создание PDF может занять некоторое время. Ожидайте.")

        res = self.create(message.from_user.id)
        if not res:
            return await message.answer("Ошибка!")

        await message.answer_document(open(res, "rb"))
        self.delete_temp_dir(message.from_user.id)

    async def handle_clear(self, message):
        self.delete_temp_dir(message.from_user.id)
        await message.answer("Текущие фотографии удалены")

    #   ---==== Creator functions ====---   #

    def create(self, user_id):
        path = os.path.join(self._temp_dir, str(user_id))
        res = self._creator.create(
            path,
            path,
            self.get_user_settings(user_id) or {}
        )
        return res

    def delete_temp_dir(self, user_id):
        path = os.path.join(self._temp_dir, str(user_id))
        try:
            shutil.rmtree(path)
        except FileNotFoundError:
            pass
        self.delete_from_deleting_queue(user_id)

    #   ---==== Database ====---   #

    def save_user_settings(self, user_id, settings):
        settings = [user_id, settings]

        database = None
        with open("db.pickle", "rb") as f:
            database = pickle.load(f)

        current_settings = filter(lambda x: x[0] == user_id, database)
        current_settings = list(current_settings)
        if current_settings:
            database.remove(current_settings[0])
            settings[1] = {**current_settings[0][1], **settings[1]}

        database.append(settings)
        with open("db.pickle", "wb") as f:
            pickle.dump(database, f)

    def get_user_settings(self, user_id):
        with open("db.pickle", "rb") as f:
            database = pickle.load(f)

        for user, settings in database:
            if user == user_id:
                return settings

        return None

    #   ---==== Deleting queue ====---   #

    def add_to_deleting_queue(self, user_id):
        queue = self._deleting_queue
        queue = list(filter(lambda x: x[0] != user_id, queue))
        queue.append((user_id, time.time() + 60*10))
        self._deleting_queue = queue

    def delete_from_deleting_queue(self, user_id):
        queue = self._deleting_queue
        queue = list(filter(lambda x: x[0] != user_id, queue))
        self._deleting_queue = queue

    def deleting_queue_loop(self):
        while True:
            queue = self._deleting_queue
            for user_id, end_time in queue:
                if end_time < time.time():
                    self.delete_temp_dir(user_id)
                    queue.remove((user_id, end_time))

            time.sleep(1)


bot = TelegramBot(TOKEN, "temp_dirs")
bot.start()
