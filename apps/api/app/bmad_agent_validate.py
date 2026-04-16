"""Validation helpers for BMAD markdown agent definitions."""

from __future__ import annotations

import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

@dataclass(frozen=True)
class MenuItem:
    index: int
    cmd_attr: str
    label: str
    workflow: str | None
    exec_path: str | None
    tmpl: str | None
    data: str | None
    action: str | None
    validate_workflow: str | None


@dataclass(frozen=True)
class AgentDefinition:
    agent_id: str
    name: str
    title: str
    icon: str
    capabilities: str | None
    config_relative_path: str
    menu: tuple[MenuItem, ...]


class AgentValidationError(Exception):
    """Structured validation failure for a single agent file."""

    def __init__(self, path: Path, messages: list[str]) -> None:
        self.path = path
        self.messages = messages
        super().__init__(f"{path}: " + "; ".join(messages))


def workspace_root_from_api_app(app_dir: Path | None = None) -> Path:
    """apps/api/app -> repo root (contains _bmad/)."""
    if app_dir is None:
        app_dir = Path(__file__).resolve().parent
    # app_dir is .../apps/api/app
    return app_dir.parents[2]


def load_manifest_rows(manifest_path: Path) -> list[dict[str, str]]:
    with manifest_path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _extract_agent_xml_block(markdown: str) -> str:
    start = markdown.find("<agent")
    if start == -1:
        raise ValueError("missing <agent> block")
    end = markdown.rfind("</agent>")
    if end == -1:
        raise ValueError("missing </agent> closing tag")
    return markdown[start : end + len("</agent>")]


_CONFIG_PATH_IN_ACTIVATION = re.compile(
    r"\{project-root\}/(_bmad/(?:core|bmm|cis|tea)/config\.yaml)",
    re.IGNORECASE,
)


def _activation_step2_text(activation_el: ET.Element) -> str:
    parts: list[str] = []
    for step in activation_el.findall("step"):
        n = step.attrib.get("n")
        if n == "2":
            parts.append("".join(step.itertext()))
    return "\n".join(parts)


def _parse_menu_items(root: ET.Element) -> tuple[MenuItem, ...]:
    menu_el = root.find("menu")
    if menu_el is None:
        raise ValueError("missing <menu>")
    items: list[MenuItem] = []
    for idx, item in enumerate(menu_el.findall("item"), start=1):
        label = "".join(item.itertext()).strip()
        items.append(
            MenuItem(
                index=idx,
                cmd_attr=item.attrib.get("cmd", ""),
                label=label,
                workflow=item.attrib.get("workflow"),
                exec_path=item.attrib.get("exec"),
                tmpl=item.attrib.get("tmpl"),
                data=item.attrib.get("data"),
                action=item.attrib.get("action"),
                validate_workflow=item.attrib.get("validate-workflow"),
            )
        )
    if not items:
        raise ValueError("menu has no <item> elements")
    return tuple(items)


def parse_agent_markdown(text: str) -> AgentDefinition:
    xml_block = _extract_agent_xml_block(text)
    try:
        root = ET.fromstring(xml_block)
    except ET.ParseError as exc:  # pragma: no cover - defensive
        raise ValueError(f"invalid agent XML: {exc}") from exc

    agent_id = root.attrib.get("id", "").strip()
    name = root.attrib.get("name", "").strip()
    title = root.attrib.get("title", "").strip()
    icon = root.attrib.get("icon", "").strip()
    capabilities = root.attrib.get("capabilities")

    if not agent_id or not name or not title or not icon:
        raise ValueError("agent id, name, title, and icon are required")

    activation = root.find("activation")
    if activation is None:
        raise ValueError("missing <activation>")
    step2 = _activation_step2_text(activation)
    if "config.yaml" not in step2.lower():
        raise ValueError("activation step 2 must reference config.yaml")
    if "{project-root}/" not in step2:
        raise ValueError("activation step 2 must use {project-root}/ paths")

    cfg_m = _CONFIG_PATH_IN_ACTIVATION.search(step2.replace("\\", "/"))
    if not cfg_m:
        raise ValueError(
            "activation step 2 must load {project-root}/_bmad/<module>/config.yaml "
            "for module core, bmm, cis, or tea"
        )
    config_relative_path = cfg_m.group(1)

    menu = _parse_menu_items(root)
    return AgentDefinition(
        agent_id=agent_id,
        name=name,
        title=title,
        icon=icon,
        capabilities=capabilities,
        config_relative_path=config_relative_path,
        menu=menu,
    )


def resolve_project_path(workspace: Path, project_relative: str) -> Path:
    rel = project_relative.replace("{project-root}/", "").lstrip("/")
    return (workspace / rel).resolve()


