import os
import json
import random
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ForceReply

TOKEN = os.environ["TOKEN"]
CHAT_ID = os.environ.get("CHAT_ID")
STATE_FILE = "state.json"
TIMEZONE = ZoneInfo("Europe/Moscow")
SEND_HOUR = 7  # во сколько утра слать рацион (по Москве)
START_WEIGHT = 90.0  # с чего начали — для расчёта прогресса в /ves
QUIT_SMOKING_DATE = datetime(2026, 8, 17, 0, 0, tzinfo=TIMEZONE)

DAY_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
MEALS = ["завтрак", "обед", "перекус", "ужин"]
MEAL_EMOJI = {"завтрак": "🌅", "обед": "🍲", "перекус": "🍎", "ужин": "🌙"}

BTN_MENU = "📅 Рацион"
BTN_SHOP = "🛒 Покупки"
BTN_WORKOUT = "🏋️ Тренировка"

MAIN_KEYBOARD = ReplyKeyboardMarkup([[BTN_MENU, BTN_SHOP], [BTN_WORKOUT]], resize_keyboard=True)

KNOWN_BUTTONS = {BTN_MENU, BTN_SHOP, BTN_WORKOUT}
KNOWN_COMMANDS = {"/start", "/menu", "/pokupki", "/ves", "/chatid"}

# ---------- МЕНЮ НА НЕДЕЛЮ (0 = Пн ... 6 = Вс), повторяется весь месяц ----------
MENU = {
    0: {
        "завтрак": "Овсянка на молоке 1,5% (70 г крупы + 250 мл молока), банан, 20 г грецких орехов — ≈520 ккал",
        "обед": "Куриная грудка на гриле 180 г, гречка отварная 80 г (сухой вес), овощной салат + 1 ч.л. масла — ≈640 ккал",
        "перекус": "Творог 5% 180 г + груша — ≈260 ккал",
        "ужин": "Треска/минтай запечённая 200 г, брокколи и морковь на пару 250 г, 1 ч.л. масла — ≈440 ккал",
    },
    1: {
        "завтрак": "2 яйца + 1 белок, тост из цельнозернового хлеба, авокадо 50 г, помидор — ≈450 ккал",
        "обед": "Индейка тушёная 200 г, рис отварной 80 г (сухой вес), овощи гриль — ≈660 ккал",
        "перекус": "Натуральный йогурт 150 г + ягоды 100 г + 15 г мюсли без сахара — ≈230 ккал",
        "ужин": "Куриные бёдра без кожи запечённые 200 г, тушёная капуста/овощное рагу 200 г — ≈510 ккал",
    },
    2: {
        "завтрак": "Омлет из 3 яиц на молоке (100 мл), шпинат, помидор, 20 г сыра, тост цельнозерновой — ≈460 ккал",
        "обед": "Постная говядина тушёная 180 г, картофель отварной 200 г, овощной салат 150 г — ≈640 ккал",
        "перекус": "Кефир 1% 250 мл + 20 г орехов — ≈230 ккал",
        "ужин": "Куриная грудка запечённая с овощами (150 г курицы + 250 г овощей) — ≈380 ккал",
    },
    3: {
        "завтрак": "Овсянка на воде и молоке пополам (60 г крупы), 1 яйцо варёное, 15 г орехов, 10 г мёда — ≈470 ккал",
        "обед": "Сёмга/горбуша запечённая 150 г, булгур или рис 70 г (сухой вес), овощной салат — ≈630 ккал",
        "перекус": "Творог 5% 150 г + банан — ≈260 ккал",
        "ужин": "Куриная грудка на гриле 150 г, печёный картофель 150 г, овощи на пару — ≈480 ккал",
    },
    4: {
        "завтрак": "Сырники запечённые (творог 200 г, 1 яйцо, 2 ст.л. муки), ягодный соус без сахара — ≈400 ккал",
        "обед": "Индейка на гриле 200 г, гречка отварная 70 г (сухой вес), овощной салат — ≈600 ккал",
        "перекус": "Натуральный йогурт 150 г + 15 г миндаля — ≈200 ккал",
        "ужин": "Треска/минтай 220 г, рис отварной 50 г, овощи гриль + 1 ч.л. масла — ≈480 ккал",
    },
    5: {
        "завтрак": "Омлет 3 яйца, овощи, 20 г сыра, тост цельнозерновой — ≈450 ккал",
        "обед": "Суп или горячее с курицей и овощами, без лишнего хлеба (можно вне дома) — ≈500 ккал",
        "перекус": "Фрукт + горсть орехов 20 г — ≈220 ккал",
        "ужин": "Рыба или курица с овощами и небольшой порцией гарнира 100 г (семейный ужин) — ≈550 ккал",
    },
    6: {
        "завтрак": "Творог 200 г с мёдом (10 г), орехами (15 г) и ягодами (100 г) — ≈380 ккал",
        "обед": "Плов с курицей облегчённый (курица 150 г, рис 70 г сух., морковь, лук) — ≈620 ккал",
        "перекус": "Кефир 1% 250 мл + фрукт — ≈200 ккал",
        "ужин": "Салат с тунцом (консерва в собств. соку, 185 г), овощи, 1 ч.л. масла — ≈350 ккал",
    },
}

