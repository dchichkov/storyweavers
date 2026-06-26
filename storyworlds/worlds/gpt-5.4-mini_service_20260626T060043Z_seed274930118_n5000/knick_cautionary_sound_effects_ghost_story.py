#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/knick_cautionary_sound_effects_ghost_story.py
==================================================================================================

A small ghost-story world with a cautionary turn, built around eerie sound
effects and a tiny, state-driven resolution.

Premise source tale:
---
A child hears a lonely knick in an old house at night. Each time the child
gets closer, the sound grows louder: knick, knick, knick. A warning note says
the attic should not be opened after dark. The child nearly opens it anyway,
but the sound leads the child to a safer door, where a lost cat is hiding.
The child closes the attic again, and the house grows quiet.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    darkness: float = 0.0
    creakiness: float = 0.0
    warning_present: bool = False


@dataclass
class Sound:
    id: str
    text: str
    volume: float
    caution: bool = False
    direction: str = ""


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.sounds: list[Sound] = []
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone = World(copy.deepcopy(self.place))
        clone.entities = copy.deepcopy(self.entities)
        clone.sounds = copy.deepcopy(self.sounds)
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "old_house": Place(
        id="old_house",
        label="the old house",
        darkness=0.8,
        creakiness=0.9,
        warning_present=True,
    ),
    "attic_hall": Place(
        id="attic_hall",
        label="the attic hall",
        darkness=0.9,
        creakiness=1.0,
        warning_present=True,
    ),
    "quiet_room": Place(
        id="quiet_room",
        label="the quiet room",
        darkness=0.4,
        creakiness=0.5,
        warning_present=False,
    ),
}

SOUND_LIBRARY = {
    "knick": Sound(id="knick", text="knick", volume=0.7, caution=True, direction="upstairs"),
    "tap": Sound(id="tap", text="tap", volume=0.4, caution=False, direction="near the door"),
    "scrape": Sound(id="scrape", text="scrape", volume=0.8, caution=True, direction="behind the wall"),
}

GHOSTLY_HUSH = [
    "hush",
    "whisper",
    "rustle",
]

GIRL_NAMES = ["Mina", "Lena", "Ivy", "June", "Nora", "Rose"]
BOY_NAMES = ["Eli", "Theo", "Miles", "Finn", "Noah", "Jack"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story world with cautionary sound effects centered on knick."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["grandmother", "grandfather", "mother", "father"])
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
    place = args.place or rng.choice(list(PLACES))
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["grandmother", "grandfather", "mother", "father"])
    return StoryParams(place=place, hero_name=hero_name, hero_type=gender, companion=companion)


def _make_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    companion = world.add(Entity(id="companion", kind="character", type=params.companion, label=f"the {params.companion}"))
    attic = world.add(Entity(id="attic", type="place", label="the attic"))
    note = world.add(Entity(id="note", type="thing", label="a warning note", phrase="a warning note that said not to open the attic after dark"))
    cat = world.add(Entity(id="cat", kind="character", type="thing", label="the lost cat"))

    world.facts.update(hero=hero, companion=companion, attic=attic, note=note, cat=cat)
    return world


def _emit_sound(world: World, sound: Sound) -> None:
    world.sounds.append(sound)
    if sound.caution:
        world.say(f"{sound.text}, {sound.text}—something was trying to get attention from {sound.direction}.")
    else:
        world.say(f"There was a small {sound.text} from {sound.direction}.")


