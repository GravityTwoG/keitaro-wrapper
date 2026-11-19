# Keitaro Wrapper

Обёртка над [Keitaro Admin API](https://docs.keitaro.io/en/development/admin-api.html):
создание рекламных кампаний с гео-потоком и редактор офферов существующих кампаний.

Keitaro остаётся источником истины для кампаний, потоков и офферов. Локальная БД хранит
состояние редактора до публикации.

## Демо

Короткое видео (76 секунд) и скриншоты: [`docs/demo`](docs/demo). Архив для загрузки:
[`keitaro-demo.zip`](docs/demo/keitaro-demo.zip).

![Редактор кампании](docs/demo/03-editor.png)

## Что умеет

### 1. Создаватор кампаний

Принимает название, ISO-2 гео-код (можно несколько) и оффер. Создаёт в Keitaro кампанию из двух потоков:

| Поток | Тип | Схема | Логика |
| --- | --- | --- | --- |
| 1 | `regular` | `redirect` | Принимает только выбранные страны (`country` = accept) и редиректит на Google |
| 2 | `default` | `landings` | Добирает весь остальной трафик и отправляет на выбранный оффер |

У кампании настраиваются **домен, группа и источник трафика**. Берутся первые активные сущности
из Keitaro; при необходимости конкретные ID можно зафиксировать через `DEFAULT_*` переменные.

Создание кампании и двух потоков — сага: если любой шаг падает, обёртка удаляет уже созданные
потоки и кампанию.

### 2. Редактор кампании

- Постраничный список кампаний Keitaro и переход к кампании по ID.
  У `/campaigns` в Admin API нет поиска, поэтому список листается через `limit/offset`, а не
  выгружается целиком.
- **Загрузить потоки** — получить потоки и офферы кампании из Keitaro в локальное состояние редактора.
- Потоки без офферов показываются минимально: имя и пометка «Поток без офферов», без парсинга
  фильтров и редиректов.
- Добавление оффера в поток через поиск по офферам Keitaro. Веса пересчитываются автоматически:
  четыре оффера — по 25%, три — 34/33/33.
- Удаление оффера: он становится серым с весом 0%, поток — жёлтым (есть изменения). Изменения не уходят
  в Keitaro до нажатия **Опубликовать**.
- **Отмена** возвращает изменения к последней опубликованной версии: добавленные офферы удаляются,
  удалённые и веса восстанавливаются.
- После публикации удалённый оффер исчезает из Keitaro, но остаётся в локальном архиве с кнопкой
  **Вернуть**. Внешние удаления в Keitaro определяются при повторной загрузке: пропавшие потоки
  удаляются локально, а пропавшие офферы переводятся в архив.
- Вес оффера можно **закрепить**. При добавлении/удалении/возврате офферов закреплённый вес
  сохраняется, а свободные веса пересчитываются так, чтобы сумма была 100%.
- Состояние редактора хранится в БД, поэтому переживает перезагрузку страницы; в Keitaro изменения уходят
  только по кнопке **Опубликовать**.

## Стек

**Backend:** Python 3.12, FastAPI, SQLAlchemy 2 (async), asyncpg, Alembic, Pydantic v2,
httpx, uv, ruff.

**Frontend:** React 19, Vite, TypeScript (strictest), Mantine 9, TanStack Query, TanStack Form,
React Router, oxlint, oxfmt, knip, React Doctor.

**Инфраструктура:** PostgreSQL 17, Docker + Docker Compose, Playwright,
testcontainers, husky + lint-staged + commitlint.

## Архитектура

Слои на бэкенде: `controller (router) → service → repository / Keitaro client`.
Фича-слайсы вертикальные: внутри `features/<slice>` лежат роутер, сервис, репозиторий, схемы и модели.
Транспорт Keitaro изолирован в `integrations/keitaro`.

```text
backend/src/keitaro_wrapper/
├── core/                    # конфиг, БД, ошибки, DI, middleware
├── integrations/keitaro/    # типизированный async-клиент Admin API
├── features/
│   ├── campaigns/           # кампании, офферы, редактор
│   └── health/              # live/ready
└── main.py                  # сборка приложения

frontend/src/
├── app/                     # layout, router, тема
├── shared/                  # api client, типы, форматтеры, UI-примитивы
└── features/
    ├── campaigns/           # список кампаний
    ├── campaign-create/     # форма создания + асинхронный выбор оффера
    └── campaign-editor/     # офферы, веса, публикация
```

Почему локальная БД, если Keitaro — источник истины:

- `campaign_streams` / `campaign_offers` — локальное состояние потоков, офферов, архива и весов.
  В Keitaro изменения уходят только по кнопке «Опубликовать».

## Быстрый старт (демо без реального Keitaro)

Требуются Docker и Docker Compose.

```bash
cp .env.example .env
docker compose up -d --build --wait
```

Откройте <http://localhost:8080>. Порты опубликованы только на `127.0.0.1`: без авторизации
выставлять редактор в сеть с доступом к общему Keitaro опасно. При необходимости измените
маппинг портов в `docker-compose.yml`.

В комплекте идёт **mock Keitaro** (`backend/src/mock_keitaro`): детерминированная in-memory
реализация нужных методов Admin API с доменом, группой, источником, офферами и тестовыми
кампаниями. Он нужен только для демо и e2e — боевой код работает с настоящим API.

Проверка API и интерактивная документация:

- Swagger: <http://localhost:8000/docs>
- Health: <http://localhost:8000/api/v1/health/ready>

## Подключение реального Keitaro

1. Создайте API-ключ в админке Keitaro: **Профиль → API ключи** (нужна редакция PRO и выше).
2. В `.env` укажите:

   ```dotenv
   KEITARO_BASE_URL=https://your-keitaro.example/admin_api/v1
   KEITARO_API_KEY=your-real-api-key
   ```

3. Убедитесь, что в Keitaro есть хотя бы один активный домен, группа кампаний и источник трафика.
   При необходимости зафиксируйте нужные ID:

   ```dotenv
   DEFAULT_DOMAIN_ID=1
   DEFAULT_CAMPAIGN_GROUP_ID=1
   DEFAULT_TRAFFIC_SOURCE_ID=1
   ```

4. **E2E изолирован.** `scripts/e2e.sh` использует `docker-compose.e2e.yml`, где адрес Keitaro
   и ключ mock прописаны жёстко; значения из локального `.env` на тесты не влияют.

5. Перезапустите backend:

   ```bash
   docker compose up -d --build backend
   ```

Mock-контейнер можно не запускать (`docker compose up -d db backend frontend`) — backend обращается
только к `KEITARO_BASE_URL`. Если он остаётся запущенным, он просто не используется.

## Локальная разработка

### Backend

```bash
cp backend/.env.example backend/.env
docker compose up -d db keitaro-mock

cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn keitaro_wrapper.main:app --reload
```

Backend: <http://localhost:8000>, mock Keitaro: <http://localhost:8001/admin_api/v1>.

### Frontend

```bash
npm install
npm run dev
```

Vite: <http://localhost:5173>, запросы `/api` проксируются на `http://localhost:8000`.

### Миграции

```bash
cd backend
uv run alembic upgrade head
uv run alembic downgrade -1
uv run alembic revision --autogenerate -m "add something"
```

В Docker миграции применяются автоматически в `backend/docker-entrypoint.sh` перед стартом uvicorn.
Для отката схемы используйте `alembic downgrade`.

## API

Все эндпоинты — под `/api/v1`.

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/campaigns?limit=&offset=` | Страница кампаний Keitaro |
| `POST` | `/campaigns` | Создать кампанию с гео-потоком и потоком оффера |
| `GET` | `/campaigns/{id}` | Кампания |
| `GET` | `/campaigns/{id}/editor` | Локальное состояние потоков и офферов |
| `POST` | `/campaigns/{id}/editor/fetch` | Загрузить/обновить потоки из Keitaro |
| `POST` | `/campaigns/{id}/editor/streams/{streamId}/offers` | Добавить оффер `{offer_id}` |
| `DELETE` | `/campaigns/{id}/editor/streams/{streamId}/offers/{offerId}` | Удалить оффер из потока |
| `POST` | `/campaigns/{id}/editor/streams/{streamId}/offers/{offerId}/restore` | Вернуть оффер из архива |
| `POST` | `/campaigns/{id}/editor/streams/{streamId}/offers/{offerId}/pin` | Закрепить/открепить вес `{pinned}` |
| `POST` | `/campaigns/{id}/editor/publish` | Опубликовать изменения в Keitaro |
| `POST` | `/campaigns/{id}/editor/cancel` | Отменить неопубликованные изменения |
| `GET` | `/offers?search=&limit=&offset=` | Поиск офферов для автокомплита |
| `GET` | `/health/live`, `/health/ready` | Liveness / готовность (БД + Keitaro) |

Пример создания:

```bash
curl -X POST http://localhost:8000/api/v1/campaigns \
  -H 'Content-Type: application/json' \
  -d '{"name":"AU — Beauty RO","geo":["AU"],"offer_id":3749}'
```

Ошибки имеют единый формат:

```json
{ "code": "not_found", "message": "Оффер с ID 999 не найден в Keitaro", "request_id": "…" }
```

## Переменные окружения

| Переменная | По умолчанию | Описание |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+asyncpg://keitaro:keitaro@localhost:5433/keitaro` | Подключение к PostgreSQL |
| `KEITARO_BASE_URL` | `http://keitaro-mock:8000/admin_api/v1` | База Admin API |
| `KEITARO_API_KEY` | `dev-api-key` | API-ключ (заголовок `Api-Key`) |
| `KEITARO_TIMEOUT_SECONDS` | `15` | Таймаут запросов к Keitaro |
| `DEFAULT_DOMAIN_ID` | — | Домен для новых кампаний |
| `DEFAULT_CAMPAIGN_GROUP_ID` | — | Группа кампаний |
| `DEFAULT_TRAFFIC_SOURCE_ID` | — | Источник трафика |
| `GEO_REDIRECT_URL` | `https://google.com` | Куда ведёт гео-поток |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:8080,http://127.0.0.1:5173` | Разрешённые origins |
| `FRONTEND_PORT` | `8080` | Host-порт фронтенда |
| `BACKEND_PORT` | `8000` | Host-порт backend |
| `MOCK_KEITARO_PORT` | `8001` | Host-порт mock Keitaro |
| `POSTGRES_PORT` | `5433` | Host-порт PostgreSQL |

## Тесты

### Backend

```bash
cd backend
uv run pytest                       # unit + integration
uv run pytest -m "not integration"  # только unit, без Docker
```

Интеграционные тесты поднимают PostgreSQL через **testcontainers**, прогоняют Alembic и проверяют
создание кампании, потоки, фильтр страны, а также редактор офферов: fetch, локальные изменения,
publish, cancel, архив, восстановление и закреплённые веса на in-process mock Keitaro.

### E2E

```bash
npm --prefix e2e run install-browsers   # один раз
npm run test:e2e
```

`scripts/e2e.sh` собирает **реальные Docker-образы** backend и frontend, поднимает весь compose-стек,
ждёт healthcheck, запускает Playwright и удаляет контейнеры/volume. Мокается только Keitaro upstream —
фронтенд ходит в настоящий backend и настоящую БД.

E2E запускается в отдельном compose-проекте `keitaro-wrapper-e2e` на портах `18080/18000/18001/15433`,
поэтому не конфликтует с демо-стеком и не удаляет его volume. Порты можно переопределить через
`E2E_FRONTEND_PORT`, `E2E_BACKEND_PORT`, `E2E_MOCK_PORT`, `E2E_POSTGRES_PORT`.

Сценарии: создание кампании через UI, загрузка потоков, локальное добавление оффера с сохранением
после reload, cancel, publish, удаление в архив, «Вернуть» и закрепление веса.

## Качество кода и git hooks

```bash
# backend
cd backend && uv run ruff check . && uv run ruff format --check .

# frontend
npm --prefix frontend run format:check
npm --prefix frontend run lint        # oxlint --deny-warnings
npm --prefix frontend run typecheck   # tsc со strictest-настройками
npm --prefix frontend run knip
npm --prefix frontend run doctor      # react-doctor
```

На коммите:

- **pre-commit** — `lint-staged`: ruff для `*.py`, oxfmt + oxlint для фронтенда;
- **commit-msg** — commitlint, Conventional Commits.

```bash
git commit -m "feat(editor): add offer share control"
git commit -m "fix(api): map keitaro 404 to not_found"
```

## Структура проекта

```text
.
├── backend/                 # FastAPI + SQLAlchemy + Alembic
│   ├── src/keitaro_wrapper/
│   ├── src/mock_keitaro/    # демо/e2e upstream
│   ├── migrations/
│   └── tests/
├── frontend/                # React SPA + nginx
├── e2e/                     # Playwright
├── scripts/e2e.sh           # compose + Playwright + cleanup
├── docker-compose.yml
└── docker-compose.e2e.yml
```

## Решения и ограничения

- **Без авторизации.** Это внутренний инструмент под тестовое задание; multi-user/auth не добавлялись.
- **Веса офферов.** Активные и добавленные офферы делят 100% поровну; закреплённые веса не
  меняются, а остаток распределяется между свободными. Удалённые офферы получают 0%. После
  публикации локальные веса синхронизируются с ответом Keitaro.
- **Архив офферов.** Удалённый из потока оффер не удаляется из локальной БД: он хранится со
  статусом `archived` и может быть возвращён кнопкой «Вернуть». В поиске офферов архивные позиции
  не участвуют.
- **Загрузка потоков** блокируется, пока есть неопубликованные изменения: сначала нужно
  опубликовать или отменить изменения.
- **Mock Keitaro** реализует только используемые методы Admin API и не претендует на полную
  совместимость; для реального трекера используется настоящий API.
- **Архив и удаление.** `GET /campaigns` не возвращает архивные кампании; они в
  интерфейс обёртки не попадают. Обёртка архивирует только ту
  кампанию, которую сама создала, и только если создание упало на следующем шаге. Массового
  удаления/архивации в ней нет.
- **E2E и реальный API.** E2E поднимает отдельный compose-проект с `docker-compose.e2e.yml`:
  адрес Keitaro и ключ mock прописаны в нём жёстко, поэтому локальный `.env` не может направить
  тесты в общий трекер. Ручные проверки на реальном API выполняются отдельно и осознанно.
