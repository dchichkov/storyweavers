#!/usr/bin/env python3
"""
storyworlds/worlds/spike_succession_conflict_rhyming_story.py
==============================================================

A small story world for a rhyming, child-facing tale about succession, a
careful turn-taking order, and a prickly little spike that causes conflict.

The world is deliberately tiny:
- a handful of characters
- one shared object passed in succession
- one "spike" hazard that creates tension
- a gentle resolution that restores order

The story engine simulates state changes, then turns those changes into prose,
questions, and a small ASP twin for parity checking.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    owner: Optional[str] = None
    held_by: Optional[str] = None
    turned: bool = False
    dangerous: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wear": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "conflict": 0.0, "patience": 0.0}


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Hero:
    name: str
    species: str
    trait: str


@dataclass
class ObjectCfg:
    label: str
    phrase: str
    spike: bool = False


@dataclass
class StoryParams:
    place: str
    hero1: str
    hero2: str
    hero3: str
    object: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}
        self.turn_order: list[str] = []
        self.next_index: int = 0
        self.spike_touched: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.turn_order = list(self.turn_order)
        clone.next_index = self.next_index
        clone.spike_touched = self.spike_touched
        return clone


SETTINGS = {
    "porch": Setting(place="the porch", detail="The porch was bright with bunting and a warm breeze."),
    "stage": Setting(place="the small stage", detail="The small stage had a painted sign and a neat line of chairs."),
    "yard": Setting(place="the yard", detail="The yard was open and sunny, with a ribbon path to follow."),
}

HEROES = {
    "pip": Hero(name="Pip", species="mouse", trait="spry"),
    "milo": Hero(name="Milo", species="fox", trait="cheery"),
    "tess": Hero(name="Tess", species="rabbit", trait="brave"),
    "nori": Hero(name="Nori", species="duck", trait="bright"),
}

OBJECTS = {
    "crown": ObjectCfg(label="crown", phrase="a shiny little crown", spike=True),
    "wand": ObjectCfg(label="wand", phrase="a ribbon wand", spike=False),
    "bell": ObjectCfg(label="bell", phrase="a tiny brass bell", spike=False),
}

PLACES = list(SETTINGS.keys())
HERO_NAMES = list(HEROES.keys())
OBJECT_NAMES = list(OBJECTS.keys())
TRAITS = ["spry", "cheery", "brave", "bright"]


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} and {b}"


def _rhyming_intro(hero1: Entity, hero2: Entity, hero3: Entity, obj: Entity, world: World) -> None:
    world.say(
        f"At {world.setting.place}, {hero1.label}, {hero2.label}, and {hero3.label} came to play;"
    )
    world.say(
        f"They loved to pass {obj.phrase} in a merry, rhyming way."
    )
    world.say(world.setting.detail)
    world.say(
        f"{hero1.label} would grin, {hero2.label} would spin, and {hero3.label} would sway."
    )


def _predict_conflict(world: World, obj: Entity) -> bool:
    return obj.dangerous


def _start_turns(world: World, order: list[str]) -> None:
    world.turn_order = order
    world.next_index = 0


def _next_character(world: World) -> Entity:
    return world.get(world.turn_order[world.next_index % len(world.turn_order)])


def _advance_turn(world: World) -> None:
    world.next_index = (world.next_index + 1) % len(world.turn_order)


def _attempt_grab(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["patience"] += 0.25
    hero.memes["conflict"] += 1.0
    obj.meters["wear"] += 1.0
    world.spike_touched = True


def _conflict_beat(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["conflict"] += 1.0
    world.say(
        f"But when {obj.label} came round, {hero.label} rushed in with a flurry and a fray."
    )
    world.say(
        f"A little spike on {obj.label} gave a prickly poke, and the bright game went gray."
    )
    world.say(
        f"{hero.label} frowned, and the others frowned too, because no one liked that way."
    )


def _mentor_fix(world: World, obj: Entity, heroes: list[Entity]) -> None:
    lead = heroes[0]
    second = heroes[1]
    third = heroes[2]
    for h in heroes:
        h.memes["conflict"] = max(0.0, h.memes["conflict"] - 1.0)
        h.memes["joy"] += 1.0
        h.memes["patience"] += 1.0
    if obj.dangerous:
        obj.dangerous = False
    world.say(
        f"Then {lead.label} said, 'Let's use our turns in order, neat and fine.'"
    )
    world.say(
        f"'First {lead.label}, then {second.label}, then {third.label}—that's a kinder line.'"
    )
    world.say(
        f"They wrapped the spike with soft blue tape, so it could not scratch or shine."
    )
    world.say(
        f"Now each could take a proper turn, and the song returned in time."
    )


def tell(setting: Setting, hero_cfgs: list[Hero], obj_cfg: ObjectCfg) -> World:
    world = World(setting)
    heroes = []
    for i, cfg in enumerate(hero_cfgs, 1):
        heroes.append(
            world.add(
                Entity(
                    id=f"hero{i}",
                    kind="character",
                    type=cfg.species,
                    label=cfg.name,
                )
            )
        )
    obj = world.add(
        Entity(
            id="shared",
            type=obj_cfg.label,
            label=obj_cfg.label,
            phrase=obj_cfg.phrase,
            dangerous=obj_cfg.spike,
        )
    )

    _rhyming_intro(heroes[0], heroes[1], heroes[2], obj, world)

    world.para()
    order = [h.id for h in heroes]
    _start_turns(world, order)
    world.say(
        f"They agreed on succession: {heroes[0].label} first, then {heroes[1].label}, then {heroes[2].label}."
    )
    world.say(
        f"That plan was smooth as syrup, a careful little line of delight."
    )

    current = _next_character(world)
    current.memes["joy"] += 1.0
    world.say(
        f"{current.label} took the first turn and passed {obj.label} with a happy little sight."
    )
    _advance_turn(world)

    world.para()
    if _predict_conflict(world, obj):
        troublesome = _next_character(world)
        _attempt_grab(world, troublesome, obj)
        _conflict_beat(world, troublesome, obj)
        _mentor_fix(world, obj, heroes)
    else:
        world.say("The turns kept moving in a tidy ring, and nothing turned unkind.")

    world.facts.update(
        setting=setting,
        heroes=heroes,
        obj=obj,
        order=order,
        conflict=any(h.memes["conflict"] >= THRESHOLD for h in heroes),
        resolved=not obj.dangerous,
    )
    return world


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for obj in OBJECTS:
            if obj == "crown":
                combos.append((place, obj))
    return combos


def explain_rejection(place: str, obj: str) -> str:
    return f"(No story: the chosen object '{obj}' does not create the spike-and-succession conflict we need.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A rhyming story world about succession, a spike, and a small conflict."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--name3")
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
    if args.object and args.object != "crown":
        raise StoryError(explain_rejection(args.place or "", args.object))
    place = args.place or rng.choice(list(SETTINGS))
    obj = args.object or "crown"
    n1 = args.name1 or rng.choice(list(HEROES))
    n2 = args.name2 or rng.choice([n for n in HEROES if n != n1])
    n3 = args.name3 or rng.choice([n for n in HEROES if n not in {n1, n2}])
    return StoryParams(place=place, hero1=n1, hero2=n2, hero3=n3, object=obj)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    heroes = f["heroes"]
    obj = f["obj"]
    return [
        f'Write a short rhyming story for a young child about a {obj.label}, a turn order, and a small conflict.',
        f"Tell a gentle story where {heroes[0].label}, {heroes[1].label}, and {heroes[2].label} share {obj.phrase} in succession.",
        f"Write a simple rhyme in which a spike causes trouble, then the friends fix it and take turns again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    heroes = f["heroes"]
    obj = f["obj"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Where did {heroes[0].label} and the others play?",
            answer=f"They played at {place}, where they shared {obj.phrase} in a neat succession.",
        ),
        QAItem(
            question=f"What caused the little conflict in the story?",
            answer=f"The conflict came from a spike on the {obj.label}, which made the game prickly and upset the turns.",
        ),
        QAItem(
            question=f"How did the friends solve the problem?",
            answer="They wrapped the spike with soft tape and kept their turns in order, so everyone could play safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is succession?",
            answer="Succession means things happen in an order, one after another, instead of all at once.",
        ),
        QAItem(
            question="What is a spike?",
            answer="A spike is a sharp point, so people should handle it carefully.",
        ),
        QAItem(
            question="Why do friends take turns?",
            answer="Friends take turns so play stays fair and everyone gets a chance.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    for e in world.entities.values():
        lines.append(
            f"  {e.id:8} ({e.kind:9}) label={e.label!r} dangerous={e.dangerous} "
            f"meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    lines.append(f"  turn_order={world.turn_order} next_index={world.next_index} spike_touched={world.spike_touched}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place, Obj) :- setting(Place), object(Obj), needs_conflict(Obj).

needs_conflict(crown).

risky_spike(crown).
succession_story(Place) :- setting(Place).

#show valid_story/2.
#show succession_story/1.
#show risky_spike/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
        if OBJECTS[o].spike:
            lines.append(asp.fact("has_spike", o))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2.\n#show succession_story/1.\n#show risky_spike/1."))
    valid = set(asp.atoms(model, "valid_story"))
    succ = set(asp.atoms(model, "succession_story"))
    risky = set(asp.atoms(model, "risky_spike"))

    py_valid = set((p, "crown") for p in SETTINGS)
    py_succ = set((p,) for p in SETTINGS)
    py_risky = {("crown",)}

    if valid != py_valid or succ != py_succ or risky != py_risky:
        print("MISMATCH between ASP and Python")
        print("ASP valid:", sorted(valid))
        print("PY valid :", sorted(py_valid))
        print("ASP succ :", sorted(succ))
        print("PY succ  :", sorted(py_succ))
        print("ASP risk :", sorted(risky))
        print("PY risk  :", sorted(py_risky))
        return 1

    print(f"OK: ASP matches Python across {len(py_valid)} valid stories.")
    return 0


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    hero_cfgs = [HEROES[params.hero1], HEROES[params.hero2], HEROES[params.hero3]]
    obj_cfg = OBJECTS[params.object]
    world = tell(setting, hero_cfgs, obj_cfg)
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


CURATED = [
    StoryParams(place="porch", hero1="pip", hero2="milo", hero3="tess", object="crown"),
    StoryParams(place="stage", hero1="nori", hero2="pip", hero3="milo", object="crown"),
    StoryParams(place="yard", hero1="tess", hero2="nori", hero3="pip", object="crown"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2.\n#show succession_story/1.\n#show risky_spike/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show valid_story/2.\n#show succession_story/1.\n#show risky_spike/1."))
        print("valid stories:")
        for atom in sorted(set(asp.atoms(model, "valid_story"))):
            print(" ", atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.place} / {p.object}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
