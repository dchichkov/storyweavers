#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/love_dim_lunge_wacko_bad_ending_whodunit.py
============================================================================

A small whodunit-style storyworld about a dim party room, a sudden lunge, a
wacko clue, and a bad ending where the mystery is solved too late. The domain is
kept tiny and state-driven: one detective child, one puzzling suspect, one
careless helper, and one object that goes missing in the dark.

The seed words are woven into the world model and the prose:
- love-dim
- lunge
- wacko

The ending is intentionally bad: the clue is recovered, but only after the
celebration is ruined and the crowd leaves upset.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/love_dim_lunge_wacko_bad_ending_whodunit.py
    python storyworlds/worlds/gpt-5.4-mini/love_dim_lunge_wacko_bad_ending_whodunit.py --all
    python storyworlds/worlds/gpt-5.4-mini/love_dim_lunge_wacko_bad_ending_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/love_dim_lunge_wacko_bad_ending_whodunit.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Room:
    id: str
    label: str
    dimness: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    wacko: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Suspect:
    id: str
    label: str
    alibi: str
    weird: str
    truth: str
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Setting:
    id: str
    place: str
    opening: str
    atmosphere: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class StoryParams:
    setting: str
    detective: str
    suspect: str
    helper: str
    clue: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.clues: dict[str, Clue] = {}
        self.suspects: dict[str, Suspect] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

    def add_suspect(self, suspect: Suspect) -> Suspect:
        self.suspects[suspect.id] = suspect
        return suspect

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.rooms = _copy.deepcopy(self.rooms)
        w.clues = _copy.deepcopy(self.clues)
        w.suspects = _copy.deepcopy(self.suspects)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "love_dim": Setting(
        id="love_dim",
        place="the love-dim library hall",
        opening="The library hall was love-dim, with one weak lamp and shelves that swallowed shadows.",
        atmosphere="quiet and suspicious",
    ),
    "parlor": Setting(
        id="parlor",
        place="the old parlor",
        opening="The old parlor was love-dim too, with velvet chairs and a clock that ticked like a secret.",
        atmosphere="soft and uneasy",
    ),
    "gallery": Setting(
        id="gallery",
        place="the narrow gallery",
        opening="The narrow gallery was love-dim and hushed, with framed pictures staring down like witnesses.",
        atmosphere="hushed and watchful",
    ),
}

DETECTIVES = {
    "mira": Entity(id="Mira", kind="character", type="girl", label="Mira", role="detective"),
    "otto": Entity(id="Otto", kind="character", type="boy", label="Otto", role="detective"),
    "ivy": Entity(id="Ivy", kind="character", type="girl", label="Ivy", role="detective"),
}

HELPERS = {
    "nurse": Entity(id="Nell", kind="character", type="woman", label="Nell", role="helper"),
    "janitor": Entity(id="Jax", kind="character", type="man", label="Jax", role="helper"),
    "uncle": Entity(id="Uncle_Ray", kind="character", type="man", label="Uncle Ray", role="helper"),
}

SUSPECTS = {
    "penny": Suspect(
        id="Penny",
        label="Penny",
        alibi="She said she never left the coat rack.",
        weird="Her shoes were dusty and one sleeve was inside out.",
        truth="She had only chased a rolling marble.",
    ),
    "mr_moon": Suspect(
        id="Mr_Moon",
        label="Mr. Moon",
        alibi="He said he was polishing a brass spoon.",
        weird="His tie was crooked and full of chalk dust.",
        truth="He had tripped over the chair and spilled chalk everywhere.",
    ),
    "aunt_rose": Suspect(
        id="Aunt Rose",
        label="Aunt Rose",
        alibi="She said she was counting teacups in the corner.",
        weird="Her gloves were wet, as if she had touched the window plant.",
        truth="She had watered the plant and heard nothing at first.",
    ),
}

CLUES = {
    "brooch": Clue(id="brooch", label="brooch", phrase="a silver brooch shaped like a star", wacko=False),
    "whistle": Clue(id="whistle", label="whistle", phrase="a tiny whistle with a red ribbon", wacko=True),
    "key": Clue(id="key", label="key", phrase="a small brass key with a wobbly tag", wacko=False),
}

BAD_ENDINGS = {"late", "smash"}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for did in DETECTIVES:
            for su in SUSPECTS:
                for cl in CLUES:
                    combos.append((sid, did, su, cl))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.detective not in DETECTIVES:
        raise StoryError("Unknown detective.")
    if params.suspect not in SUSPECTS:
        raise StoryError("Unknown suspect.")
    if params.helper not in HELPERS:
        raise StoryError("Unknown helper.")
    if params.clue not in CLUES:
        raise StoryError("Unknown clue.")


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    d = world.add_entity(DETECTIVES[params.detective])
    h = world.add_entity(HELPERS[params.helper])
    s = world.add_suspect(SUSPECTS[params.suspect])
    c = world.add_clue(CLUES[params.clue])
    room = world.add_room(Room(id="room", label=setting.place, dimness=setting.atmosphere))
    world.facts.update(detective=d, helper=h, suspect=s, clue=c, room=room, setting=setting)
    return world


def predict_lunge(world: World) -> bool:
    return True


def tell_opening(world: World) -> None:
    setting = world.facts["setting"]
    d = world.facts["detective"]
    world.say(f"{setting.opening} {d.id} noticed that something in the room felt off.")
    world.say(f"{d.id} loved clues, but this room did not love being easy to read.")


