#!/usr/bin/env python3
"""
Story world: Tuesday ghost sounds and a bad ending.

A small simulated domain inspired by a spooky, child-facing ghost story:
on Tuesday, a child hears strange sound effects in an old house, follows
the clues, and ends with a bad ending that still proves the world changed.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    haunted: bool = False
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    dark: bool = True


@dataclass
class StoryParams:
    name: str
    gender: str
    companion: str
    setting: str = "old house"
    seed: Optional[int] = None
    tuesday: bool = True


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.traces: list[str] = []

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


THRESHOLD = 1.0
SOUND_EFFECTS = {
    "creak": "creeeak",
    "tap": "tap-tap-tap",
    "whisper": "shhhhhh",
    "bang": "BANG",
    "rattle": "clack-clack-clack",
    "wind": "whooooosh",
}


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "old house": Setting(place="the old house", dark=True),
    "attic": Setting(place="the attic", dark=True),
    "hallway": Setting(place="the hallway", dark=True),
}

# Bad-ending ghost story: every valid story leads to trouble, never cleanly fixed.
TUESDAY_SCENES = {
    "old house": {
        "sound": "creak",
        "sfx": SOUND_EFFECTS["creak"],
        "creature": "ghost",
        "turn": "a floorboard sighed underfoot",
        "result": "the door shut on its own",
    },
    "attic": {
        "sound": "rattle",
        "sfx": SOUND_EFFECTS["rattle"],
        "creature": "ghost",
        "turn": "something small rattled in the dark",
        "result": "the lantern went out",
    },
    "hallway": {
        "sound": "tap",
        "sfx": SOUND_EFFECTS["tap"],
        "creature": "ghost",
        "turn": "little taps came from the empty wall",
        "result": "the hallway felt colder than before",
    },
}

TRAITS = ["curious", "quiet", "brave", "shy", "restless"]


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------
def _sound_line(sound: str) -> str:
    return SOUND_EFFECTS.get(sound, sound)


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.gender not in {"girl", "boy"}:
        raise StoryError("Unknown gender.")
    setting = SETTINGS[params.setting]
    world = World(setting)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"fear": 0.0, "courage": 1.0, "cold": 0.0, "ghost_close": 0.0},
        memes={"curiosity": 1.0, "unease": 0.0, "hope": 1.0},
    ))
    companion = world.add(Entity(
        id="companion",
        kind="character",
        type="cat" if params.companion == "cat" else "dog",
        label=params.companion,
        meters={"fear": 0.0, "warmth": 1.0},
        memes={"alert": 1.0},
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="ghost",
        label="the ghost",
        haunted=True,
        hidden=True,
        meters={"cold": 1.0, "near": 0.0},
        memes={"mischief": 1.0},
    ))
    key = world.add(Entity(
        id="music_box",
        kind="thing",
        type="music box",
        label="music box",
        phrase="an old music box with chipped paint",
        hidden=True,
        meters={"dust": 1.0},
    ))
    world.facts.update(child=child, companion=companion, ghost=ghost, key=key)
    return world


def predict_scare(world: World) -> bool:
    return world.get("ghost").meters["near"] >= THRESHOLD


def narrate_setup(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    comp = world.get("companion")
    scene = TUESDAY_SCENES[params.setting]

    world.say(
        f"It was Tuesday, and {child.label} was in {world.setting.place} with {comp.label}."
    )
    world.say(
        f"{child.label.capitalize()} liked listening for strange sound effects, because "
        f"the quiet could suddenly turn into {_sound_line(scene['sound'])}."
    )
    world.say(
        f"That day, the dark room felt tense, and {comp.label} kept its ears pointed at the corners."
    )


def narrate_turn(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    scene = TUESDAY_SCENES[params.setting]
    ghost = world.get("ghost")
    key = world.get("music_box")

    child.memes["curiosity"] += 1
    world.say(
        f"Then {scene['turn']}; {child.label} heard {_sound_line(scene['sound'])} again, "
        f"so {child.label} followed the sound deeper inside."
    )

    ghost.hidden = False
    ghost.meters["near"] = 1.0
    child.meters["ghost_close"] += 1.0
    child.meters["fear"] += 1.0
    child.memes["unease"] += 1.0

    world.say(
        f"Behind a dusty chair, {child.label} found {key.phrase}. "
        f"It gave one last {_sound_line(scene['sound'])}, and the air went cold."
    )
    world.say(
        f"From the corner, the ghost drifted closer without a sound, even though the room was full of sound effects."
    )


def narrate_bad_ending(world: World, params: StoryParams) -> None:
    child = world.get(params.name)
    comp = world.get("companion")
    scene = TUESDAY_SCENES[params.setting]
    ghost = world.get("ghost")
    key = world.get("music_box")

    child.meters["fear"] += 1.0
    child.meters["cold"] += 1.0
    child.memes["hope"] = 0.0
    ghost.meters["near"] += 1.0

    world.say(
        f"Then {_sound_line('bang')}! {scene['result'].capitalize()}, and {child.label} could not reach the door in time."
    )
    world.say(
        f"The ghost took the music box, {comp.label} backed into the wall, and the last thing {child.label} heard was {_sound_line('whisper')} from the dark."
    )
    world.say(
        f"By the time the lights came on, the music box was gone, and Tuesday felt like it had left a cold spot behind."
    )

    key.hidden = True
    world.facts["ending"] = "bad"
    world.facts["sound"] = scene["sound"]
    world.facts["sfx"] = scene["sfx"]


def tell(params: StoryParams) -> World:
    world = build_world(params)
    narrate_setup(world, params)
    world.para()
    narrate_turn(world, params)
    world.para()
    narrate_bad_ending(world, params)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def story_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    return [
        "Write a short ghost story for a young child that takes place on Tuesday and uses sound effects.",
        f"Tell a spooky story about {child.label} hearing strange noises in the old house and finding a hidden music box.",
        "Write a child-friendly ghost story with a scary ending, a Tuesday setting, and lots of eerie sounds.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    comp = world.facts["companion"]
    ghost = world.facts["ghost"]
    key = world.facts["key"]
    sound = world.facts["sound"]
    sfx = world.facts["sfx"]

    return [
        QAItem(
            question=f"What day was it when {child.label} heard the strange sound effects?",
            answer="It was Tuesday, when the house felt extra quiet and spooky.",
        ),
        QAItem(
            question=f"What sound did {child.label} keep hearing in the dark place?",
            answer=f"{child.label.capitalize()} kept hearing {_sound_line(sound)}, and it pulled them farther into the house.",
        ),
        QAItem(
            question=f"What did {child.label} find behind the dusty chair?",
            answer=f"{child.label} found {key.phrase}, and it made a final {sfx} before the ghost came closer.",
        ),
        QAItem(
            question=f"Who stayed with {child.label} during the spooky night?",
            answer=f"{comp.label} stayed nearby, but even the companion could not stop the scary ending.",
        ),
        QAItem(
            question="How did the story end?",
            answer="It ended badly: the ghost took the music box, the lights came on too late, and the cold feeling stayed behind.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a spooky tale about a ghost, strange noises, and a place that feels eerie or haunted.",
        ),
        QAItem(
            question="Why do sound effects matter in a ghost story?",
            answer="Sound effects matter because creaks, whispers, and bangs help make the story feel spooky and tense.",
        ),
        QAItem(
            question="Why is Tuesday mentioned in the story?",
            answer="Tuesday is part of the setup, so the story feels like one particular day when something strange happened.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_story(C) :- child(C).
spooky_day(tuesday) :- tuesday(day).
sound_event(creak) :- sound(creak).
sound_event(tap) :- sound(tap).
sound_event(rattle) :- sound(rattle).

bad_ending(C) :- child_story(C), ghost_near(C), took_item(ghost, music_box).
ghost_near(C) :- fear(C), near_ghost(C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    lines.append(asp.fact("tuesday", "day"))
    lines.append(asp.fact("setting", "old_house"))
    lines.append(asp.fact("sound", "creak"))
    lines.append(asp.fact("sound", "tap"))
    lines.append(asp.fact("sound", "rattle"))
    lines.append(asp.fact("child", "hero"))
    lines.append(asp.fact("took_item", "ghost", "music_box"))
    lines.append(asp.fact("near_ghost", "hero"))
    lines.append(asp.fact("fear", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_check() -> bool:
    # Lazy import only if ASP mode is used.
    import asp
    program = asp_program("#show spooky_day/1. #show sound_event/1. #show bad_ending/1.")
    model = asp.one_model(program)
    atoms = set(asp.atoms(model, "spooky_day")) | set(asp.atoms(model, "sound_event")) | set(asp.atoms(model, "bad_ending"))
    py = {("day",), ("creak",), ("tap",), ("rattle",), ("hero",)}
    return len(atoms) >= 2 and ("day",) in atoms


# ---------------------------------------------------------------------------
# Generate / emit
# ---------------------------------------------------------------------------
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


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} hidden={e.hidden} haunted={e.haunted} meters={e.meters} memes={e.memes}")
    lines.append(f"facts={world.facts}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Theo", "Lily", "Max"]
COMPANIONS = ["cat", "dog"]
GENDERS = ["girl", "boy"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small Tuesday ghost story world with sound effects and a bad ending.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--setting", choices=list(SETTINGS))
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
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    setting = args.setting or rng.choice(list(SETTINGS))
    return StoryParams(name=name, gender=gender, companion=companion, setting=setting, seed=args.seed)


def verify() -> int:
    try:
        ok = asp_check()
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if ok:
        print("OK: ASP twin exercised.")
        return 0
    print("ASP check failed.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show spooky_day/1. #show sound_event/1. #show bad_ending/1."))
        return
    if args.verify:
        sys.exit(verify())
    if args.asp:
        try:
            import asp
            model = asp.one_model(asp_program("#show spooky_day/1. #show sound_event/1. #show bad_ending/1."))
            for atom in model:
                print(atom)
        except Exception as e:
            raise SystemExit(str(e))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for i, nm in enumerate(NAMES[:5]):
            p = StoryParams(name=nm, gender="girl" if i % 2 == 0 else "boy", companion=COMPANIONS[i % 2], setting=list(SETTINGS)[i % len(SETTINGS)], seed=base_seed + i)
            samples.append(generate(p))
    else:
        seen = set()
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
