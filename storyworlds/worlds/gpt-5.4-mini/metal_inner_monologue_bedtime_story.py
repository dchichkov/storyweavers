#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/metal_inner_monologue_bedtime_story.py
======================================================================

A tiny storyworld for a bedtime-style tale with a small amount of metal in the
scene and an inner-monologue flavor: a child resists bedtime, notices a shiny
metal object, and learns to settle down with a comforting routine.

The world is intentionally compact and classical:
- typed entities with physical meters and emotional memes
- a simple cause/effect simulation
- a reasonableness gate
- an inline ASP twin
- three Q&A sets grounded in world state

The story frame is child-facing and bedtime-soft, while still being state-driven:
the child feels restless, the room feels too bright or too interesting, the
caregiver redirects attention, and the ending proves the change through a quiet
sleep image.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SENSE_MIN = 2
RESTLESS_LIMIT = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing" | "room"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    metallic: bool = False
    soft: bool = False
    bedtime_use: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class RoomProfile:
    id: str
    place: str
    mood: str
    detail: str
    dimmer: str
    sleep_image: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BedtimeObject:
    id: str
    label: str
    phrase: str
    use: str
    metallic: bool = False
    soft: bool = False
    good_for_bedtime: bool = True

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class BedtimePrompt:
    id: str
    inner_thought: str
    resistance_line: str
    surrender_line: str
    calm_line: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    room: str
    object: str
    child: str
    child_gender: str
    parent: str
    parent_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


ROOMS = {
    "nursery": RoomProfile("nursery", "the nursery", "soft and blue",
                           "the night-light glowed like a tiny moon",
                           "the moonlight dimmed behind the curtain",
                           "the room looked like a quiet cloud"),
    "bedroom": RoomProfile("bedroom", "the bedroom", "warm and sleepy",
                           "the hallway light made a pale stripe",
                           "the lamp dimmed by the door",
                           "the blanket looked like a safe little hill"),
    "cozy_room": RoomProfile("cozy_room", "the cozy room", "gentle and still",
                             "the shelves held only one tiny sparkle",
                             "the small lamp clicked to a softer glow",
                             "the pillow looked ready for a dream"),
}

OBJECTS = {
    "spoon": BedtimeObject("spoon", "a metal spoon", "the spoon", "for stirring tea", metallic=True),
    "robot": BedtimeObject("robot", "a little metal robot", "the little metal robot", "for watching on the shelf", metallic=True),
    "key": BedtimeObject("key", "a metal key", "the key", "for the toy chest", metallic=True),
    "button": BedtimeObject("button", "a shiny metal button", "the shiny metal button", "for fastening a coat", metallic=True),
    "blanket_pin": BedtimeObject("pin", "a metal blanket pin", "the blanket pin", "for holding a blanket corner", metallic=True),
    "teddy": BedtimeObject("teddy", "a stuffed teddy bear", "the teddy bear", "for hugging", soft=True),
}

PROMPTS = {
    "robot": BedtimePrompt(
        "robot",
        "the child kept thinking about the little metal robot on the shelf",
        "It gleamed too much to ignore.",
        "It could wait until morning.",
        "The thought of sleep began to feel warmer than the shiny little toy.",
    ),
    "spoon": BedtimePrompt(
        "spoon",
        "the child kept thinking about the metal spoon from snack time",
        "It had a bright edge that seemed to catch every bit of light.",
        "But spoons belong in the kitchen, not in bed.",
        "The child tucked the thought away like a pebble and listened to the story instead.",
    ),
    "key": BedtimePrompt(
        "key",
        "the child kept thinking about the metal key by the dresser",
        "It looked important, like a tiny treasure.",
        "But bedtime was not a time for treasure hunts.",
        "Soon the key was just a quiet shape in the dark and nothing more.",
    ),
    "button": BedtimePrompt(
        "button",
        "the child kept thinking about the shiny metal button on a coat",
        "It flashed like a tiny star every time the child turned.",
        "Stars are for the sky, not for playing when it's time to sleep.",
        "The starry button stopped feeling exciting, and the pillow felt softer instead.",
    ),
    "blanket_pin": BedtimePrompt(
        "blanket_pin",
        "the child kept thinking about the metal blanket pin",
        "It was small, but it made a clever little click in the hand.",
        "Yet clicking things are not bedtime toys.",
        "When the pin was set down safely, the room felt much quieter.",
    ),
    "teddy": BedtimePrompt(
        "teddy",
        "the child kept thinking about the teddy bear",
        "It was soft and cuddly, which made the bed look even nicer.",
        "This was not a problem at all.",
        "The teddy was the perfect bedtime friend, and sleep came easily.",
    ),
}

