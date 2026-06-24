#!/usr/bin/env python3
"""
A small animal-story world about curiosity, misunderstandings, and noisy little
discoveries.

The seed words are woven into the domain: coffin, gel, fuse.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat", "kitten", "fox", "rabbit", "hare", "mouse"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"bird", "crow", "owl", "squirrel", "dog"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class ObjectKind:
    id: str
    label: str
    phrase: str
    risk: str
    noise: str
    fix: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    object_kind: str
    name: str
    animal: str
    friend: str
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def normalize_word(text: str) -> str:
    return text.strip().lower().replace(" ", "_")


SETTINGS = {
    "garden": Setting("the garden", {"peek", "listen", "fix"}),
    "barn": Setting("the barn", {"peek", "listen", "fix"}),
    "porch": Setting("the porch", {"peek", "listen", "fix"}),
    "shed": Setting("the shed", {"peek", "listen", "fix"}),
}

OBJECTS = {
    "coffin": ObjectKind(
        id="coffin",
        label="coffin",
        phrase="a small wooden coffin-shaped box",
        risk="spooky",
        noise="thump",
        fix="old latch gel",
        tags={"coffin", "curiosity", "misunderstanding", "sound_effects"},
    ),
    "gel": ObjectKind(
        id="gel",
        label="gel",
        phrase="a clear jar of sticky gel",
        risk="slippery",
        noise="glorp",
        fix="a soft cloth",
        tags={"gel", "curiosity", "sound_effects"},
    ),
    "fuse": ObjectKind(
        id="fuse",
        label="fuse",
        phrase="a tiny fuse for the lantern",
        risk="dim",
        noise="fssst",
        fix="a careful twist",
        tags={"fuse", "misunderstanding", "sound_effects"},
    ),
}

ANIMALS = {
    "cat": {"names": ["Milo", "Pip", "Nina", "Toby"], "kind": "cat"},
    "rabbit": {"names": ["Luna", "Bun", "Momo", "Kiki"], "kind": "rabbit"},
    "squirrel": {"names": ["Nutsy", "Coco", "Penny", "Rolo"], "kind": "squirrel"},
    "crow": {"names": ["Cora", "Jet", "Mara", "Echo"], "kind": "crow"},
}

FRIENDS = {
    "cat": ["mouse", "rabbit", "bird"],
    "rabbit": ["cat", "squirrel", "crow"],
    "squirrel": ["rabbit", "bird", "cat"],
    "crow": ["rabbit", "squirrel", "cat"],
}

SOUND_EFFECTS = {
    "coffin": "thump-thump",
    "gel": "glorp-glorp",
    "fuse": "fssst-fssst",
}

KNOWLEDGE = {
    "coffin": [("What is a coffin?", "A coffin is a box made for a person or animal to lie in after dying.")],
    "gel": [("What is gel?", "Gel is a soft, jelly-like material that can wiggle or stick a little.")],
    "fuse": [("What is a fuse?", "A fuse is a small part that helps something light up or start safely.")],
    "sound_effects": [("What are sound effects?", "Sound effects are words that help show the sounds things make, like bang or pop.")],
    "curiosity": [("What is curiosity?", "Curiosity is the feeling that makes you want to look, ask, and learn.")],
    "misunderstanding": [("What is a misunderstanding?", "A misunderstanding happens when someone thinks something means one thing, but it really means another.")],
}


ASP_RULES = r"""
curious(A) :- animal(A), feeling(A, curiosity).
misunderstands(A, O) :- curious(A), sees(A, O), spooky(O).
hears_sound(A, O) :- soundy(O), nearby(A, O).
worries(A, O) :- misunderstands(A, O), hears_sound(A, O).
reassured(A, O) :- explains(B, O), friend(B), worries(A, O).
resolved(A, O) :- reassured(A, O), learned(A, O).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for aid in ANIMALS:
        lines.append(asp.fact("animal", aid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("soundy", oid))
        for tag in obj.tags:
            lines.append(asp.fact("tagged", oid, tag))
        if oid == "coffin":
            lines.append(asp.fact("spooky", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show resolved/2. #show worries/2. #show misunderstands/2.")
    model = asp.one_model(program)
    atoms = {sym.name for sym in model}
    if "resolved" in atoms or "worries" in atoms or "misunderstands" in atoms:
        print("OK: ASP rules load and produce a model.")
        return 0
    print("MISMATCH: ASP model did not contain expected atoms.")
    return 1


def choose_setting(rng: random.Random, name: Optional[str]) -> str:
    if name:
        if name not in SETTINGS:
            raise StoryError(f"Unknown setting: {name}")
        return name
    return rng.choice(list(SETTINGS))


def choose_object(rng: random.Random, name: Optional[str]) -> str:
    if name:
        if name not in OBJECTS:
            raise StoryError(f"Unknown object: {name}")
        return name
    return rng.choice(list(OBJECTS))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = choose_setting(rng, args.setting)
    object_kind = choose_object(rng, args.object)
    animal = args.animal or rng.choice(list(ANIMALS))
    name = args.name or rng.choice(ANIMALS[animal]["names"])
    friend = args.friend or rng.choice(FRIENDS[animal])
    return StoryParams(setting=setting, object_kind=object_kind, name=name, animal=animal, friend=friend)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world of curiosity and misunderstandings.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend", choices=["mouse", "rabbit", "bird", "cat", "squirrel", "crow"])
    ap.add_argument("--name")
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


def generate_story(world: World, params: StoryParams) -> None:
    hero = world.add(Entity(id=params.name, kind="character", type=params.animal, label=params.name))
    friend = world.add(Entity(id="Friend", kind="character", type=params.friend, label=params.friend))
    obj = world.add(Entity(
        id=params.object_kind,
        kind="thing",
        type=params.object_kind,
        label=OBJECTS[params.object_kind].label,
        phrase=OBJECTS[params.object_kind].phrase,
    ))
    world.facts.update(hero=hero, friend=friend, obj=obj, params=params)

    world.say(f"{hero.id} was a curious little {params.animal} who liked to peek at every odd thing in {world.setting.place}.")
    world.say(f"One day, {hero.id} spotted {obj.phrase}. It made a soft {SOUND_EFFECTS[params.object_kind]} sound.")
    world.say(f"{hero.id} leaned closer, because curiosity tugged hard.")
    world.para()
    world.say(f"\"{SOUND_EFFECTS[params.object_kind].capitalize()}!\" went the little box again, and {hero.id} jumped back.")
    if params.object_kind == "coffin":
        world.say(f"For a moment, {hero.id} thought the coffin was scary and full of trouble.")
    elif params.object_kind == "gel":
        world.say(f"For a moment, {hero.id} thought the gel might spill everywhere and make a mess.")
    else:
        world.say(f"For a moment, {hero.id} thought the fuse might mean the lantern was broken.")
    world.say(f"That was a misunderstanding, but {hero.id} did not know it yet.")
    world.para()
    world.say(f"{friend.id} came over and looked too. {friend.id} smiled and explained what it really was.")
    if params.object_kind == "coffin":
        world.say(f"It was only a tiny box for keeping a stage prop safe, not a bad surprise at all.")
        world.say(f"{friend.id} squeezed a little gel on the squeaky latch, and it went {SOUND_EFFECTS['gel']}.")
        world.say(f"Then the lid closed softly with one last {SOUND_EFFECTS['coffin']}.")
    elif params.object_kind == "gel":
        world.say(f"It was only a jar of gel for fixing a little wobble, not something messy to fear.")
        world.say(f"{friend.id} showed how a careful touch made the gel sit neatly, while the lid said {SOUND_EFFECTS['gel']}.")
        world.say(f"A tiny nearby lantern fuse hissed {SOUND_EFFECTS['fuse']} and kept the porch light steady.")
    else:
        world.say(f"It was only a safe little fuse for a lantern, not a danger.")
        world.say(f"{friend.id} used a dab of gel to steady the holder, and the fuse answered with a tiny {SOUND_EFFECTS['fuse']}.")
        world.say(f"The box by the wall gave a quiet {SOUND_EFFECTS['coffin']}, because the old latch had settled.")
    world.para()
    world.say(f"{hero.id}'s ears relaxed. The scary idea was gone.")
    world.say(f"{hero.id} and {friend.id} sat together, listened to the sound effects, and laughed at the misunderstanding.")
    world.say(f"By the end, curiosity had turned into a happy lesson, and {hero.id} looked much braver in the warm little place.")


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f'Write an animal story for a young child about curiosity, a misunderstanding, and a noisy "{p.object_kind}".',
        f"Tell a gentle story where {p.name}, a {p.animal}, hears a sound effect and learns what {p.object_kind} really is.",
        f"Write a short story that includes the words coffin, gel, and fuse in a child-friendly animal scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    obj = world.facts["obj"]
    return [
        QAItem(
            question=f"Who was the curious little animal in the story?",
            answer=f"The curious little animal was {hero.id}, a {p.animal} who liked to peek at odd things.",
        ),
        QAItem(
            question=f"What did {hero.id} first think when the {obj.label} made a sound?",
            answer=f"{hero.id} first thought something was wrong, because the sound effect made {hero.id} misunderstand the object.",
        ),
        QAItem(
            question=f"Who explained the object to {hero.id}?",
            answer=f"{friend.id} explained it and helped turn the misunderstanding into a happy lesson.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    tags = set(OBJECTS[p.object_kind].tags)
    out: list[QAItem] = []
    for tag in ["sound_effects", "curiosity", "misunderstanding", p.object_kind]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="garden", object_kind="coffin", name="Milo", animal="cat", friend="rabbit"),
    StoryParams(setting="barn", object_kind="gel", name="Luna", animal="rabbit", friend="squirrel"),
    StoryParams(setting="porch", object_kind="fuse", name="Cora", animal="crow", friend="cat"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.setting])
    generate_story(world, params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/2. #show worries/2. #show misunderstands/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show resolved/2. #show worries/2. #show misunderstands/2."))
        print(" ".join(str(a) for a in model))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
