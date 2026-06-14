#!/usr/bin/env python3
"""
ast_rewrite_transform_demo.py - World-gated AST rewrite demo for gen6.

This is deliberately a demo, like memeplex_demo.py: it registers one demo-only
replacement kernel, then applies a candidate transform to story ASTs only when:

  1. the AST contains the required transition shape,
  2. that transition binds two declared character carriers, and
  3. executing the story with the old transition erased leaves enough embedded
     Love memeplex in both carriers for the new transition to be world-compatible.

Run:
    python3 ast_rewrite_transform_demo.py
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Callable, Dict, Optional, Tuple

from gen6registry import REGISTRY  # noqa: F401  (loads the full engine + packs)
from gen6 import (
    DEFAULT_RULES,
    Character,
    Entity,
    Executor,
    Rewrite,
    World,
    match_pattern,
    narrate,
    rewrite_tree,
    substitute,
    tag_coherence,
)


@REGISTRY.kernel("Lovers")
def Lovers(ctx: World, a: Character, b: Character) -> str:
    """Demo-only ending: a stronger relationship transition than Friendship."""
    a.add_meme("Love", 0.5)
    b.add_meme("Love", 0.5)
    a.add_link("Love", b)
    b.add_link("Love", a)
    ctx.actor = a
    return f"{ctx.say(a)} and {b} let their friendship grow into love."


@REGISTRY.kernel("_TransformProbe")
def TransformProbe(ctx: World) -> str:
    """No-op placeholder used to execute the source story without the old ending."""
    return ""


@dataclass
class Candidate:
    node: ast.AST
    env: Dict[str, ast.AST]
    rewritten_source: str
    probe_source: str


@dataclass
class Decision:
    applied: bool
    reason: str
    source_after: str
    world_before: Optional[World] = None


class _FirstMatch(ast.NodeVisitor):
    def __init__(self, rule: Rewrite):
        self.pattern = rule.pattern_ast()
        self.node: Optional[ast.AST] = None
        self.env: Optional[Dict[str, ast.AST]] = None

    def generic_visit(self, node: ast.AST) -> None:
        if self.node is not None:
            return
        env = match_pattern(self.pattern, node, {})
        if env is not None:
            self.node = node
            self.env = env
            return
        super().generic_visit(node)


class _ReplaceExact(ast.NodeTransformer):
    def __init__(self, old: ast.AST, new: ast.AST):
        self.old = old
        self.new = new
        self.did_change = False

    def generic_visit(self, node: ast.AST) -> ast.AST:
        if not self.did_change and ast.dump(node, include_attributes=False) == ast.dump(self.old, include_attributes=False):
            replacement = copy.deepcopy(self.new)
            ast.copy_location(replacement, node)
            ast.fix_missing_locations(replacement)
            self.did_change = True
            return replacement
        return super().generic_visit(node)


def _declared_characters(tree: ast.AST) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
            continue
        if node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "Character":
            names.add(node.func.id)
    return names


def _name_binding(env: Dict[str, ast.AST], key: str) -> Optional[str]:
    node = env.get(key)
    return node.id if isinstance(node, ast.Name) else None


def _execute(source: str) -> World:
    tree = rewrite_tree(ast.parse(source), DEFAULT_RULES)
    tree = tag_coherence(tree)
    return Executor().execute_tree(tree)


def _render(source: str) -> str:
    return narrate(_execute(source))


def _candidate(source: str, rule: Rewrite) -> Optional[Candidate]:
    tree = ast.parse(source)
    finder = _FirstMatch(rule)
    finder.visit(tree)
    if finder.node is None or finder.env is None:
        return None

    rewrite_node = substitute(rule.output_ast(), finder.env)
    probe_node = ast.Call(func=ast.Name(id="_TransformProbe", ctx=ast.Load()), args=[], keywords=[])

    rewritten_tree = _ReplaceExact(finder.node, rewrite_node).visit(copy.deepcopy(tree))
    probe_tree = _ReplaceExact(finder.node, probe_node).visit(copy.deepcopy(tree))
    ast.fix_missing_locations(rewritten_tree)
    ast.fix_missing_locations(probe_tree)
    return Candidate(
        node=finder.node,
        env=finder.env,
        rewritten_source=ast.unparse(rewritten_tree),
        probe_source=ast.unparse(probe_tree),
    )


def _romance_allowed(world: World, a_name: str, b_name: str, *, min_love: float) -> Tuple[bool, str]:
    a = world.entities.get(a_name)
    b = world.entities.get(b_name)
    if not (_is_person(a) and _is_person(b)):
        return False, f"{a_name} and {b_name} are not both person-like character carriers"
    a_love = a.meme("Love")
    b_love = b.meme("Love")
    if a_love < min_love or b_love < min_love:
        return False, f"Love too low before the ending ({a_name}={a_love:.2f}, {b_name}={b_love:.2f}, need {min_love:.2f})"
    return True, f"allowed ({a_name}.Love={a_love:.2f}, {b_name}.Love={b_love:.2f})"


def _is_person(entity: Optional[Entity]) -> bool:
    if entity is None or entity.kind != "character":
        return False
    return entity.type_name.lower() in {
        "boy", "girl", "child", "person", "human", "friend", "man", "woman",
        "lady", "mother", "father", "parent", "adult",
    }


def apply_world_gated_rewrite(
    source: str,
    rule: Rewrite,
    allow: Callable[[World, Dict[str, ast.AST]], Tuple[bool, str]],
) -> Decision:
    tree = ast.parse(source)
    candidate = _candidate(source, rule)
    if candidate is None:
        return Decision(False, "AST does not contain Friendship(__A, __B)", source)

    a_name = _name_binding(candidate.env, "__A")
    b_name = _name_binding(candidate.env, "__B")
    if not a_name or not b_name or a_name == b_name:
        return Decision(False, "matched transition does not bind two distinct character names", source)

    declared = _declared_characters(tree)
    if a_name not in declared or b_name not in declared:
        return Decision(False, f"matched names are not both declared characters: {a_name}, {b_name}", source)

    world_before = _execute(candidate.probe_source)
    ok, reason = allow(world_before, candidate.env)
    if not ok:
        return Decision(False, reason, source, world_before)
    return Decision(True, reason, candidate.rewritten_source, world_before)


FRIENDS_TO_LOVERS = Rewrite(
    pattern_src="Friendship(__A, __B)",
    output_src="Lovers(__A, __B)",
)


def allow_lovers(world: World, env: Dict[str, ast.AST]) -> Tuple[bool, str]:
    a_name = _name_binding(env, "__A")
    b_name = _name_binding(env, "__B")
    if a_name is None or b_name is None:
        return False, "rewrite did not bind two names"
    return _romance_allowed(world, a_name, b_name, min_love=0.5)


NO_PAIR_STORY = """
Maya(Character, woman, Curious)
Discovery(Maya, flower)
Friendship(Maya, flower)
"""


LOW_LOVE_STORY = """
Maya(Character, woman, Curious)
Noah(Character, man, Friendly)

