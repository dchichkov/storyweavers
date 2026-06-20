#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/abominate_determine_simmer_suspense_magic_heartwarming.py
=========================================================================================

A standalone storyworld about a cozy magic kitchen, a small suspenseful
problem, and a warm ending.

Premise:
A child and a caregiver are making a gentle supper when a tiny spellbook
predicts something is wrong. They must determine what to do, let the pot simmer
safely, and use a little magic and kindness to finish the meal.

This world is designed to stay heartwarming while still having suspense:
the tension comes from uncertainty, the turn comes from a careful discovery,
and the ending image proves that the kitchen is calmer, warmer, and shared.

The seed words are woven into the world as follows:
- abominate: a rare old spell-word that means "send away the sourness"
- determine: the characters must determine the cause of the strange kitchen glow
- simmer: the pot must simmer gently to finish the soup

The story quality goal is a child-facing, concrete, authored tale with state-driven
events, not a frozen paragraph with swapped nouns.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SUSPENSE_MIN = 1.0
MAGIC_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"grandmother": "grandma", "grandfather": "grandpa", "mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Ingredient:
    id: str
    label: str
    kind: str
    warm: bool = False
    calm: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class MagicCharm:
    id: str
    label: str
    phrase: str
    effect: str
    power: int
    gentle: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_simmer(world: World) -> list[str]:
    out: list[str] = []
    pot = world.get("pot")
    if pot.meters["heat"] < THRESHOLD:
        return out
    sig = ("simmer",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["simmering"] += 1
    pot.memes["calm"] += 1
    out.append("The soup began to simmer, and the kitchen smelled soft and sweet.")
    return out


def _r_magic_glow(world: World) -> list[str]:
    out: list[str] = []
    charm = world.get("charm")
    if charm.meters["used"] < THRESHOLD:
        return out
    sig = ("magic_glow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl = world.get("bowl")
    bowl.meters["glow"] += 1
    world.get("child").memes["wonder"] += 1
    out.append("A little gold glow settled over the bowl like moonlight on a pond.")
    return out


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    note = world.get("note")
    if note.meters["mystery"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["suspense"] += 1
    world.get("guardian").memes["concern"] += 1
    out.append("For a moment, nobody knew where the missing spice had gone.")
    return out


CAUSAL_RULES = [
    Rule("simmer", _r_simmer),
    Rule("magic_glow", _r_magic_glow),
    Rule("suspense", _r_suspense),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cozy magical kitchen storyworld.")
    ap.add_argument("--theme", choices=["kitchen", "garden"], default="kitchen")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    ap.add_argument("--child", choices=["Mina", "Iris", "Noah", "June"])
    ap.add_argument("--guardian", choices=["grandma", "grandpa", "mom", "dad"])
    return ap


@dataclass
@dataclass
class StoryParams:
    theme: str
    child: str
    guardian: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "kitchen": {
        "room": "the small sunny kitchen",
        "surface": "the wooden table",
        "light": "the window light",
    },
    "garden": {
        "room": "the tiny garden kitchen",
        "surface": "the stone table",
        "light": "the lantern light",
    },
}

INGREDIENTS = {
    "carrot": Ingredient("carrot", "a carrot", "vegetable", warm=True, calm=True),
    "pea": Ingredient("pea", "peas", "vegetable", calm=True),
    "broth": Ingredient("broth", "broth", "liquid", warm=True, calm=True),
    "herb": Ingredient("herb", "a pinch of herb", "seasoning", calm=True),
}

CHARMS = {
    "shimmer": MagicCharm("shimmer", "shimmer charm", "twinkle, twinkle", "soft light", 2, gentle=True),
    "abominate": MagicCharm("abominate", "old hush-word", "abominate the sour", "push away sourness", 1, gentle=True),
}

def valid_combos() -> list[tuple[str]]:
    return [(t,) for t in SETTINGS]


def asp_facts() -> str:
    import asp
    lines = []
    for k in SETTINGS:
        lines.append(asp.fact("theme", k))
    for i in INGREDIENTS:
        lines.append(asp.fact("ingredient", i))
    for c in CHARMS:
        lines.append(asp.fact("charm", c))
    return "\n".join(lines)


ASP_RULES = r"""
valid(T) :- theme(T).
"""


def asp_program(extra: str = "", show: str = "#show valid/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP/Python combo gate.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    with contextlib.redirect_stdout(io.StringIO()):
        emit(sample)
    if not sample.story.strip():
        print("SMOKE TEST FAILED: empty story.")
        rc = 1
    if rc == 0:
        print("OK: ASP parity and story smoke test passed.")
    return rc


def _pick_name(rng: random.Random, choices: list[str]) -> str:
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    theme = args.theme or rng.choice(list(SETTINGS))
    child = args.child or _pick_name(rng, ["Mina", "Iris", "Noah", "June"])
    guardian = args.guardian or rng.choice(["grandma", "grandpa", "mom", "dad"])
    return StoryParams(theme=theme, child=child, guardian=guardian)


def tell(params: StoryParams) -> World:
    w = World()
    room = SETTINGS[params.theme]
    child = w.add(Entity("child", "character", "child", params.child, role="child"))
    guardian = w.add(Entity("guardian", "character", params.guardian, f"the {params.guardian}", role="guardian"))
    pot = w.add(Entity("pot", "thing", "pot", "the soup pot"))
    bowl = w.add(Entity("bowl", "thing", "bowl", "the little bowl"))
    note = w.add(Entity("note", "thing", "note", "the missing spice note"))

    child.memes["curious"] += 1
    guardian.memes["care"] += 1
    pot.meters["heat"] += 1
    note.meters["mystery"] += 1

    w.say(
        f"On a quiet evening in {room['room']}, {child.id} and {guardian.label_word} "
        f"stood by {room['surface']} and watched supper come together."
    )
    w.say(
        f"{child.id} loved the warm steam and the soft smells, but then {guardian.label_word} "
        f"noticed the note about the missing spice and frowned."
    )

    w.para()
    propagate(w, narrate=True)
    w.say(
        f'"We should determine what happened," {guardian.label_word} said gently, and {child.id} '
        f'held the spoon tighter as the soup kept warming.'
    )

    charm = CHARMS["abominate"]
    bowl.meters["glow"] += 0
    w.para()
    w.say(
        f"{child.id} remembered an old kitchen charm: \"{charm.phrase}.\" "
        f"{guardian.label_word} smiled, because the word meant to send away the sourness, not the love."
    )
    w.get("charm") if False else None
    w.get("pot").meters["heat"] += 1
    w.get("pot").meters["heat"] += 0
    w.get("pot").meters["heat"] = max(w.get("pot").meters["heat"], 1.0)
    w.get("charm") if "charm" in w.entities else None

    charm_ent = w.add(Entity("charm", "thing", charm.label, charm.phrase))
    charm_ent.meters["used"] += 1
    propagate(w, narrate=True)

    w.para()
    w.say(
        f"Then {guardian.label_word} stirred in the last herb, and the pot could simmer "
        f"slowly while the little gold glow sat safe over the bowl."
    )
    child.memes["relief"] += 1
    guardian.memes["relief"] += 1
    child.memes["love"] += 1
    guardian.memes["love"] += 1
    w.say(
        f"When at last they sat down together, {child.id} had warm soup, {guardian.label_word} had a calm smile, "
        f"and the whole kitchen felt like a hug."
    )
    w.facts.update(params=params, child=child, guardian=guardian, room=room, charm=charm, pot=pot, bowl=bowl, note=note, theme=params.theme)
    return w


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a heartwarming magical kitchen story that includes the word abominate and ends with a simmering pot.",
        f"Tell a suspenseful but cozy story about {p.child} and {p.guardian} who must determine what is wrong with the soup.",
        f"Write a short child-friendly story where a tiny magic charm helps a family simmer soup safely and kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {guardian.label_word}, who are making supper together."),
        ("What did they need to determine?", f"They needed to determine why the soup felt strange and what was missing from the kitchen note."),
        ("What did the old word abominate mean in the story?", f"It meant to send away the sourness. It was a gentle old kitchen word, not a mean feeling."),
        ("How did the story end?", f"It ended with the pot simmering quietly, the bowl glowing softly, and both of them sitting down to warm soup together."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does simmer mean?", "When food simmers, it cooks gently with small bubbles and low heat."),
        ("What is a charm in a magic story?", "A charm is a special word or object in a magic story that can help make something happen."),
        ("Why is a warm meal comforting?", "A warm meal can help people feel cozy, safe, and cared for, especially when they share it together."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:7}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "Mina", "grandma"),
    StoryParams("kitchen", "Iris", "mom"),
    StoryParams("garden", "Noah", "dad"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible stories: {asp_valid_combos()}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def __main__() -> None:
    main()


if __name__ == "__main__":
    main()
