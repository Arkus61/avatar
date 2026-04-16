"""Проверяем загрузку/валидацию скиллов и резолвинг по alias."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

TEMPLATE_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TEMPLATE_ROOT.parent.parent))

from templates.agent.runtime.skill_registry import SkillRegistry, SkillValidationError  # noqa: E402


class SkillRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.registry = SkillRegistry(TEMPLATE_ROOT / "skills")
        self.registry.load()

    def test_loads_all_skills(self) -> None:
        ids = {s.id for s in self.registry.all()}
        self.assertIn("research.web", ids)
        self.assertIn("code.review", ids)
        self.assertIn("a2a.delegate", ids)

    def test_resolve_by_alias(self) -> None:
        skill = self.registry.resolve("delegate")
        self.assertIsNotNone(skill)
        assert skill is not None
        self.assertEqual(skill.id, "a2a.delegate")

    def test_limits_defaults(self) -> None:
        skill = self.registry.resolve("code.review")
        assert skill is not None
        self.assertGreaterEqual(skill.limits.tool_call_budget, 1)
        self.assertGreaterEqual(skill.limits.max_duration_sec, 1)

    def test_rejects_invalid_id(self) -> None:
        bad = TEMPLATE_ROOT / "skills" / "bad.skill.yaml"
        bad.write_text(
            "id: BAD_ID\nname: x\nversion: 0.1.0\nhandler: llm\n"
            "inputs:\n  x: { type: string }\n"
            "outputs:\n  y: { type: string }\n",
            encoding="utf-8",
        )
        try:
            fresh = SkillRegistry(TEMPLATE_ROOT / "skills")
            with self.assertRaises(SkillValidationError):
                fresh.load()
        finally:
            bad.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