Meet(Maya, Noah)
Play(Maya, Noah)
Friendship(Maya, Noah)
"""


# Compressed from TinyStories_kernels/data01.kernels.jsonl:4785 into clean,
# well-supported kernels. The mutual hugs embed enough Love in both carriers.
HIGH_LOVE_STORY = """
Maya(Character, woman, Caring + Brave)
Noah(Character, man, Sad + Happy)

Meet(Maya, Noah)
Hug(Maya, Noah)
Hug(Noah, Maya)
Friendship(Maya, Noah)
"""


def _show(label: str, source: str) -> None:
    decision = apply_world_gated_rewrite(source, FRIENDS_TO_LOVERS, allow_lovers)
    print(f"=== {label} ===")
    print(f"decision: {'APPLY' if decision.applied else 'SKIP'} - {decision.reason}")
    if decision.world_before is not None:
        love = {
            name: ent.meme("Love")
            for name, ent in decision.world_before.entities.items()
            if ent.kind == "character"
        }
        print(f"love before candidate ending: {love}")
    print("source before:")
    print(source.strip())
    print("generated before:")
    print(_render(source))
    print("source after decision:")
    print(decision.source_after.strip())
    print("generated after decision:")
    print(_render(decision.source_after))
    print()


def _demo() -> None:
    print("Rule: Friendship(__A, __B) -> Lovers(__A, __B)")
    print("Gate: __A and __B must be declared person-like characters with Love >= 0.5 before the ending.")
    print()
    _show("matched transition, blocked by non-character endpoint", NO_PAIR_STORY)
    _show("matching AST, blocked by low Love", LOW_LOVE_STORY)
    _show("matching AST, allowed by accumulated Love", HIGH_LOVE_STORY)


if __name__ == "__main__":
    _demo()
