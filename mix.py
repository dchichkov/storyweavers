#!/usr/bin/env python3
"""
mix.py - mechanically mix two transformation-arc kernels into one.

The thesis (see README "Composing Kernels"): meta-kernels like `Journey`,
`Identity`, `Quest`, `Cautionary` are the *same family* -- a transformation arc
with a shared slot skeleton (state -> catalyst -> process -> insight ->
transformation -> outcome). Once both kernels are mapped onto that skeleton, the
*merge* is pure `story.py` algebra applied slot-by-slot:

    1. normalize    each kernel onto the canonical slot skeleton
    2. unify        the protagonists (rename one onto the other; union traits)
    3. merge        per slot: `+`-union the fillers, dedup, prune subsumed bare names
    4. nest         a whole guest sub-arc (e.g. Identity) into its kind's slot
    5. gate         reject if a slot collects incompatible kinds (Death + Friendship)

Steps 2-4 are mechanical (reusing gen6's `flatten_add` / `rebuild_add`). Steps 1
and 5 are the only judgment, and that judgment is exactly the type-system /
compatibility layer the README describes -- here `compatible()` is a small stub
that later consults the KernelSignature / ASP graph.

Run:
    python mix.py                # mix the two demo kernels (Sophie/Journey x Whale/Identity)
    python mix.py --conflict     # show the gate rejecting an incompatible mix
"""
from __future__ import annotations

import argparse
import ast
import copy
import sys

from gen6 import flatten_add, rebuild_add  # the `+`-chain tools

# Canonical transformation-arc skeleton (output order).
CANONICAL_SLOTS = ["state", "catalyst", "process", "insight",
                   "transformation", "outcome"]

# Map each meta-kernel's own slot names onto the canonical skeleton.
SLOT_ALIASES = {
    "state": "state", "catalyst": "catalyst", "process": "process",
    "insight": "insight", "transformation": "transformation", "outcome": "outcome",
    "new": "transformation", "reaction": "insight",        # Identity
    "event": "catalyst", "consequence": "outcome", "lesson": "insight",  # Cautionary
    "result": "outcome",
}

# Recognized arc heads, and -- when one is used as a *guest* sub-arc nested whole
# into the host -- which canonical slot it drops into.
META_KERNELS = {"Journey", "Identity", "Quest", "Cautionary", "Conflict",
                "Resolution", "Encounter", "Transformation", "Friendship"}
GUEST_KIND_SLOT = {
    "Identity": "transformation", "Transformation": "transformation",
    "Friendship": "transformation", "Resolution": "outcome",
    "Quest": "process", "Cautionary": "process", "Conflict": "process",
    "Encounter": "catalyst", "Journey": "process",
}
LOOSE_DEFAULT_SLOT = "process"   # bare top-level action lines land here

# Compatibility gate: kinds that must not co-occur in one slot.
INCOMPATIBLE = [
    {"Death", "Friendship"}, {"Death", "Engaged"}, {"Death", "Acceptance"},
    {"Death", "Joy"}, {"Betrayal", "Friendship"},
]


# ---------------------------------------------------------------------------
# Parsing one kernel into a normalized arc.
# ---------------------------------------------------------------------------
class _Rename(ast.NodeTransformer):
    def __init__(self, old: str, new: str):
        self.old, self.new = old, new

    def visit_Name(self, node: ast.Name) -> ast.Name:
        if node.id == self.old:
            return ast.copy_location(ast.Name(id=self.new, ctx=node.ctx), node)
        return node


def _is_char_decl(call: ast.Call) -> bool:
    return (isinstance(call.func, ast.Name) and call.args
            and isinstance(call.args[0], ast.Name) and call.args[0].id == "Character")


class Arc:
    """A kernel normalized onto the canonical skeleton."""
    def __init__(self, src: str):
        tree = ast.parse(src)
        self.decl: ast.Call | None = None          # protagonist Character(...) decl
        self.head: str | None = None               # meta-kernel name (Journey, ...)
        self.protagonist: str | None = None
        self.meta_call: ast.Call | None = None
        self.loose: list[ast.AST] = []             # bare top-level expressions

        for stmt in tree.body:
            if not isinstance(stmt, ast.Expr):
                continue
            node = stmt.value
            if isinstance(node, ast.Call) and _is_char_decl(node):
                if self.decl is None:               # first decl = protagonist
                    self.decl = node
                continue
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in META_KERNELS):
                self.meta_call = node
                self.head = node.func.id
                if node.args and isinstance(node.args[0], ast.Name):
                    self.protagonist = node.args[0].id
                continue
            self.loose.append(node)                 # action line -> process

    @property
    def slot_count(self) -> int:
        return len(self.meta_call.keywords) if self.meta_call else 0

    def traits(self) -> list[ast.AST]:
        if self.decl is None or len(self.decl.args) < 3:
            return []
        out: list[ast.AST] = []
        for a in self.decl.args[2:]:
            out += flatten_add(a)
        return out


# ---------------------------------------------------------------------------
# Merge helpers.
# ---------------------------------------------------------------------------
def _dedup(items: list[ast.AST]) -> list[ast.AST]:
    seen: set[str] = set()
    out: list[ast.AST] = []
    for it in items:
        key = ast.dump(it)
        if key not in seen:
            seen.add(key)
            out.append(it)
    return out


