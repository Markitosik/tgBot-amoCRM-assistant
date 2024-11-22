import asyncio
import logging
from datetime import datetime, time, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command

from config import TOKEN, CHAT_ID, TARGET_HOUR, TARGET_MINUTE
from get_stats import calculate_manager_stats


current_task = None

# Настройки логгера
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def send_message():
    try:
        manager_stats = await calculate_manager_stats()

        for manager, stats in manager_stats.items():
            report = []
            report.append(f"*Менеджер: {manager}*")
            report.append("**Общие данные:**")
            report.append(f"  - Всего сделок: {stats['total_deals']}")
            report.append(f"  - Завершенных сделок: {stats['total_completed_deals']}")
            report.append(f"  - Сумма всех сделок: {stats['total_deals_sum']}$")
            report.append(f"  - Сумма завершенных сделок: {stats['total_completed_deals_sum']}$")
            report.append("\n**Последние сутки:**")
            report.append(f"  - Сделок за сутки: {stats['recent_deals']}")
            report.append(f"  - Завершенных за сутки: {stats['recent_completed_deals']}")
            report.append(f"  - Сумма сделок за сутки: {stats['recent_deals_sum']}$")
            report.append(f"  - Сумма завершенных за сутки: {stats['recent_completed_deals_sum']}$")
            report.append("\n**Текущая неделя:**")
            report.append(f"  - Сделок за неделю: {stats['week_deals']}")
            report.append(f"  - Завершенных за неделю: {stats['week_completed_deals']}")
            report.append(f"  - Сумма сделок за неделю: {stats['week_deals_sum']}$")
            report.append(f"  - Сумма завершенных за неделю: {stats['week_completed_deals_sum']}$")
            report.append("\n**Текущий месяц:**")
            report.append(f"  - Сделок за месяц: {stats['month_deals']}")
            report.append(f"  - Завершенных за месяц: {stats['month_completed_deals']}")
            report.append(f"  - Сумма сделок за месяц: {stats['month_deals_sum']}$")
            report.append(f"  - Сумма завершенных за месяц: {stats['month_completed_deals_sum']}$")

            report = "\n".join(report)

            await bot.send_message(chat_id=CHAT_ID, text=report, parse_mode="Markdown")

        logging.info("Сообщения отправлены.")
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения: {e}")


# Обработчик команды /start
async def cmd_help(message: types.Message):
    help_text = (
        "Доступные команды:\n\n"
        "/start — Запустить бота и начать рассылку отчета по расписанию.\n\n"
        "/set_time HH:MM — Установить новое время отправки сообщений. Например: `/set_time 12:30`.\n"
        "   После изменения времени старая задача отменяется, и новая начинает выполняться с указанным временем.\n\n"
        "/help — Показать это сообщение с подсказками по работе с ботом."
    )
    await message.answer(help_text, parse_mode="HTML")


# Обработчик команды /start
async def cmd_start(message: types.Message):
    global current_task
    await message.answer("Привет, я бот!")

    # Создаем задачу schedule_daily_message
    current_task = asyncio.create_task(schedule_daily_message())


# Обработчик команды /echo
async def cmd_set_time(message: types.Message):
    global TARGET_HOUR, TARGET_MINUTE, current_task

    try:
        # Получаем время из команды
        time_text = message.text.strip().replace('/set_time', '')

        hour, minute = map(int, time_text.split(":"))
        # Проверяем, что время корректное
        if 0 <= hour < 24 and 0 <= minute < 60:
            TARGET_HOUR = hour
            TARGET_MINUTE = minute
            await message.answer(f"Время отправки отчетов обновлено на {TARGET_HOUR}:{TARGET_MINUTE}")
            # Отменяем текущую задачу, если она существует
            if current_task is not None and not current_task.done():
                current_task.cancel()
                await current_task  # Ждем, чтобы убедиться в завершении

            # Запускаем новую задачу
            current_task = asyncio.create_task(schedule_daily_message())
        else:
            await message.answer("Некорректное время. Убедитесь, что формат правильный и время корректно.")

    except (IndexError, ValueError):
        await message.answer("Использование: /set_time HH:MM (например, /set_time 12:30)")


# Асинхронный цикл для запуска задачи в указанное время
async def schedule_daily_message():
    try:
        while True:
            now = datetime.now()
            logging.info(f"{TARGET_HOUR}:{TARGET_MINUTE}")
            target_time = time(TARGET_HOUR, TARGET_MINUTE)  # Время, когда нужно отправить сообщение
            target_datetime = datetime.combine(now.date(), target_time)

            # Если уже позднее целевого времени, берем следующий день
            if now > target_datetime:
                target_datetime = datetime.combine(now.date(), target_time) + timedelta(days=1)

            wait_time = (target_datetime - now).total_seconds()
            logging.info(f"Следующие отчеты будут отправлено в {target_datetime}")

            await asyncio.sleep(wait_time)  # Ждём до целевого времени
            await send_message()  # Отправляем сообщение
    except asyncio.CancelledError:
        logging.info("schedule_daily_message отменена.")  # Логируем отмену задачи


# Основная асинхронная функция для запуска бота
async def main():
    await dp.start_polling(bot, skip_updates=True)


# Регистрация обработчиков команд
def register_command_handlers(dp):
    dp.message.register(cmd_start, Command("start"))  # Регистрируем обработчик команды /start
    dp.message.register(cmd_set_time, Command("set_time"))    # Регистрируем обработчик команды /set_time
    dp.message.register(cmd_help, Command("help"))  # Регистрируем обработчик команды /help


register_command_handlers(dp)


# Запуск бота
if __name__ == "__main__":
    asyncio.run(main())
