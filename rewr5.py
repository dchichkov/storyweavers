"""
rewr5.py - Prototype: declarative AST rewrites expressed in story algebra syntax.

Goal
----
Support a rule like:

Rewrite(
  pattern = Fear(__C, __OBJ) + Brave(__C),
  output  = Fear(__C, __OBJ) + Brave(__C, _after="fear", _use_pronoun=True),
  when    = PhaseIs("setup"),
  effect  = SetPhase("climax"),
)

Key idea
--------
Inside Rewrite.pattern / Rewrite.output, identifiers starting with "__" are treated
as metavariables (binders) during matching/substitution. This keeps rules readable
and "kernel-like" while still using real Python AST.
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ----------------------------
# Rewrite rule representation
# ----------------------------

@dataclass(frozen=True)
class Rewrite:
    pattern_src: str
    output_src: str
    when_src: str = ""     # optional guard expression, e.g. "PhaseIs('setup')"
    effect_src: str = ""   # optional effect expression, e.g. "SetPhase('climax')"

    def pattern_ast(self) -> ast.AST:
        return ast.parse(self.pattern_src, mode="eval").body

    def output_ast(self) -> ast.AST:
        return ast.parse(self.output_src, mode="eval").body

    def when_ast(self) -> Optional[ast.AST]:
        if not self.when_src.strip():
            return None
        return ast.parse(self.when_src, mode="eval").body

    def effect_ast(self) -> Optional[ast.AST]:
        if not self.effect_src.strip():
            return None
        return ast.parse(self.effect_src, mode="eval").body


@dataclass
class RewriteContext:
    """State accessible to guards/effects (kept intentionally minimal)."""
    phase: str = "setup"


# -------------------------------------
# Guard/effect evaluation (minimal DSL)
# -------------------------------------

def _const_str(node: ast.AST) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def eval_guard(expr: ast.AST, ctx: RewriteContext) -> bool:
    """
    Evaluate a guard expression AST.

    Minimal support:
      - PhaseIs("setup")
      - True / False
      - and/or/not (bool ops)
    """
    if isinstance(expr, ast.Constant) and isinstance(expr.value, bool):
        return expr.value

    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.Not):
        return not eval_guard(expr.operand, ctx)

    if isinstance(expr, ast.BoolOp):
        if isinstance(expr.op, ast.And):
            return all(eval_guard(v, ctx) for v in expr.values)
        if isinstance(expr.op, ast.Or):
            return any(eval_guard(v, ctx) for v in expr.values)

    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        if expr.func.id == "PhaseIs" and len(expr.args) == 1:
            wanted = _const_str(expr.args[0])
            return wanted is not None and ctx.phase == wanted

    # Default: if we don't understand it, be conservative (don't fire).
    return False


def apply_effect(expr: ast.AST, ctx: RewriteContext) -> None:
    """
    Apply an effect expression AST.

    Minimal support:
      - SetPhase("climax")
    """
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name):
        if expr.func.id == "SetPhase" and len(expr.args) == 1:
            new_phase = _const_str(expr.args[0])
            if new_phase is not None:
                ctx.phase = new_phase


# -------------------------
# Pattern matching utilities
# -------------------------

def _is_meta_name(name: str) -> bool:
    # Convention: metavariables start with "__", e.g. "__C", "__OBJ"
    return name.startswith("__") and len(name) > 2


def _ast_equal(a: ast.AST, b: ast.AST) -> bool:
    # Structural equality ignoring location info.
    return ast.dump(a, include_attributes=False) == ast.dump(b, include_attributes=False)


Bindings = Dict[str, ast.AST]


def flatten_add(node: ast.AST) -> List[ast.AST]:
    """
    Flatten an addition/composition chain into a list.

    Python parses A + B + C as nested BinOp(Add), so we canonicalize:
      BinOp(BinOp(A,+,B),+,C) -> [A, B, C]
      BinOp(A,+,BinOp(B,+,C)) -> [A, B, C]
    """
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        return flatten_add(node.left) + flatten_add(node.right)
    return [node]


def rebuild_add(items: List[ast.AST]) -> ast.AST:
    """Rebuild a left-associated A + B + C BinOp chain from a list."""
    if not items:
        raise ValueError("Cannot rebuild empty add-chain")
    node = copy.deepcopy(items[0])
    for item in items[1:]:
        node = ast.BinOp(left=node, op=ast.Add(), right=copy.deepcopy(item))
    return node


def match_pattern(pattern: ast.AST, target: ast.AST, env: Bindings) -> Optional[Bindings]:
    """
    Try to match 'pattern' against 'target'. Return updated env on success, else None.

    Metavariables:
      - ast.Name(id="__X") binds to any subtree and must be consistent on reuse.
    """
    # Meta-variable binding
    if isinstance(pattern, ast.Name) and _is_meta_name(pattern.id):
        bound = env.get(pattern.id)
        if bound is None:
            env2 = dict(env)
            env2[pattern.id] = target
            return env2
        return env if _ast_equal(bound, target) else None

    # Exact Name matching for non-meta names
    if isinstance(pattern, ast.Name) and isinstance(target, ast.Name):
        return env if pattern.id == target.id else None

    # Constants
    if isinstance(pattern, ast.Constant) and isinstance(target, ast.Constant):
        return env if pattern.value == target.value else None

    # Calls: match function name + args + keywords (exact keyword names; values can contain metavars)
    if isinstance(pattern, ast.Call) and isinstance(target, ast.Call):
        if not (isinstance(pattern.func, ast.Name) and isinstance(target.func, ast.Name)):
            return None
        if pattern.func.id != target.func.id:
            return None

        if len(pattern.args) != len(target.args):
            return None

        env2: Optional[Bindings] = dict(env)
        for pa, ta in zip(pattern.args, target.args):
            env2 = match_pattern(pa, ta, env2)
            if env2 is None:
                return None

        # Keywords: require same count and same keyword args in the same order for this prototype
        if len(pattern.keywords) != len(target.keywords):
            return None
        for pkw, tkw in zip(pattern.keywords, target.keywords):
            if pkw.arg != tkw.arg:
                return None
            env2 = match_pattern(pkw.value, tkw.value, env2)
            if env2 is None:
                return None

        return env2

    # BinOp (composition): only support Add in this prototype.
    # NOTE: For matching inside longer chains, we handle flattening/windowing in the applier.
    if isinstance(pattern, ast.BinOp) and isinstance(target, ast.BinOp):
        if not (isinstance(pattern.op, ast.Add) and isinstance(target.op, ast.Add)):
            return None
        env2 = match_pattern(pattern.left, target.left, dict(env))
        if env2 is None:
            return None
        return match_pattern(pattern.right, target.right, env2)

    # Fallback: exact structural match
    return env if _ast_equal(pattern, target) else None


def substitute(template: ast.AST, env: Bindings) -> ast.AST:
    """Substitute metavariables in template using env."""
    if isinstance(template, ast.Name) and _is_meta_name(template.id) and template.id in env:
        return copy.deepcopy(env[template.id])

    if isinstance(template, ast.Call):
        return ast.Call(
            func=copy.deepcopy(template.func),
            args=[substitute(a, env) for a in template.args],
            keywords=[ast.keyword(arg=kw.arg, value=substitute(kw.value, env)) for kw in template.keywords],
        )

    if isinstance(template, ast.BinOp):
        return ast.BinOp(
            left=substitute(template.left, env),
            op=copy.deepcopy(template.op),
            right=substitute(template.right, env),
        )

    # Default: deep copy node
    return copy.deepcopy(template)


# -------------------------
# Rewrite application engine
# -------------------------

class _ApplyOneRule(ast.NodeTransformer):
    def __init__(self, rule: Rewrite, ctx: RewriteContext):
        self.rule = rule
        self.ctx = ctx
        self.did_change = False
        self._pattern = rule.pattern_ast()
        self._output = rule.output_ast()
        self._when = rule.when_ast()
        self._effect = rule.effect_ast()

    def generic_visit(self, node: ast.AST) -> ast.AST:
        # bottom-up application: rewrite children first
        node = super().generic_visit(node)

        if self.did_change:
            return node

        if self._when is not None and not eval_guard(self._when, self.ctx):
            return node

        # Sequence-aware matching for + chains:
        # If both pattern and node are Add-chains, allow matching a contiguous window.
        if (
            isinstance(self._pattern, ast.BinOp)
            and isinstance(self._pattern.op, ast.Add)
            and isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Add)
        ):
            pat_seq = flatten_add(self._pattern)
            tgt_seq = flatten_add(node)

            if len(tgt_seq) >= len(pat_seq) and len(pat_seq) >= 2:
                for start in range(0, len(tgt_seq) - len(pat_seq) + 1):
                    env: Bindings = {}
                    ok = True
                    for i, p_item in enumerate(pat_seq):
                        env2 = match_pattern(p_item, tgt_seq[start + i], env)
                        if env2 is None:
                            ok = False
                            break
                        env = env2
                    if not ok:
                        continue

                    replaced_ast = substitute(self._output, env)
                    out_seq = (
                        flatten_add(replaced_ast)
                        if isinstance(replaced_ast, ast.BinOp) and isinstance(replaced_ast.op, ast.Add)
                        else [replaced_ast]
                    )

                    new_seq = tgt_seq[:start] + out_seq + tgt_seq[start + len(pat_seq) :]
                    replacement = rebuild_add(new_seq) if len(new_seq) > 1 else copy.deepcopy(new_seq[0])

                    ast.copy_location(replacement, node)
                    ast.fix_missing_locations(replacement)

                    if self._effect is not None:
                        apply_effect(self._effect, self.ctx)

                    self.did_change = True
                    return replacement

        env = match_pattern(self._pattern, node, {})
        if env is None:
            return node

        replacement = substitute(self._output, env)
        ast.copy_location(replacement, node)
        ast.fix_missing_locations(replacement)

        if self._effect is not None:
            apply_effect(self._effect, self.ctx)

        self.did_change = True
        return replacement


def rewrite_source(source: str, rules: List[Rewrite], ctx: Optional[RewriteContext] = None, max_iters: int = 10) -> str:
    """
    Apply rules to `source` until a fixed point or max_iters.
    """
    ctx = ctx or RewriteContext()
    tree = ast.parse(source)

    for _ in range(max_iters):
        changed_any = False
        for rule in rules:
            applier = _ApplyOneRule(rule, ctx)
            tree = applier.visit(tree)
            if applier.did_change:
                changed_any = True
        if not changed_any:
            break

    ast.fix_missing_locations(tree)
    return ast.unparse(tree)


# -------------------------
# Demo: one rule (the one you asked for)
# -------------------------

RULES: List[Rewrite] = [
    Rewrite(
        pattern_src="Fear(__C, __OBJ) + Brave(__C)",
        output_src="Fear(__C, __OBJ) + Brave(__C, _after='fear', _use_pronoun=True)",
        when_src="PhaseIs('setup')",
        effect_src="SetPhase('climax')",
    )
]


if __name__ == "__main__":
    src = """
Lily(Character, girl, Curious)
Fear(Lily, dog) + Brave(Lily)
Happy(Lily)
"""
    print("--- BEFORE ---")
    print(src.strip())
    print("\n--- AFTER ---")
    print(rewrite_source(src, RULES).strip())
