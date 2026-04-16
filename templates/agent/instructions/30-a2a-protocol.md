# A2A (Agent-to-Agent) Protocol

Ты участвуешь в федерации агентов по протоколу A2A. Агенты находят друг друга через
**Agent Card** (`/.well-known/agent-card.json`) и обмениваются задачами (`tasks`) и
сообщениями (`messages`).

## Роли

- **Provider.** Ты принимаешь входящие задачи: `POST /a2a/v1/tasks`. Запускаешь нужный
  скилл, стримишь события через SSE `/a2a/v1/tasks/{id}/events`, возвращаешь результат.
- **Consumer.** Ты делегируешь задачи другим агентам через `a2a/client.py` или скилл
  `a2a.delegate`. В запросе обязателен `trace_id`.

## Контракт сообщения

```json
{
  "id": "uuid",
  "role": "user | agent | tool | system",
  "parts": [
    { "kind": "text",  "text": "..."              },
    { "kind": "data",  "data": { "...": "..." }  },
    { "kind": "file",  "name": "report.pdf", "uri": "..." }
  ],
  "created_at": "2026-04-16T12:34:56Z"
}
```

## Контракт задачи

```json
{
  "id": "uuid",
  "skill_id": "research.web",
  "input": { "...": "..." },
  "stream": true,
  "context": { "trace_id": "uuid", "parent_task": "uuid|null" },
  "deadline_sec": 120,
  "reply_to": "https://caller/a2a/v1/tasks/<id>/messages"
}
```

Статусы: `queued`, `running`, `needs_input`, `completed`, `failed`, `cancelled`.

## Правила

1. **Идентификация.** Перед делегированием тяни Agent Card партнёра и убедись, что
   требуемый `skill_id` есть в `card.skills`.
2. **Аутентификация.** Если Agent Card указывает `auth.schemes`, добавь соответствующий
   заголовок (bearer/mTLS/OIDC). Неаутентифицированные вызовы не допускаются в продакшене.
3. **Таймауты.** Уважай `deadline_sec`. По истечении — отменяй подзадачи (`DELETE /a2a/v1/tasks/{id}`).
4. **Стриминг.** Если `stream=true` — отправляй инкрементальные события:
   `progress`, `partial_output`, `requires_input`, `final`, `error`.
5. **Согласование контекста.** Если партнёрский агент просит уточнение (`needs_input`),
   не додумывай за пользователя — проксируй запрос выше по цепочке (до исходного клиента).
6. **Никакой рекурсии без лимита.** Глубина делегирования ограничена полем
   `a2a.max_delegation_depth` в `agent.yaml` (по умолчанию 3).
7. **Трассировка.** `trace_id` из входящего запроса должен пробрасываться во все
   исходящие вызовы и логи.

## Как выбирать партнёра

Предпочтение — в порядке:

1. Явно указанный пользователем/родительской задачей `peer`.
2. Статический список `agent.yaml.a2a.peers`.
3. Discovery-реестр (если задан `a2a.discovery_url`) — поиск по capability/tag.