SHOPPING_LIST = (
    "🛒 *Список покупок на неделю*\n\n"
    "*Белковое:* куриная грудка/бёдра ~1 кг, индейка ~400 г, рыба (треска/сёмга) ~800 г, "
    "говядина постная ~200 г, творог 5% ~1 кг, яйца 15 шт, натуральный йогурт 500 мл, кефир 1% 500 мл\n\n"
    "*Крупы:* гречка 300 г, рис 250 г, булгур 100 г, хлеб цельнозерновой\n\n"
    "*Овощи/фрукты:* огурцы, помидоры, брокколи, морковь, кабачки, перец, капуста, зелень, "
    "картофель, бананы, яблоки, груши, ягоды, лимон\n\n"
    "*Прочее:* оливковое масло, грецкие орехи, миндаль, мёд, специи"
)

WORKOUT_TEXT = (
    "🏋️ *Тренировка (зал, всё тело)*\n\n"
    "Разминка 7–10 мин (дорожка/велотренажёр) + суставная гимнастика\n\n"
    "1️⃣ Жим ногами — 3×12-15\nhttps://www.youtube.com/watch?v=EBcmwSJ1W_0\n\n"
    "2️⃣ Жим гантелей лёжа — 3×10-12\nhttps://www.youtube.com/watch?v=FeWqaRSA9A0\n\n"
    "3️⃣ Тяга верхнего блока — 3×12-15\nhttps://www.youtube.com/watch?v=-3B1gjQ78Kg\n\n"
    "4️⃣ Жим гантелей сидя (плечи) — 3×10-12\nhttps://www.youtube.com/watch?v=X5bgyaiWoJI\n\n"
    "5️⃣ Тяга горизонтального блока — 3×12\nhttps://www.youtube.com/watch?v=cbW-4RcZ4G0\n\n"
    "6️⃣ Планка — 3×20-40 сек\nhttps://www.youtube.com/watch?v=3v-P5h0fBKg\n\n"
    "Заминка — растяжка 5 мин\n\n"
    "⚠️ Боль в груди, сильная одышка, головокружение — сразу стоп и к врачу."
)

REST_TEXT = (
    "😴 Отдых — тоже часть плана. Прогулка 30–40 минут (лес/пляж с металлоискателем "
    "считается на 100%) и лёгкая растяжка."
)

NUDGES = [
    "Эй! Хватит греть диван — встал и потянулся 🙆",
    "Тело затекло? 5 минут разминки прямо сейчас — и полегчает",
    "Не засиживайся! Пройдись хотя бы до кухни и обратно 🚶",
    "Пора подвигаться — тело не для того, чтобы просто сидеть",
    "Эй, ленивая пятая точка — встряхнись! 😄",
    "Опять сидим? Вставай, 10 приседаний — и можно дальше",
    "Организм требует движения, а не ещё пять минут в телефоне",
    "Потянись как кот — и почувствуешь разницу",
]
NUDGE_IMAGES = ["images/move1.png", "images/move2.png", "images/move3.png", "images/move4.png"]

START_TEXT = (
    "Привет! Каждое утро между 7:00 и 7:10 по Москве буду присылать сюда рацион на день, "
    "плюс 3-4 раза за день буду напоминать подвигаться. Раз в неделю спрошу вес.\n\n"
    "Кнопки внизу всегда под рукой."
)

SMOKE_REFRESH_MARKUP = InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Обновить", callback_data="refresh_smoke")]])


def short_label(dish: str, limit: int = 26) -> str:
    return dish if len(dish) <= limit else dish[:limit].rstrip() + "…"


def build_day_message(day_idx: int):
    day = MENU[day_idx]
    text = f"📅 *{DAY_NAMES[day_idx]} — рацион на день*\n\n"
    for meal in MEALS:
        text += f"{MEAL_EMOJI[meal]} *{meal.capitalize()}:* {day[meal]}\n\n"
    buttons = [
        [InlineKeyboardButton(f"🔄 {meal}", callback_data=f"swap:{day_idx}:{meal}") for meal in MEALS[:2]],
        [InlineKeyboardButton(f"🔄 {meal}", callback_data=f"swap:{day_idx}:{meal}") for meal in MEALS[2:]],
        [
            InlineKeyboardButton("✅ Тренировка есть", callback_data="workout:yes"),
            InlineKeyboardButton("😴 Сегодня отдых", callback_data="workout:rest"),
        ],
    ]
    return text, InlineKeyboardMarkup(buttons)


