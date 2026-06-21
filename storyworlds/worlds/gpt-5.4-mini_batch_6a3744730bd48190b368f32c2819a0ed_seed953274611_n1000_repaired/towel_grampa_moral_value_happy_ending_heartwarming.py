#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/towel_grampa_moral_value_happy_ending_heartwarming.py
=====================================================================================

A tiny, heartwarming storyworld about a child, a towel, and a grampa.

Premise
-------
A child wants to use a favorite towel for play, but learns a kinder moral:
asking first, helping others, and sharing carefully can make everyone happier.

This world is intentionally small and classical:
- typed entities with meters and memes
- a forward-chained causal model
- a reasonableness gate
- an inline ASP twin
- three QA sets grounded in world state

Seed words: towel, grampa
Style: heartwarming
Features: moral value, happy ending
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

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "grampa"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return "grampa" if self.type == "grampa" else self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Place:
    id: str
    label: str
    warmth: int = 0
    cozy: bool = True
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Towel:
    id: str
    label: str
    phrase: str
    special: bool = False
    absorbency: int = 1
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class Action:
    id: str
    verb: str
    need: str
    moral: str
    kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    g = world.entities.get("grampa")
    if not g or g.meters["chilly"] < THRESHOLD:
        return out
    sig = ("cold",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    g.memes["sad"] += 1
    out.append("__cold__")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    c = world.entities.get("child")
    g = world.entities.get("grampa")
    towel = world.entities.get("towel")
    if not (c and g and towel):
        return out
    if c.memes["kindness"] < THRESHOLD or towel.meters["dry"] < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    g.meters["warmth"] += 1
    g.memes["grateful"] += 1
    c.memes["pride"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES = [Rule("cold", "physical", _r_cold), Rule("help", "social", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_action(action: Action, towel: Towel) -> bool:
    return action.kind in towel.tags


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for action in ACTIONS:
            if choose_action(ACTIONS[action], TOWELS["towel"]):
                combos.append((place, action))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming towel-and-grampa storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, action=action, child_name=name, child_gender=gender)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    grampa = world.add(Entity(id="grampa", kind="character", type="grampa", role="elder", label="grampa"))
    towel = world.add(Entity(id="towel", kind="thing", type="towel", label="the towel"))
    place = world.add(Entity(id="place", kind="thing", type=params.place, label=PLACES[params.place].label))
    act = ACTIONS[params.action]

    child.memes["curious"] += 1
    child.memes["love"] += 1

    world.say(
        f"On a soft afternoon, {child.id} and {grampa.label_word} sat in {place.label}. "
        f"{grampa.id} had {towel.label} folded neatly beside him."
    )
    world.say(
        f"{child.id} wanted to {act.verb}, because {act.need} felt like fun and the day was cozy."
    )

    world.para()
    if params.action == "playcape":
        child.memes["playful"] += 1
        child.meters["tug"] += 1
        towel.meters["worn"] += 1
        world.say(f'{child.id} wrapped {towel.phrase} around {child.pronoun("possessive")} shoulders and giggled.')
        world.say(f'But {grampa.id} smiled and said, "{act.moral}"')
        world.para()
        child.memes["kindness"] += 1
        towel.meters["dry"] += 1
        grampa.meters["chilly"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{child.id} tucked {towel.phrase} around {grampa.id} instead, so {grampa.pronoun()} could stay warm.'
        )
        world.say(
            f'{grampa.id} gave a happy sigh, and {child.id} felt proud for choosing the kinder thing.'
        )
    else:
        child.memes["kindness"] += 1
        towel.meters["dry"] += 1
        grampa.meters["warmth"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{child.id} brought {towel.phrase} to {grampa.id} first, and {grampa.pronoun()} used it with a thankful smile.'
        )
        world.say(
            f'Then {child.id} got to use it too, and the whole room felt warmer for having been shared.'
        )

    world.para()
    world.say(
        f'At the end, {child.id} learned that asking first and helping others can turn a small choice into a happy one.'
    )
    world.say(
        f'{grampa.id} patted {child.id} on the head, and the towel stayed soft, dry, and ready for tomorrow.'
    )

    world.facts.update(
        child=child,
        grampa=grampa,
        towel=towel,
        place=place,
        action=act,
        outcome="happy",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, g = f["child"], f["grampa"]
    act = f["action"]
    return [
        f'Write a heartwarming story for a young child that includes the words "towel" and "grampa".',
        f"Tell a gentle moral story where {c.id} learns to ask before using the towel and helps {g.id}.",
        f'Write a happy-ending story about kindness and sharing that uses the phrase "{act.moral}".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    c, g, towel = f["child"], f["grampa"], f["towel"]
    return [
        (
            "Who are the story about?",
            f"It is about {c.id} and {g.id}. The story is small and cozy, and the towel is part of the choice they make together.",
        ),
        (
            "What did the child learn?",
            f"{c.id} learned to ask first and help others instead of grabbing what looked fun. That made the moment kinder for {g.id}, too.",
        ),
        (
            "How did the story end?",
            f"It ended happily, with {g.id} feeling warm and thankful and {c.id} feeling proud. The towel stayed dry and ready to be shared again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        (
            "What is a towel?",
            "A towel is a cloth used for drying hands, hair, or skin. It can also be folded up neatly after someone is done with it.",
        ),
        (
            "Who is a grampa?",
            "A grampa is a child's grandfather. In stories, a grampa is often gentle, wise, and happy to help.",
        ),
        (
            "Why is asking first kind?",
            "Asking first shows respect for other people's things and feelings. It helps everyone stay calm and happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.cozy:
            lines.append(asp.fact("cozy", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("kind", aid, a.kind))
    lines.append(asp.fact("towel", "towel"))
    lines.append(asp.fact("grampa", "grampa"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, A) :- place(P), action(A), kind(A, K), towel_kind(K).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, action=None, name=None, gender=None), random.Random(0)))
        _ = sample.story
    except Exception as err:
        print(f"FAIL: smoke generate crashed: {err}")
        return 1
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches.")
    else:
        print("FAIL: ASP parity mismatch.")
        rc = 1
    try:
        # normal generate/emit smoke test
        emit(sample, trace=False, qa=False)
    except Exception as err:
        print(f"FAIL: emit crashed: {err}")
        rc = 1
    return rc


PLACES = {
    "kitchen": Place(id="kitchen", label="the kitchen"),
    "porch": Place(id="porch", label="the porch"),
    "garden": Place(id="garden", label="the garden"),
}

TOWELS = {
    "towel": Towel(id="towel", label="towel", phrase="the towel", special=True, absorbency=2, tags={"warmth", "sharing"}),
}

ACTIONS = {
    "dry_grampa": Action(id="dry_grampa", verb="dry Grampa's hands", need="his hands were damp from the cool air", moral="A kind choice can warm a cold moment.", kind="warmth", tags={"warmth"}),
    "share_towel": Action(id="share_towel", verb="share the towel", need="sharing felt good", moral="Sharing makes a small thing feel bigger.", kind="sharing", tags={"sharing"}),
    "playcape": Action(id="playcape", verb="wear the towel like a cape", need="pretend play felt exciting", moral="Fun is better when we respect other people's things.", kind="play", tags={"warmth"}),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Noah", "Eli", "Ben", "Sam", "Theo"]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.action not in ACTIONS:
        raise StoryError("invalid params")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        for p, a in combos:
            print(p, a)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(place="kitchen", action="dry_grampa", child_name="Mia", child_gender="girl")),
            generate(StoryParams(place="porch", action="share_towel", child_name="Noah", child_gender="boy")),
            generate(StoryParams(place="garden", action="playcape", child_name="Lily", child_gender="girl")),
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
