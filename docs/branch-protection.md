# Branch protection (required CI checks)

CI workflows report these **check names** (workflow / job). Use them when configuring GitHub **Rulesets** or classic branch protection so merges are blocked until all pass.

| Check name (as shown on PR) | Workflow file        |
|----------------------------|----------------------|
| `ci-web / web`             | `.github/workflows/ci-web.yml` |
| `ci-api / api`             | `.github/workflows/ci-api.yml` |
| `ci-contracts / contracts` | `.github/workflows/ci-contracts.yml` |

## GitHub Rulesets (recommended)

1. Repo **Settings** → **Rules** → **Rulesets** → **New ruleset** → **New branch ruleset**.
2. Target: default branch (`main` or `master`).
3. Enable **Require status checks to pass**.
4. Add the three checks above (search by name after at least one workflow run on the default branch).
5. Optional: **Block force pushes**, restrict who can push.

## Verify

Open a PR that intentionally breaks lint; confirm merge stays blocked until fixed.

## Script (Windows)

From repo root after `gh auth login` and `origin` on GitHub:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/apply-branch-protection.ps1
```

REST `PUT .../protection` требует блок **`required_pull_request_reviews`** (можно `required_approving_review_count: 0`, если ревью не нужны) — см. `scripts/apply-branch-protection.ps1`.

See also `_bmad-output/implementation-artifacts/TODO-branch-protection.md` for the full checklist and **GitHub CLI** JSON example.
