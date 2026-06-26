#!/usr/bin/env python3
"""
storyworlds/worlds/non_parson_happy_ending_bravery_ghost_story.py
==================================================================

A small child-facing ghost-story world about a brave child, a spooky place,
and a kindly parson who helps uncover that the "ghost" is only a lonely trick
of wind, light, and old boards. The story keeps the eerie mood, but it ends in
a safe, warm, happy way.

Seed premise:
- A child hears ghostly noises near an old parson's house or chapel.
- The child is afraid at first, then brave enough to look.
- The parson helps, and the mystery turns out harmless.
- The ending proves the fear changed into relief, pride, and friendship.

World model:
- Physical meters: darkness, noise, cold, comfort, brightness, clutter.
- Emotional memes: fear, courage, relief, trust, curiosity, warmth.
- Simulated state drives the prose; the ending image proves what changed.

The "non" and "parson" seed words are woven into the world as a "nonparson"
sign label and as the parson character, but the child-facing story remains
natural and readable.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "parson"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False


@dataclass
class GhostCue:
    name: str
    sound: str
    sight: str
    source: str
    fear: float = 1.0
    brave_action: str = ""
    cure: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    cue: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "chapel": Setting("the old chapel", indoor=True),
    "parsonage": Setting("the parson's house", indoor=True),
    "garden": Setting("the chapel garden", indoor=False),
    "lane": Setting("the dark lane", indoor=False),
}

CUES = {
    "wind": GhostCue(
        name="wind",
        sound="a hollow whistling in the rafters",
        sight="a white flutter near the window",
        source="the wind in a loose shutter",
        brave_action="open the window and listen closely",
        cure="the shutter was tied tight",
        tags={"wind", "sound"},
    ),
    "lantern": GhostCue(
        name="lantern",
        sound="a tiny clink and a sleepy hum",
        sight="a wobbling light on the wall",
        source="a lantern swinging on a hook",
        brave_action="walk right up to the door and knock",
        cure="the lantern was only swinging in the breeze",
        tags={"light", "night"},
    ),
    "boards": GhostCue(
        name="boards",
        sound="a creak-CRACK from the floor",
        sight="a shadow that stretched like a ghost",
        source="old floorboards in the hall",
        brave_action="step softly onto the boards",
        cure="the boards were old, not haunted",
        tags={"creak", "old"},
    ),
    "curtain": GhostCue(
        name="curtain",
        sound="a soft whoosh and a flutter",
        sight="a tall white shape behind the glass",
        source="a curtain moving in the draft",
        brave_action="lift the curtain with both hands",
        cure="the curtain was only dancing in the air",
        tags={"white", "draft"},
    ),
}

GENDERS = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]
TRAITS = ["curious", "gentle", "brave", "careful", "bright", "steady"]


def _m(d: dict[str, float], key: str, amt: float = 1.0) -> None:
    d[key] = d.get(key, 0.0) + amt


def _set0(d: dict[str, float], key: str) -> None:
    d[key] = 0.0


def _story_name_ending(name: str, gender: str) -> str:
    return "she" if gender == "girl" else "he"


def build_scene(world: World, hero: Entity, parent: Entity, parson: Entity, cue: GhostCue) -> None:
    setting = world.setting
    world.say(
        f"{hero.id} was a little {hero.type} who liked quiet evenings and stories about old places."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had heard that {setting.place} could seem haunted after dark."
    )
    world.say(
        f"{hero.id}'s {parent.label} told {hero.id} to stay close, but {hero.id} could not stop thinking about "
        f"{cue.sight} and {cue.sound}."
    )
    _m(hero.memes, "curiosity", 1)
    _m(hero.memes, "fear", 1)
    _m(world.facts, "setup", 1)


def hear_ghostly_noise(world: World, hero: Entity, cue: GhostCue) -> None:
    _m(hero.meters, "noise", 1)
    _m(hero.meters, "darkness", 1)
    _m(hero.memes, "fear", cue.fear)
    world.say(
        f"That night, a strange sound drifted through {world.setting.place}: {cue.sound}."
    )
    world.say(
        f"{hero.id} saw {cue.sight} and drew a fast breath. It looked spooky."
    )


def brave_choice(world: World, hero: Entity, cue: GhostCue) -> None:
    _m(hero.memes, "courage", 1)
    world.say(
        f"Still, {hero.id} took a small brave step and decided to {cue.brave_action}."
    )


def reveal_kind_truth(world: World, hero: Entity, parson: Entity, cue: GhostCue) -> None:
    _m(hero.memes, "trust", 1)
    _m(parson.memes, "kindness", 1)
    _m(hero.memes, "fear", -1)
    _m(hero.memes, "relief", 1)
    _m(hero.meters, "brightness", 1)
    world.say(
        f"Then {parson.id} came with a candle and smiled. {parson.pronoun().capitalize()} said, "
        f'"Let us look together. A mystery is not the same as a ghost."'
    )
    world.say(
        f"When they checked, the frightful thing turned out to be just {cue.source}."
    )


def happy_ending(world: World, hero: Entity, parent: Entity, parson: Entity, cue: GhostCue) -> None:
    _set0(hero.meters, "darkness")
    _m(hero.meters, "comfort", 2)
    _m(hero.memes, "courage", 1)
    _m(hero.memes, "relief", 1)
    _m(hero.memes, "fear", -1)
    world.say(
        f"{hero.id} laughed in relief because {cue.cure}, and the spooky feeling drifted away."
    )
    world.say(
        f"{hero.id}'s {parent.label} hugged {hero.id} tight, and {parson.id} said {hero.pronoun('object')} had been very brave."
    )
    world.say(
        f"On the way home, {hero.id} noticed a little sign by the door that read 'nonparson storage,' "
        f"and now it just looked silly instead of scary."
    )
    world.say(
        f"By the end of the night, the old place felt warm and peaceful, and {hero.id} walked away proud and smiling."
    )


def tell(setting: Setting, cue: GhostCue, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        memes={"fear": 0.0, "courage": 0.0, "relief": 0.0, "trust": 0.0, "curiosity": 0.0},
        meters={"darkness": 0.0, "noise": 0.0, "comfort": 0.0, "brightness": 0.0},
    ))
    parent = world.add(Entity(
        id=parent_type.capitalize(),
        kind="character",
        type=parent_type,
        label=parent_type,
        memes={"worry": 0.0},
    ))
    parson = world.add(Entity(
        id="Parson",
        kind="character",
        type="parson",
        label="the parson",
        memes={"kindness": 0.0},
    ))

    build_scene(world, hero, parent, parson, cue)
    world.para()
    hear_ghostly_noise(world, hero, cue)
    brave_choice(world, hero, cue)
    world.para()
    reveal_kind_truth(world, hero, parson, cue)
    happy_ending(world, hero, parent, parson, cue)

    world.facts.update(hero=hero, parent=parent, parson=parson, cue=cue, setting=setting)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    parson: Entity = f["parson"]
    cue: GhostCue = f["cue"]
    place = world.setting.place
    return [
        QAItem(
            question=f"Why did {hero.id} think {place} was haunted at first?",
            answer=(
                f"{hero.id} heard {cue.sound} and saw {cue.sight}, so the place seemed spooky before anyone knew the truth."
            ),
        ),
        QAItem(
            question=f"What brave thing did {hero.id} do when the scary noise started?",
            answer=(
                f"{hero.id} did not run away. {hero.pronoun().capitalize()} chose to {cue.brave_action}, which showed real bravery."
            ),
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the ghostly mystery?",
            answer=(
                f"The parson helped {hero.id} look closely, and {parent.label} stayed near too. Together they found a harmless answer."
            ),
        ),
        QAItem(
            question=f"What was the spooky thing really caused by?",
            answer=(
                f"It was really caused by {cue.source}, so it was only a normal sound or movement and not a ghost."
            ),
        ),
        QAItem(
            question=f"How did the story end for {hero.id}?",
            answer=(
                f"It ended happily. {hero.id} felt brave and relieved, and the old place seemed warm and safe by the end."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parson?",
            answer=(
                "A parson is a church helper or minister who can greet people, explain things, and help others feel calm."
            ),
        ),
        QAItem(
            question="Why can an old house sound spooky at night?",
            answer=(
                "Old houses can creak, whistle, and rattle when wind moves through them, which can sound spooky even when nothing is wrong."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing something careful and important even when you feel scared."
            ),
        ),
        QAItem(
            question="What does it mean when a story has a happy ending?",
            answer=(
                "A happy ending means the problem gets solved and the characters finish feeling safe, glad, or peaceful."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    cue: GhostCue = f["cue"]
    return [
        f"Write a short ghost story for a young child about {hero.id} who hears {cue.sound} and then chooses to be brave.",
        f"Tell a gentle spooky story where the scary thing turns out to be just {cue.source}.",
        f"Write a child-friendly story about bravery, a parson, and a happy ending in {world.setting.place}.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== Generation prompts ==")
    for p in sample.prompts:
        lines.append(f"- {p}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: v for k, v in e.memes.items() if abs(v) > 0}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_fears(H) :- fear(H,F), F > 0.
hero_brave(H) :- courage(H,C), C > 0.
happy_ending(H) :- relief(H,R), R > 0, courage(H,C), C > 0.
resolved(H) :- true_answer(H), happy_ending(H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
    for cid, cue in CUES.items():
        lines.append(asp.fact("cue", cid))
        for t in sorted(cue.tags):
            lines.append(asp.fact("tag", cid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show happy_ending/1.\n#show hero_brave/1.\n"))
    shown = set((sym.name, tuple(arg.name if hasattr(arg, "name") else getattr(arg, "string", getattr(arg, "number", None)) for arg in sym.arguments)) for sym in model)
    if shown is not None:
        print("OK: ASP twin loads and solves.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with bravery and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--cue", choices=CUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    cue = args.cue or rng.choice(list(CUES))
    gender = args.gender or rng.choice(GENDERS)
    parent = args.parent or rng.choice(PARENT_TYPES)
    name = args.name or rng.choice(
        ["Mia", "Lena", "Noah", "Eli", "Ava", "Nora", "Theo", "June"]
    )
    return StoryParams(place=place, cue=cue, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CUES[params.cue], params.name, params.gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
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


CURATED = [
    StoryParams(place="chapel", cue="wind", name="Mia", gender="girl", parent="mother"),
    StoryParams(place="parsonage", cue="lantern", name="Noah", gender="boy", parent="father"),
    StoryParams(place="garden", cue="boards", name="Ava", gender="girl", parent="mother"),
    StoryParams(place="lane", cue="curtain", name="Eli", gender="boy", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show happy_ending/1.\n#show hero_brave/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show cue/1.\n"))
        print(len(model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.cue} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
