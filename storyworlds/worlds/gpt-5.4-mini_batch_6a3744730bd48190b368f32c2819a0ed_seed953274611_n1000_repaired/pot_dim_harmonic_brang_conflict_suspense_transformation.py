#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pot_dim_harmonic_brang_conflict_suspense_transformation.py
===========================================================================================

A tiny ghost-story world for a dim old house, a quarrel over a strange brass
thing, a suspenseful night sound, and a transformation that turns fear into a
gentle farewell.

The seed words are threaded through the world:
- pot-dim
- harmonic
- brang

The story model is small and classical: a child enters a dark room, a conflict
arises around a mysterious sound-making object, suspense builds as the house
answers back, and the ending reveals a soft transformation rather than a scare.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
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
class HouseRoom:
    id: str
    name: str
    dim: str
    is_haunted: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
class StrangeSound:
    id: str
    word: str
    source: str
    onomatopoeia: str
    kind: str = "sound"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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
class Transformation:
    id: str
    before: str
    after: str
    method: str
    effect: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.room: Optional[HouseRoom] = None
        self.sound: Optional[StrangeSound] = None
        self.change: Optional[Transformation] = None
        self.lines: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict = {}

    def add(self, ent):
        if isinstance(ent, Entity):
            self.entities[ent.id] = ent
        elif isinstance(ent, HouseRoom):
            self.room = ent
        elif isinstance(ent, StrangeSound):
            self.sound = ent
        elif isinstance(ent, Transformation):
            self.change = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.room = _copy.deepcopy(self.room)
        w.sound = _copy.deepcopy(self.sound)
        w.change = _copy.deepcopy(self.change)
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_gender: str
    parent_name: str
    parent_gender: str
    object_name: str
    sound_name: str
    transformation_name: str
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


SETTINGS = {
    "old_house": {"room": "the hallway", "dim": "pot-dim", "mood": "the air felt hushed and old"},
    "attic": {"room": "the attic", "dim": "pot-dim", "mood": "dust floated like tiny ghosts"},
    "cellar": {"room": "the cellar", "dim": "pot-dim", "mood": "the dark felt close and cool"},
}

OBJECTS = {
    "harmonic_box": {"label": "a little harmonic music box", "role": "mystery", "source": "under the floorboard"},
    "harmonic_bell": {"label": "a harmonic brass bell", "role": "mystery", "source": "on a shelf"},
}

SOUNDS = {
    "brang": StrangeSound(id="brang", word="brang", source="the hidden thing", onomatopoeia="Brang!", kind="sound"),
    "soft_brang": StrangeSound(id="soft_brang", word="brang", source="the hidden thing", onomatopoeia="brang...", kind="sound"),
}

TRANSFORMS = {
    "fear_to_calm": Transformation(
        id="fear_to_calm",
        before="fear",
        after="calm",
        method="listening",
        effect="the ghostly hush turned into a friendly song",
    ),
    "cold_to_warm": Transformation(
        id="cold_to_warm",
        before="cold",
        after="warm",
        method="speaking kindly",
        effect="the room seemed less lonely",
    ),
}

