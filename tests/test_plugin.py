#!/usr/bin/env python3
"""Plugin packaging lockstep + emit smoke + Orca-specific rules."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VERSION = "0.2.0"
NAME = "orca-ager"
sys.path.insert(0, str(REPO / "scripts"))

NAMED_ROLE_RE = re.compile(r"^[A-Z][A-Za-z0-9]*(-[A-Z][A-Za-z0-9]*)+$")


class PluginPackagingTests(unittest.TestCase):
    def test_manifest_versions_stay_in_lockstep(self) -> None:
        claude = json.loads((REPO / ".claude-plugin/plugin.json").read_text())
        codex = json.loads((REPO / ".codex-plugin/plugin.json").read_text())
        cursor = json.loads((REPO / ".cursor-plugin/plugin.json").read_text())
        root = json.loads((REPO / "plugin.json").read_text())
        claude_market = json.loads((REPO / ".claude-plugin/marketplace.json").read_text())
        grok = json.loads((REPO / ".grok-plugin/marketplace.json").read_text())
        root_market = json.loads((REPO / "marketplace.json").read_text())
        found = {
            claude["version"],
            codex["version"],
            cursor["version"],
            root["version"],
            claude_market["plugins"][0]["version"],
            grok["version"],
            grok["plugins"][0]["version"],
            root_market["plugins"][0]["version"],
        }
        self.assertEqual(found, {VERSION})

    def test_names_match(self) -> None:
        for path in (
            "plugin.json",
            ".claude-plugin/plugin.json",
            ".codex-plugin/plugin.json",
            ".cursor-plugin/plugin.json",
        ):
            data = json.loads((REPO / path).read_text())
            self.assertEqual(data["name"], NAME, path)

    def test_agent_plugins_schema(self) -> None:
        root = json.loads((REPO / "plugin.json").read_text())
        self.assertTrue(root["$schema"].startswith("https://agent-plugins.org/"))

    def test_codex_skills_resolve(self) -> None:
        manifest = json.loads((REPO / ".codex-plugin/plugin.json").read_text())
        self.assertTrue((REPO / manifest["skills"]).is_dir())

    def test_cursor_pointers_resolve(self) -> None:
        manifest = json.loads((REPO / ".cursor-plugin/plugin.json").read_text())
        self.assertTrue((REPO / manifest["skills"]).is_dir())
        self.assertTrue((REPO / manifest["rules"]).is_dir())
        self.assertTrue((REPO / manifest["commands"]).is_dir())

    def test_skill_frontmatter(self) -> None:
        for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
            text = skill.read_text()
            match = re.match(r"^---\n(.*?)\n---", text, re.S)
            self.assertIsNotNone(match, skill)
            block = match.group(1)
            self.assertRegex(block, r"(?m)^name: [a-z0-9-]+$")
            self.assertRegex(block, r"(?m)^description: .+$")

    def test_commands_exist(self) -> None:
        for name in ("orca-init", "orca-compile", "orca-validate", "orca-emit", "ager-to-orca", "orca-skills", "orca-reverse"):
            self.assertTrue((REPO / "commands" / f"{name}.md").is_file(), name)

    def test_peer_skill_stubs_shipped(self) -> None:
        for name in ("orca-cli", "orchestration"):
            skill = REPO / "skills" / name / "SKILL.md"
            self.assertTrue(skill.is_file(), name)
            text = skill.read_text()
            self.assertIn("discovery stub", text)
            self.assertIn("skills get", text)


class EmitTests(unittest.TestCase):
    def test_sample_emits_named_agents_and_worktrees(self) -> None:
        from emit import emit, named_role
        from ir import load_sample
        from validate import validate_graph, validate_project
        from emit import build_project

        self.assertEqual(named_role("claude", "Plan-Drafter"), "Claude-Plan-Drafter")
        self.assertEqual(named_role("grok", "Mediator", "Acme"), "Acme-Grok-Mediator")
        self.assertRegex("Final-Spec-Reviewer", NAMED_ROLE_RE)

        graph = load_sample()
        graph_check = validate_graph(graph)
        self.assertTrue(graph_check.ok, [e.message for e in graph_check.errors])

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            written = emit(graph, out)
            self.assertGreaterEqual(len(written), 20)
            self.assertTrue((out / "orca-project.yaml").is_file())
            self.assertTrue((out / "scripts/run-feature.sh").is_file())
            self.assertTrue((out / "remote-control.json").is_file())
            self.assertTrue((out / "COMPILE.md").is_file())
            self.assertTrue((out / "agents/Claude-Plan-Drafter/SYSTEM.md").is_file())
            self.assertTrue((out / "agents/Grok-Mediator/SYSTEM.md").is_file())
            self.assertTrue((out / "agents/Final-Spec-Reviewer/SYSTEM.md").is_file())

            project = build_project(graph)
            project_check = validate_project(project)
            self.assertTrue(project_check.ok, [e.message for e in project_check.errors])
            names = [a["name"] for a in project["spec"]["agents"]]
            self.assertEqual(len(names), len(set(names)))
            self.assertEqual(len(names), 12)
            for name in names:
                self.assertRegex(name, NAMED_ROLE_RE)
            implementers = [a for a in project["spec"]["agents"] if a["role"] == "Implementer"]
            trees = sorted(a["worktree"] for a in implementers)
            self.assertEqual(trees, ["wt-claude", "wt-codex", "wt-grok"])
            judges = [a for a in project["spec"]["agents"] if a["role"] == "Judge"]
            self.assertEqual(sorted(a["worktree"] for a in judges), ["wt-judge-claude", "wt-judge-codex", "wt-judge-grok"])

            remote = json.loads((out / "remote-control.json").read_text())
            self.assertEqual(remote["policy"], "rename")
            self.assertIn("claude-plan-drafter", remote["map"])

            script = (out / "scripts/run-feature.sh").read_text()
            self.assertIn("--name Claude-Implementer", script)
            self.assertIn("worktree create --name wt-claude", script)
            self.assertIn("gate-create", script)
            self.assertIn("orca-ide", script)
            self.assertIn("skills get orca-cli", script)
            self.assertIn("skills get orchestration --full", script)
            self.assertNotIn("git worktree add", script)
            self.assertNotIn("git worktree create", script)
            self.assertTrue((out / "agents/Orca-Coordinator/SYSTEM.md").is_file())
            self.assertTrue((out / "skills/orca-cli/SKILL.md").is_file())
            self.assertTrue((out / "skills/orchestration/SKILL.md").is_file())
            self.assertTrue((out / "ORCA_SKILLS.md").is_file())
            prompt = (out / "agents/Claude-Implementer/SYSTEM.md").read_text()
            self.assertIn("orca skills get orca-cli", prompt)
            self.assertIn("orca skills get orchestration --full", prompt)
            self.assertIn("Never raw `git worktree`", prompt)
            coord = (out / "agents/Orca-Coordinator/SYSTEM.md").read_text()
            self.assertIn("orchestration", coord)
            self.assertIn("Claude-Implementer", coord)
            yaml = (out / "orca-project.yaml").read_text()
            self.assertIn("orca-cli", yaml)
            self.assertIn("Orca-Coordinator", yaml)
            self.assertRegex(yaml, r"(?m)^\s+skills:\n\s+primary: orca-cli")
            self.assertTrue((out / "knowledge-bind.yaml").is_file())
            self.assertTrue((out / "SECOND_BRAIN.md").is_file())
            bind = (out / "knowledge-bind.yaml").read_text()
            self.assertIn("KnowledgeBind", bind)
            self.assertIn("DecisionRecord", bind)
            self.assertIn("TicketLink", bind)
            judge = (out / "agents/Claude-Judge/SYSTEM.md").read_text()
            self.assertIn("DecisionRecord", judge)
            self.assertIn("second-brain/", judge)

    def test_fails_on_worktree_overlap(self) -> None:
        from emit import emit
        from ir import load_sample

        graph = load_sample()
        grok = next(a for a in graph.agents if a.id == "grok-implementer")
        grok.worktree = "wt-claude"
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(SystemExit) as ctx:
                emit(graph, Path(td))
            self.assertIn("Worktree", str(ctx.exception))

    def test_fails_on_missing_schemas(self) -> None:
        from ir import SchemaRef, load_sample
        from validate import validate_graph

        graph = load_sample()
        graph.agents[0].input_schema = SchemaRef("", {})
        check = validate_graph(graph)
        self.assertFalse(check.ok)
        self.assertTrue(any(e.code == "schema.input" for e in check.errors))

    def test_fails_on_name_collision(self) -> None:
        from emit import build_project
        from ir import load_sample
        from validate import validate_project

        graph = load_sample()
        graph.agents[1].title = "Claude-Plan-Drafter"
        graph.agents[1].host = "claude"
        graph.agents[1].role = "Plan-Drafter"
        project = build_project(graph)
        check = validate_project(project)
        self.assertFalse(check.ok)
        self.assertTrue(any(e.code == "name.collision" for e in check.errors))

    def test_remote_control_disable_and_prefix(self) -> None:
        from emit import emit
        from ir import load_sample

        graph = load_sample()
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            emit(graph, out, remote_control="disable", name_prefix="Fleet")
            remote = json.loads((out / "remote-control.json").read_text())
            self.assertEqual(remote["policy"], "disable")
            self.assertTrue((out / "agents/Fleet-Claude-Plan-Drafter/SYSTEM.md").is_file())

    def test_loop_policy_order(self) -> None:
        from ir import load_sample

        graph = load_sample()
        self.assertEqual(graph.loop.check_order, ["goal", "deadline", "price_budget", "max_turns", "no_progress"])


class ReverseTests(unittest.TestCase):
    def test_parse_sample_orca_project(self) -> None:
        from layout import parse_yaml

        raw = parse_yaml((REPO / "sample-orca/orca-project.yaml").read_text())
        self.assertEqual(raw["kind"], "Project")
        self.assertEqual(len(raw["spec"]["agents"]), 12)

    def test_reverse_round_trip_sample(self) -> None:
        from reverse import reverse_project, load_orca_project

        graph = reverse_project(load_orca_project(REPO / "sample-orca/orca-project.yaml"))
        self.assertEqual(len(graph.agents), 12)
        self.assertEqual(graph.entry, "claude-plan-drafter")
        self.assertEqual(graph.loop.max_turns, 12)
        self.assertEqual(graph.remote_control, "rename")
        ids = [a.id for a in graph.agents]
        self.assertIn("claude-implementer", ids)
        self.assertNotIn("orca-coordinator", ids)
        implementer = next(a for a in graph.agents if a.id == "claude-implementer")
        self.assertEqual(implementer.worktree, "wt-claude")
        self.assertIn("claude-implementer", graph.stages[3].agents)
        self.assertEqual(graph.gate.after, "final-spec-reviewer")
        self.assertEqual(graph.knowledge_bind, "second-brain/")
        trees = sorted(a.worktree for a in graph.agents if a.worktree)
        self.assertEqual(
            trees,
            ["wt-claude", "wt-codex", "wt-grok", "wt-judge-claude", "wt-judge-codex", "wt-judge-grok"],
        )

    def test_reverse_cli_writes_draft(self) -> None:
        from reverse import load_orca_project, reverse_project, graph_to_compact
        from layout import to_yaml, write

        graph = reverse_project(load_orca_project(REPO / "sample-orca/orca-project.yaml"))
        with tempfile.TemporaryDirectory() as td:
            dest = write(Path(td), "reversed-ager.yaml", to_yaml(graph_to_compact(graph)))
            text = dest.read_text()
            self.assertIn("claude-plan-drafter", text)
            self.assertIn("wt-claude", text)
            self.assertNotIn("Orca-Coordinator", text)


if __name__ == "__main__":
    unittest.main()
