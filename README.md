# HealthDiaryBackend

Backend API для дневника здоровья: пользователи, приёмы лекарств с повторениями, активность, вода, сон, температура тела и подписки.

## Стек

| Компонент | Версия |
|---|---|
| Python | 3.14 |
| Poetry | 2.5.1 |
| FastAPI | 0.142.2 |
| Uvicorn | 0.54.0 |
| SQLAlchemy | 2.0.54 |
| asyncpg | 0.31.0 |
| Alembic | 1.20.0 |
| Pydantic / pydantic-settings | 2.13.5 / 2.15.0 |
| Redis (redis-py) | 8.1.0 |
| PostgreSQL | 18.0 |
| APScheduler | 3.11.3 |
| Pillow | 12.3.0 |
| slowapi | 0.1.10 |

Остальные зависимости: `bcrypt`, `PyJWT`, `aiofiles`, `aiosmtplib`, `Jinja2`, `orjson`, `python-multipart`, `email-validator`, `python-dateutil`.

## Запуск

### Docker

```bash
cp app/.env.template app/.env
docker compose up -d --build
```

Поднимаются четыре сервиса:

| Сервис | Контейнер | Порт |
|---|---|---|
| backend | healthdiarybackend | 8000 |
| db | healthdiarydb | 5432 |
| db-test | healthdiarydb-test | 5433 |
| redis | healthdiarybackend-redis-1 | 6379 |

Миграции накатываются автоматически при старте контейнера — `app/prestart.sh` выполняет `alembic upgrade head` перед запуском приложения.

Документация: http://localhost:8000/docs

### Локально

```bash
poetry install
poetry add <package>        # установка новых зависимостей
poetry run alembic -c app/alembic.ini upgrade head
poetry run python app/main.py
```

## Переменные окружения

Шаблон — `app/.env.template`.

| Переменная | Назначение |
|---|---|
| `APP_CONFIG__DB__URL` | DSN PostgreSQL для asyncpg |
| `APP_CONFIG__SECRET_KEY` | ключ подписи JWT |
| `APP_CONFIG__REDIS__URL` | адрес Redis |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | доступы к БД |
| `SMTP_USER`, `SMTP_PASS` | отправка писем с OTP-кодами |

Префикс `APP_CONFIG__` задан в `SettingsConfigDict`, вложенность разделяется `__`. При `RUNNING_IN_DOCKER=1` адреса БД и Redis переопределяются на имена сервисов compose.

## API

Базовый префикс — `/api`. Дневниковые ресурсы вложены в пользователя: `/api/v1/users/{user_id}/...`.

### Auth — `/api/v1/auth`

| Метод | Путь | Описание |
|---|---|---|
| POST | `/login` | выдача access/refresh пары |
| POST | `/refresh` | ротация пары по refresh-токену |
| POST | `/logout` | отзыв одного refresh-токена |
| POST | `/logout/all` | отзыв всех токенов пользователя |
| POST | `/request-verify` | отправка кода подтверждения почты |
| POST | `/verify` | подтверждение почты |
| POST | `/request-reset-password` | отправка кода для сброса пароля |
| POST | `/reset-password` | сброс пароля |

`/request-verify` и `/request-reset-password` ограничены лимитом 1 запрос в минуту.

### Users — `/api/v1/users`

| Метод | Путь | Описание |
|---|---|---|
| GET | `/me` | текущий пользователь |
| GET | `/{user_id}` | профиль (без email) |
| POST | `` | регистрация, лимит 5 запросов в минуту |
| PATCH | `/{user_id}` | обновление профиля |
| POST | `/{user_id}/avatar` | загрузка аватара |
| DELETE | `/{user_id}` | удаление пользователя |

### Дневник

| Префикс | Методы |
|---|---|
| `/api/v1/users/{user_id}/tasks` | GET, POST, PATCH `/{task_guid}`, DELETE `/{task_guid}` |
| `/api/v1/users/{user_id}/activities` | GET (периоды day/week/month/year), POST |
| `/api/v1/users/{user_id}/water_intakes` | GET (периоды day/week/month), POST |
| `/api/v1/users/{user_id}/sleeps` | GET, POST |
| `/api/v1/users/{user_id}/body_temperatures` | GET, POST, DELETE `/{body_temp_guid}` |
| `/api/v1/users/{user_id}/subscriptions` | GET `/plans`, GET `/current`, POST `/activate/{plan_id}` |

Записи по активности, воде, сну и температуре создаются через upsert по ключу `(user_id, record_date)` или `(user_id, record_datetime)`. Активность и вода поддерживают поле `add_to_existing` — при `true` значения прибавляются к существующим, при `false` (по умолчанию) перезаписываются. Upsert выполняется одним запросом `INSERT ... ON CONFLICT DO UPDATE` без чтения строки перед записью.

### Медиа

`GET /media/users/{user_id}/{filename}` — отдача файлов из `media/`. Проверяется, что итоговый путь остаётся внутри каталога медиа.

## Структура

```
app/
  api/
    deps.py            # зависимости: текущий пользователь, проверка прав
    v1/                # роутеры
  core/
    config.py          # настройки
    limiter.py         # общий rate limiter
    redis_client.py    # клиент Redis
    scheduler.py       # APScheduler
    models/            # модели SQLAlchemy
    schemas/           # Pydantic-схемы и валидаторы
  crud/
    base.py            # CRUDBase с общими операциями
  services/            # otp, periods, media, subscriptions, user_avatar, task_generator
  alembic/             # миграции и seed-данные
tests/
  api/v1/              # тесты роутеров
  factories/           # фабрики объектов
  conftest.py          # фикстуры
```

CRUD построен на базовом классе `CRUDBase` с generic-параметрами `[Model, CreateSchema, UpdateSchema]`. Каждый круд — класс-наследник и готовый экземпляр в конце файла (`users_crud`, `tasks_crud`).

## Хранение OTP-кодов

Коды подтверждения хранятся в Redis, а не в базе: запись `SET` с TTL, счётчик попыток через `INCR` с отдельным ключом. При превышении лимита попыток оба ключа удаляются. Ключи задаются шаблонами в конфиге:

```python
otp_code_key: str = "otp:code:{verification_type}:{user_id}"
otp_attempts_key: str = "otp:attempts:{verification_type}:{user_id}"
otp_max_attempts: int = 5
```

## Повторяющиеся задачи

`app/services/task_generator.py` раз в минуту (`CronTrigger(minute="*")`) выбирает задачи с `start_datetime <= now()`, у которых есть повторение, и создаёт следующую задачу со сдвигом на интервал повторения. Выборка идёт батчами по `TASKS_BATCH_SIZE` с одним `commit` на батч. Задача, просроченная на несколько интервалов, догоняется за один запуск. По `start_datetime` есть индекс.

## Проверки

```bash
poetry run pytest         # тесты
poetry run mypy .         # строгая проверка типов
poetry run ruff check .   # линтер
poetry run ruff format .  # форматирование
```

Тесты требуют запущенных сервисов `db-test` (порт 5433) и `redis`. Адреса переопределяются переменными `TEST_DATABASE_URL` и `TEST_REDIS_URL`; по умолчанию тесты используют `redis://localhost:6379/15` — отдельный индекс, который очищается перед каждым тестом и после него.

Схема тестовой БД создаётся через `Base.metadata.create_all`, а не миграциями, поэтому миграции проверяются отдельно против чистой базы.
