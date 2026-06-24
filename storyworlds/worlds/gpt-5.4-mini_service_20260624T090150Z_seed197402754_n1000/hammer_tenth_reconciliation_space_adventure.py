#!/usr/bin/env python3
"""
A tiny space-adventure storyworld about a child, a damaged tool, a tense flight
decision, and a reconciliation that makes the mission possible again.

Seed tale:
---
On the tenth day of practice, Mira loved fixing the little ship with her
bright hammer. But during a rushed launch, she and her brother Rowan argued
about the order of the repairs. The hammer slipped, a panel bent, and the ship
could not safely fly.

Mira felt sad. Rowan felt sorry. They talked, apologized, and shared the work.
Together they straightened the panel, tightened the bolts, and launched on the
tenth mission at last.

The world models:
- physical meters: damage, repair, readiness, distance
- emotional memes: worry, pride, apology, trust, relief, reconciliation
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Scene:
    place: str = "the dock"
    route: str = "the star lane"
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    mess: str
    fix: str
    can_repair: bool = True


@dataclass
class StoryParams:
    place: str
    tool: str
    hero: str
    sibling: str
    ship: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("damage", 0) < THRESHOLD:
            continue
        if ent.id == "ship" and ("damage_seen", ent.id) not in world.fired:
            world.fired.add(("damage_seen", ent.id))
            out.append("The ship shuddered and could not safely launch.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    ship = world.entities.get("ship")
    if not ship:
        return out
    if ship.meters.get("repair", 0) >= THRESHOLD and ("repair_done",) not in world.fired:
        world.fired.add(("repair_done",))
        ship.meters["damage"] = 0
        ship.meters["ready"] = 1
        out.append("The bent panel was straight again, and the ship was ready.")
    return out


def _r_reconciliation(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    sibling = world.entities.get("sibling")
    if not hero or not sibling:
        return out
    if hero.memes.get("apology", 0) >= THRESHOLD and sibling.memes.get("apology", 0) >= THRESHOLD:
        if hero.memes.get("reconciliation", 0) < THRESHOLD:
            hero.memes["reconciliation"] = 1
            sibling.memes["reconciliation"] = 1
            hero.memes["trust"] = hero.memes.get("trust", 0) + 1
            sibling.memes["trust"] = sibling.memes.get("trust", 0) + 1
            out.append("They forgave each other and worked together again.")
    return out


RULES = [_r_damage, _r_repair, _r_reconciliation]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SCENE = Scene(
    place="the dock",
    route="the star lane",
    affords={"repair", "launch"},
)

TOOLS = {
    "hammer": Tool(
        id="hammer",
        label="hammer",
        phrase="a bright little hammer",
        mess="dent",
        fix="straighten",
    ),
}

SHIP_NAMES = {
    "sprout": "the Sprout",
    "comet": "the Comet",
    "lantern": "the Lantern",
}


KNOWLEDGE = {
    "hammer": [
        ("What is a hammer for?", "A hammer is a tool used to tap, fix, and build things."),
    ],
    "tenth": [
        ("What does tenth mean?", "Tenth means number ten in order, after ninth and before eleventh."),
    ],
    "space": [
        ("What is space?", "Space is the very big region beyond Earth where stars, planets, and ships travel."),
    ],
    "ship": [
        ("What is a spaceship?", "A spaceship is a vehicle made to travel in space."),
    ],
    "dock": [
        ("What is a dock?", "A dock is a place where ships stop, load, and get ready to leave."),
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation means making up after a disagreement and becoming friendly again."),
    ],
}


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("scene", "dock"))
    lines.append(asp.fact("affords", "dock", "repair"))
    lines.append(asp.fact("affords", "dock", "launch"))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("kind", tid, tool.mess))
        lines.append(asp.fact("fixes", tid, tool.fix))
    for s in SHIP_NAMES:
        lines.append(asp.fact("ship", s))
    lines.append(asp.fact("number_word", "tenth"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(dock, hammer, tenth) :- scene(dock), tool(hammer), number_word(tenth).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld about a hammer, the tenth mission, and reconciliation.")
    ap.add_argument("--place", choices=["dock"])
    ap.add_argument("--tool", choices=list(TOOLS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place != "dock":
        raise StoryError("This storyworld only supports the dock setting.")
    tool = args.tool or "hammer"
    hero = "Mira"
    sibling = "Rowan"
    ship = rng.choice(list(SHIP_NAMES))
    return StoryParams(place="dock", tool=tool, hero=hero, sibling=sibling, ship=ship)


def reasonableness_check(params: StoryParams) -> None:
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool choice.")
    if params.place != "dock":
        raise StoryError("The mission only makes sense at the dock.")
    if params.ship not in SHIP_NAMES:
        raise StoryError("Unknown ship choice.")


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    world = World(SCENE)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero))
    sibling = world.add(Entity(id="sibling", kind="character", type="boy", label=params.sibling))
    ship = world.add(Entity(id="ship", kind="thing", type="ship", label=SHIP_NAMES[params.ship], phrase=SHIP_NAMES[params.ship]))
    tool = TOOLS[params.tool]
    hammer = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    tenth = world.add(Entity(id="tenth", kind="thing", type="number", label="tenth"))
    ship.meters["damage"] = 1
    ship.meters["ready"] = 0
    hero.memes["pride"] = 1
    sibling.memes["worry"] = 1

    world.say(f"On the tenth day of practice, {hero.label} carried {hammer.phrase} to {world.scene.place}.")
    world.say(f"{hero.label} loved fixing {ship.label} with {hammer.label}, because every tap felt like a step toward the stars.")
    world.para()
    world.say(f"At the dock, {hero.label} wanted to launch {ship.label} right away, but {sibling.label} said the panel still looked bent.")
    hero.memes["frustration"] = 1
    sibling.memes["worry"] += 1
    ship.meters["damage"] += 1
    world.say(f"The rushed push made the wobbling panel worse, and the ship was not safe for the star lane.")
    propagate(world, narrate=True)
    world.para()
    world.say(f"Then {hero.label} and {sibling.label} looked at each other and said sorry.")
    hero.memes["apology"] = 1
    sibling.memes["apology"] = 1
    propagate(world, narrate=True)
    world.say(f"They shared the work, used the hammer carefully, and straightened the bent panel together.")
    ship.meters["repair"] = 1
    propagate(world, narrate=True)
    world.say(f"At last, the {params.ship} was ready for the tenth mission, and both children smiled as it slid into the sky.")
    world.facts.update(hero=hero, sibling=sibling, ship=ship, tool=hammer, tenth=tenth, params=params)
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    return [
        "Write a short space-adventure story for a young child about a hammer, a broken ship, and two children making up.",
        f"Tell a gentle story where {hero.label} and {sibling.label} disagree on the tenth launch, then reconcile and fix the ship.",
        "Write a simple story about space travel that ends with apology, teamwork, and a ship ready to fly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sibling = f["sibling"]
    ship = f["ship"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.label} and {sibling.label}, who were getting {ship.label} ready for the tenth mission.",
        ),
        QAItem(
            question=f"Why could {ship.label} not launch at first?",
            answer=f"{ship.label} could not launch at first because its panel was bent and the ship was not safe for the star lane.",
        ),
        QAItem(
            question=f"What fixed the problem after the argument?",
            answer=f"Apology and teamwork fixed the problem. {hero.label} and {sibling.label} reconciled, used the hammer carefully, and straightened the panel together.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"At the end, {ship.label} was ready, and it launched on the tenth mission while the children smiled.",
        ),
    ]


def world_qa(_: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["hammer", "tenth", "space", "ship", "dock", "reconciliation"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [("dock", "hammer", "tenth")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(asp_valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos().")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, tool, token) combos:\n")
        for item in combos:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place="dock", tool="hammer", hero="Mira", sibling="Rowan", ship=s, seed=base_seed)) for s in SHIP_NAMES]
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
