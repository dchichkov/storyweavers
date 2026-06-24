#!/usr/bin/env python3
"""
storyworlds/worlds/eight_camera_bad_ending_bravery_myth.py
==========================================================

A tiny myth-like storyworld about a brave child, an eight-fold omen, and a
camera that cannot survive the dark water.

The seed-tale image:
---
In an old mythic valley, a brave child received a small camera from a village
elder. The elder said the camera could catch the faces of spirits if it was
held steady through one hard trial. Far above the river, eight moon-marked
stones glimmered in a cave. The child wanted a picture of all eight stones,
even though the path was steep and the river below was loud.

The child climbed anyway. A warning came from the elder to stay on the safe
stone ledge and wait for daylight, but the child wanted to prove bravery right
away. At the darkest turn, the child slipped, the camera struck the rock, and
the last bright shot was ruined. The child came home with empty hands, but with
a quieter understanding of what bravery can and cannot do.

World model:
---
    actors have meters (physical) and memes (emotional)
    bravery can push a child toward risky motion
    the camera has durability, wetness, and a captured-image count
    the eight moon stones are the target of the quest
    the ending is bad on purpose: the camera breaks before the picture is made
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "elder"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    kind: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    danger: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    quest: str
    relic: str
    name: str
    gender: str
    elder: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def mget(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def eget(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump(ent: Entity, key: str, amt: float = 1.0, *, emotional: bool = False) -> None:
    store = ent.memes if emotional else ent.meters
    store[key] = store.get(key, 0.0) + amt


def clear_world() -> World:
    raise StoryError("internal error: no world to clear")


SETTINGS = {
    "river_cave": Setting(place="the river cave", kind="cave", affords={"capture"}),
    "moon_bridge": Setting(place="the moon bridge", kind="bridge", affords={"capture"}),
    "temple_steps": Setting(place="the temple steps", kind="steps", affords={"capture"}),
}

QUESTS = {
    "capture": Quest(
        id="capture",
        verb="capture the eight moon stones",
        gerund="capturing the eight moon stones",
        risk="dark water and slick stone",
        danger="the camera could slip and break",
        keyword="eight",
        tags={"eight", "camera", "bravery", "myth"},
    )
}

RELICS = {
    "camera": Relic(
        id="camera",
        label="camera",
        phrase="a small brass camera with a glass eye",
        region="hands",
    ),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Asha", "Mina", "Suri", "Lina", "Rhea", "Tala"]
BOY_NAMES = ["Kian", "Niko", "Dara", "Rumi", "Soren", "Ivo"]
ELDERS = ["elder", "grandmother", "old priest", "wise aunt"]
TRAITS = ["brave", "bold", "earnest", "fierce", "steadfast"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic story world about bravery, eight stones, and a camera.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(GENDERS))
    ap.add_argument("--elder", choices=ELDERS)
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
    if args.quest and args.relic and (args.quest != "capture" or args.relic != "camera"):
        raise StoryError("(No story: this world only tells the myth of a brave child with a camera and the eight stones.)")
    place = args.place or rng.choice(list(SETTINGS))
    quest = args.quest or "capture"
    relic = args.relic or "camera"
    gender = args.gender or rng.choice(sorted(GENDERS))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(ELDERS)
    return StoryParams(place=place, quest=quest, relic=relic, name=name, gender=gender, elder=elder)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, q, r) for p in SETTINGS for q in QUESTS for r in RELICS]


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
        lines.append(asp.fact("affords", p, "capture"))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
        lines.append(asp.fact("needs", q, "camera"))
        lines.append(asp.fact("contains", q, "eight"))
        lines.append(asp.fact("theme", q, "bravery"))
        lines.append(asp.fact("theme", q, "myth"))
    for r in RELICS:
        lines.append(asp.fact("relic", r))
        lines.append(asp.fact("kind", r, "camera"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,R) :- place(P), quest(Q), relic(R), affords(P,Q), needs(Q,R), contains(Q,eight), theme(Q,bravery).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("python only:", sorted(py - cl))
    print("clingo only:", sorted(cl - py))
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.relic != "camera" or params.quest != "capture":
        raise StoryError("(No story: only the camera quest of the eight moon stones is supported.)")


def _attempt(world: World, hero: Entity, quest: Quest) -> None:
    bump(hero, "resolve", 1, emotional=True)
    bump(hero, "bravery", 1, emotional=True)
    bump(hero, "motion", 1)
    if world.setting.place == "the river cave":
        bump(hero, "risk", 1, emotional=True)
    else:
        bump(hero, "risk", 0.5, emotional=True)


def predict_break(world: World, hero: Entity, camera: Entity) -> bool:
    sim = world.copy()
    _attempt(sim, sim.get(hero.id), QUESTS["capture"])
    return True


def tell(setting: Setting, hero_name: str, hero_gender: str, elder_title: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    elder = world.add(Entity(id="Elder", kind="character", type="elder", label=elder_title))
    camera = world.add(Entity(
        id="camera",
        kind="thing",
        type="camera",
        label="camera",
        phrase="a small brass camera with a glass eye",
        owner=hero.id,
        caretaker=elder.id,
        meters={"durability": 2.0, "wet": 0.0, "captured": 0.0},
    ))
    stones = world.add(Entity(
        id="stones",
        kind="thing",
        type="stones",
        label="eight moon stones",
        phrase="eight moon stones",
        plural=True,
        meters={"glow": 1.0},
    ))

    hero.memes["bravery"] = 1.0
    hero.memes["desire"] = 1.0
    elder.memes["worry"] = 1.0

    world.say(f"In {setting.place}, {hero.id} was a {hero.pronoun('subject')} child who carried a brave heart.")
    world.say(f"{hero.id} treasured {hero.pronoun('possessive')} {camera.label}, because it could hold a moment like a bright bead.")
    world.say(f"Beyond the path waited {stones.label}, and everyone in the valley said there were exactly eight of them.")

    world.para()
    world.say(f"One night, {hero.id} stood at the edge of {setting.place} and listened to the river mutter below.")
    world.say(f"{hero.id} wanted to {QUESTS['capture'].verb}, even though the way was full of {QUESTS['capture'].risk}.")
    world.say(f"{elder_title.capitalize()} warned {hero.id} to wait for safer light, but {hero.id} felt {hero.pronoun('possessive')} bravery burn too hot to stop.")

    world.para()
    world.say(f"{hero.id} climbed anyway, because {hero.pronoun('subject')} wanted to prove that bravery meant never turning back.")
    hero.memes["stubborn"] = 1.0
    bump(camera, "wet", 1.0)
    bump(camera, "damage", 1.0)
    bump(camera, "captured", 0.0)
    world.say(f"At the slick turn, {hero.id}'s foot slipped on black stone.")
    world.say(f"The {camera.label} struck the rock, and its glass eye cracked before it could catch the eight shining faces.")

    world.para()
    hero.memes["sadness"] = 1.0
    elder.memes["tenderness"] = 1.0
    world.say(f"{hero.id} came home with no picture at all.")
    world.say(f"{elder_title.capitalize()} wrapped the broken {camera.label} in cloth and told {hero.id} that bravery is not the same as rushing into the dark.")
    world.say(f"In the end, the river kept the last sound, the stones kept their secret glow, and {hero.id} held the cracked {camera.label} like a small failed star.")

    world.facts.update(hero=hero, elder=elder, camera=camera, stones=stones, setting=setting, quest=QUESTS["capture"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short myth for a child about {hero.id}, the word "eight", and a camera that cannot survive the dark water.',
        f"Tell a brave but sad story where {hero.id} wants to capture eight moon stones with a camera, but the path is too dangerous.",
        f'Write a myth-like story with the words "camera" and "eight" that ends in a bad ending but still feels complete.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, camera, stones = f["hero"], f["elder"], f["camera"], f["stones"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the camera?",
            answer=f"{hero.id} wanted to capture the eight moon stones with the camera.",
        ),
        QAItem(
            question=f"Why did {elder.label} warn {hero.id} to wait?",
            answer=f"{elder.label.capitalize()} warned {hero.id} because the path had dark water and slick stone, and the camera might slip and break.",
        ),
        QAItem(
            question=f"What happened to the camera at the end?",
            answer=f"The camera struck the rock, cracked, and did not catch the eight shining faces.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the bad ending?",
            answer=f"{hero.id} felt sad, but also quieter and wiser after learning that bravery is not the same as rushing into danger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a camera for?",
            answer="A camera is a tool for making pictures by catching a moment of light.",
        ),
        QAItem(
            question="What does the number eight mean?",
            answer="Eight is the number that comes after seven and before nine.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means being willing to face something hard or scary.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people tell to explain wonders, heroes, or strange events.",
        ),
    ]


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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    world = tell(SETTINGS[params.place], params.name, params.gender, params.elder)
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
    StoryParams(place="river_cave", quest="capture", relic="camera", name="Asha", gender="girl", elder="elder"),
    StoryParams(place="moon_bridge", quest="capture", relic="camera", name="Kian", gender="boy", elder="old priest"),
    StoryParams(place="temple_steps", quest="capture", relic="camera", name="Mina", gender="girl", elder="wise aunt"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
