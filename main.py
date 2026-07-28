import os, asyncio, yt_dlp
from aiogram import Bot, Dispatcher, F, types
from google import genai

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = genai.Client(api_key=GEMINI_API_KEY)

async def process_ai_video(video_path, message, status_msg):
    try:
        await status_msg.edit_text("🧠 Анализирую нейро-видео...")
        f = client.files.upload(file=video_path)
        while f.state.name == "PROCESSING":
            await asyncio.sleep(5)
            f = client.files.get(name=f.name)

        prompt = "Ты продюсер ИИ-контента. Оцени ролик: 1. Артефакты и качество генерации (1-10). 2. Хук и динамику. 3. Звук и липсинк. 4. Дай 3 конкретных совета по улучшению."
        response = client.models.generate_content(model='gemini-2.5-flash', contents=[f, prompt])
        await message.answer(response.text)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    finally:
        if os.path.exists(video_path):
            os.remove(video_path)

@dp.message(F.text.contains("http"))
async def handle_link(message: types.Message):
    status_msg = await message.answer("📥 Скачиваю...")
    path = f"video_{message.from_user.id}.mp4"
    try:
        with yt_dlp.YoutubeDL({'format': 'mp4', 'outtmpl': path, 'overwrites': True, 'quiet': True}) as ydl:
            ydl.download([message.text])
        await process_ai_video(path, message, status_msg)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@dp.message(F.video | F.document)
async def handle_video_file(message: types.Message):
    status_msg = await message.answer("📥 Загружаю...")
    path = f"file_{message.from_user.id}.mp4"
    file_id = message.video.file_id if message.video else message.document.file_id
    file_info = await bot.get_file(file_id)
    await bot.download_file(file_info.file_path, path)
    await process_ai_video(path, message, status_msg)

async def main():
    print("🚀 Бот запущен на Render!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
