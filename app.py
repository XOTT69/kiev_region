import os
import asyncio
import matplotlib
matplotlib.use('Agg')  # Для роботи на сервері без екрану
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import requests
import io
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.filters import Command
from dotenv import load_dotenv
from datetime import datetime

# Завантаження токена
load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Ваші групи (підгрупи як у репозиторії)
GROUPS = {
    '1️⃣.1 Група 1.1': '1.1', '1️⃣.2 Група 1.2': '1.2',
    '2️⃣.1 Група 2.1': '2.1', '2️⃣.2 Група 2.2': '2.2',
    '3️⃣.1 Група 3.1': '3.1', '3️⃣.2 Група 3.2': '3.2',
    '4️⃣.1 Група 4.1': '4.1', '4️⃣.2 Група 4.2': '4.2',
    '5️⃣.1 Група 5.1': '5.1', '5️⃣.2 Група 5.2': '5.2',
    '6️⃣.1 Група 6.1': '6.1', '6️⃣.2 Група 6.2': '6.2',
}

@dp.message(Command('start'))
async def start(message: types.Message):
    # Створюємо клавіатуру з двома кнопками в ряд
    buttons = [InlineKeyboardButton(text=name, callback_data=f'chart_{code}') for name, code in GROUPS.items()]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i:i+2] for i in range(0, len(buttons), 2)])
    
    await message.reply(
        '⚡ **Моніторинг відключень (Київська область)**\n\n'
        'Дані беруться з репозиторію XOTT69.\n'
        '👇 **Оберіть вашу групу:**',
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@dp.callback_query(F.data.startswith('chart_'))
async def send_chart(callback: types.CallbackQuery):
    group_code = callback.data.split('_')[1]
    group_name = next((k for k, v in GROUPS.items() if v == group_code), group_code)
    
    await callback.message.edit_text(f'⏳ Завантажую дані для **{group_name}**...')

    try:
        # 1. Отримуємо список файлів репозиторію
        repo_url = 'https://api.github.com/repos/XOTT69/kiev_region/contents'
        files_resp = requests.get(repo_url, timeout=10).json()
        
        # Шукаємо файл з "kiev" або "kyiv" у назві (або просто перший .json)
        json_file_obj = next((f for f in files_resp if f['name'].endswith('.json')), None)
        
        if not json_file_obj:
            await callback.message.edit_text("❌ Не знайдено файл даних у репозиторії.")
            return

        # 2. Завантажуємо сам JSON
        data = requests.get(json_file_obj['download_url'], timeout=10).json()

        # 3. Парсинг (Fact > Preset)
        # Спочатку шукаємо у фактичних даних, якщо немає - у планових
        source_type = "Фактичні (Fact)"
        outages = data.get('fact', {}).get('outages', [])
        
        if not outages:
            source_type = "Планові (Preset)"
            outages = data.get('preset', {}).get('outages', [])

        # Формуємо графік на 24 години (True = є світло)
        hours_status = [True] * 24 
        
        for outage in outages:
            # Перевіряємо, чи стосується відключення нашої групи
            # У репозиторії групи можуть бути списком або рядком
            affected_groups = outage.get('groups', [])
            if group_code in affected_groups:
                # Отримуємо години (потрібно брати start і end)
                start_h = int(outage.get('start', 0))
                end_h = int(outage.get('end', 24))
                
                # Позначаємо години як "без світла"
                for h in range(start_h, end_h):
                    if 0 <= h < 24:
                        hours_status[h] = False

        # Статистика
        off_count = hours_status.count(False)
        on_count = hours_status.count(True)

        # 4. Малюємо красивий графік
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 4))
        
        # Кольори: зелений (#00E676) та червоний (#FF1744)
        colors = ['#00E676' if s else '#FF1744' for s in hours_status]
        ax.bar(range(24), [1]*24, color=colors, width=0.8, edgecolor='#212121')
        
        # Налаштування осей
        ax.set_xticks(range(24))
        ax.set_xticklabels([str(h) for h in range(24)], fontsize=8, color='#B0BEC5')
        ax.set_yticks([])
        ax.set_xlim(-0.5, 23.5)
        
        # Прибираємо зайві рамки
        for spine in ax.spines.values():
            spine.set_visible(False)
            
        ax.set_title(f'Графік: {group_name}', color='white', pad=15, fontweight='bold')
        
        # Легенда
        green_patch = mpatches.Patch(color='#00E676', label='Світло є')
        red_patch = mpatches.Patch(color='#FF1744', label='Відключення')
        ax.legend(handles=[green_patch, red_patch], loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2, frameon=False)

        # Зберігаємо в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#121212')
        buf.seek(0)
        plt.close()

        # Відправка
        file = BufferedInputFile(buf.getvalue(), filename="chart.png")
        caption = (
            f"💡 **{group_name}**\n"
            f"📊 Джерело: {source_type}\n"
            f"🛑 Немає світла: **{off_count} год.**\n"
            f"✅ Є світло: **{on_count} год.**\n"
            f"📅 Оновлено: {datetime.now().strftime('%H:%M')}"
        )

        await callback.message.delete()
        await bot.send_photo(callback.message.chat.id, photo=file, caption=caption, parse_mode='Markdown')

    except Exception as e:
        await callback.message.edit_text(f"⚠️ Помилка отримання даних: {e}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
