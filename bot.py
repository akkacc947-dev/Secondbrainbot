import asyncio
import logging
import aiosqlite
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import LabeledPrice, PreCheckoutQuery

# O'Z TOKENINGIZNI YOZING
BOT_TOKEN = "8601439855:AAGo_ZCzMQ-9IPnN6nbhuALYvgxb3f_zf_0"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
logging.basicConfig(level=logging.INFO)

DB_NAME = "second_brain.db"

# --- 🌍 TARJIMALAR LUG'ATI ---
I18N = {
    'uz': {
        'welcome': "🧠 **Second Brain Botga Xush Kelibsiz!**\nMenga istalgan narsani yuboring va men uni saqlayman.\n\n"
                   "📌 **Buyruqlar:**\n"
                   "📂 /my_notes - Saqlanganlarni ko'rish va o'chirish\n"
                   "➕ /add_category - Yangi kategoriya yaratish\n"
                   "✏️ /edit_category - Kategoriyani tahrirlash\n"
                   "🔍 /search <so'z> - Matnlardan qidirish\n"
                   "💎 /premium - Premium statusini sotib olish",
        'choose_lang': "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Choose language:",
        'lang_saved': "🇺🇿 O'zbek tili tanlandi!",
        'add_cat': "✍️ Yangi kategoriya nomini yozing:",
        'cat_added': "✅ Kategoriya qo'shildi!",
        'edit_cat_old': "✏️ Tahrirlamoqchi bo'lgan kategoriya nomini yozing:",
        'edit_cat_new': "🔄 Yangi nomni yozing:",
        'cat_edited': "✅ Kategoriya o'zgartirildi!",
        'choose_cat': "🗂 Qaysi kategoriyaga saqlaymiz?",
        'saved': "📥 Muvaffaqiyatli saqlandi!",
        'no_cats': "Sizda hali kategoriyalar yo'q. /add_category orqali yarating.",
        'no_notes': "Sizda hali hech narsa saqlanmagan.",
        'search_prompt': "🔍 Qidirish uchun so'z kiriting: `/search kitob`",
        'no_results': "Hech narsa topilmadi 😕",
        'premium_desc': "Premium versiya yordamida cheksiz xotira va aqlli summary funksiyalarini oching!",
        'delete_btn': "❌ O'chirish",
        'deleted': "🗑 Ma'lumot muvaffaqiyatli o'chirildi!"
    },
    'ru': {
        'welcome': "🧠 **Добро пожаловать в Second Brain Bot!**\nОтправьте мне что угодно, и я это сохраню.\n\n"
                   "📌 **Команды:**\n"
                   "📂 /my_notes - Просмотр и удаление заметок\n"
                   "➕ /add_category - Создать новую категорию\n"
                   "✏️ /edit_category - Редактировать категорию\n"
                   "🔍 /search <слово> - Поиск по сохраненным\n"
                   "💎 /premium - Купить Премиум статус",
        'choose_lang': "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Choose language:",
        'lang_saved': "🇷🇺 Русский язык выбран!",
        'add_cat': "✍️ Введите название новой категории:",
        'cat_added': "✅ Категория добавлена!",
        'edit_cat_old': "✏️ Введите название категории для изменения:",
        'edit_cat_new': "🔄 Введите новое название:",
        'cat_edited': "✅ Категория изменена!",
        'choose_cat': "🗂 В какую категорию сохранить?",
        'saved': "📥 Успешно сохранено!",
        'no_cats': "У вас нет категорий. Создайте через /add_category.",
        'no_notes': "У вас еще ничего не сохранено.",
        'search_prompt': "🔍 Введите слово для поиска: `/search книга`",
        'no_results': "Ничего не найдено 😕",
        'premium_desc': "С Премиум версией откройте безлимитное хранилище и умные саммари!",
        'delete_btn': "❌ Удалить",
        'deleted': "🗑 Заметка успешно удалена!"
    },
    'en': {
        'welcome': "🧠 **Welcome to Second Brain Bot!**\nSend me anything to save it.\n\n"
                   "📌 **Commands:**\n"
                   "📂 /my_notes - View and delete notes\n"
                   "➕ /add_category - Create a new category\n"
                   "✏️ /edit_category - Edit a category\n"
                   "🔍 /search <word> - Search saved data\n"
                   "💎 /premium - Buy Premium status",
        'choose_lang': "🇺🇿 Tilni tanlang / 🇷🇺 Выберите язык / 🇬🇧 Choose language:",
        'lang_saved': "🇬🇧 English language selected!",
        'add_cat': "✍️ Enter the new category name:",
        'cat_added': "✅ Category added!",
        'edit_cat_old': "✏️ Enter the category name to edit:",
        'edit_cat_new': "🔄 Enter the new name:",
        'cat_edited': "✅ Category updated!",
        'choose_cat': "🗂 Choose a category to save:",
        'saved': "📥 Successfully saved!",
        'no_cats': "No categories yet. Create one via /add_category.",
        'no_notes': "You haven't saved anything yet.",
        'search_prompt': "🔍 Enter a word to search: `/search book`",
        'no_results': "Nothing found 😕",
        'premium_desc': "Unlock unlimited storage and smart summaries with Premium version!",
        'delete_btn': "❌ Delete",
        'deleted': "🗑 Note successfully deleted!"
    }
}