def _prune_subsumed(items: list[ast.AST]) -> list[ast.AST]:
    """Drop a bare Name if a richer sibling already contains it
    (e.g. drop `Acceptance` when `Philosophical(Acceptance(Change))` is present)."""
    out = []
    for i, it in enumerate(items):
        if isinstance(it, ast.Name):
            others = [o for j, o in enumerate(items) if j != i]
            if any(any(isinstance(n, ast.Name) and n.id == it.id
                       for n in ast.walk(o)) for o in others):
                continue
        out.append(it)
    return out


def _kinds_in(fillers: list[ast.AST]) -> set[str]:
    names: set[str] = set()
    for f in fillers:
        for n in ast.walk(f):
            if isinstance(n, ast.Name):
                names.add(n.id)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                names.add(n.func.id)
    return names


def compatible(slot: str, fillers: list[ast.AST]) -> tuple[bool, str]:
    """The gate. Today: a small incompatibility table; later: KernelSignature/ASP."""
    kinds = _kinds_in(fillers)
    for bad in INCOMPATIBLE:
        if bad <= kinds:
            return False, f"slot '{slot}' collects incompatible kinds {sorted(bad)}"
    return True, ""


def mix(src_a: str, src_b: str) -> str:
    # Host = the richer arc (more slots); guest folds into it.
    host_src, guest_src = ((src_a, src_b)
                           if Arc(src_a).slot_count >= Arc(src_b).slot_count
                           else (src_b, src_a))
    host = Arc(host_src)
    if host.meta_call is None:
        raise ValueError("host kernel has no recognized meta-arc")

    # 2. unify protagonists: rename guest's protagonist onto the host's.
    guest_pre = Arc(guest_src)
    if (guest_pre.protagonist and host.protagonist
            and guest_pre.protagonist != host.protagonist):
        guest_src = ast.unparse(
            _Rename(guest_pre.protagonist, host.protagonist).visit(ast.parse(guest_src)))
    guest = Arc(guest_src)

    proto = host.protagonist

    # 3. collect fillers per canonical slot, host first then guest.
    slots: dict[str, list[ast.AST]] = {s: [] for s in CANONICAL_SLOTS}
    for kw in host.meta_call.keywords:
        slots.setdefault(SLOT_ALIASES.get(kw.arg, kw.arg), []).extend(flatten_add(kw.value))

    # guest's loose action lines -> process
    for node in guest.loose:
        slots[LOOSE_DEFAULT_SLOT].extend(flatten_add(node))

    # 4. guest meta-arc: same head -> merge its slots; different head -> nest whole.
    if guest.meta_call is not None:
        if guest.head == host.head:
            for kw in guest.meta_call.keywords:
                slots.setdefault(SLOT_ALIASES.get(kw.arg, kw.arg), []).extend(
                    flatten_add(kw.value))
        else:
            target = GUEST_KIND_SLOT.get(guest.head, LOOSE_DEFAULT_SLOT)
            slots[target].append(guest.meta_call)

    # dedup + prune subsumed bare names
    for s in slots:
        slots[s] = _prune_subsumed(_dedup(slots[s]))

    # 5. gate
    for s, fillers in slots.items():
        ok, reason = compatible(s, fillers)
        if not ok:
            raise ValueError(f"incompatible mix: {reason}")

    # merged character decl: host kind, union of traits.
    traits = _prune_subsumed(_dedup(host.traits() + guest.traits()))
    decl_args = [ast.Name(id="Character", ctx=ast.Load())]
    if len(host.decl.args) >= 2:
        decl_args.append(host.decl.args[1])          # keep host kind
    if traits:
        decl_args.append(rebuild_add(traits))
    decl = ast.Call(func=ast.Name(id=proto, ctx=ast.Load()), args=decl_args, keywords=[])

    # rebuild the host meta-arc with merged slots (canonical order, non-empty only).
    keywords = [ast.keyword(arg=s, value=rebuild_add(slots[s]))
                for s in CANONICAL_SLOTS if slots[s]]
    arc = ast.Call(func=ast.Name(id=host.head, ctx=ast.Load()),
                   args=[ast.Name(id=proto, ctx=ast.Load())], keywords=keywords)

    return ast.unparse(decl) + "\n" + ast.unparse(arc)


# ---------------------------------------------------------------------------
# Demo kernels (mirror mine_kernels.py few-shot pairs).
# ---------------------------------------------------------------------------
SOPHIE = """
Sophie(Character, girl, Dreamy)
Journey(Sophie,
    state = Routine + Longing([Dragons, Flight]) + Loneliness / 10,
    catalyst = Surprise + Wind,
    process = Quest + Obstacles + Surrender / 5 + Persistence,
    insight = Philosophical(Acceptance(Change)),
    transformation = Engaged(World) + Friendship(Sophie, Wind))
"""

WHALE = """
Whale(Character, Imaginary, Delicate + Kind)
Test(Speed) + Community(Support, cheered) + Happy
Identity(Whale, new=Shark, reaction=Acceptance + Community(Support, Liked))
"""

WHALE_CONFLICT = """
Whale(Character, Imaginary, Delicate + Kind)
Test(Speed) + Community(Support, cheered)
Identity(Whale, new=Shark, reaction=Death)
"""


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conflict", action="store_true",
                    help="mix an incompatible guest (Death) to show the gate reject")
    args = ap.parse_args()

    guest = WHALE_CONFLICT if args.conflict else WHALE
    print("=== kernel A (host) ===" + SOPHIE.rstrip())
    print("\n=== kernel B (guest) ===" + guest.rstrip())
    print("\n=== mechanical mix ===")
    try:
        print(mix(SOPHIE, guest))
    except ValueError as err:
        print(f"REJECTED: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