GIRLS = ["Mina", "Lily", "Nora", "Ivy", "Rose"]
BOYS = ["Theo", "Finn", "Leo", "Owen", "Eli"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Ghost-story storyworld with dim rooms, a strange sound, and a gentle transformation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_name", choices=OBJECTS)
    ap.add_argument("--sound", dest="sound_name", choices=SOUNDS)
    ap.add_argument("--transformation", dest="transformation_name", choices=TRANSFORMS)
    ap.add_argument("--child")
    ap.add_argument("--parent")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(s, o, snd) for s in SETTINGS for o in OBJECTS for snd in SOUNDS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.sound_name and args.sound_name not in SOUNDS:
        raise StoryError("Unknown sound.")
    if args.object_name and args.object_name not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.transformation_name and args.transformation_name not in TRANSFORMS:
        raise StoryError("Unknown transformation.")

    setting = args.setting or rng.choice(list(SETTINGS))
    object_name = args.object_name or rng.choice(list(OBJECTS))
    sound_name = args.sound_name or rng.choice(list(SOUNDS))
    transformation_name = args.transformation_name or rng.choice(list(TRANSFORMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRLS if gender == "girl" else BOYS)
    parent_name = args.parent or rng.choice(["Mara", "Jon", "Ellen", "Bram"])
    parent_gender = "mother" if parent_name in {"Mara", "Ellen"} else "father"
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_gender=gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        object_name=object_name,
        sound_name=sound_name,
        transformation_name=transformation_name,
        seed=args.seed,
    )


def _build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Invalid setting.")
    if params.object_name not in OBJECTS:
        raise StoryError("Invalid object.")
    if params.sound_name not in SOUNDS:
        raise StoryError("Invalid sound.")
    if params.transformation_name not in TRANSFORMS:
        raise StoryError("Invalid transformation.")

    world = World()
    setting = SETTINGS[params.setting]
    obj = OBJECTS[params.object_name]
    sound = SOUNDS[params.sound_name]
    change = TRANSFORMS[params.transformation_name]

    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    parent = world.add(Entity(id=params.parent_name, kind="character", type=params.parent_gender, role="parent"))
    room = world.add(HouseRoom(id="room", name=setting["room"], dim=setting["dim"]))
    world.add(sound)
    world.add(change)
    world.facts.update(child=child, parent=parent, setting=setting, obj=obj, sound=sound, change=change, room=room)

    child.memes["curiosity"] = 1.0
    child.memes["fear"] = 0.0
    room.meters["dimness"] = 1.0
    world.say(
        f"{child.id} and {parent.id} stepped into {setting['room']} where the light was {setting['dim']}."
    )
    world.say(f"{setting['mood']}. On a dusty shelf sat {obj['label']}.")
    world.para()

    child.memes["unease"] += 1.0
    world.say(
        f"Then came {sound.onomatopoeia} from {obj['source']}, and the sound seemed to say the word {sound.word}."
    )
    world.say(
        f"{child.id} frowned. {parent.id} said the house was only creaking, but the room stayed quiet in a way that made the silence feel louder."
    )
    world.para()

    child.memes["conflict"] += 1.0
    parent.memes["conflict"] += 1.0
    world.say(
        f"{child.id} wanted to run, but {parent.id} wanted to listen. They argued in whispers about whether the sound was a ghost or just an old thing waking up."
    )
    world.say(
        f"The longer they waited, the more the dark corners seemed to lean closer, and even the wallpaper looked like it was holding its breath."
    )
    world.para()

    room.meters["suspense"] += 1.0
    world.say(
        f"At last, {parent.id} knelt beside {child.id} and held up a lamp. Together they followed the sound to the shelf and found {obj['label']} humming softly."
    )
    world.say(
        f"When {child.id} touched it, the brang turned from a scare into a song, and {change.effect}."
    )
    child.memes["fear"] = 0.0
    child.memes["calm"] += 1.0
    parent.memes["calm"] += 1.0
    world.para()

    room.meters["transformed"] += 1.0
    world.say(
        f"The house did not get less old, but it felt different now. {child.id} smiled, {parent.id} smiled too, and the little {change.method} made the dim room seem kind instead of cold."
    )
    world.say(
        f"By the end, the mysterious {sound.word} had become a friendly harmony, and the night felt safe enough for sleep."
    )

    world.facts["outcome"] = "transformed"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a young child that includes the words "pot-dim", "{f["sound"].word}", and "harmonic".',
        f"Tell a suspenseful but gentle story where {f['child'].id} hears {f['sound'].onomatopoeia} in a {f['setting']['room']} and discovers it is not a monster.",
        f"Write a story about conflict over a strange sound, suspense in an old house, and a transformation from fear to calm.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sound = f["sound"]
    change = f["change"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {parent.id}, who go into a dim old house together."),
        ("What strange word did the sound seem to say?", f"It seemed to say {sound.word}. That made the room feel spooky at first."),
        ("What was the conflict in the story?", f"{child.id} wanted to flee, but {parent.id} wanted to listen first. They had to decide whether the sound was a ghost or just an old hidden object."),
        ("How did the suspense end?", f"They found the source and learned the sound was harmless. The fear changed into calm when the object began to sing softly."),
        ("How did the room change?", f"It felt less cold and much kinder by the end. The house stayed old, but the feeling of it transformed."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a ghost story?", "A ghost story is a spooky tale that can still be gentle and safe for children."),
        ("What does dim mean?", "Dim means there is not much light, so it is hard to see clearly."),
        ("What does harmony mean?", "Harmony means sounds fit together nicely, like a soft song."),
        ("What is suspense?", "Suspense is the feeling of waiting to find out what will happen next."),
        ("What is transformation?", "Transformation means something changes into a new form or feeling."),
    ]


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
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    if world.room:
        lines.append(f"  room: {world.room.name} dim={world.room.dim} meters={dict(world.room.meters)}")
    if world.sound:
        lines.append(f"  sound: {world.sound.word} / {world.sound.onomatopoeia}")
    if world.change:
        lines.append(f"  change: {world.change.before}->{world.change.after}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,N) :- setting(S), object(O), sound(N).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for n in SOUNDS:
        lines.append(asp.fact("sound", n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, object_name=None, sound_name=None, transformation_name=None,
            child=None, parent=None, gender=None, seed=777
        ), random.Random(777)))
        _ = sample.story
    except Exception as exc:
        print(f"MISMATCH: smoke test failed: {exc}")
        return 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        emit(sample, trace=False, qa=False)
    print("OK: verify smoke test ran.")
    return rc


CURATED = [
    StoryParams(setting="old_house", child_name="Mina", child_gender="girl", parent_name="Mara", parent_gender="mother", object_name="harmonic_box", sound_name="brang", transformation_name="fear_to_calm"),
    StoryParams(setting="attic", child_name="Theo", child_gender="boy", parent_name="Bram", parent_gender="father", object_name="harmonic_bell", sound_name="soft_brang", transformation_name="cold_to_warm"),
]


def generate(params: StoryParams) -> StorySample:
    world = _build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.object_name and args.object_name not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.sound_name and args.sound_name not in SOUNDS:
        raise StoryError("Unknown sound.")
    if args.transformation_name and args.transformation_name not in TRANSFORMS:
        raise StoryError("Unknown transformation.")
    setting = args.setting or rng.choice(list(SETTINGS))
    object_name = args.object_name or rng.choice(list(OBJECTS))
    sound_name = args.sound_name or rng.choice(list(SOUNDS))
    transformation_name = args.transformation_name or rng.choice(list(TRANSFORMS))
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child or rng.choice(GIRLS if gender == "girl" else BOYS)
    parent_name = args.parent or rng.choice(["Mara", "Bram", "Ellen", "Jon"])
    parent_gender = "mother" if parent_name in {"Mara", "Ellen"} else "father"
    return StoryParams(
        setting=setting,
        child_name=child_name,
        child_gender=gender,
        parent_name=parent_name,
        parent_gender=parent_gender,
        object_name=object_name,
        sound_name=sound_name,
        transformation_name=transformation_name,
        seed=args.seed,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, o, n in asp_valid_combos():
            print(f"  {s} {o} {n}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        print(json.dumps(samples[0].to_dict() if len(samples) == 1 else [s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
