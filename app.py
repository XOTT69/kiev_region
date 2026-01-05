import os
import asyncio
import matplotlib.pyplot as plt
import requests
import io
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from dotenv import load_dotenv
from datetime import datetime
import json

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ✅ ПРАВИЛЬНІ ГРУПИ КИЇВЩИНИ
KYIV_GROUPS = {
    '1️⃣ Група 1': 'group_1',
    '1️⃣.2 Група 1.2': 'group_1_2',
    '2️⃣ Група 2': 'group_2',
    '2️⃣.2 Група 2.2': 'group_2_2',
    '3️⃣ Група 3': 'group_3',
    '4️⃣ Група 4': 'group_4',
    '5️⃣ Група 5': 'group_5',
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
    
    await callback.message.edit_text(f'⏳ Читаю **{group_name}**...')
    
    try:
        # Читаємо репозиторій
        api_url = 'https://api.github.com/repos/XOTT69/kiev_region/contents'
        files = requests.get(api_url).json()
        
        # Перший JSON файл
        json_file = next((f for f in files if f['name'].endswith('.json')), None)
        
        if json_file:
            data = requests.get(json_file['download_url']).json()
            
            # ✅ ТЕСТОВИЙ ГРАФІК (заміни на реальний парсинг)
            statuses = [True] * 24
            if '1_2' in group_code:
                statuses[8:12] = [False] * 4  # Приклад відключення
            elif '2_2' in group_code:
                statuses[14:18] = [False] * 4
            
            # ГРАФІК
            fig, ax = plt.subplots(figsize=(12, 5))
            hours = range(24)
            colors = ['green' if s else 'red' for s in statuses]
            
            ax.bar(hours, [1]*24, color=colors, alpha=0.8)
            ax.set_title(f'🔌 {group_name} - КИЇВЩИНА', fontsize=16)
            ax.set_xlabel('🕐 Години'); ax.set_ylabel('Статус')
            ax.grid(True, alpha=0.3)
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            caption = f'🔌 **{group_name}**\n📍 КИЇВСЬКА ОБЛАСТЬ\n🕐 {datetime.now().strftime("%H:%M")}\n\n/start - змінити'
            
            await callback.message.delete()
            await bot.send_photo(callback.message.chat.id, photo=buf, caption=caption)
        else:
            await callback.message.edit_text('❌ JSON не знайдено!')
            
    except Exception as e:
        await callback.message.edit_text(f'❌ Помилка: {str(e)}')
    
    await callback.answer()

async def main():
    print('🚀 КИЇВЩИНА Bot онлайн!')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
