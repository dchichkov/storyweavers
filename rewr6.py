"""
rewr6.py - AST rewrite demo that composes with wrld6.py.

This file answers a boundary question:

  rewrites do not need to derive from wrld6.
  rewrites transform kernel source first; wrld6 executes the transformed source.

The useful compatibility point is that both layers speak the same pseudo-Python
story algebra. A rewrite rule can talk about character declarations:

  __C(Character, mother, Strict)
      -> __C(Character, mother, Strict + Caring)

and then wrld6's typed executor sees the enriched character meme state.

Compared with rewr5.py, this tiny demo also lets metavariables bind call names,
so `__C(...)` can match `Mom(...)` or `Grandma(...)`.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Dict, List, Optional

from wrld6 import execute_world


@dataclass(frozen=True)
class Rewrite:
    pattern_src: str
    output_src: str

    def pattern_ast(self) -> ast.AST:
        return ast.parse(self.pattern_src, mode="eval").body

    def output_ast(self) -> ast.AST:
        return ast.parse(self.output_src, mode="eval").body


Bindings = Dict[str, ast.AST]


def _is_meta_name(name: str) -> bool:
    return name.startswith("__") and len(name) > 2


def _ast_equal(a: ast.AST, b: ast.AST) -> bool:
    return ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)


def flatten_add(node: ast.AST) -> List[ast.AST]:
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return flatten_add(node.left) + flatten_add(node.right)
    return [node]


def rebuild_add(items: List[ast.AST]) -> ast.AST:
    if not items:
        raise ValueError("Cannot rebuild empty add-chain")
    node = copy.deepcopy(items[0])
    for item in items[1:]:
        node = ast.BinOp(left=node, op=ast.Add(), right=copy.deepcopy(item))
    return node


def match_pattern(pattern: ast.AST, target: ast.AST, env: Bindings) -> Optional[Bindings]:
    if isinstance(pattern, ast.Name) and _is_meta_name(pattern.id):
        bound = env.get(pattern.id)
        if bound is None:
            env2 = dict(env)
            env2[pattern.id] = target
            return env2
        return env if _ast_equal(bound, target) else None

    if isinstance(pattern, ast.Name) and isinstance(target, ast.Name):
        return env if pattern.id == target.id else None

    if isinstance(pattern, ast.Constant) and isinstance(target, ast.Constant):
        return env if pattern.value == target.value else None

    if isinstance(pattern, ast.Call) and isinstance(target, ast.Call):
        env2: Optional[Bindings] = dict(env)

        # rewr6 improvement: allow meta call names like __C(...).
        env2 = match_pattern(pattern.func, target.func, env2)
        if env2 is None:
            return None

        if len(pattern.args) != len(target.args):
            return None
        for p_arg, t_arg in zip(pattern.args, target.args):
            env2 = match_pattern(p_arg, t_arg, env2)
            if env2 is None:
                return None

        if len(pattern.keywords) != len(target.keywords):
            return None
        for p_kw, t_kw in zip(pattern.keywords, target.keywords):
            if p_kw.arg != t_kw.arg:
                return None
            env2 = match_pattern(p_kw.value, t_kw.value, env2)
            if env2 is None:
                return None

        return env2

    if isinstance(pattern, ast.BinOp) and isinstance(target, ast.BinOp):
        if not (isinstance(pattern.op, ast.Add) and isinstance(target.op, ast.Add)):
            return None
        env2 = match_pattern(pattern.left, target.left, dict(env))
        if env2 is None:
            return None
        return match_pattern(pattern.right, target.right, env2)

    return env if _ast_equal(pattern, target) else None


def substitute(template: ast.AST, env: Bindings) -> ast.AST:
    if isinstance(template, ast.Name) and _is_meta_name(template.id) and template.id in env:
        return copy.deepcopy(env[template.id])

    if isinstance(template, ast.Call):
        return ast.Call(
            func=substitute(template.func, env),
            args=[substitute(arg, env) for arg in template.args],
            keywords=[ast.keyword(arg=kw.arg, value=substitute(kw.value, env)) for kw in template.keywords],
        )

    if isinstance(template, ast.BinOp):
        return ast.BinOp(
            left=substitute(template.left, env),
            op=copy.deepcopy(template.op),
            right=substitute(template.right, env),
        )

    return copy.deepcopy(template)


class _ApplyOneRule(ast.NodeTransformer):
    def __init__(self, rule: Rewrite):
        self.did_change = False
        self.pattern = rule.pattern_ast()
        self.output = rule.output_ast()

    def generic_visit(self, node: ast.AST) -> ast.AST:
        node = super().generic_visit(node)
        if self.did_change:
            return node

        if (
            isinstance(self.pattern, ast.BinOp)
            and isinstance(self.pattern.op, ast.Add)
            and isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add)
        ):
            replaced = self._try_add_window(node)
            if replaced is not None:
                return replaced

        env = match_pattern(self.pattern, node, {})
        if env is None:
            return node

        replacement = substitute(self.output, env)
        ast.copy_location(replacement, node)
        ast.fix_missing_locations(replacement)
        self.did_change = True
        return replacement

    def _try_add_window(self, node: ast.BinOp) -> Optional[ast.AST]:
        pattern_items = flatten_add(self.pattern)
        target_items = flatten_add(node)
        if len(pattern_items) < 2 or len(target_items) < len(pattern_items):
            return None

        for start in range(0, len(target_items) - len(pattern_items) + 1):
            env: Bindings = {}
            ok = True
            for i, pattern_item in enumerate(pattern_items):
                env2 = match_pattern(pattern_item, target_items[start + i], env)
                if env2 is None:
                    ok = False
                    break
                env = env2
            if not ok:
                continue

            output = substitute(self.output, env)
            output_items = flatten_add(output) if isinstance(output, ast.BinOp) and isinstance(output.op, ast.Add) else [output]
            new_items = target_items[:start] + output_items + target_items[start + len(pattern_items):]
            replacement = rebuild_add(new_items) if len(new_items) > 1 else copy.deepcopy(new_items[0])
            ast.copy_location(replacement, node)
            ast.fix_missing_locations(replacement)
            self.did_change = True
            return replacement

        return None


def rewrite_source(source: str, rules: List[Rewrite], max_iters: int = 10) -> str:
    tree = ast.parse(source)
    for _ in range(max_iters):
        changed = False
        for rule in rules:
            applier = _ApplyOneRule(rule)
            tree = applier.visit(tree)
            changed = changed or applier.did_change
        if not changed:
            break
    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


RULES = [
    Rewrite(
        pattern_src="__C(Character, mother, Strict)",
        output_src="__C(Character, mother, Strict + Caring)",
    ),
    Rewrite(
        pattern_src="Warning(__S, __C) + Anger",
        output_src="Warning(__S, __C) + Anger(__S)",
    ),
]


if __name__ == "__main__":
    src = """
Lily(Character, girl, Curious)
Mom(Character, mother, Strict)
Warning(Mom, Lily) + Anger
"""
    rewritten = rewrite_source(src, RULES)

    print("--- BEFORE SOURCE ---")
    print(src.strip())
    print("\n--- BEFORE NARRATION ---")
    for trace in execute_world(src).traces:
        print(trace.text)

    print("\n--- AFTER SOURCE ---")
    print(rewritten.strip())
    print("\n--- AFTER NARRATION ---")
    for trace in execute_world(rewritten).traces:
        print(trace.text)