def smoking_counter_text():
    delta = datetime.now(TIMEZONE) - QUIT_SMOKING_DATE
    days, hours = delta.days, delta.seconds // 3600
    return f"🚭 *Не курю уже:* {days} дн. {hours} ч.\nСтарт: 17.08.2026 💪"


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_update_id": 0, "last_sent_date": ""}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False)


async def start_weight_prompt(bot: Bot, chat_id, state: dict):
    await bot.send_message(
        chat_id,
        "Пора взвеситься ⚖️ Напиши вес числом, например: 89.4",
        reply_markup=ForceReply(input_field_placeholder="Например: 89.4"),
    )
    state.setdefault("awaiting_weight", {})[str(chat_id)] = True


async def process_weight_input(bot: Bot, chat_id, raw_text: str, state: dict):
    try:
        value = float(raw_text.strip().replace(",", "."))
    except ValueError:
        await bot.send_message(chat_id, "Не понял число, попробуй ещё раз: /ves 89.4", reply_markup=MAIN_KEYBOARD)
        return
    history = state.setdefault("weight_log", [])
    prev = history[-1]["value"] if history else None
    history.append({"date": datetime.now(TIMEZONE).strftime("%Y-%m-%d"), "value": value})
    msg = f"⚖️ Записал: {value} кг\nОт старта ({START_WEIGHT} кг): {value - START_WEIGHT:+.1f} кг"
    if prev is not None:
        msg += f"\nС прошлой записи: {value - prev:+.1f} кг"
    await bot.send_message(chat_id, msg, reply_markup=MAIN_KEYBOARD)


async def handle_message(bot: Bot, chat_id, text: str, state: dict):
    text = text.strip()
    key = str(chat_id)
    awaiting = state.setdefault("awaiting_weight", {})
    parts = text.split()
    first_word = parts[0].split("@")[0].lower() if parts else ""
    is_known = text in KNOWN_BUTTONS or first_word in KNOWN_COMMANDS

    if awaiting.get(key):
        awaiting.pop(key, None)
        if not is_known:
            await process_weight_input(bot, chat_id, text, state)
            return

    command = first_word
    if command == "/start":
        await bot.send_message(chat_id, START_TEXT, reply_markup=MAIN_KEYBOARD)
    elif command == "/menu" or text == BTN_MENU:
        today = datetime.now(TIMEZONE).weekday()
        msg_text, markup = build_day_message(today)
        await bot.send_message(chat_id, msg_text, parse_mode="Markdown", reply_markup=markup)
    elif command == "/pokupki" or text == BTN_SHOP:
        msg = await bot.send_message(chat_id, SHOPPING_LIST, parse_mode="Markdown")
        try:
            await bot.pin_chat_message(chat_id, msg.message_id)
        except Exception:
            await bot.send_message(
                chat_id,
                "Не смог закрепить сам — закрепи вручную. Возможно, боту не дали право «Закрепление сообщений».",
            )
    elif command == "/chatid":
        await bot.send_message(chat_id, f"ID этого чата: `{chat_id}`", parse_mode="Markdown")
    elif command == "/ves" and len(parts) >= 2:
        await process_weight_input(bot, chat_id, parts[1], state)
    elif command == "/ves":
        history = state.get("weight_log", [])
        if history:
            lines = [f"{e['date']}: {e['value']} кг" for e in history[-10:]]
            change = history[-1]["value"] - START_WEIGHT
            await bot.send_message(
                chat_id,
                "⚖️ *Динамика веса*\n\n" + "\n".join(lines) + f"\n\nОт старта ({START_WEIGHT} кг): {change:+.1f} кг",
                parse_mode="Markdown",
            )
        else:
            await start_weight_prompt(bot, chat_id, state)
    elif text == BTN_WORKOUT:
        await bot.send_message(chat_id, WORKOUT_TEXT, parse_mode="Markdown", disable_web_page_preview=True)