# --- 🧠 FSM HOLATLARI ---
class CategoryState(StatesGroup):
    waiting_for_new_name = State()
    waiting_for_edit_old_name = State()
    waiting_for_edit_new_name = State()

class NoteState(StatesGroup):
    waiting_for_category = State()

# --- 💾 MA'LUMOTLAR BAZASI ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, lang TEXT DEFAULT 'uz', is_premium BOOLEAN DEFAULT 0)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS custom_categories (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, name TEXT)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, type TEXT, content TEXT, category TEXT)''')
        await db.commit()

async def get_lang(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
        res = await cursor.fetchone()
        return res[0] if res else 'uz'

# --- 🟢 START VA TIL TANLASH ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (message.from_user.id,))
        await db.commit()
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 UZ", callback_data="lang_uz")
    builder.button(text="🇷🇺 RU", callback_data="lang_ru")
    builder.button(text="🇬🇧 EN", callback_data="lang_en")
    await message.reply(I18N['uz']['choose_lang'], reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: types.CallbackQuery):
    lang_code = callback.data.split("_")[1]
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang_code, callback.from_user.id))
        await db.commit()
    await callback.message.edit_text(I18N[lang_code]['lang_saved'])
    await callback.message.answer(I18N[lang_code]['welcome'])

# --- ➕ KATEGORIYALARNI BOSHQARISH ---
@dp.message(Command("add_category"))
async def add_cat_start(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    await message.reply(I18N[lang]['add_cat'])
    await state.set_state(CategoryState.waiting_for_new_name)

@dp.message(CategoryState.waiting_for_new_name)
async def add_cat_finish(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO custom_categories (user_id, name) VALUES (?, ?)", (message.from_user.id, message.text))
        await db.commit()
    await message.reply(I18N[lang]['cat_added'])
    await state.clear()

@dp.message(Command("edit_category"))
async def edit_cat_start(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT name FROM custom_categories WHERE user_id = ?", (message.from_user.id,))
        cats = await cursor.fetchall()
    if not cats:
        await message.reply(I18N[lang]['no_cats'])
        return
    cats_text = "\n".join([f"- {c[0]}" for c in cats])
    await message.reply(f"{cats_text}\n\n{I18N[lang]['edit_cat_old']}")
    await state.set_state(CategoryState.waiting_for_edit_old_name)

@dp.message(CategoryState.waiting_for_edit_old_name)
async def edit_cat_old(message: types.Message, state: FSMContext):
    await state.update_data(old_name=message.text)
    lang = await get_lang(message.from_user.id)
    await message.reply(I18N[lang]['edit_cat_new'])
    await state.set_state(CategoryState.waiting_for_edit_new_name)

@dp.message(CategoryState.waiting_for_edit_new_name)
async def edit_cat_new(message: types.Message, state: FSMContext):
    data = await state.get_data()
    old_name = data['old_name']
    new_name = message.text
    lang = await get_lang(message.from_user.id)
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE custom_categories SET name = ? WHERE user_id = ? AND name = ?", (new_name, message.from_user.id, old_name))
        await db.execute("UPDATE notes SET category = ? WHERE user_id = ? AND category = ?", (new_name, message.from_user.id, old_name))
        await db.commit()
    await message.reply(I18N[lang]['cat_edited'])
    await state.clear()

# --- 📂 SAQLANGANLARNI KO'RISH VA O'CHIRISH ---
@dp.message(Command("my_notes"))
async def view_notes(message: types.Message):
    lang = await get_lang(message.from_user.id)
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT id, category, type, content FROM notes WHERE user_id = ? ORDER BY category", (message.from_user.id,))
        notes = await cursor.fetchall()
        
    if not notes:
        await message.reply(I18N[lang]['no_notes'])
        return
        
    await message.reply("📂 **Sening hamma saqlangan ma'lumotlaring yuklanmoqda...**")
    
    for note_id, cat, n_type, content in notes:
        caption_text = f"🗂 Kategoriya: **{cat}**"
        
        builder = InlineKeyboardBuilder()
        builder.button(text=I18N[lang]['delete_btn'], callback_data=f"del_{note_id}")
        
        if n_type == "text":
            await message.answer(f"🗂 **{cat}**:\n📝 {content}", reply_markup=builder.as_markup())
        elif n_type == "voice":
            await message.answer_voice(voice=content, caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
        elif n_type == "photo":
            await message.answer_photo(photo=content, caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
        elif n_type == "video":
            await message.answer_video(video=content, caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
        elif n_type == "document":
            await message.answer_document(document=content, caption=caption_text, parse_mode="Markdown", reply_markup=builder.as_markup())
        
        await asyncio.sleep(0.2)

# --- 🗑 O'CHIRISH HANDLING ---
@dp.callback_query(F.data.startswith("del_"))
async def delete_note(callback: types.CallbackQuery):
    lang = await get_lang(callback.from_user.id)
    note_id = callback.data.replace("del_", "")
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, callback.from_user.id))
        await db.commit()
        
    await callback.answer(I18N[lang]['deleted'])
    try:
        await callback.message.delete()
    except:
        await callback.message.edit_text(f"🗑 {I18N[lang]['deleted']}")

# --- 🔍 QIDIRUV ---
@dp.message(Command("search"))
async def search_notes(message: types.Message):
    lang = await get_lang(message.from_user.id)
    query = message.text.replace("/search", "").strip()
    if not query:
        await message.reply(I18N[lang]['search_prompt'])
        return
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT category, content FROM notes WHERE user_id = ? AND type = 'text' AND content LIKE ?", (message.from_user.id, f"%{query}%"))
        results = await cursor.fetchall()
    if not results:
        await message.reply(I18N[lang]['no_results'])
        return
    reply_text = f"📋 Topildi:\n"
    for idx, (cat, cont) in enumerate(results[:10], 1):
        reply_text += f"{idx}. 🗂 {cat}: {cont[:40]}...\n"
    await message.reply(reply_text)

# --- 💎 PREMIUM ---
@dp.message(Command("premium"))
async def buy_premium(message: types.Message):
    lang = await get_lang(message.from_user.id)
    prices = [LabeledPrice(label="Premium - 1 Oylik", amount=10)] # 10 ta Stars
    await message.bot.send_invoice(
        chat_id=message.chat.id,
        title="Second Brain Premium 💎",
        description=I18N[lang]['premium_desc'],
        payload="premium_stars_payment",
        provider_token="", 
        currency="XTR",    
        prices=prices
    )

@dp.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment_handler(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (message.from_user.id,))
        await db.commit()
    await message.reply("🎉 Premium Telegram Stars orqali faollashtirildi! Rahmat! 💎")

# --- 📥 XABARLARNI TUTISH VA SAQLASH ---
@dp.message((F.text & ~F.text.startswith('/')) | F.voice | F.photo | F.document | F.video)
async def capture_note(message: types.Message, state: FSMContext):
    lang = await get_lang(message.from_user.id)
    
    if message.text: note_type, content = "text", message.text
    elif message.voice: note_type, content = "voice", message.voice.file_id
    elif message.photo: note_type, content = "photo", message.photo[-1].file_id
    elif message.document: note_type, content = "document", message.document.file_id
    elif message.video: note_type, content = "video", message.video.file_id
    else: return

    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT name FROM custom_categories WHERE user_id = ?", (message.from_user.id,))
        cats = await cursor.fetchall()

    if not cats:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO notes (user_id, type, content, category) VALUES (?, ?, ?, ?)", (message.from_user.id, note_type, content, "General"))
            await db.commit()
        await message.reply(I18N[lang]['saved'])
        return

    await state.update_data(note_content=content, note_type=note_type)
    builder = InlineKeyboardBuilder()
    for c in cats: builder.button(text=c[0], callback_data=f"save_{c[0]}")
    builder.adjust(2)
    await message.reply(I18N[lang]['choose_cat'], reply_markup=builder.as_markup())
    await state.set_state(NoteState.waiting_for_category)

@dp.callback_query(NoteState.waiting_for_category, F.data.startswith("save_"))
async def save_with_category(callback: types.CallbackQuery, state: FSMContext):
    lang = await get_lang(callback.from_user.id)
    category_name = callback.data.replace("save_", "")
    data = await state.get_data()
    
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("INSERT INTO notes (user_id, type, content, category) VALUES (?, ?, ?, ?)", 
                         (callback.from_user.id, data.get("note_type"), data.get("note_content"), category_name))
        await db.commit()
        
    await callback.message.edit_text(f"{I18N[lang]['saved']} ({category_name})")
    await state.clear()

async def main():
    await init_db()
    print("Bot muvaffaqiyatli ishga tushdi! Docker versiya.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())