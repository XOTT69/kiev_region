import os
import asyncio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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

# Групи
KYIV_GROUPS = {
    '1️⃣ Група 1': '1', '1️⃣.2 Група 1.2': '1.2',
    '2️⃣ Група 2': '2', '2️⃣.2 Група 2.2': '2.2',
    '3️⃣ Група 3': '3', '4️⃣ Група 4': '4',
    '5️⃣ Група 5': '5'
}

@dp.message(Command('start'))
async def start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f'kiev_{code}')]
        for name, code in KYIV_GROUPS.items()
    ])
    await message.reply('💡 **Київська область: Графік відключень**\n👇 Оберіть вашу групу:', reply_markup=kb, parse_mode='Markdown')

@dp.callback_query(F.data.startswith('kiev_'))
async def kiev_chart(callback: types.CallbackQuery):
    group_code = callback.data.split('_', 2)[-1]
    group_name = next((n for n, c in KYIV_GROUPS.items() if c == group_code), 'Група')
    
    await callback.message.edit_text(f'🎨 Малюю красивий графік для **{group_name}**...')
    
    try:
        # 1. Отримання даних
        api_url = 'https://api.github.com/repos/XOTT69/kiev_region/contents'
        files = requests.get(api_url).json()
        json_file = next((f for f in files if f['name'].endswith('.json')), None)
        
        if json_file:
            # 2. Обробка даних (ПРИКЛАД: заміни на реальний парсинг з файлу)
            statuses = [True] * 24
            
            # Симуляція реальних відключень для тесту (заміни це на data['outages'])
            if '1' in group_code: statuses[18:22] = [False]*4; statuses[9:11] = [False]*2
            if '2' in group_code: statuses[14:18] = [False]*4
            
            # Підрахунок статистики
            off_hours = statuses.count(False)
            on_hours = statuses.count(True)

            # 3. Створення красивого графіку
            plt.style.use('dark_background') # Темна тема
            fig, ax = plt.subplots(figsize=(12, 5))
            
            hours = range(24)
            # Кольори: Яскравий зелений і насичений червоний
            colors = ['#00E676' if s else '#FF1744' for s in statuses]
            
            # Малюємо стовпчики
            bars = ax.bar(hours, [1]*24, color=colors, width=0.85, edgecolor='#212121', linewidth=1.5)
            
            # Налаштування осей
            ax.set_xticks(range(24))
            ax.set_xticklabels([f"{h:02d}" for h in range(24)], fontsize=10, color='#E0E0E0')
            ax.set_yticks([]) # Прибрати вісь Y
            ax.set_xlim(-0.5, 23.5)
            
            # Прибираємо рамки
            for spine in ax.spines.values():
                spine.set_visible(False)
            
            # Додаємо сітку для зручності (вертикальна)
            ax.grid(axis='x', color='#424242', linestyle='--', alpha=0.5)
            
            # Заголовок всередині картинки
            plt.title(f'Графік: {group_name}', fontsize=16, pad=20, color='white', fontweight='bold')
            
            # Легенда (знизу)
            green_patch = mpatches.Patch(color='#00E676', label='Є світло')
            red_patch = mpatches.Patch(color='#FF1744', label='Немає світла')
            plt.legend(handles=[green_patch, red_patch], loc='upper center', bbox_to_anchor=(0.5, -0.15), 
                      ncol=2, frameon=False, fontsize=12)

            # Збереження
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#121212')
            buf.seek(0)
            plt.close()
            
            # 4. Відправка
            photo_file = BufferedInputFile(buf.getvalue(), filename="chart.png")
            
            caption = (
                f'⚡ **{group_name}**\n\n'
                f'🛑 **Без світла:** {off_hours} год.\n'
                f'✅ **Зі світлом:** {on_hours} год.\n\n'
                f'📅 _Дані актуальні на {datetime.now().strftime("%H:%M")}_'
            )
            
            await callback.message.delete()
            await bot.send_photo(callback.message.chat.id, photo=photo_file, caption=caption, parse_mode='Markdown')
        
        else:
            await callback.message.edit_text('❌ Дані не знайдено.')

    except Exception as e:
        await callback.message.edit_text(f'❌ Помилка: {e}')
    
    await callback.answer()

async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