def validate_config_file(workspace: Path, config_relative: str) -> list[str]:
    errors: list[str] = []
    path = workspace / config_relative
    if not path.is_file():
        errors.append(f"missing config file: {config_relative}")
        return errors
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        errors.append(f"invalid YAML in {config_relative}: {exc}")
        return errors
    if not isinstance(data, dict):
        errors.append(f"{config_relative} must parse to a mapping")
        return errors
    for key in ("user_name", "communication_language", "output_folder"):
        if key not in data:
            errors.append(f"{config_relative} missing required key {key!r}")
    return errors


def _split_cmd_fuzzy_phrases(cmd_attr: str) -> tuple[str | None, list[str]]:
    """Return primary token (e.g. MH) and fuzzy phrases from a cmd attribute."""
    raw = (cmd_attr or "").strip()
    if not raw:
        return None, []
    parts = re.split(r"\s+or\s+fuzzy\s+match\s+on\s+", raw, flags=re.IGNORECASE)
    primary = parts[0].strip()
    token_m = re.match(r"^([A-Za-z0-9-]+)", primary)
    token = token_m.group(1).lower() if token_m else None
    phrases: list[str] = []
    for p in parts[1:]:
        p = p.strip()
        if p:
            phrases.append(p.lower())
    return token, phrases


def fuzzy_match_menu_items(user_input: str, menu: Iterable[MenuItem]) -> list[int]:
    """
    Approximate BMAD menu selection: 1-based index, exact token, or substring
    match on menu text / fuzzy phrases (case-insensitive).
    """
    text = user_input.strip()
    if not text:
        return []
    menu_list = list(menu)
    if text.isdigit():
        n = int(text, 10)
        if 1 <= n <= len(menu_list):
            return [n - 1]
        return []

    tl = text.lower()
    matches: list[int] = []
    for i, item in enumerate(menu_list):
        token, phrases = _split_cmd_fuzzy_phrases(item.cmd_attr)
        if token and tl == token:
            matches.append(i)
            continue
        label_l = item.label.lower()
        if tl in label_l:
            matches.append(i)
            continue
        for ph in phrases:
            if tl in ph or ph in tl:
                matches.append(i)
                break
    return matches


def validate_referenced_paths(
    workspace: Path, definition: AgentDefinition
) -> list[str]:
    errors: list[str] = []
    for item in definition.menu:
        for attr_name, value in (
            ("workflow", item.workflow),
            ("exec", item.exec_path),
            ("tmpl", item.tmpl),
            ("data", item.data),
            ("validate-workflow", item.validate_workflow),
        ):
            if not value or value == "todo":
                continue
            if not value.startswith("{project-root}/"):
                errors.append(
                    f"menu item {item.index} {attr_name} must start with "
                    f"{{project-root}}/: {value!r}"
                )
                continue
            p = resolve_project_path(workspace, value)
            if not p.exists():
                errors.append(
                    f"menu item {item.index} {attr_name} path does not exist: {value}"
                )
    return errors


def validate_agent_file(workspace: Path, agent_md: Path) -> None:
    """Raise AgentValidationError if the agent markdown is inconsistent."""
    messages: list[str] = []
    try:
        text = agent_md.read_text(encoding="utf-8")
    except OSError as exc:
        raise AgentValidationError(agent_md, [f"cannot read file: {exc}"]) from exc

    try:
        definition = parse_agent_markdown(text)
    except ValueError as exc:
        raise AgentValidationError(agent_md, [str(exc)]) from exc

    messages.extend(validate_config_file(workspace, definition.config_relative_path))

    # Standard menu endings (all shipped agents follow this contract)
    if len(definition.menu) < 2:
        messages.append("menu must contain at least two items")
    else:
        pm, da = definition.menu[-2], definition.menu[-1]
        pm_joined = (pm.cmd_attr + " " + pm.label).lower()
        da_joined = (da.cmd_attr + " " + da.label).lower()
        if "party" not in pm_joined:
            messages.append("second-to-last menu item should be Party Mode (PM)")
        if "dismiss" not in da_joined:
            messages.append("last menu item should dismiss the agent (DA)")

    messages.extend(validate_referenced_paths(workspace, definition))

    if messages:
        raise AgentValidationError(agent_md, messages)


def validate_agent_manifest(workspace: Path, manifest_path: Path) -> None:
    """Validate every agent row in agent-manifest.csv."""
    rows = load_manifest_rows(manifest_path)
    seen_names: set[str] = set()
    errors: list[str] = []
    for row in rows:
        name = (row.get("name") or "").strip()
        rel = (row.get("path") or "").strip().strip('"')
        if not name or not rel:
            errors.append(f"invalid manifest row: {row!r}")
            continue
        if name in seen_names:
            errors.append(f"duplicate manifest name: {name!r}")
        seen_names.add(name)
        md_path = (workspace / rel).resolve()
        if not md_path.is_file():
            errors.append(f"manifest path for {name!r} missing: {rel}")
            continue
        try:
            validate_agent_file(workspace, md_path)
        except AgentValidationError as exc:
            errors.extend(f"{name} ({rel}): {m}" for m in exc.messages)
    if errors:
        raise AgentValidationError(manifest_path, errors)
