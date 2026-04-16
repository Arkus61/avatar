# Agent Template — MCP + Skills + A2A

Шаблон разработки автономного агента с:

- **MCP инструментами** — подключение к любым MCP-серверам (filesystem, поиск, БД, и т.д.)
- **Skills** — переиспользуемые высокоуровневые навыки поверх MCP
- **Instructions** — системные инструкции, собираемые из шаблонов с рантайм-контекстом
- **A2A протокол** — общение с другими агентами (Google A2A spec)

---

## Структура

```
agent-template/
├── config/
│   └── agent_config.yaml       # Вся конфигурация (MCP серверы, LLM, A2A, скиллы)
├── instructions/
│   ├── system_prompt.md        # Шаблон системного промпта
│   ├── persona.md              # Персона агента
│   ├── rules.md                # Правила поведения
│   └── builder.py              # Сборщик итогового system prompt
├── mcp/
│   ├── tool.py                 # MCPTool — обёртка над одним инструментом
│   └── registry.py             # MCPRegistry — управляет N MCP-серверами (stdio)
├── skills/
│   ├── base.py                 # BaseSkill + SkillResult
│   ├── registry.py             # SkillRegistry
│   └── builtin/
│       ├── text_analysis.py    # Анализ текста
│       ├── summarization.py    # Суммаризация
│       ├── data_retrieval.py   # Получение данных через MCP
│       └── agent_delegation.py # Делегирование задач другим агентам (A2A)
├── a2a/
│   ├── models.py               # Pydantic-модели по Google A2A спецификации
│   ├── server.py               # A2AServer — FastAPI + JSON-RPC роутер
│   └── client.py               # A2AClient — HTTP клиент к другим агентам
├── core/
│   ├── agent.py                # Agent — главная логика (agentic loop)
│   └── factory.py              # build_agent_from_config() — сборка из YAML
├── tests/
│   ├── test_a2a_models.py
│   ├── test_skills.py
│   └── test_mcp_registry.py
├── main.py                     # Точка входа
├── requirements.txt
└── pyproject.toml
```

---

## Быстрый старт

```bash
cd agent-template
pip install -r requirements.txt
```

Задайте переменные окружения:

```bash
export OPENAI_API_KEY="sk-..."
export MONGODB_URI="mongodb://localhost:27017"
export BRAVE_API_KEY="..."
```

Запустите агента:

```bash
python main.py
```

Агент запустится на `http://localhost:8100`.

---

## A2A протокол

### Agent Card (discovery)

```
GET http://localhost:8100/.well-known/agent.json
```

Возвращает `AgentCard` — имя, описание, список скиллов, capabilities.

### Отправить задачу агенту

```
POST http://localhost:8100/a2a
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tasks/send",
  "params": {
    "message": {
      "role": "user",
      "parts": [{ "type": "text", "text": "Summarize this document: ..." }]
    }
  }
}
```

### Программное обращение агента к агенту

```python
from a2a.client import A2AClient

async with A2AClient("http://agent-002:8101") as client:
    reply = await client.ask("Translate this text to French: Hello world")
    print(reply)
```

---

## Добавление собственного скилла

```python
# skills/builtin/my_skill.py
from skills.base import BaseSkill, SkillResult

class MySkill(BaseSkill):
    id = "my_skill"
    name = "My Skill"
    description = "Does something useful."

    async def execute(self, input: str = "", **kwargs) -> SkillResult:
        result = f"Processed: {input}"
        return SkillResult(success=True, output=result)
```

Зарегистрируйте в `config/agent_config.yaml`:

```yaml
skills:
  enabled:
    - my_skill
```

И добавьте в `core/factory.py` в словарь `_BUILTIN_SKILLS`.

---

## Добавление MCP сервера

В `config/agent_config.yaml`:

```yaml
mcp:
  servers:
    - name: "my-server"
      transport: "stdio"
      command: ["python", "-m", "my_mcp_server"]
      env:
        MY_API_KEY: "${MY_API_KEY}"
```

Все инструменты сервера автоматически загружаются и передаются в LLM.

---

## Тесты

```bash
pytest agent-template/tests/ -v
```

---

## Архитектура

```
                    ┌─────────────────────────────────────┐
                    │              Agent                   │
                    │                                      │
  A2A Request  ───► │  handle_a2a_task()                   │
                    │       │                              │
                    │       ▼                              │
                    │   _run(user_message)                 │
                    │       │                              │
                    │  ┌────┴──────────┐                   │
                    │  │  LLM Backend  │ ◄─── system_prompt│
                    │  └────┬──────────┘     (Instructions)│
                    │       │ tool_call                    │
                    │  ┌────▼──────────┐                   │
                    │  │  MCPRegistry  │ ─── MCP servers   │
                    │  └───────────────┘                   │
                    │                                      │
                    │  SkillRegistry ── AgentDelegation    │
                    │                       │              │
                    └───────────────────────┼──────────────┘
                                            │ A2A
                                     ┌──────▼──────┐
                                     │ Peer Agent  │
                                     └─────────────┘
```