async def handle_callback(bot: Bot, query, state: dict):
    await bot.answer_callback_query(query.id)
    chat_id = query.message.chat_id
    data = query.data
    if data.startswith("swap:"):
        _, day_idx_str, meal = data.split(":")
        day_idx = int(day_idx_str)
        buttons = [
            [InlineKeyboardButton(short_label(MENU[d][meal]), callback_data=f"pick:{meal}:{d}")]
            for d in MENU
            if d != day_idx
        ]
        await bot.send_message(chat_id, f"Выбери замену ({meal}):", reply_markup=InlineKeyboardMarkup(buttons))
    elif data.startswith("pick:"):
        _, meal, day_idx_str = data.split(":")
        dish = MENU[int(day_idx_str)][meal]
        await bot.send_message(chat_id, f"{MEAL_EMOJI[meal]} *Заменил на:* {dish}", parse_mode="Markdown")
    elif data == "workout:yes":
        await bot.send_message(chat_id, WORKOUT_TEXT, parse_mode="Markdown", disable_web_page_preview=True)
    elif data == "workout:rest":
        await bot.send_message(chat_id, REST_TEXT, parse_mode="Markdown")
    elif data == "refresh_smoke":
        await refresh_smoke_pin(bot, state)


async def ensure_smoke_pin(bot: Bot, state: dict):
    if state.get("smoke_pin_message_id"):
        return
    msg = await bot.send_message(
        CHAT_ID, smoking_counter_text(), parse_mode="Markdown", reply_markup=SMOKE_REFRESH_MARKUP
    )
    try:
        await bot.pin_chat_message(CHAT_ID, msg.message_id)
    except Exception as e:
        print("Не смог закрепить счётчик:", e)
    state["smoke_pin_message_id"] = msg.message_id


async def refresh_smoke_pin(bot: Bot, state: dict):
    msg_id = state.get("smoke_pin_message_id")
    if not msg_id:
        return
    try:
        await bot.edit_message_text(
            chat_id=CHAT_ID,
            message_id=msg_id,
            text=smoking_counter_text(),
            parse_mode="Markdown",
            reply_markup=SMOKE_REFRESH_MARKUP,
        )
    except Exception:
        pass  # текст не изменился с прошлой проверки — это нормально


async def maybe_prompt_weekly_weight(bot: Bot, state: dict, now: datetime):
    last = state.get("last_weight_prompt_date")
    if last:
        days_since = (now.date() - datetime.strptime(last, "%Y-%m-%d").date()).days
        if days_since < 7:
            return
    if now.weekday() == 0 and now.hour == SEND_HOUR:
        await start_weight_prompt(bot, CHAT_ID, state)
        state["last_weight_prompt_date"] = now.strftime("%Y-%m-%d")


def schedule_nudges_if_needed(state: dict, today_str: str):
    if state.get("nudge_date") != today_str:
        count = random.choice([3, 4])
        hours = sorted(random.sample(range(9, 21), count))
        state["nudge_date"] = today_str
        state["nudge_times"] = [f"{h:02d}:{random.randint(0, 59):02d}" for h in hours]
        state["nudge_sent"] = []


async def maybe_send_nudges(bot: Bot, state: dict, now: datetime):
    today_str = now.strftime("%Y-%m-%d")
    schedule_nudges_if_needed(state, today_str)
    current_hm = now.strftime("%H:%M")
    for t in state.get("nudge_times", []):
        if t <= current_hm and t not in state.get("nudge_sent", []):
            text = random.choice(NUDGES)
            image_path = random.choice(NUDGE_IMAGES)
            try:
                with open(image_path, "rb") as f:
                    await bot.send_photo(CHAT_ID, photo=f, caption=text)
            except Exception as e:
                print("Не смог отправить картинку, шлю текстом:", e)
                await bot.send_message(CHAT_ID, text)
            state.setdefault("nudge_sent", []).append(t)


async def main():
    async with Bot(token=TOKEN) as bot:
        state = load_state()

        updates = await bot.get_updates(offset=state["last_update_id"] + 1, timeout=1)
        for update in updates:
            state["last_update_id"] = update.update_id
            try:
                if update.message and update.message.text:
                    await handle_message(bot, update.message.chat_id, update.message.text, state)
                elif update.callback_query:
                    await handle_callback(bot, update.callback_query, state)
            except Exception as e:
                print("Ошибка обработки апдейта:", e)

        now = datetime.now(TIMEZONE)
        today_str = now.strftime("%Y-%m-%d")
        if CHAT_ID:
            if now.hour == SEND_HOUR and state.get("last_sent_date") != today_str:
                msg_text, markup = build_day_message(now.weekday())
                await bot.send_message(chat_id=CHAT_ID, text=msg_text, parse_mode="Markdown", reply_markup=markup)
                state["last_sent_date"] = today_str

            await ensure_smoke_pin(bot, state)
            await refresh_smoke_pin(bot, state)
            await maybe_prompt_weekly_weight(bot, state, now)
            await maybe_send_nudges(bot, state, now)

        save_state(state)


if __name__ == "__main__":
    asyncio.run(main())
