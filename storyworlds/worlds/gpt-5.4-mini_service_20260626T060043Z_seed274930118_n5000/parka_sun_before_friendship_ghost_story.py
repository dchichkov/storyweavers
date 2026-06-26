#!/usr/bin/env python3
"""
A small ghost-story world about friendship, a parka, and the sun before sunrise.

A child and a friendly ghost meet in the park before the sun gets high.
The child has a warm parka. The ghost is shy and fades in bright sunlight.
They make a quiet plan, keep each other safe, and share one brave morning.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        for k in ("warmth", "light", "fade", "bravery", "joy", "friendship", "fear"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the park"
    before_sun: bool = True


@dataclass
class StoryParams:
    setting: str
    hero_name: str
    hero_type: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: callable


def _r_sun_warns(world: World) -> list[str]:
    out: list[str] = []
    sun = world.get("sun")
    ghost = world.get("ghost")
    if sun.meters["light"] < THRESHOLD:
        return out
    if ghost.worn_by and ghost.worn_by in world.entities:
        hero = world.get(ghost.worn_by)
        if "parka" in [e.id for e in world.entities.values() if e.worn_by == hero.id]:
            return out
    sig = ("fade", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["fear"] += 1
    ghost.meters["fade"] += 1
    out.append(f"The bright sun made {ghost.label} look thin and pale.")
    return out


RULES = [Rule("sun_warns", _r_sun_warns)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "park": Setting(place="the park", before_sun=True),
}

GHOSTS = {
    "pale": {"phrase": "a shy little ghost", "label": "a shy little ghost"},
}

PARKA = {
    "parka": {
        "label": "parka",
        "phrase": "a soft blue parka",
        "covers": {"chest", "arms"},
    }
}


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid_story/2.
#show sun_problem/2.

sun_problem(S, G) :- sun_high(S), ghost(G), not protected(G).
valid_story(P, G) :- place(P), ghost(G), sun_high(before), has_friendship(P, G).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        if s.before_sun:
            lines.append(asp.fact("sun_high", "before"))
    for gid in GHOSTS:
        lines.append(asp.fact("ghost", gid))
    lines.append(asp.fact("has_friendship", "park", "ghost"))
    lines.append(asp.fact("protected", "ghost"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_story_check() -> bool:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    atoms = set(asp.atoms(model, "valid_story"))
    return ("park", "ghost") in atoms


def asp_verify() -> int:
    py = bool(valid_combos())
    asp_ok = asp_story_check()
    if py == asp_ok:
        print("OK: ASP/Python parity matches.")
        return 0
    print(f"MISMATCH: python={py} asp={asp_ok}")
    return 1


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [("park", "pale", "parka")]


def select_gear() -> dict:
    return PARKA["parka"]


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label=params.ghost_name))
    sun = world.add(Entity(id="sun", kind="thing", type="sun", label="the sun"))
    parka = world.add(Entity(
        id="parka",
        kind="thing",
        type="clothes",
        label="parka",
        phrase="a soft blue parka",
        owner=hero.id,
        protective=True,
        covers={"chest", "arms"},
    ))

    world.say(f"Before the sun climbed over {world.setting.place}, {hero.label} walked there in a soft blue parka.")
    world.say(f"At the gate, {hero.label} found {ghost.label}, a shy little ghost who liked quiet mornings.")
    hero.memes["joy"] += 1
    ghost.memes["joy"] += 1
    hero.memes["friendship"] += 1
    ghost.memes["friendship"] += 1
    world.say(f"They became friends right away, because both of them liked the hush before the day got loud.")

    world.para()
    world.say(f"{hero.label} wanted to stay in the park and show {ghost.label} the swings before the sun got bright.")
    ghost.memes["fear"] += 1
    world.say(f"But {ghost.label} looked at the sky and whispered that bright sun made ghosts feel thin and worried.")

    sun.meters["light"] += 1
    if hero.id not in world.fired:
        propagate(world, narrate=True)

    world.para()
    hero.memes["bravery"] += 1
    world.say(f"So {hero.label} lifted the parka and held it like a small shade over {ghost.label}.")
    ghost.memes["fear"] = 0.0
    ghost.meters["fade"] = 0.0
    ghost.memes["joy"] += 1
    hero.memes["friendship"] += 1
    world.say(f"With the parka keeping the glare off, {ghost.label} drifted through the grass without fading.")
    world.say(f"The two friends laughed, watched the sun turn gold, and left the park together before noon.")

    world.facts.update(
        hero=hero,
        ghost=ghost,
        sun=sun,
        parka=parka,
        setting=params.setting,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    return [
        f"Write a gentle ghost story about friendship before the sun gets high in the park.",
        f"Tell a child-sized story where {hero.label} meets {ghost.label} and a parka helps them stay safe before sunrise.",
        f"Write a quiet morning story with a sun, a parka, and two friends who choose each other first.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    ghost = world.facts["ghost"]
    return [
        QAItem(
            question=f"Who became friends before the sun got bright?",
            answer=f"{hero.label} and {ghost.label} became friends before the sun got bright in the park.",
        ),
        QAItem(
            question=f"Why did {ghost.label} worry about staying outside?",
            answer=f"{ghost.label} worried because bright sunlight made ghosts feel thin and scared.",
        ),
        QAItem(
            question=f"How did {hero.label} help {ghost.label} at the end?",
            answer=f"{hero.label} held up the parka like a small shade so {ghost.label} could stay safe until they went home.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a parka?",
        answer="A parka is a warm coat that helps keep a person cozy in chilly weather.",
    ),
    QAItem(
        question="Why do some ghosts hide from the sun in stories?",
        answer="Some ghost stories say ghosts feel weak or see-through in strong sunlight, so they prefer shade or twilight.",
    ),
    QAItem(
        question="What is friendship?",
        answer="Friendship is when people care about each other, help each other, and like being together.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world about friendship, a parka, and the sun before sunrise.")
    ap.add_argument("--setting", choices=SETTINGS.keys(), default="park")
    ap.add_argument("--name", default="Mina")
    ap.add_argument("--ghost", default="Pip")
    ap.add_argument("--gender", choices=["girl", "boy"], default="girl")
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
    return StoryParams(
        setting=args.setting,
        hero_name=args.name or rng.choice(["Mina", "Lena", "Noor"]),
        hero_type=args.gender or "girl",
        ghost_name=args.ghost or rng.choice(["Pip", "Wisp", "Murmur"]),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    rng = random.Random(base_seed)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(setting="park", hero_name="Mina", hero_type="girl", ghost_name="Pip"))]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i + 1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
