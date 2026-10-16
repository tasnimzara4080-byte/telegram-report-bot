import asyncio
import datetime
import logging
import os
from threading import Thread
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message
from flask import Flask

# Keep-alive web server for Render Web Service
app = Flask(__name__)


@app.route('/')
def home():
  return 'Bot is running 24/7 online!'


def run_web():
  port = int(os.environ.get('PORT', 8080))
  app.run(host='0.0.0.0', port=port)


def keep_alive():
  t = Thread(target=run_web)
  t.daemon = True
  t.start()


API_TOKEN = os.getenv('BOT_TOKEN')

router = Router()

COUNTRY_MAP = {
    '+57': 'Colombia',
    '+56': 'Chile',
    '+374': 'Armenia',
    '+880': 'Bangladesh',
    '+92': 'Pakistan',
    '+91': 'India',
}


@router.message(Command('start'))
async def cmd_start(message: Message):
  help_text = (
      '👋 স্বাগতম! আপনার ডাটা নিচের ফরম্যাটে পাঠান:\n\n'
      '+57: 204 37.61\n'
      '+56: 27 4.98\n'
      '+374: 2\n\n'
      'usdt: 42.96\n'
      'usd: 0\n'
      'bdt: 0\n'
      'pkr: 0'
  )
  await message.answer(help_text)


@router.message(F.text)
async def handle_report(message: Message):
  text = message.text
  lines = text.strip().split('\n')

  accounts_data = {}
  finances = {'usdt': 0.0, 'usd': 0.0, 'bdt': 0.0, 'pkr': 0.0}

  for line in lines:
    line = line.strip()
    if not line or ':' not in line:
      continue

    parts = line.split(':', 1)
    key = parts[0].strip().lower()
    val = parts[1].strip()

    if key in finances:
      try:
        finances[key] = float(val.replace('$', ''))
      except ValueError:
        pass
    elif key.startswith('+'):
      try:
        val_parts = val.split()
        acc_count = int(val_parts[0])
        dollar_val = (
            float(val_parts[1].replace('$', '')) if len(val_parts) > 1 else 0.0
        )
        accounts_data[key] = {'count': acc_count, 'dollars': dollar_val}
      except ValueError:
        pass

  total_accounts = sum(item['count'] for item in accounts_data.values())
  timestamp = datetime.datetime.now().strftime('%d/%m/%y %H:%M:%S')

  country_lines = []
  for code, data in accounts_data.items():
    country_name = COUNTRY_MAP.get(code, 'Other')
    count = data['count']
    dollars = data['dollars']
    if dollars > 0:
      country_lines.append(
          f'  {code} ({country_name}) => {count} {dollars:.2f}$'
      )
    else:
      country_lines.append(f'  {code} ({country_name}) => {count}')

  country_stats_str = (
      '\n'.join(country_lines) if country_lines else '  কোনো ডাটা পাওয়া যায়নি।'
  )

  report = f"""📊 ═══ CALCULATION REPORT ═══

💰 Financial Summary:
  • Total USDT: ${finances['usdt']:.2f}
  • Total USD: ${finances['usd']:.2f}
  • Total BDT: {finances['bdt']:.2f}
  • Total PKR: {finances['pkr']:.2f}

👥 Total Accounts: {total_accounts}

🌍 Country Statistics:
{country_stats_str}

📅 Generated: {timestamp}

✅ Calculation Complete!"""

  await message.answer(report)


async def main():
  logging.basicConfig(level=logging.INFO)
  keep_alive()  # Start the web server
  bot = Bot(token=API_TOKEN)
  dp = Dispatcher()
  dp.include_router(router)
  await dp.start_polling(bot)


if __name__ == '__main__':
  asyncio.run(main())