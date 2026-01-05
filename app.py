import os
import asyncio
import matplotlib
matplotlib.use('Agg')  # 🔥 ВАЖЛИВО: для роботи на сервері без екрану
import matplotlib.pyplot as plt
import requests
import io
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Групи Київської області
KYIV_GROUPS = {
    '1️⃣ Група 1': '1',
    '1️⃣.2 Група 1.2': '1.2',
    '2️⃣ Група 2': '2',
    '2️⃣.2 Група 2.2': '2.2',
    '3️⃣ Група 3': '3',
    '4️⃣ Група 4': '4',
    '5️⃣ Група 5': '5',
    '🔌 Всі': 'all'
}

@dp.message(Command('start'))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f'kiev_{code}')]
        for name, code in KYIV_GROUPS.items()
    ])
    
    await message.reply(
        '🔌 **КИЇВСЬКА ОБЛАСТЬ** 🔌\n\n'
        '👇 Обери **свою групу** 👇\n\n'
        f'_🕐 {datetime.now().strftime("%H:%M %d.%m")}_',
        reply_markup=kb,
        parse_mode='Markdown'
    )

@dp.callback_query(F.data.startswith('kiev_'))
async def kiev_chart(callback: types.CallbackQuery):
    group_code = callback.data.split('_', 2)[-1]
    group_name = next((name for name, code in KYIV_GROUPS.items() if code == group_code), 'Група')
    
    await callback.message.edit_text(f'⏳ Малюю графік для **{group_name}**...')
    
    try:
        # 1. Читаємо дані з GitHub
        api_url = 'https://api.github.com/repos/XOTT69/kiev_region/contents'
        files = requests.get(api_url).json()
        
        # Шукаємо JSON
        json_file = next((f for f in files if f['name'].endswith('.json')), None)
        
        if json_file:
            # 2. Малюємо графік
            # Поки дані тестові, щоб точно перевірити картинку
            statuses = [True] * 24
            if '1.2' in group_code or '1' in group_code:
                statuses[18:22] = [False] * 4  # Тестове відключення ввечері
            
            fig, ax = plt.subplots(figsize=(10, 4), facecolor='#f8f9fa')
            hours = range(24)
            
            # Кольори: Зелений = Світло, Червоний = Немає
            colors = ['#28a745' if s else '#dc3545' for s in statuses]
            
            # Створюємо стовпчики
            ax.bar(hours, [1]*24, color=colors, width=0.9)
            
            # Налаштування вигляду
            ax.set_title(f'Графік: {group_name}', fontsize=14, pad=15)
            ax.set_xlabel('Години доби (0-23)')
            ax.set_yticks([]) # Прибрати зайві цифри збоку
            ax.set_xticks(range(0, 24, 2)) # Години через одну
            ax.set_xlim(-0.5, 23.5)
            
            # Рамка навколо графіка
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # 3. Зберігаємо в пам'ять (буфер)
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=100)
            buf.seek(0)
            plt.close()
            
            # 4. Відправляємо фото
            photo_file = BufferedInputFile(buf.getvalue(), filename="chart.png")
            
            caption = (
                f'🔌 **{group_name}**\n'
                f'📍 Київська область\n'
                f'🕐 Оновлено: {datetime.now().strftime("%H:%M")}\n'
                f'🔗 Джерело: GitHub XOTT69'
            )
            
            # Видаляємо повідомлення "Завантажую..." і шлемо фото
            await callback.message.delete()
            await bot.send_photo(
                callback.message.chat.id, 
                photo=photo_file, 
                caption=caption,
                parse_mode='Markdown'
            )
        else:
            await callback.message.edit_text('❌ Не знайдено файл даних на GitHub!')
            
    except Exception as e:
        # Логування помилки прямо в чат, щоб ти бачив
        await callback.message.edit_text(f'❌ Помилка: {str(e)}')
    
    await callback.answer()

async def main():
    print('🚀 Бот запущено!')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
