#!/usr/bin/env python3
"""
storyworlds/worlds/soggy_wasp_shotgun_mystery_to_solve_curiosity.py
====================================================================

A small spooky-but-child-safe story world about curiosity, a soggy mystery,
and a wasp humming near an old shotgun in a creaky shed.

This world is built to feel like a ghost story: moonlight, whispers, bumps in
the dark, and one brave child who keeps looking until the mystery makes sense.

The source tale premise:
---
A curious child hears strange buzzing in a damp old shed after a storm. The
floor is soggy, an old shotgun is locked away in a dusty case, and everyone
wonders if something spooky is hiding there. The child follows the clues,
finds a wasp nest near a leak in the roof, and helps the grown-up fix the leak
and move the old shotgun safely aside. What felt haunted turns out to have a
simple, real cause.

Causal state updates:
---
    curiosity -> child.memes["curiosity"] += 1
    mystery clue found -> child.memes["curiosity"] += 1 ; clue meter rises
    soggy floor + leak -> floor.wet += 1 ; footprint trail appears
    wasp near light -> buzzing += 1 ; child.startle += 1
    wasp nest removed / leak patched -> spooky tension falls ; relief rises
    safe handling of the old shotgun -> object stays locked, no danger

Narrative instruments:
---
    ghost-story atmosphere: moon, creaks, shadows, hush
    mystery-to-solve spine: clues, false alarms, reveal
    curiosity engine: child keeps asking, looking, and connecting details
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    locked: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old shed"
    indoor: bool = True
    mood: str = "spooky"


@dataclass
class Clue:
    id: str
    label: str
    kind: str
    reveal: str


@dataclass
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = "after the storm"
        self.mystery_level: float = 0.0
        self.solved: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        clone.mystery_level = self.mystery_level
        clone.solved = self.solved
        return clone


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    place: str
    seed: Optional[int] = None


SETTINGS = {
    "shed": Setting(place="the old shed", indoor=True, mood="spooky"),
    "attic": Setting(place="the attic", indoor=True, mood="spooky"),
    "porch": Setting(place="the back porch", indoor=False, mood="foggy"),
}

NAMES_GIRL = ["Mina", "Ivy", "Nora", "Elsie", "June", "Clara"]
NAMES_BOY = ["Finn", "Theo", "Owen", "Milo", "Eli", "Beau"]
PARENTS = ["mother", "father", "grandma", "grandpa"]


def hero_title(hero: Entity) -> str:
    return f"little {next((t for t in hero.traits if t != 'little'), 'curious')} {hero.type}"


def setup_world(setting: Setting, name: str, gender: str, parent_type: str) -> World:
    w = World(setting)
    hero = w.add(Entity(id=name, kind="character", type=gender, traits=["little", "curious", "brave"]))
    parent = w.add(Entity(id="Parent", kind="character", type=parent_type))
    shed = w.add(Entity(id="shed", type="place", label=setting.place))
    old_shotgun = w.add(Entity(id="shotgun", type="object", label="old shotgun", locked=True))
    wasp = w.add(Entity(id="wasp", type="insect", label="wasp"))
    lantern = w.add(Entity(id="lantern", type="object", label="lantern"))
    boots = w.add(Entity(id="boots", type="thing", label="rain boots", worn_by=hero.id))
    leak = w.add(Entity(id="leak", type="thing", label="roof leak"))
    clue = w.add(Entity(id="clue", type="thing", label="wet clue"))
    w.facts.update(hero=hero, parent=parent, shed=shed, shotgun=old_shotgun,
                   wasp=wasp, lantern=lantern, boots=boots, leak=leak, clue=clue)
    return w


def _r_leak(w: World) -> list[str]:
    out = []
    leak = w.get("leak")
    if leak.meters["open"] < THRESHOLD:
        return out
    sig = ("leak",)
    if sig in w.fired:
        return out
    w.fired.add(sig)
    w.mystery_level += 1
    out.append("Cold drops kept falling from the roof, and the floor turned soggy.")
    return out


def _r_wasp_buzz(w: World) -> list[str]:
    out = []
    wasp = w.get("wasp")
    if wasp.meters["buzz"] < THRESHOLD:
        return out
    sig = ("buzz",)
    if sig in w.fired:
        return out
    w.fired.add(sig)
    out.append("A sharp buzz skated through the dark like a tiny ghostly violin.")
    return out


def _r_clue(w: World) -> list[str]:
    out = []
    clue = w.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return out
    sig = ("clue",)
    if sig in w.fired:
        return out
    w.fired.add(sig)
    w.mystery_level += 1
    out.append("The child found a wet clue near the wall.")
    return out


def _r_solved(w: World) -> list[str]:
    out = []
    if w.solved:
        return out
    hero = w.get(w.facts["hero"].id)
    if hero.memes["curiosity"] < 2:
        return out
    if w.get("leak").meters["fixed"] < THRESHOLD:
        return out
    if w.get("wasp").meters["gone"] < THRESHOLD:
        return out
    w.solved = True
    out.append("The spooky sounds were not a ghost at all; they were a leak and a wasp nest.")
    return out


RULES: list[Callable[[World], list[str]]] = [_r_leak, _r_wasp_buzz, _r_clue, _r_solved]


def propagate(w: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(w)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            w.say(s)
    return produced


def inspect(w: World, hero: Entity) -> None:
    hero.memes["curiosity"] += 1
    w.say(f"{hero.id} peered into {w.setting.place} and listened for the strange little sound.")
    w.say(f"{hero.pronoun().capitalize()} was the kind of child who wanted to solve every mystery.")


def discover_soggy_floor(w: World, hero: Entity) -> None:
    w.get("leak").meters["open"] += 1
    w.get("clue").meters["found"] += 1
    hero.memes["curiosity"] += 1
    w.say("The floor felt soggy under the boots, and one shiny puddle pointed toward the corner.")
    w.say("A wet clue glimmered there as if it wanted to be noticed.")


def notice_shotgun(w: World, hero: Entity) -> None:
    shotgun = w.get("shotgun")
    w.say(f"On a shelf sat an old {shotgun.label}, tucked away in a dusty case.")
    w.say(f"{hero.id} did not touch it; {hero.pronoun()} only looked, because safe hands matter.")
    hero.memes["care"] += 1


def hear_wasp(w: World, hero: Entity) -> None:
    wasp = w.get("wasp")
    wasp.meters["buzz"] += 1
    hero.memes["startle"] += 1
    hero.memes["curiosity"] += 1
    w.say("Then the buzzing came again, thin and quick, from somewhere near the rafters.")
    w.say("It sounded spooky for a moment, but the child kept listening instead of running away.")


def solve_mystery(w: World, hero: Entity, parent: Entity) -> None:
    w.get("leak").meters["fixed"] += 1
    w.get("wasp").meters["gone"] += 1
    w.solved = True
    hero.memes["relief"] += 1
    parent.memes["relief"] += 1
    w.say(f"{hero.id} followed the clues and pointed to a crack in the roof.")
    w.say(f"{parent.id} patched the leak, and together they carefully moved the old shotgun farther back and locked its case.")
    w.say("The wasp flew out through a cracked board, and the shed grew quiet at last.")


def ending_image(w: World, hero: Entity, parent: Entity) -> None:
    w.say(f"By the end, the floor was dry, the buzzing was gone, and the dark old room felt ordinary again.")
    w.say(f"{hero.id} smiled up at {parent.id}, glad that curiosity had solved the mystery.")


def tell(setting: Setting, hero_name: str, gender: str, parent_type: str) -> World:
    w = setup_world(setting, hero_name, gender, parent_type)
    hero = w.get(hero_name)
    parent = w.get("Parent")

    inspect(w, hero)
    notice_shotgun(w, hero)

    w.para()
    discover_soggy_floor(w, hero)
    hear_wasp(w, hero)
    propagate(w, narrate=True)

    w.para()
    solve_mystery(w, hero, parent)
    propagate(w, narrate=True)
    ending_image(w, hero, parent)
    propagate(w, narrate=True)

    w.facts.update(setting=setting, solved=w.solved)
    return w


KNOWLEDGE = {
    "soggy": [
        ("What does soggy mean?",
         "Soggy means very wet and soft, like bread left in rain or a floor soaked by a leak.")
    ],
    "wasp": [
        ("What is a wasp?",
         "A wasp is a flying insect that can buzz loudly and sometimes sting if it feels threatened.")
    ],
    "shotgun": [
        ("What is a shotgun?",
         "A shotgun is a kind of gun that only grown-ups should handle very carefully and keep locked away.")
    ],
    "curiosity": [
        ("What is curiosity?",
         "Curiosity is the feeling that makes you want to look closer, ask questions, and learn what is going on.")
    ],
    "mystery": [
        ("What is a mystery?",
         "A mystery is something you do not understand yet, so you keep looking for clues until it makes sense.")
    ],
}


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    return [
        f'Write a gentle ghost-story mystery for a child named {hero.id} that uses the words "soggy", "wasp", and "shotgun".',
        f"Tell a spooky but safe story where {hero.id} follows clues, hears a buzzing sound, and solves a mystery in {world.setting.place}.",
        "Write a curiosity-filled story about a child who thinks a damp room is haunted, but the real answer is ordinary.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    return [
        QAItem(
            question=f"Why did {hero.id} keep looking around the old room instead of leaving?",
            answer=f"{hero.id} was curious and wanted to solve the mystery, so {hero.pronoun()} kept looking for clues.",
        ),
        QAItem(
            question="What made the floor soggy?",
            answer="A leak in the roof made the floor soggy after the storm.",
        ),
        QAItem(
            question=f"What was the buzzing sound near {world.setting.place}?",
            answer="The buzzing sound came from a wasp near the rafters.",
        ),
        QAItem(
            question=f"How did {parent.id} and {hero.id} make the room safe again?",
            answer="They patched the leak, let the wasp fly out, and kept the old shotgun locked away safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["soggy"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["wasp"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["shotgun"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["curiosity"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["mystery"])
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
        if e.locked:
            bits.append("locked=True")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  mystery_level={world.mystery_level}")
    lines.append(f"  solved={world.solved}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story mystery world: soggy floor, wasp buzz, old shotgun, curious child.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(NAMES_GIRL if gender == "girl" else NAMES_BOY)
    parent = args.parent or rng.choice(PARENTS)
    place = args.place or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, parent=parent, place=place)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.name, params.gender, params.parent)
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


ASP_RULES = r"""
curious_child(C) :- child(C), curiosity(C).
soggy_place(P) :- wet(P), leak(P).
mystery_solved(C) :- curious_child(C), clue(C), reveal(R), R = ordinary.
#show curious_child/1.
#show soggy_place/1.
#show mystery_solved/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("curiosity", "hero"))
    lines.append(asp.fact("wet", "shed"))
    lines.append(asp.fact("leak", "shed"))
    lines.append(asp.fact("clue", "hero"))
    lines.append(asp.fact("reveal", "ordinary"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams(name="Mina", gender="girl", parent="grandpa", place="shed"),
    StoryParams(name="Finn", gender="boy", parent="mother", place="attic"),
    StoryParams(name="Ivy", gender="girl", parent="father", place="porch"),
]


def main() -> None:
    args = build_parser().parse_args()
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
