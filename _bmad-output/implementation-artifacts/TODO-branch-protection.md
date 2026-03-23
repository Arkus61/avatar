# TODO - Branch Protection Enforcement

## Если в PowerShell: «gh не распознано»

После `winget install` путь часто **ещё не в PATH** в текущем окне. Сделай так:

**Вариант A — полный путь (сразу работает):**

```powershell
& "C:\Program Files\GitHub CLI\gh.exe" auth login
```

**Вариант B — добавить в PATH только в этой сессии:**

```powershell
$env:Path += ";C:\Program Files\GitHub CLI"
gh auth login
```

Потом можно закрыть терминал и открыть новый — тогда `gh` обычно уже находится.

## Автоматизация в репозитории

1. Установи **GitHub CLI** (если ещё нет): `winget install GitHub.cli`
2. Авторизация — **один** из вариантов:
   - Интерактивно: `gh auth login` (если `gh` в PATH) **или** `& "C:\Program Files\GitHub CLI\gh.exe" auth login`.
   - Без браузера (PAT): классический token с правом **`repo`** (или fine-grained: **Administration** на репозиторий), затем в той же сессии PowerShell:
     ```powershell
     $env:GH_TOKEN = "ghp_xxxxxxxx"   # или github_pat_...
     powershell -ExecutionPolicy Bypass -File scripts/apply-branch-protection.ps1
     ```
     Токен в чат/репозиторий не коммить.
3. Убедись, что есть **`git remote origin`** на GitHub, ветка по умолчанию (часто `main`) запушена и **хотя бы раз** отработали workflows (иначе checks не появятся в списке).
4. Из корня репо:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/apply-branch-protection.ps1
```

При ошибке `422` (unknown context) — сначала дождись зелёного прогона CI на `main`, проверь точные имена checks во вкладке PR → **Checks**, при необходимости поправь строки `context` в `scripts/apply-branch-protection.ps1` или настрой **Rulesets** вручную: `docs/branch-protection.md`.

## Чеклист (отметь после выполнения)

- [ ] Enable repository branch protection (or rulesets) for default branch.
- [ ] Require passing checks before merge:
  - `ci-web / web`
  - `ci-api / api`
  - `ci-contracts / contracts`
- [ ] Disable direct pushes to protected branch (except approved maintainers if required).
- [ ] Verify merge is blocked when any required check fails.

## Ручной fallback: GitHub CLI (classic API)

Замените `OWNER`, `REPO`, `BRANCH`. Имена checks — как в UI PR после прогона Actions.

```bash
gh api -X PUT "repos/OWNER/REPO/branches/BRANCH/protection" --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "checks": [
      { "context": "ci-web / web" },
      { "context": "ci-api / api" },
      { "context": "ci-contracts / contracts" }
    ]
  },
  "enforce_admins": false,
  "restrictions": null
}
EOF
```

Если API отклонит тело запроса — **Rulesets** в UI: `docs/branch-protection.md`.
