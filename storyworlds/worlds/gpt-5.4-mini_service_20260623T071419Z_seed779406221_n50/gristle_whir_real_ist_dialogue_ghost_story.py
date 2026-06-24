#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50/gristle_whir_real_ist_dialogue_ghost_story.py
=======================================================================================================================

A small, standalone storyworld in a ghost-story style: a child hears a strange
whir in an old house, meets a friendly "real-ist" ghost, and learns that the
creak in the walls is only gristle-like settling wood, not a danger. The story
is driven by typed entities with physical meters and emotional memes, dialogue,
and a turn from fear to understanding.

Seed words: gristle, whir, real-ist
Style: Ghost Story
Feature: Dialogue
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
    attrs: dict = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    mood: str
    sound: str
    hiding: str
    safe: bool = True
    tags: list[str] = field(default_factory=list)


@dataclass
class Sound:
    id: str
    label: str
    whir: str
    source: str
    tags: list[str] = field(default_factory=list)


@dataclass
class Ghost:
    id: str
    label: str
    type: str
    real_ist: bool
    phrase: str
    tags: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str
    sound: str
    ghost: str
    child: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        return c


def _r_whir(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("whir", 0.0) < THRESHOLD:
            continue
        sig = ("whir", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        child = world.get("child")
        child.memes["fear"] = child.memes.get("fear", 0.0) + 1
        out.append("__whir__")
    return out


def _r_real_ist(world: World) -> list[str]:
    ghost = world.get("ghost")
    child = world.get("child")
    if ghost.attrs.get("real_ist") and child.memes.get("fear", 0.0) >= THRESHOLD:
        sig = ("calm", ghost.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.memes["calm"] = child.memes.get("calm", 0.0) + 1
        return ["__calm__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_whir, _r_real_ist):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


PLACE_REGISTRY = {
    "attic": Place(
        id="attic",
        label="the attic",
        mood="dusty and quiet",
        sound="the floor had old boards",
        hiding="the beams above the boxes",
        tags=["house", "quiet"],
    ),
    "hallway": Place(
        id="hallway",
        label="the hallway",
        mood="narrow and moonlit",
        sound="the walls were close together",
        hiding="the closet door at the end",
        tags=["house", "quiet"],
    ),
    "cellar": Place(
        id="cellar",
        label="the cellar",
        mood="cool and dim",
        sound="the pipes hummed softly",
        hiding="the dark corner by the jars",
        tags=["house", "quiet"],
    ),
}

SOUND_REGISTRY = {
    "gristle": Sound(
        id="gristle",
        label="gristle",
        whir="a small gristle-like whir",
        source="the old boards settling",
        tags=["gristle", "whir"],
    ),
    "whistle": Sound(
        id="whistle",
        label="whistle",
        whir="a thin whir that sounded like a whistle",
        source="the loose window latch",
        tags=["whir"],
    ),
    "fan": Sound(
        id="fan",
        label="fan",
        whir="a steady whir from a small fan",
        source="the little machine by the shelf",
        tags=["whir"],
    ),
}

GHOST_REGISTRY = {
    "real_ist": Ghost(
        id="real_ist",
        label="a real-ist ghost",
        type="ghost",
        real_ist=True,
        phrase="I am a real-ist ghost. I tell real things, even at night.",
        tags=["ghost", "real-ist"],
    ),
    "paper": Ghost(
        id="paper",
        label="a paper ghost",
        type="ghost",
        real_ist=False,
        phrase="I only like pretend things.",
        tags=["ghost"],
    ),
}

CHILDREN = {
    "Mina": ("girl", "curious"),
    "Noah": ("boy", "careful"),
    "Pia": ("girl", "brave"),
    "Eli": ("boy", "quiet"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACE_REGISTRY:
        for sound in SOUND_REGISTRY:
            for ghost in GHOST_REGISTRY:
                if ghost == "real_ist" and sound == "gristle":
                    combos.append((place, sound, ghost))
    return combos


def explain_rejection(place: str, sound: str, ghost: str) -> str:
    if ghost != "real_ist":
        return "(No story: this world needs a real-ist ghost so the ending can explain the noise truthfully.)"
    return f"(No story: {sound} does not fit the gristle-like whir seed for {place}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story storyworld with dialogue and a gristle-like whir.")
    ap.add_argument("--place", choices=PLACE_REGISTRY)
    ap.add_argument("--sound", choices=SOUND_REGISTRY)
    ap.add_argument("--ghost", choices=GHOST_REGISTRY)
    ap.add_argument("--child")
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
              and (args.sound is None or c[1] == args.sound)
              and (args.ghost is None or c[2] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, ghost = rng.choice(sorted(combos))
    child = args.child or rng.choice(sorted(CHILDREN))
    return StoryParams(place=place, sound=sound, ghost=ghost, child=child)


def tell(place: Place, sound: Sound, ghost: Ghost, child_name: str) -> World:
    if child_name not in CHILDREN:
        raise StoryError("Unknown child.")
    child_type, trait = CHILDREN[child_name]
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name,
                             attrs={"trait": trait}, meters={"whir": 0.0}, memes={"fear": 0.0, "calm": 0.0}))
    ghost_ent = world.add(Entity(id="ghost", kind="character", type="ghost", label=ghost.label,
                                 attrs={"real_ist": ghost.real_ist}, meters={"whir": 0.0}, memes={"mystery": 1.0}))
    noise = world.add(Entity(id="noise", type="sound", label=sound.label,
                             phrase=sound.whir, attrs={"source": sound.source},
                             meters={"whir": 0.0}, memes={}))
    world.facts["child"] = child
    world.facts["ghost"] = ghost_ent
    world.facts["noise"] = noise
    world.say(f"{child_name} went into {place.label}.")
    world.say(f"The air was {place.mood}, and {place.sound}.")
    world.say(f'"Did you hear that?" {child_name} whispered.')
    world.say(f'"Yes," said the room, or something like a room. "{sound.whir}."')
    child.meters["whir"] += 1
    noise.meters["whir"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(f'"Who is there?" {child_name} asked.')
    world.say(f'"I am {ghost.label}," said the ghost. "{ghost.phrase}"')
    if ghost.real_ist:
        world.say(f'"That sound is {sound.source}," the ghost said.')
        world.say(f'"It is only {sound.label}, not a monster."')
        child.memes["fear"] = 0.0
        child.memes["calm"] += 1
        world.say(f"{child_name} listened, and the whir became just an old-house sound.")
        world.say(f"The night stayed dark, but it was gentle, and {place.hiding} looked ordinary now.")
    else:
        world.say('"Maybe," said the ghost, but it did not sound sure.')
    world.facts.update(place=place, sound=sound, ghost=ghost, child_name=child_name, trait=trait)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACE_REGISTRY[params.place], SOUND_REGISTRY[params.sound], GHOST_REGISTRY[params.ghost], params.child)
    story_qa = [
        QAItem(
            question=f"Why did {params.child} feel scared in {world.place.label}?",
            answer=f"{params.child} heard a {SOUND_REGISTRY[params.sound].whir} and thought it might be a ghost. The old house sounded strange, so fear rose before the truth was clear.",
        ),
        QAItem(
            question=f"What did the ghost tell {params.child} about the noise?",
            answer=f"The ghost said the noise was only {SOUND_REGISTRY[params.sound].source}. It was a real-ist ghost, so it told the real reason instead of a spooky guess.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"{params.child} became calmer and understood the sound. The whir stayed in the house, but it no longer felt scary.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is gristle-like whir in this world?",
            answer="It is the small old-house sound made by boards, pipes, or a loose latch settling and moving.",
        ),
        QAItem(
            question="What does real-ist mean here?",
            answer="A real-ist ghost tells the real explanation, even when the truth sounds spooky at first.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=[
        f'Write a ghost story for a small child with the words "gristle", "whir", and "real-ist".',
        f"Tell a gentle dialogue story where {params.child} hears a whir in {world.place.label} and learns the truth from a real-ist ghost.",
    ], story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(place="attic", sound="gristle", ghost="real_ist", child="Mina"),
    StoryParams(place="hallway", sound="gristle", ghost="real_ist", child="Noah"),
    StoryParams(place="cellar", sound="gristle", ghost="real_ist", child="Pia"),
]


ASP_RULES = r"""
valid(Place,Sound,Ghost) :- place(Place), sound(Sound), ghost(Ghost), real_ist(Ghost), gristle_sound(Sound).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in PLACE_REGISTRY:
        lines.append(asp.fact("place", p))
    for s in SOUND_REGISTRY:
        lines.append(asp.fact("sound", s))
        if s == "gristle":
            lines.append(asp.fact("gristle_sound", s))
    for g in GHOST_REGISTRY:
        lines.append(asp.fact("ghost", g))
        if GHOST_REGISTRY[g].real_ist:
            lines.append(asp.fact("real_ist", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: ASP matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH.")
    print("only in asp:", sorted(a - b))
    print("only in python:", sorted(b - a))
    return 1


def generate_for_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for item in asp_valid_combos():
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
