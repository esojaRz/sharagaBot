# LFG: Game Matchmaker

Telegram-бот для поиска тиммейтов: геймер собирает лобби, куратор модерирует, админ управляет играми.

## Стек

- Python **3.12 или 3.13** (не 3.15: у `pydantic-core` / `aiohttp` нет готовых Windows-wheel, pip пытается собрать пакеты из исходников и падает)
- aiogram 3
- SQLite (`user` + `orders` со внешним ключом `orders.leader_id → user.id`)

## Структура

- `main.py` — точка входа
- `database.py` — работа с БД
- `handlers/` — роутеры (геймер / куратор / админ)
- `states.py` — FSM

## Запуск

1. Создай бота в [@BotFather](https://t.me/BotFather), скопируй токен.
2. Узнай свой Telegram ID (например через `@userinfobot`).
3. Скопируй `.env.example` в `.env` и подставь значения:

```
BOT_TOKEN=...
ADMIN_TG_ID=твой_id
```

4. Поставь [Python 3.12](https://www.python.org/downloads/release/python-31210/) (галочка **Add python.exe to PATH**). Проверка: `py -3.12 --version`.
5. Установи зависимости и запусти:

```
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install -U pip
pip install -r requirements.txt
python main.py
```

Если venv уже создавался на 3.15 — удали папку `.venv` и создай заново командами выше.

Первый `/start` от `ADMIN_TG_ID` получает роль админа. Остальные — геймеры. Роли куратора выдаёт админ кнопкой «Выдать роль».

## FSM создания лобби

Игра → платформа → ранг → время старта (`ЧЧ:ММ`) → число свободных мест.

Валидатор мест принимает только цифры в диапазоне **1 … min(5, формат_игры − 1)** (лидер уже занимает слот). Буквы и слишком большие числа отсекаются.
