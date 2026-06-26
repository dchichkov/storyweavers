#!/usr/bin/env python3
"""
storyworlds/worlds/first_sound_effects_curiosity_mystery.py
===========================================================

A small story world about a first strange sound, a curious child, and a mystery
that turns out to have a gentle answer.

Premise:
- A child hears a first sound effect in a quiet place.
- Curiosity grows.
- The child and a helper investigate.
- The mystery ends when the sound source is found and the worry turns into relief.

The simulated world keeps track of physical state in meters and emotional state
in memes, so the prose is driven by what actually changed in the model.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["noise", "dust", "flicker", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["curiosity", "worry", "relief", "bravery", "joy"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    quiet: bool
    detail: str


@dataclass
class Sound:
    id: str
    effect: str
    source_label: str
    source_phrase: str
    clue: str
    resolution: str
    room: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    sound: Optional[Sound] = None

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.sound = copy.deepcopy(self.sound)
        return clone


SETTINGS = {
    "house": Setting(place="the house", quiet=True, detail="the hallway was very still"),
    "attic": Setting(place="the attic", quiet=True, detail="the boxes and beams made the room echo"),
    "kitchen": Setting(place="the kitchen", quiet=False, detail="little everyday sounds hid in the corners"),
    "library": Setting(place="the library", quiet=True, detail="the shelves stood like sleepy walls"),
}

SOUNDS = {
    "tick": Sound(
        id="tick",
        effect="tick-tick",
        source_label="a tiny clock",
        source_phrase="a tiny clock with a silver face",
        clue="the sound came from something very small and regular",
        resolution="the clock was just waking up again",
        room="house",
        tags={"clock", "metal", "time"},
    ),
    "tap": Sound(
        id="tap",
        effect="tap-tap",
        source_label="a loose pipe",
        source_phrase="a loose pipe behind the wall",
        clue="the sound came from behind the wall",
        resolution="the pipe only tapped when warm water moved through it",
        room="kitchen",
        tags={"water", "pipe", "wall"},
    ),
    "whirr": Sound(
        id="whirr",
        effect="whirr-whirr",
        source_label="a toy robot",
        source_phrase="a forgotten toy robot under a chair",
        clue="the sound was soft and motor-like",
        resolution="the robot had been bumped on by accident and started to spin",
        room="house",
        tags={"toy", "motor", "battery"},
    ),
    "creak": Sound(
        id="creak",
        effect="creak",
        source_label="a ladder rung",
        source_phrase="an old ladder rung in the attic",
        clue="the sound came from something wooden and old",
        resolution="the wood creaked because the room was dry and the rung shifted",
        room="attic",
        tags={"wood", "attic", "old"},
    ),
    "scratch": Sound(
        id="scratch",
        effect="scritch-scratch",
        source_label="a kitten",
        source_phrase="a kitten behind a basket",
        clue="the sound sounded tiny and quick",
        resolution="the kitten was busy nudging a crumpled ribbon",
        room="library",
        tags={"animal", "fur", "basket"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tim", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["curious", "careful", "brave", "gentle", "bright", "patient"]


@dataclass
class StoryParams:
    place: str
    sound: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A tiny mystery story world about a first sound effect and curiosity."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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


def select_sound_by_place(place: str) -> list[str]:
    allowed = [sid for sid, snd in SOUNDS.items() if snd.room == place or snd.room == "house"]
    return allowed


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for sid in select_sound_by_place(place):
            out.append((place, sid))
    return out


def explain_rejection(place: str, sound: str) -> str:
    snd = SOUNDS[sound]
    return (
        f"(No story: {snd.effect} does not fit well in {SETTINGS[place].place} "
        f"for this mystery setup.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sound:
        if (args.place, args.sound) not in valid_combos():
            raise StoryError(explain_rejection(args.place, args.sound))

    combos = [
        (p, s)
        for p, s in valid_combos()
        if (args.place is None or p == args.place)
        and (args.sound is None or s == args.sound)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, sound = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, sound=sound, name=name, gender=gender, helper=helper, trait=trait)


def _is_silence(world: World) -> bool:
    return world.setting.quiet


def _hear_first_sound(world: World, child: Entity, sound: Sound) -> None:
    child.memes["curiosity"] += 1
    if _is_silence(world):
        child.memes["worry"] += 0.5
    world.say(
        f"It was the first {sound.effect} the day had made, and {child.id} stopped at once."
    )
    world.say(
        f"In the quiet {world.setting.place}, the sound felt small, strange, and important."
    )


def _follow_clue(world: World, child: Entity, helper: Entity, sound: Sound) -> None:
    child.memes["curiosity"] += 1
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} tilted {child.pronoun('possessive')} head and listened again, because {sound.clue}."
    )
    world.say(
        f"{helper.label} smiled and said they could look together, one careful step at a time."
    )


def _search_room(world: World, child: Entity, helper: Entity, sound: Sound) -> None:
    child.memes["worry"] += 0.5
    world.say(
        f"They searched near the {world.setting.place.split('the ')[-1]} corner, behind baskets and under chairs."
    )
    world.say(
        f"Every little pause made the mystery feel bigger, until {child.id} heard the same sound again."
    )


def _reveal_source(world: World, child: Entity, helper: Entity, sound: Sound) -> None:
    src = world.add(Entity(
        id="source",
        kind="thing",
        type="thing",
        label=sound.source_label,
        phrase=sound.source_phrase,
        hidden=False,
    ))
    src.meters["noise"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["relief"] += 1.0
    child.memes["joy"] += 1.0
    world.say(
        f"Then they found {sound.source_phrase}. That was the answer to the mystery."
    )
    world.say(
        f"{sound.resolution.capitalize()}, so the room was safe after all."
    )


def tell(setting: Setting, sound: Sound, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(setting=setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait]))
    adult = world.add(Entity(id="Helper", kind="character", type=helper, label=f"the {helper}"))

    world.sound = sound
    world.facts["child"] = child
    world.facts["helper"] = adult
    world.facts["sound"] = sound
    world.facts["place"] = setting.place

    world.say(
        f"{child.id} was a little {trait} {gender} who liked quiet rooms and noticed details."
    )
    world.say(
        f"{child.id} had never heard a first {sound.effect} like that before."
    )
    world.para()
    _hear_first_sound(world, child, sound)
    _follow_clue(world, child, adult, sound)
    world.para()
    _search_room(world, child, adult, sound)
    _reveal_source(world, child, adult, sound)

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    sound = world.facts["sound"]
    place = world.facts["place"]
    return [
        f"Write a short mystery for a young child about the first {sound.effect} heard in {place}.",
        f"Tell a gentle story where {child.id} follows curiosity after hearing {sound.effect}.",
        f"Write a child-friendly mystery with a clear clue, a careful search, and a reveal about {sound.effect}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    helper = world.facts["helper"]
    sound = world.facts["sound"]
    place = world.facts["place"]
    return [
        QAItem(
            question=f"What first sound did {child.id} hear in {place}?",
            answer=f"{child.id} heard {sound.effect} for the first time in {place}.",
        ),
        QAItem(
            question=f"Why did {child.id} and {helper.label} look around?",
            answer=(
                f"They looked around because the sound was strange and {child.id} was curious "
                f"about where it came from."
            ),
        ),
        QAItem(
            question=f"What did they find at the end of the mystery?",
            answer=f"They found {sound.source_phrase}, and that explained the sound.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    sound = world.facts["sound"]
    if "clock" in sound.tags:
        return [QAItem(question="What does a clock do?", answer="A clock keeps track of time by making ticks as it moves.")]
    if "pipe" in sound.tags:
        return [QAItem(question="What does a pipe do in a house?", answer="A pipe carries water through a house from one place to another.")]
    if "toy" in sound.tags:
        return [QAItem(question="What is a toy robot?", answer="A toy robot is a play thing that can look and move like a little robot.")]
    if "wood" in sound.tags:
        return [QAItem(question="Why can old wood creak?", answer="Old wood can creak when it shifts a little or gets dry.")]
    return [QAItem(question="Why do kittens make tiny sounds?", answer="Kittens are small, so their paws and noses often make little soft sounds.")]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="house", sound="tick", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="kitchen", sound="tap", name="Leo", gender="boy", helper="father", trait="careful"),
    StoryParams(place="attic", sound="creak", name="Ava", gender="girl", helper="father", trait="brave"),
    StoryParams(place="library", sound="scratch", name="Noah", gender="boy", helper="mother", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.quiet:
            lines.append(asp.fact("quiet", pid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("effect", sid, sound.effect))
        lines.append(asp.fact("source_in", sid, sound.room))
    return "\n".join(lines)


ASP_RULES = r"""
relevant(P,S) :- place(P), sound(S), source_in(S,P).
mystery(P,S) :- relevant(P,S), quiet(P).
#show mystery/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mystery/2."))
    return sorted(set(asp.atoms(model, "mystery")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = { (p, s) for p, s in valid_combos() if SETTINGS[p].quiet }
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], SOUNDS[params.sound], params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show mystery/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} quiet mystery combos:\n")
        for place, sound in combos:
            print(f"  {place:8} {sound:8}")
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
            header = f"### {p.name}: {p.sound} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
