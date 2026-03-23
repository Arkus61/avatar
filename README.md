# avatar

Monorepo baseline for the avatar platform.

## Apps

- `apps/web` - Next.js App Router frontend
- `apps/api` - FastAPI backend
- `packages/contracts` - OpenAPI and generated client artifacts

## Quick Start

### Web

```bash
npm --prefix apps/web install
npm run dev:web -- --port 3010
```

### API

```bash
python -m pip install -r apps/api/requirements.txt
npm run dev:api
```

### Database (PostgreSQL)

```bash
npm run db:up
```

### Unified Local Validation Workflow

Run services in separate terminals:

```bash
npm run db:up
npm run dev:api
npm run dev:web -- --port 3010
```

Then validate local environment:

```bash
npm run check:local-env
```

Expected checks:
- `web_health` -> `200`
- `api_health` -> `200`
- `db_tcp` -> open port on `5432`
- `db_pg_isready` -> Postgres readiness via container `avatar-postgres`

### Temporary Local Postgres Mode (without Docker)

If Docker pull is unstable, you can use an already running local Postgres:

**PowerShell**

```powershell
$env:DB_MODE="local"
npm run check:local-env
```

**Bash**

```bash
export DB_MODE=local
npm run check:local-env
```

Optional strict local DB command check:

```powershell
$env:LOCAL_PG_CHECK_CMD='psql -h 127.0.0.1 -p 5432 -U avatar -d avatar -c "select 1"'
npm run check:local-env
```

```bash
export LOCAL_PG_CHECK_CMD='psql -h 127.0.0.1 -p 5432 -U avatar -d avatar -c "select 1"'
npm run check:local-env
```

## CI Quality Gates

The repository includes baseline CI workflows:

- `ci-web` - lint/typecheck/test/build for `apps/web`
- `ci-api` - lint/typecheck/test/build for `apps/api`
- `ci-contracts` - static + runtime OpenAPI/client contract sync validation

Required merge-blocking status checks must be configured in repository branch protection (see `docs/branch-protection.md`):
- `ci-web / web`
- `ci-api / api`
- `ci-contracts / contracts`

## Quality Commands

```bash
npm run lint
npm run typecheck
npm run test
npm run build
```
