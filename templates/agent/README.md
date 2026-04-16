# Agent Template · MCP + Skills + Instructions + A2A

Шаблон для быстрой сборки автономного агента, который:

- **подключает MCP-инструменты** (stdio/HTTP) и использует их из цикла рассуждения;
- **имеет каталог скиллов** — переиспользуемых процедур, собираемых из MCP-инструментов и локального кода;
- **управляется инструкциями** — system prompt, политики, BMAD-совместимое активационное описание;
- **умеет общаться с другими агентами по A2A** (Agent-to-Agent) — публикует Agent Card, принимает/отправляет задачи, стримит результат.

Шаблон не привязан к конкретной LLM: провайдер передаётся через `LLMProvider`-интерфейс (см. `runtime/llm.py`). По умолчанию используется OpenAI-совместимый клиент.

## Структура

```text
templates/agent/
├── agent.yaml                      # Декларативный манифест агента
├── persona/
│   ├── agent.md                    # BMAD-совместимый файл агента (XML persona)
│   └── customize.yaml              # Пользовательская кастомизация персоны
├── instructions/
│   ├── 00-system.md                # Базовый system prompt
│   ├── 10-tool-use.md              # Правила работы с MCP-инструментами
│   ├── 20-skills.md                # Правила использования скиллов
│   ├── 30-a2a-protocol.md          # Протокол общения с другими агентами
│   └── 40-safety.md                # Safety / guardrails
├── mcp/
│   ├── mcp.config.json             # Список MCP-серверов и их запуск
│   └── tools.manifest.yaml         # Разрешённые инструменты + политики
├── skills/
│   ├── _schema.yaml                # Схема описания скилла
│   ├── research.web.yaml           # Пример: веб-исследование
│   ├── code.review.yaml            # Пример: код-ревью
│   └── a2a.delegate.yaml           # Пример: делегирование задачи другому агенту
├── a2a/
│   ├── agent-card.json             # Agent Card (публичный дескриптор A2A)
│   ├── schemas.py                  # Pydantic-модели сообщений/тасков
│   ├── server.py                   # FastAPI A2A-эндпоинты
│   └── client.py                   # A2A-клиент для вызова других агентов
├── runtime/
│   ├── __init__.py
│   ├── agent.py                    # Главный цикл агента (think → act → observe)
│   ├── llm.py                      # Абстракция LLM-провайдера
│   ├── mcp_client.py               # Тонкий MCP-клиент (stdio + http)
│   ├── skill_registry.py           # Загрузка и диспетчеризация скиллов
│   ├── memory.py                   # Короткая + эпизодическая память
│   └── handlers/
│       ├── __init__.py
│       └── a2a.py                  # Хендлеры входящих A2A-тасков
├── tests/
│   ├── test_skill_registry.py
│   └── test_a2a_roundtrip.py
├── examples/
│   └── run_local.py                # Локальный запуск агента + A2A-сервера
├── requirements.txt
└── .env.example
```

## Быстрый старт

```bash
cp -r templates/agent apps/my-agent
cd apps/my-agent
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# запускаем A2A-сервер агента (порт 7701 по умолчанию)
python -m a2a.server

# вызываем агента из другого процесса через A2A
python examples/run_local.py
```

## Как устроен агент

1. **Манифест `agent.yaml`** — единый источник правды: имя, версия, модели, MCP-серверы,
   каталог скиллов, A2A-эндпоинты, файлы инструкций.
2. **Инструкции** — собираются в system prompt в порядке имени файла (`00-…`, `10-…`, …).
   Разделение по темам нужно, чтобы менять политики без переписывания всего промпта.
3. **MCP-инструменты** — подключаются через `runtime/mcp_client.py`. Их схемы кэшируются и
   подаются в LLM как function-calling tools. `mcp/tools.manifest.yaml` фильтрует, какие из
   обнаруженных инструментов вообще разрешены.
4. **Скиллы** — высокоуровневые процедуры (`research.web`, `code.review`,
   `a2a.delegate` и т.д.). Каждый скилл описан YAML-ом и может содержать пред- и
   постобработку; исполнение по умолчанию идёт через LLM-план, но может быть переопределено
   Python-хендлером из `runtime/handlers/`.
5. **A2A** — шаблон реализует подмножество [A2A-протокола](https://a2aproject.org):
   - `GET /.well-known/agent-card.json` — публикация возможностей,
   - `POST /a2a/v1/tasks` — приём задачи,
   - `GET /a2a/v1/tasks/{id}` — опрос статуса,
   - `GET /a2a/v1/tasks/{id}/events` (SSE) — стрим событий,
   - `POST /a2a/v1/tasks/{id}/messages` — дообмен сообщениями.
   Исходящие вызовы к другим агентам идут через `a2a/client.py` и скилл `a2a.delegate`.

## Как расширять

- **Добавить MCP-сервер** → описать в `mcp/mcp.config.json`, разрешить инструменты в
  `mcp/tools.manifest.yaml`.
- **Добавить скилл** → скопировать `skills/_schema.yaml`, заполнить поля; при
  необходимости — добавить Python-хендлер в `runtime/handlers/`.
- **Поменять поведение** → править файлы `instructions/*.md`; ничего не трогая в коде.
- **Выставить новые возможности для A2A** → обновить `a2a/agent-card.json` (поле `skills`
  автоматически подтягивается из `skills/`, см. `examples/run_local.py`).

## Примечания по безопасности

- MCP-инструменты вызываются только если они перечислены в `tools.manifest.yaml`.
- Входящие A2A-задачи исполняются по allow-list скиллов из Agent Card.
- Все исходящие A2A-вызовы логируются с trace_id, таймаутами и лимитом попыток.
- См. `instructions/40-safety.md`.
