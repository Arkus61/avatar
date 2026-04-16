"""Tests for BMAD markdown agent definitions and validation helpers."""

from __future__ import annotations

import csv
import sys
import textwrap
import unittest
from pathlib import Path

API_APP_DIR = Path(__file__).resolve().parents[1]
if str(API_APP_DIR) not in sys.path:
    sys.path.insert(0, str(API_APP_DIR))

from app import bmad_agent_validate as v  # noqa: E402


WORKSPACE = v.workspace_root_from_api_app(Path(__file__).resolve().parents[1] / "app")
MANIFEST = WORKSPACE / "_bmad" / "_config" / "agent-manifest.csv"


MINIMAL_AGENT = textwrap.dedent(
    r'''
    ```xml
    <agent id="test.agent.yaml" name="T" title="Test Agent" icon="🧪">
    <activation critical="MANDATORY">
      <step n="2">Load and read {project-root}/_bmad/core/config.yaml NOW</step>
    </activation>
    <menu>
      <item cmd="MH or fuzzy match on menu or help">[MH] Redisplay Menu Help</item>
      <item cmd="CH or fuzzy match on chat">[CH] Chat</item>
      <item cmd="PM or fuzzy match on party-mode" exec="{project-root}/_bmad/core/workflows/party-mode/workflow.md">[PM] Start Party Mode</item>
      <item cmd="DA or fuzzy match on exit" workflow="todo">[DA] Dismiss Agent</item>
    </menu>
    </agent>
    ```
    '''
).strip()


class WorkspaceRootTests(unittest.TestCase):
    def test_workspace_root_points_at_repo(self) -> None:
        self.assertTrue((WORKSPACE / "_bmad").is_dir())
        self.assertTrue((WORKSPACE / "package.json").is_file())


class ParseAgentMarkdownTests(unittest.TestCase):
    def test_parses_minimal_agent(self) -> None:
        d = v.parse_agent_markdown(MINIMAL_AGENT)
        self.assertEqual(d.agent_id, "test.agent.yaml")
        self.assertEqual(d.config_relative_path, "_bmad/core/config.yaml")
        self.assertEqual(len(d.menu), 4)
        self.assertEqual(d.menu[0].cmd_attr, "MH or fuzzy match on menu or help")

    def test_raises_without_agent_block(self) -> None:
        with self.assertRaises(ValueError):
            v.parse_agent_markdown("# hello")

    def test_raises_without_menu_items(self) -> None:
        bad = textwrap.dedent(
            r'''
            ```xml
            <agent id="x.agent.yaml" name="X" title="Y" icon="🧪">
            <activation critical="MANDATORY">
              <step n="2">{project-root}/_bmad/tea/config.yaml</step>
            </activation>
            <menu></menu>
            </agent>
            ```
            '''
        ).strip()
        with self.assertRaises(ValueError) as ctx:
            v.parse_agent_markdown(bad)
        self.assertIn("no <item>", str(ctx.exception).lower())


class ConfigValidationTests(unittest.TestCase):
    def test_valid_core_config(self) -> None:
        errs = v.validate_config_file(WORKSPACE, "_bmad/core/config.yaml")
        self.assertEqual(errs, [])

    def test_reports_missing_keys(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as d:
            cfg = Path(d) / "cfg.yaml"
            cfg.write_text("user_name: A\n", encoding="utf-8")
            errs = v.validate_config_file(Path(d), "cfg.yaml")
        self.assertTrue(any("missing required key" in e for e in errs))


class ResolvePathTests(unittest.TestCase):
    def test_resolve_strips_project_root_prefix(self) -> None:
        p = v.resolve_project_path(
            WORKSPACE, "{project-root}/_bmad/core/config.yaml"
        )
        self.assertTrue(p.is_file())


class FuzzyMatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.menu = v.parse_agent_markdown(MINIMAL_AGENT).menu

    def test_numeric_selection(self) -> None:
        self.assertEqual(v.fuzzy_match_menu_items("1", self.menu), [0])
        self.assertEqual(v.fuzzy_match_menu_items("4", self.menu), [3])

    def test_numeric_out_of_range(self) -> None:
        self.assertEqual(v.fuzzy_match_menu_items("0", self.menu), [])
        self.assertEqual(v.fuzzy_match_menu_items("99", self.menu), [])

    def test_primary_token(self) -> None:
        self.assertEqual(v.fuzzy_match_menu_items("pm", self.menu), [2])

    def test_substring_on_label(self) -> None:
        self.assertEqual(v.fuzzy_match_menu_items("party", self.menu), [2])

    def test_empty_input(self) -> None:
        self.assertEqual(v.fuzzy_match_menu_items("", self.menu), [])
        self.assertEqual(v.fuzzy_match_menu_items("   ", self.menu), [])

    def test_multiple_matches_returns_all(self) -> None:
        # "agent" appears in CH label and possibly elsewhere — use a phrase matching two
        menu = (
            v.MenuItem(
                1,
                "A or fuzzy match on foo",
                "[A] first",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
            v.MenuItem(
                2,
                "B or fuzzy match on foo",
                "[B] second",
                None,
                None,
                None,
                None,
                None,
                None,
            ),
        )
        idxs = v.fuzzy_match_menu_items("foo", menu)
        self.assertEqual(sorted(idxs), [0, 1])


class ValidateReferencedPathsTests(unittest.TestCase):
    def test_todo_workflow_skipped(self) -> None:
        d = v.parse_agent_markdown(MINIMAL_AGENT)
        errs = v.validate_referenced_paths(WORKSPACE, d)
        # party-mode workflow exists; todo skipped
        self.assertEqual(errs, [])


class AgentValidationErrorTests(unittest.TestCase):
    def test_str_contains_path(self) -> None:
        p = Path("/tmp/x.md")
        err = v.AgentValidationError(p, ["a", "b"])
        self.assertIn("x.md", str(err))


class ValidateAgentFileIntegrationTests(unittest.TestCase):
    def test_each_manifest_agent_passes(self) -> None:
        with MANIFEST.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        self.assertGreaterEqual(len(rows), 10)
        for row in rows:
            rel = row["path"].strip().strip('"')
            md = WORKSPACE / rel
            with self.subTest(name=row["name"], path=rel):
                v.validate_agent_file(WORKSPACE, md)

    def test_validate_manifest_bulk(self) -> None:
        v.validate_agent_manifest(WORKSPACE, MANIFEST)

    def test_broken_agent_raises(self) -> None:
        import tempfile

        bad = textwrap.dedent(
            r'''
            ```xml
            <agent id="bad.agent.yaml" name="B" title="Bad" icon="🧪">
            <activation critical="MANDATORY">
              <step n="2">Load {project-root}/_bmad/core/config.yaml</step>
            </activation>
            <menu>
              <item cmd="X">[X] only one item</item>
            </menu>
            </agent>
            ```
            '''
        ).strip()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "bad.md"
            p.write_text(bad, encoding="utf-8")
            with self.assertRaises(v.AgentValidationError) as ctx:
                v.validate_agent_file(WORKSPACE, p)
            self.assertTrue(len(ctx.exception.messages) >= 1)


if __name__ == "__main__":
    unittest.main()
