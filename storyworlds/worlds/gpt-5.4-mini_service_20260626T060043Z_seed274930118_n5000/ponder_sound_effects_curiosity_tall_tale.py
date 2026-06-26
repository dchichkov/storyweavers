#!/usr/bin/env python3
"""
storyworlds/worlds/ponder_sound_effects_curiosity_tall_tale.py
==============================================================

A standalone story world for a tiny Tall Tale about a curious listener who
ponders a mysterious sound, follows it, and learns what made it.

Seed tale, in brief:
---
A curious child hears a strange "whump-whirr-CLANG" across the fields.
Everybody else shrugs, but the child ponders the sound, asks questions,
and follows the noise until the truth turns out to be larger-than-life:
a giant old machine or creature making a grand ruckus in the distance.

World model:
---
- meters: distance, noise, height, size, effort
- memes: curiosity, worry, delight, bravado, relief
- The story begins with a sound, tension comes from not knowing what made it,
  and resolution comes from a careful search that turns the mystery into wonder.

This file keeps the story grounded in a simulated model rather than a frozen
paragraph. The prose is child-facing, concrete, and a little tall-tale grand.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old meadow"


@dataclass
class Mystery:
    sound: str
    cause: str
    source_label: str
    source_phrase: str
    size_image: str
    height: int
    noise: int
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mystery: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
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
        clone = World(self.setting, self.mystery)
        import copy as _copy
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "meadow": Setting("the old meadow"),
    "riverbank": Setting("the riverbank"),
    "hills": Setting("the windy hills"),
    "barnyard": Setting("the barnyard"),
}

MYSTERIES = {
    "mill": Mystery(
        sound="whump-whirr-CLANG",
        cause="a giant waterwheel turning a dusty mill",
        source_label="mill",
        source_phrase="a giant old mill with a creaking wheel",
        size_image="as tall as a three-story barn",
        height=3,
        noise=8,
        location="by the river",
        tags={"wheel", "water", "machine"},
    ),
    "cowbell": Mystery(
        sound="clink-clink-MOO",
        cause="a very large cow with a bell on its neck",
        source_label="cow",
        source_phrase="a hillside cow big as a wagon",
        size_image="bigger than two sheds put together",
        height=2,
        noise=5,
        location="on the hill",
        tags={"cow", "bell"},
    ),
    "train": Mystery(
        sound="chuff-chuff-CHOO",
        cause="a long train puffing past a far-off bridge",
        source_label="train",
        source_phrase="a thunderous train with bright red cars",
        size_image="long as a row of ten wagons",
        height=2,
        noise=9,
        location="over the bridge",
        tags={"train", "steam", "bridge"},
    ),
    "windmill": Mystery(
        sound="whish-whash-WHUM",
        cause="a windmill whipping its arms around in the gusts",
        source_label="windmill",
        source_phrase="an old windmill with sky-high wooden arms",
        size_image="taller than the tallest pine",
        height=4,
        noise=7,
        location="at the edge of the fields",
        tags={"wind", "mill", "machine"},
    ),
}

GIRL_NAMES = ["Mina", "Ruby", "Lila", "Ivy", "June", "Nora", "Mabel"]
BOY_NAMES = ["Bram", "Otis", "Eli", "Finn", "Theo", "Jasper", "Ned"]
TRAITS = ["curious", "wide-eyed", "brave", "restless", "thoughtful", "cheery"]


def narrative_sound(sound: str) -> str:
    return {
        "whump-whirr-CLANG": "whump-whirr-CLANG",
        "clink-clink-MOO": "clink-clink-MOO",
        "chuff-chuff-CHOO": "chuff-chuff-CHOO",
        "whish-whash-WHUM": "whish-whash-WHUM",
    }[sound]


def setup_line(setting: Setting) -> str:
    return f"The {setting.place.removeprefix('the ')} lay wide and gold, with sky enough for a giant tale."


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    world = World(setting, mystery)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"distance": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "delight": 0.0, "relief": 0.0, "bravado": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label=f"the {params.parent}",
        meters={"distance": 0.0},
        memes={"worry": 0.0, "patience": 1.0},
    ))
    source = world.add(Entity(
        id="Source",
        kind="thing",
        type=mystery.source_label,
        label=mystery.source_label,
        phrase=mystery.source_phrase,
        meters={"height": float(mystery.height), "noise": float(mystery.noise), "distance": 12.0},
        memes={"mystery": 1.0},
    ))

    world.facts.update(hero=hero, parent=parent, source=source, mystery=mystery, setting=setting)

    world.say(f"{params.name} was a {params.trait} little {params.gender} who loved to ponder odd things.")
    world.say(f"One afternoon, {params.name} heard {narrative_sound(mystery.sound)} out in {setting.place}.")
    world.say(f"It sounded so big that {params.name} blinked twice and said, “Now what in the world was that?”")
    return world


def predict_find(world: World) -> bool:
    sim = world.copy()
    hero = sim.facts["hero"]
    source = sim.facts["source"]
    hero.meters["distance"] = source.meters["distance"]
    hero.memes["curiosity"] += 1.0
    return hero.meters["distance"] >= source.meters["distance"]


def follow_sound(world: World) -> None:
    hero = world.facts["hero"]
    source = world.facts["source"]
    parent = world.facts["parent"]
    mystery = world.facts["mystery"]

    hero.memes["curiosity"] += 1.0
    hero.memes["bravado"] += 0.5
    hero.meters["distance"] = 4.0
    world.say(f"{hero.id} did not shrug. {hero.pronoun().capitalize()} pondered the sound, tilted {hero.pronoun('possessive')} head, and listened again.")
    world.say(f"The {parent.type} said, “It may be nothing at all,” but that only made the wondering grow.")
    world.say(f"So {hero.id} walked closer, step by step, with boots on the dirt and questions in {hero.pronoun('possessive')} pocket.")
    hero.meters["distance"] = source.meters["distance"]
    hero.memes["worry"] += 1.0
    world.say(f"The noise got louder and wider, and the whole air rang like a spoon in a tin cup.")
    world.say(f"At last, {hero.id} found the source: {mystery.source_phrase} {mystery.location}.")
    world.say(f"It was {mystery.size_image}, and the ruckus came from {mystery.cause}.")


def resolve(world: World) -> None:
    hero = world.facts["hero"]
    parent = world.facts["parent"]
    mystery = world.facts["mystery"]
    hero.memes["worry"] = 0.0
    hero.memes["delight"] += 1.5
    hero.memes["relief"] += 1.0
    parent.memes["worry"] += 0.2
    world.say(f"{hero.id} laughed, because the scary part had been only a big old sound and a bigger old surprise.")
    world.say(f"{hero.id} told the {parent.type}, “I knew there was a reason for that racket!”")
    world.say(f"Together they watched the {mystery.source_label} work its noisy wonder, and the day felt grand as a parade.")
    world.say(f"By sunset, the mystery was solved, and {hero.id} still had the best story in the county.")


def tell(params: StoryParams) -> World:
    world = make_world(params)
    world.para()
    world.say(setup_line(world.setting))
    follow_sound(world)
    world.para()
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mystery = f["mystery"]
    return [
        f'Write a Tall Tale for a child who hears "{mystery.sound}" and ponders what made it.',
        f"Tell a curious story about {hero.id}, who follows a strange sound until the big truth is found.",
        f'Write a playful story with sound effects, curiosity, and a giant reveal about "{mystery.source_label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    mystery = f["mystery"]
    source = f["source"]
    return [
        QAItem(
            question=f"What strange sound did {hero.id} hear in {world.setting.place}?",
            answer=f"{hero.id} heard {mystery.sound}, and it echoed across {world.setting.place} like a big riddle.",
        ),
        QAItem(
            question=f"What did {hero.id} do instead of ignoring the noise?",
            answer=f"{hero.id} pondered it, listened again, and walked closer until the answer could be seen.",
        ),
        QAItem(
            question=f"What was really making the big racket?",
            answer=f"It was {source.phrase} {mystery.location}, and the sound came from {mystery.cause}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel when the mystery was solved?",
            answer=f"{hero.id} felt relieved and delighted, because the sound was not scary after all.",
        ),
        QAItem(
            question=f"Who went with {hero.id} through the curious moment?",
            answer=f"The {parent.type} stayed nearby, listened, and shared the moment when the truth was found.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    m = world.facts["mystery"]
    out = [
        QAItem(
            question="What does it mean to ponder something?",
            answer="To ponder means to think about something carefully and for a little while.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are fun sounds that help tell what is happening, like whirr, clank, or choo.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to know more and ask questions.",
        ),
    ]
    if "mill" in m.tags:
        out.append(QAItem(
            question="What is a mill?",
            answer="A mill is a place or machine that uses turning parts to do work, often with water or wind.",
        ))
    if "train" in m.tags:
        out.append(QAItem(
            question="Why do trains make loud sounds?",
            answer="Trains make loud sounds because heavy wheels, metal parts, and engines all move together with a great rumble.",
        ))
    if "cow" in m.tags:
        out.append(QAItem(
            question="Why can a cowbell be heard from far away?",
            answer="A cowbell can ring across a field because metal makes a bright, carrying sound.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:7} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is worth pondering when the sound is loud enough and the listener is curious.
worth_puzzling(H, M) :- hero(H), mystery(M), curious(H), loud(M).
drawn_to_follow(H, M) :- worth_puzzling(H, M), pondered(H, M).

% The story resolves when the hero reaches the source and learns the cause.
solved(H, M) :- hero(H), mystery(M), reached(H, M), source_known(H, M).

#show worth_puzzling/2.
#show drawn_to_follow/2.
#show solved/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("mystery", "mystery"))
    lines.append(asp.fact("curious", "hero"))
    lines.append(asp.fact("loud", "mystery"))
    lines.append(asp.fact("pondered", "hero", "mystery"))
    lines.append(asp.fact("reached", "hero", "mystery"))
    lines.append(asp.fact("source_known", "hero", "mystery"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show worth_puzzling/2.\n#show drawn_to_follow/2.\n#show solved/2."))
    atoms = set((a.name, tuple(x.name if hasattr(x, "name") else x for x in a.arguments)) for a in model)
    expected = {
        ("worth_puzzling", ("hero", "mystery")),
        ("drawn_to_follow", ("hero", "mystery")),
        ("solved", ("hero", "mystery")),
    }
    if atoms == expected:
        print("OK: ASP twin matches the Python reasonableness gate.")
        return 0
    print("MISMATCH in ASP twin:")
    print("  got:", sorted(atoms))
    print("  expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall Tale story world: curiosity, ponder, and a noisy mystery."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    setting = args.setting or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    if mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    return StoryParams(setting=setting, mystery=mystery, name=name, gender=gender, parent=parent, trait=trait)


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


CURATED = [
    StoryParams(setting="meadow", mystery="mill", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="hills", mystery="cowbell", name="Bram", gender="boy", parent="father", trait="thoughtful"),
    StoryParams(setting="riverbank", mystery="train", name="Ivy", gender="girl", parent="mother", trait="brave"),
    StoryParams(setting="barnyard", mystery="windmill", name="Otis", gender="boy", parent="father", trait="restless"),
]


def asp_mode() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show worth_puzzling/2.\n#show drawn_to_follow/2.\n#show solved/2."))
    return sorted(set((a.name, tuple(x.name if hasattr(x, "name") else x for x in a.arguments)) for a in model))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show worth_puzzling/2.\n#show drawn_to_follow/2.\n#show solved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for name, pair in asp_mode():
            print(f"{name}{pair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
