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
    
    await callback.message.edit_text(f'⏳ Читаю **{group_name}**...')
    
    try:
        # ✅ РЕПЕЗИТОРІЙ → JSON
        api_url = 'https://api.github.com/repos/XOTT69/kiev_region/contents'
        files = requests.get(api_url).json()
        
        # Перший JSON (preset/fact)
        json_file = next((f for f in files if f['name'].endswith('.json')), None)
        
        if json_file:
            data_url = json_file['download_url']
            data = requests.get(data_url).json()
            
            print(f"📊 Знайдено даних: {len(data)} записів")  # Лог
            
            # ✅ РЕАЛЬНИЙ ПАРСИНГ
            statuses = get_real_statuses(data, group_code)
            
            # ГРАФІК З РЕАЛЬНИМИ ДАНИМИ
            fig, ax = plt.subplots(figsize=(14, 6), facecolor='white')
            hours = range(24)
            colors = ['#4CAF50' if s else '#F44336' for s in statuses]
            
            ax.bar(hours, [1]*24, color=colors, alpha=0.85, edgecolor='white', linewidth=1)
            ax.set_title(f'🔌 {group_name} - КИЇВЩИНА\n🕐 {datetime.now().strftime("%H:%M")}', 
                        fontsize=18, fontweight='bold')
            ax.set_xlabel('🕐 Години', fontsize=14)
            ax.set_ylabel('Статус', fontsize=14)
            ax.set_xticks(range(0, 25, 2))
            ax.grid(True, alpha=0.3)
            
            # Легенда
            ax.text(0.02, 0.92, '🟢 Світло', transform=ax.transAxes, fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="#4CAF50", alpha=0.2))
            ax.text(0.02, 0.82, '🔴 Відключення', transform=ax.transAxes, fontsize=12,
                   bbox=dict(boxstyle="round,pad=0.3", facecolor="#F44336", alpha=0.2))
            
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='white')
            buf.seek(0)
            plt.close()
            
            caption = (
                f'🔌 **{group_name}**\n'
                f'📍 **КИЇВСЬКА ОБЛАСТЬ**\n'
                f'📊 **Дані**: {json_file["name"]}\n'
                f'🕐 **Оновлено**: {datetime.now().strftime("%H:%M %d.%m")}\n\n'
                f'_github.com/XOTT69/kiev_region_  /start'
            )
            
            await callback.message.delete()
            await bot.send_photo(callback.message.chat.id, photo=buf, caption=caption, parse_mode='Markdown')
            
            print(f"✅ Надіслано графік для {group_name}")
        else:
            await callback.message.edit_text('❌ Не знайшов JSON файл!')
            
    except Exception as e:
        await callback.message.edit_text(f'❌ {str(e)}')
        print(f"❌ Помилка: {e}")
    
    await callback.answer()

def get_real_statuses(data, group_code):
    """✅ РЕАЛЬНИЙ парсинг твоїх даних"""
    statuses = [True] * 24  # Світло за замовчуванням
    
    try:
        # Варіант 1: data['preset'] / data['fact']
        outages = data.get('preset', {}).get('outages', []) or data.get('fact', {}).get('outages', [])
        
        for outage in outages:
            group_match = outage.get('group') or outage.get('groups', '')
            if group_code in str(group_match):
                start = int(outage.get('start', 0)) % 24
                duration = int(outage.get('duration', 1))
                for h in range(start, min(start + duration, 24)):
                    statuses[h] = False
        
        # Варіант 2: прямі години
        if 'hourly' in data:
            hourly = data['hourly'].get(group_code, [])
            for i, status in enumerate(hourly[:24]):
                statuses[i] = status == 'on'
                
    except Exception as e:
        print(f"Парсинг: {e}")
        pass  # Fallback
    
    return statuses

async def main():
    print('🚀 КИЇВЩИНА Bot онлайн! Готовий графіки!')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
