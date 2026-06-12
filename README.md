# otmt — Otomoto → Telegram Bot

Автоматический мониторинг объявлений о продаже авто на Otomoto.pl с публикацией в Telegram-канал.

## Структура

```
otmt/
├─ .github/workflows/otomoto.yml   # GitHub Actions cron job
├─ data/
│  └─ sent_ids_otomoto.json        # ID уже отправленных объявлений (state)
├─ src/
│  ├─ config.py        # Настройки и env-переменные
│  ├─ state.py         # Загрузка/сохранение state
│  ├─ otomoto_client.py # GraphQL-запросы к Otomoto
│  ├─ formatter.py     # Форматирование поста для Telegram
│  ├─ telegram_client.py # Отправка в Telegram
│  └─ main.py          # Главный скрипт
└─ requirements.txt
```

## Настройка

### 1. Telegram

1. Создай бота через [@BotFather](https://t.me/BotFather), получи `BOT_TOKEN`.
2. Создай канал, добавь бота как администратора.
3. Получи `CHAT_ID` канала (например через [@userinfobot](https://t.me/userinfobot)).

### 2. GitHub Secrets

Зайди: `Settings → Secrets and variables → Actions → New repository secret`

| Secret | Значение |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен из BotFather |
| `TELEGRAM_CHAT_ID` | id канала, например `-1001234567890` |

### 3. Запуск

- Автоматически: каждые 15 минут по cron.
- Вручную: `Actions → Otomoto Telegram Scraper → Run workflow`.

## Фильтры

Фильтры задаются в `src/otomoto_client.py` → функция `build_variables()`.

По умолчанию:
- без битых (`filter_enum_damaged: 0`)
- цена до `MAX_PRICE_PLN` (из env, по умолчанию 10000 PLN)

Для добавления фильтра по марке/модели, топливу и т.д. — добавь в список `filters` нужные параметры.

## Локальный запуск

```bash
pip install -r requirements.txt
export TELEGRAM_BOT_TOKEN=your_token
export TELEGRAM_CHAT_ID=your_chat_id
python -m src.main
```
