"""Telegram Bot (Async/FastAPI Polling)"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from orchestration.graph import orchestration_graph
from config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram бот для взаимодействия с пользователями"""
    
    def __init__(self):
        self.app = Application.builder().token(settings.telegram_bot_token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков"""
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        self.app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        await update.message.reply_text(
            "Привет! Я AI-ассистент для управления 3D-принтером.\n\n"
            "Я могу:\n"
            "• Анализировать G-code файлы\n"
            "• Искать информацию в базе знаний\n"
            "• Анализировать изображения печати\n"
            "• Управлять принтером\n\n"
            "Просто напиши мне свой вопрос или отправь файл/изображение!"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /help"""
        await update.message.reply_text(
            "Доступные команды:\n"
            "/start - Начать работу\n"
            "/help - Показать эту справку\n"
            "/status - Статус принтера\n\n"
            "Также ты можешь:\n"
            "• Отправить G-code файл для анализа\n"
            "• Отправить фото печати для анализа\n"
            "• Задать вопрос о 3D-печати"
        )
    
    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /status"""
        from agents.hardware.tool import hardware_tool
        
        try:
            status = await hardware_tool.get_status()
            temp = await hardware_tool.get_temperature()
            
            status_text = f"Статус принтера:\n\n"
            status_text += f"Температура стола: {temp.get('bed', 0)}°C\n"
            status_text += f"Температура сопла: {temp.get('nozzle', 0)}°C\n"
            status_text += f"\nДетали: {status}"
            
            await update.message.reply_text(status_text)
        except Exception as e:
            await update.message.reply_text(f"Ошибка при получении статуса: {str(e)}")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Показываем индикатор печати
        await update.message.reply_text("Обрабатываю запрос...")
        
        try:
            # Обрабатываем через граф оркестрации
            result = await orchestration_graph.process(
                user_message,
                context={"user_id": user_id, "telegram": True}
            )
            
            response = result.get("response", "Не удалось обработать запрос")
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await update.message.reply_text(f"Произошла ошибка: {str(e)}")
    
    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка фотографий"""
        photo = update.message.photo[-1]  # Берем самое большое фото
        file = await photo.get_file()
        
        # Сохраняем фото
        file_path = f"data/temp/{update.effective_user.id}_{photo.file_id}.jpg"
        import os
        os.makedirs("data/temp", exist_ok=True)
        await file.download_to_drive(file_path)
        
        await update.message.reply_text("Анализирую изображение...")
        
        try:
            # Обрабатываем через граф оркестрации
            result = await orchestration_graph.process(
                "Проанализируй это изображение печати",
                context={"image_path": file_path, "user_id": update.effective_user.id}
            )
            
            response = result.get("response", "Не удалось проанализировать изображение")
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error processing photo: {e}")
            await update.message.reply_text(f"Произошла ошибка при анализе: {str(e)}")
    
    def run(self):
        """Запуск бота"""
        logger.info("Запуск Telegram бота...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    bot = TelegramBot()
    bot.run()