def build_tension(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    c = world.facts["clue"]
    h = world.facts["helper"]
    d.memes["curiosity"] += 1
    world.say(f"Then {s.label} gave a story that sounded almost right, but not quite.")
    world.say(f"{s.alibi} {s.weird}")
    if c.wacko:
        world.say(f"On the table lay {c.phrase}; it looked wacko enough to be a clue, and that made everyone stare.")
    else:
        world.say(f"On the table lay {c.phrase}, plain enough to make the room even quieter.")
    world.say(f"{h.id} frowned, because the room's silence made every little thing feel suspicious.")


def do_lunge(world: World) -> None:
    d = world.facts["detective"]
    c = world.facts["clue"]
    s = world.facts["suspect"]
    d.memes["bravery"] += 1
    c.meters["grasped"] += 1
    world.say(f"Suddenly, {d.id} made a quick lunge for {c.label}.")
    world.say(f"The move was fast, almost a wacko leap of hope, and it startled {s.label} more than anyone expected.")


def reveal_too_late(world: World) -> None:
    d = world.facts["detective"]
    h = world.facts["helper"]
    s = world.facts["suspect"]
    c = world.facts["clue"]
    c.meters["lost"] += 1
    room = world.facts["room"]
    room.meters["trouble"] += 1
    world.say(f"{h.id} shouted that the clue had already been moved, but the warning came too late.")
    world.say(f"{s.label} backed away, the lamp flickered, and the room tipped from curious to messy.")
    world.say(f"By the time {d.id} looked again, {c.phrase} was under a chair and the neat trail was broken.")


def bad_ending(world: World) -> None:
    d = world.facts["detective"]
    s = world.facts["suspect"]
    h = world.facts["helper"]
    world.say(f"{d.id} finally solved it: {s.label} had not stolen anything at all.")
    world.say(f"But the reveal was too late to save the evening. {h.id} was upset, the guests were gone, and the party had turned sour.")
    world.say(f"{s.label} left in tears, and {d.id} stood in the love-dim hall with the answer in hand and nobody happy to hear it.")


def tell_story(params: StoryParams) -> World:
    world = build_world(params)
    tell_opening(world)
    world.para()
    build_tension(world)
    world.para()
    if predict_lunge(world):
        do_lunge(world)
    world.para()
    reveal_too_late(world)
    bad_ending(world)
    world.facts.update(
        outcome="bad",
        clue_found=True,
        room_trouble=world.facts["room"].meters["trouble"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a whodunit story that includes the words "love-dim", "lunge", and "wacko".',
        f"Tell a child-friendly mystery where {f['detective'].id} notices a clue in a love-dim room, makes a lunge for it, and learns the truth too late.",
        f"Write a bad-ending detective story with a suspicious helper, a wacko clue, and an answer that comes after the evening has already gone wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = f["detective"]
    s = f["suspect"]
    h = f["helper"]
    c = f["clue"]
    return [
        QAItem(question="Who was trying to solve the mystery?", answer=f"{d.id} was trying to solve the mystery in the love-dim room."),
        QAItem(question="What made the room feel suspicious?", answer=f"The room felt suspicious because {s.label} sounded odd, {c.phrase} looked wacko, and everyone kept watching each other."),
        QAItem(question="Why was the ending bad?", answer=f"The truth came out too late, so the party was ruined, {h.id} was upset, and {s.label} left in tears."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a clue in a mystery?", answer="A clue is a little piece of information that helps someone figure out what happened."),
        QAItem(question="What does it mean to lunge?", answer="To lunge means to move quickly and suddenly toward something."),
        QAItem(question="What does wacko mean?", answer="Wacko means very strange or silly in a way that makes people stare."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()) + list(world.suspects.values()) + list(world.clues.values()):
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if getattr(e, "role", ""):
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,D,U,C) :- setting(S), detective(D), suspect(U), clue(C).
bad_end :- clue_found, room_trouble.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for did in DETECTIVES:
        lines.append(asp.fact("detective", did))
    for uid in SUSPECTS:
        lines.append(asp.fact("suspect", uid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo lists differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny love-dim whodunit with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--detective", choices=DETECTIVES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--clue", choices=CLUES)
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
    combos = valid_combos()
    filtered = [c for c in combos
                if (args.setting is None or c[0] == args.setting)
                and (args.detective is None or c[1] == args.detective)
                and (args.suspect is None or c[2] == args.suspect)
                and (args.clue is None or c[3] == args.clue)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    setting, detective, suspect, clue = rng.choice(filtered)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(setting=setting, detective=detective, suspect=suspect, helper=helper, clue=clue)


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    if params.setting not in SETTINGS or params.detective not in DETECTIVES or params.suspect not in SUSPECTS or params.helper not in HELPERS or params.clue not in CLUES:
        raise StoryError("Invalid parameters.")
    world = tell_story(params)
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
    StoryParams(setting="love_dim", detective="mira", suspect="penny", helper="nurse", clue="whistle"),
    StoryParams(setting="parlor", detective="otto", suspect="mr_moon", helper="janitor", clue="brooch"),
    StoryParams(setting="gallery", detective="ivy", suspect="aunt_rose", helper="uncle", clue="key"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(map(str, asp_valid_combos())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=args.trace, qa=args.qa)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