def _setup(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    world.say(f"{hero.id} spent the evening in {world.place.label} with {companion.label}.")
    world.say(f"The rooms were dark, and the boards answered every step with a soft creak.")
    world.say(f"Near the stair door, a note warned that nobody should open the attic after dark.")


def _turn(world: World) -> None:
    hero = world.facts["hero"]
    world.para()
    _emit_sound(world, SOUND_LIBRARY["knick"])
    world.say(f"{hero.id} paused, because the sound felt like a tiny finger tapping from upstairs.")
    _emit_sound(world, SOUND_LIBRARY["knick"])
    world.say(f"This time the {SOUND_LIBRARY['knick'].text} sounded closer, and {hero.id} felt a little scared.")
    world.facts["caution"] = True
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1


def _warn(world: World) -> None:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    world.say(f'"Do not open the attic," {companion.label} said softly. "If the house is warning us, we should listen."')
    hero.memes["hesitation"] = hero.memes.get("hesitation", 0.0) + 1


def _resolve(world: World) -> None:
    hero = world.facts["hero"]
    cat = world.facts["cat"]
    world.para()
    _emit_sound(world, SOUND_LIBRARY["scrape"])
    world.say(f"The scrape came from the side door instead of the attic, so {hero.id} followed it carefully.")
    world.say(f"Behind the safer door, {cat.label} was curled into a warm little ball, hiding from the dark.")
    world.say(f"{hero.id} picked up {cat.label}, shut the attic door again, and the whole house fell into a gentle hush.")
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["fear"] = 0.0
    world.facts["resolved"] = True


def tell(params: StoryParams) -> World:
    world = _make_world(params)
    _setup(world)
    _turn(world)
    _warn(world)
    _resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    return [
        'Write a short ghost story for a young child that includes the sound "knick" and ends safely.',
        f"Tell a cautionary story where {hero.id} hears a knick in {world.place.label} and {companion.label} helps {hero.pronoun('object')} choose the safe door.",
        "Make the story eerie but gentle, with sound effects and a warning that is obeyed in the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    companion = world.facts["companion"]
    cat = world.facts["cat"]
    return [
        QAItem(
            question=f"What sound kept coming from upstairs in the story?",
            answer="The sound was knick, and it kept getting closer, which made the night feel spooky.",
        ),
        QAItem(
            question=f"Why did {hero.id} decide not to open the attic?",
            answer=f"{companion.label} warned that the attic should not be opened after dark, and the eerie knick sound made {hero.id} listen.",
        ),
        QAItem(
            question=f"What did {hero.id} find behind the safer door?",
            answer=f"{hero.id} found {cat.label}, a lost cat hiding from the dark, so the scary feeling turned into relief.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a warning note?",
            answer="A warning note is a message that tells someone to be careful or to avoid doing something unsafe.",
        ),
        QAItem(
            question="What does a creaky floor sound like?",
            answer="A creaky floor sounds like an old wooden board making little squeaks or groans when someone steps on it.",
        ),
        QAItem(
            question="Why can dark rooms feel spooky?",
            answer="Dark rooms can feel spooky because you cannot see well, so small sounds seem bigger and more mysterious.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
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
    lines.append(f"place: {world.place.label} darkness={world.place.darkness} creakiness={world.place.creakiness}")
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  sounds: {[s.text for s in world.sounds]}")
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


ASP_RULES = r"""
% A cautious story is valid when the knick sound appears, a warning exists,
% and the child reaches a safe resolution instead of opening the attic.
heard_knick(knick).
warning_present(old_house).
safe_resolution(old_house) :- heard_knick(knick), warning_present(old_house).
valid_story(old_house) :- safe_resolution(old_house).
#show valid_story/1.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("heard_knick", "knick"),
        asp.fact("warning_present", "old_house"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py_ok = {"old_house"}
    asp_ok = {a[0] for a in asp_valid()}
    if asp_ok == py_ok:
        print("OK: ASP and Python agree on the cautionary ghost-story gate.")
        return 0
    print("MISMATCH:")
    print("  asp:", sorted(asp_ok))
    print("  py :", sorted(py_ok))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="old_house", hero_name="Mina", hero_type="girl", companion="grandmother"),
    StoryParams(place="attic_hall", hero_name="Eli", hero_type="boy", companion="father"),
    StoryParams(place="quiet_room", hero_name="June", hero_type="girl", companion="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        print(asp_program("#show valid_story/1."))
        print("Models:", asp_valid())
        return

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
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
            header = f"### {p.hero_name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