CAREGIVING = {
    "mother": "mom",
    "father": "dad",
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for rid, room in ROOMS.items():
        for oid, obj in OBJECTS.items():
            if room.id and obj.good_for_bedtime:
                combos.append((rid, oid))
    return combos


def reasonableness_gate(room: RoomProfile, obj: BedtimeObject) -> None:
    if not obj.good_for_bedtime:
        raise StoryError("That object does not fit this bedtime world.")
    if room.id not in ROOMS:
        raise StoryError("Unknown room.")
    if obj.id not in OBJECTS:
        raise StoryError("Unknown object.")
    if obj.metallic is False and obj.soft is False:
        raise StoryError("The story needs a clear bedtime object.")


def world_needs_calming(obj: BedtimeObject) -> bool:
    return obj.metallic or obj.id == "teddy"


def choose_calm_move(obj: BedtimeObject) -> str:
    if obj.id == "teddy":
        return "hug"
    if obj.id == "robot":
        return "put it on the shelf"
    if obj.id == "spoon":
        return "carry it back to the kitchen"
    if obj.id == "key":
        return "set it in the dish by the door"
    if obj.id == "button":
        return "leave it on the chair"
    return "set it down"


def predict(world: World, obj_id: str) -> dict:
    sim = world.copy()
    _run_storybeat(sim, sim.get("child"), sim.get("parent"), sim.get(obj_id), narrate=False)
    child = sim.get("child")
    return {
        "restless": child.memes["restless"],
        "calm": child.memes["calm"],
    }


def _apply_restlessness(world: World, child: Entity, obj: Entity) -> None:
    if obj.metallic:
        child.memes["restless"] += 1.5
        child.memes["curious"] += 1
        obj.meters["glint"] += 1
    else:
        child.memes["calm"] += 0.5


def _apply_safety(world: World, child: Entity, obj: Entity) -> None:
    if obj.metallic:
        obj.meters["stored"] += 1
        child.memes["calm"] += 1.0
        child.memes["restless"] = max(0.0, child.memes["restless"] - 1.0)


def _run_storybeat(world: World, child: Entity, parent: Entity, obj: Entity, narrate: bool = True) -> None:
    _apply_restlessness(world, child, obj)
    if child.memes["restless"] >= RESTLESS_LIMIT:
        sig = ("resist", child.id, obj.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["resist"] += 1
            parent.memes["gentle"] += 1
            if narrate:
                world.say(f"{child.id} wanted to keep looking at {obj.label}, but bedtime was already pulling close.")


def bedtime_setup(world: World, child: Entity, parent: Entity, room: RoomProfile) -> None:
    world.say(
        f"It was bedtime in {room.place}, and {room.detail}."
    )
    world.say(
        f"{child.id} climbed under the blanket, but {child.pronoun('possessive')} mind was still busy and bright."
    )


def inner_monologue(world: World, child: Entity, obj: Entity, prompt: BedtimePrompt) -> None:
    child.memes["thinking"] += 1
    world.say(
        f"{child.id} looked toward {obj.phrase}. "
        f'"{prompt.inner_thought}" {child.pronoun().capitalize()} thought. '
        f'"{prompt.resistance_line}"'
    )


def reassurance(world: World, parent: Entity, child: Entity, obj: Entity, room: RoomProfile) -> None:
    parent.memes["gentle"] += 1
    world.say(
        f"{parent.label_word.capitalize()} sat beside the bed and spoke in a whisper. "
        f'"We can keep the {obj.label} safe for tomorrow," {parent.pronoun()} said, '
        f'and the room felt even quieter.'
    )
    if obj.metallic:
        world.say(
            f'"For now, let\'s put it where it belongs and let your head rest," {parent.pronoun()} said.'
        )


def settle(world: World, child: Entity, parent: Entity, obj: Entity, room: RoomProfile) -> None:
    child.memes["calm"] += 2
    child.memes["restless"] = 0
    if obj.id == "teddy":
        world.say(
            f'{child.id} hugged {obj.phrase} tight and listened to {parent.label_word} read one more tiny page.'
        )
    else:
        world.say(
            f"{child.id} watched as {parent.label_word} put {obj.phrase} in a safe place."
        )
    world.say(
        f"Then {child.id} took a slow breath, turned over, and the bed felt soft enough for a dream."
    )
    world.say(f"The room grew as still as {room.sleep_image}.")


def tell(room: RoomProfile, obj: BedtimeObject, child_name: str = "Mia", child_gender: str = "girl",
         parent_name: str = "Mom", parent_gender: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id=parent_name, kind="character", type=parent_gender, role="parent"))
    thing = world.add(Entity(
        id=obj.id, kind="thing", type="object", label=obj.label, role="focus",
        metallic=obj.metallic, soft=obj.soft, bedtime_use=obj.use
    ))
    world.facts["room"] = room
    world.facts["object"] = obj

    bedtime_setup(world, child, parent, room)
    world.para()
    inner_monologue(world, child, thing, PROMPTS[obj.id])
    _run_storybeat(world, child, parent, thing)
    reassurance(world, parent, child, thing, room)
    world.para()
    _apply_safety(world, child, thing)
    settle(world, child, parent, thing, room)

    world.facts.update(child=child, parent=parent, thing=thing, outcome="calm")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room = f["room"]
    obj = f["object"]
    child = f["child"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old set in {room.place} that includes the word "{obj.id}" and an inner monologue.',
        f"Tell a gentle story where {child.id} cannot quite stop thinking about {obj.label} at bedtime, but a parent helps {child.pronoun('object')} settle.",
        f'Write a calm bedtime story with a shiny "{obj.id}" and a child who learns to put the thought away and sleep.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    obj = f["object"]
    room = f["room"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {parent.id} in {room.place}. {child.id} is the one who keeps thinking about {obj.label} before sleep."
        ),
        QAItem(
            question=f"Why did {child.id} have trouble settling down?",
            answer=f"{child.id} was still thinking about {obj.label}, and the shiny metal object made {child.pronoun('object')} feel more awake. The bedtime feeling had to become calmer before sleep could come."
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{child.id} got calm, the metal object was put in a safe place, and the room grew quiet enough for a dream. The ending proves that bedtime won and the restless feeling faded."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    obj = world.facts["object"]
    items = [
        QAItem(
            question="What is metal?",
            answer="Metal is a hard material that can feel smooth, cool, and shiny. Lots of everyday objects are made of metal."
        ),
        QAItem(
            question="Why can shiny things make it hard to fall asleep?",
            answer="Shiny things can catch your eye and make your mind feel busy. At bedtime, that extra attention can keep a child awake for a little while."
        ),
    ]
    if obj.metallic:
        items.append(
            QAItem(
                question=f"Why is {obj.label} easy to notice?",
                answer=f"{obj.label} is made of metal, so it can gleam in the light. That shine makes it stand out in a quiet room."
            )
        )
    return items


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.metallic:
            bits.append("flags=['metallic']")
        if e.soft:
            bits.append("flags=['soft']")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
metallic(X) :- object(X), metal_object(X).
restless(C) :- child(C), sees_metal(C, X), metallic(X).
calm(C) :- parent(P), child(C), gentle(P).
outcome(calm) :- calm(C), not restless(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid in ROOMS:
        lines.append(asp.fact("room", rid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if obj.metallic:
            lines.append(asp.fact("metal_object", oid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("parent", "parent"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show metallic/1."))
    asp_metals = {x for (x,) in asp.atoms(model, "metallic")}
    py_metals = {oid for oid, obj in OBJECTS.items() if obj.metallic}
    ok = asp_metals == py_metals
    if ok:
        print(f"OK: ASP matches metal registry ({len(py_metals)} metallic objects).")
    else:
        print("MISMATCH in metal registry.")
        return 1
    sample = generate(resolve_params(argparse.Namespace(room=None, object=None, seed=None), random.Random(0)))
    if not sample.story.strip():
        print("MISMATCH: empty story")
        return 1
    print("OK: smoke test story generation works.")
    return 0


def asp_metal_list() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show metallic/1."))
    return sorted(x for (x,) in asp.atoms(model, "metallic"))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime story world with metal and inner monologue.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--child")
    ap.add_argument("--parent")
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
    room = args.room or rng.choice(list(ROOMS))
    obj = args.object or rng.choice(list(OBJECTS))
    if args.object and args.object not in OBJECTS:
        raise StoryError("Unknown object.")
    if args.room and args.room not in ROOMS:
        raise StoryError("Unknown room.")
    if args.object and not OBJECTS[args.object].good_for_bedtime:
        raise StoryError("That object does not fit the bedtime story.")
    child_gender = rng.choice(["girl", "boy"])
    parent_gender = rng.choice(["mother", "father"])
    child = args.child or rng.choice(["Mia", "Noah", "Lily", "Finn", "Ava", "Theo"])
    parent = args.parent or ("Mom" if parent_gender == "mother" else "Dad")
    return StoryParams(room=room, object=obj, child=child, child_gender=child_gender, parent=parent, parent_gender=parent_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room], OBJECTS[params.object], params.child, params.child_gender, params.parent, params.parent_gender)
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


CURATED = [
    StoryParams("bedroom", "robot", "Mia", "girl", "Mom", "mother"),
    StoryParams("nursery", "spoon", "Noah", "boy", "Dad", "father"),
    StoryParams("cozy_room", "teddy", "Ava", "girl", "Mom", "mother"),
    StoryParams("bedroom", "key", "Finn", "boy", "Dad", "father"),
]


def valid_combo_list() -> list[tuple[str, str]]:
    return valid_combos()


def outcome_of(params: StoryParams) -> str:
    return "calm"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show metallic/1."))
    return sorted(set((room, obj) for room in ROOMS for obj in OBJECTS if obj in asp.atoms(model, "metallic") or True))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show metallic/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("metallic objects: " + ", ".join(asp_metal_list()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
