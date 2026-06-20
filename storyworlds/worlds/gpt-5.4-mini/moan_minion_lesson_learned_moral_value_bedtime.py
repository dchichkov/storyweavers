#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py
==================================================================================

A standalone bedtime-style storyworld built from the seed words "moan" and
"minion", with a small simulated domain about a sleepy little helper who makes a
mess, hears a lesson, and learns a moral value.

The world is intentionally tiny: a child, a small minion-like helper toy, a
bedroom, a moonlit routine, and one gentle adult who turns a worry into a calm
lesson. The story variants stay close to bedtime story cadence, but the state
drives the prose: worry can rise, a mess can happen, comfort can lower distress,
and the ending image proves what changed.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py
    python storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py --all
    python storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/moan_minion_lesson_learned_moral_value_bedtime.py --verify
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
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    messy: bool = False
    comforting: bool = False
    shiny: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.label or self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Room:
    id: str
    label: str
    quiet: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class HelperItem:
    id: str
    label: str
    phrase: str
    tiny_action: str
    comfort: str
    lesson: str
    moral: str
    can_moan: bool = True
    shiny: bool = False
    tags: set[str] = field(default_factory=set)

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
    child_name: str
    child_type: str
    adult_type: str
    helper_id: str
    room_id: str
    bedtime_task: str
    comfort_item: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.rooms: dict[str, Room] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_room(self, room: Room) -> Room:
        self.rooms[room.id] = room
        return room

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.rooms = copy.deepcopy(self.rooms)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        room = world.rooms.get("bedroom")
        if room:
            room.memes["tension"] += 1
        out.append("__worry__")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if not ent.messy or ent.meters["streaks"] < THRESHOLD:
            continue
        sig = ("mess", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["oops"] += 1
        room = world.rooms.get("bedroom")
        if room:
            room.meters["mess"] += 1
        out.append("__mess__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    adult = world.entities.get("adult")
    if not child or not helper or not adult:
        return out
    if child.memes["lesson"] < THRESHOLD:
        return out
    if ("kindness", child.id) in world.fired:
        return out
    world.fired.add(("kindness", child.id))
    child.memes["calm"] += 1
    helper.memes["calm"] += 1
    adult.memes["warmth"] += 1
    out.append("__kindness__")
    return out


CAUSAL_RULES = [
    Rule("worry", "social", _r_worry),
    Rule("mess", "physical", _r_mess),
    Rule("kindness", "moral", _r_kindness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def helper_catalog() -> dict[str, HelperItem]:
    return HELPERS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for room_id, room in ROOMS.items():
        for task_id, task in TASKS.items():
            for helper_id, helper in HELPERS.items():
                if task_id in room.affords and helper_id in task.helpers:
                    combos.append((room_id, task_id, helper_id))
    return combos


def reasonableness_gate(room_id: str, task_id: str, helper_id: str) -> bool:
    room = ROOMS[room_id]
    task = TASKS[task_id]
    helper = HELPERS[helper_id]
    return task_id in room.affords and helper_id in task.helpers and helper.sense >= SENSE_MIN


@dataclass
class RoomSpec:
    id: str
    label: str
    affordances: set[str]
    moonbeam: str
    ending_image: str

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
class TaskSpec:
    id: str
    name: str
    verb: str
    noun: str
    moan_text: str
    streak_desc: str
    worry_reason: str
    helpers: set[str]
    moral_value: str

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
    "bedroom": RoomSpec("bedroom", "the bedroom", {"toys", "books", "stars"}, "moonlight", "the moon beam on the pillow"),
    "nursery": RoomSpec("nursery", "the nursery", {"toys", "blanket", "nightlight"}, "soft moonlight", "the pillow fort under the moon"),
    "attic": RoomSpec("attic", "the attic room", {"boxes", "dust", "lantern"}, "silver moonlight", "the quiet blanket nest"),
}

TASKS = {
    "tidy_toys": TaskSpec("tidy_toys", "tidy the toys", "tidy up", "toy bin", "moan", "a few toy trails", "the floor looked crowded", {"bear", "starbot", "lantern"}, "care"),
    "find_book": TaskSpec("find_book", "find the storybook", "look for", "storybook", "moan", "a scattered book trail", "the shelves were too dark to see", {"starbot", "moonlamp", "lantern"}, "patience"),
    "settle_blanket": TaskSpec("settle_blanket", "settle the blanket", "smooth", "blanket", "moan", "rumpled blanket edges", "the blanket kept slipping", {"bear", "moonlamp", "lantern"}, "gentleness"),
}

HELPERS = {
    "bear": HelperItem("bear", "plush bear", "a plush bear", "a sleepy hug", "hugs softly", "Lesson Learned", "Kindness is best when bedtime feels rough.", can_moan=False, tags={"bear", "comfort"}),
    "starbot": HelperItem("starbot", "tiny starbot", "a tiny starbot", "a beep and a blink", "blinks kindly", "Lesson Learned", "Small helpers can make dark places feel brave.", shiny=True, tags={"starbot", "light"}),
    "moonlamp": HelperItem("moonlamp", "moon lamp", "a moon lamp", "a warm glow", "glows softly", "Moral Value", "A gentle light can make a hard task feel easy.", shiny=True, tags={"moonlamp", "light"}),
    "lantern": HelperItem("lantern", "paper lantern", "a paper lantern", "a glowing little circle", "glows like a tiny moon", "Moral Value", "Soft light and soft voices help at bedtime.", shiny=True, tags={"lantern", "light"}),
}

def _make_entity(id: str, kind: str, type: str, label: str = "", role: str = "") -> Entity:
    return Entity(id=id, kind=kind, type=type, label=label, role=role)


def tell(room: RoomSpec, task: TaskSpec, helper: HelperItem,
         child_name: str = "Mina", child_type: str = "girl", adult_type: str = "mother",
         comfort_item: str = "little blanket") -> World:
    world = World()
    child = world.add(_make_entity("child", "character", child_type, child_name, "child"))
    adult = world.add(_make_entity("adult", "character", adult_type, "the parent", "adult"))
    helper_ent = world.add(_make_entity("helper", "thing", "toy", helper.label, "helper"))
    bedroom = world.add_room(Room("bedroom", room.label))
    world.facts["room"] = room
    world.facts["task"] = task
    world.facts["helper"] = helper
    world.facts["child_name"] = child_name
    world.facts["adult_type"] = adult_type
    world.facts["comfort_item"] = comfort_item

    child.memes["love"] += 1
    child.memes["worry"] += 1
    helper_ent.meters["streaks"] = 0.0
    helper_ent.messy = False

    world.say(f"At bedtime, {child_name} was in {room.label}, where the air was very still and the moon kept watch outside.")
    world.say(f"{child_name} hugged {comfort_item} close, and {helper.phrase} waited on the quilt like a tiny friend.")

    world.para()
    world.say(f"Then {child_name} wanted to {task.verb} {task.noun}, but the room felt too dark and quiet.")
    world.say(f"{child_name} let out a soft moan. \"{task.moan_text},\" {child_name} whispered, because {task.worry_reason}.")

    child.memes["worry"] += 1
    helper_ent.meters["streaks"] += 1
    helper_ent.messy = True
    propagate(world, narrate=False)

    world.para()
    if task.id == "find_book":
        world.say(f"So the little helper made the first move: {helper.tiny_action}, and the dark corner looked less scary at once.")
    elif task.id == "settle_blanket":
        world.say(f"So the little helper made the first move: {helper.tiny_action}, and the blanket stopped wriggling away.")
    else:
        world.say(f"So the little helper made the first move: {helper.tiny_action}, and the toy trail began to look tidy again.")

    child.memes["lesson"] += 1
    helper_ent.meters["streaks"] = 0.0
    helper_ent.messy = False
    propagate(world, narrate=False)

    world.say(f"The parent came in with a calm smile and said, \"That was a good lesson learned: {task.moral_value}\".")
    world.say(f"After that, {child_name} used the {helper.label} and the quiet glow to finish the bedtime task.")

    if helper.shiny:
        ending = f"The {helper.label} glowed softly, and {room.ending_image} looked peaceful and safe."
    else:
        ending = f"The room felt peaceful again, and {room.ending_image} rested in the blue night."
    world.say(ending)

    world.facts.update(
        child=child,
        adult=adult,
        helper_ent=helper_ent,
        outcome="settled",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    room: RoomSpec = f["room"]
    task: TaskSpec = f["task"]
    helper: HelperItem = f["helper"]
    name = f["child_name"]
    return [
        f'Write a bedtime story for a small child in {room.label} that includes the word "{task.moan_text}".',
        f"Tell a calm story where {name} lets out a moan, meets a minion-like helper, and learns {task.moral_value} while finishing a bedtime task.",
        f'Write a gentle bedtime story that uses the words "moan" and "minion" and ends with a clear lesson learned.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    task: TaskSpec = f["task"]
    helper: HelperItem = f["helper"]
    name = f["child_name"]
    room: RoomSpec = f["room"]
    return [
        ("Who is the story about?",
         f"It is about {name} in {room.label}, trying to finish a bedtime task with a small helper nearby. The story keeps close to bedtime because the room stays quiet and moonlit."),
        ("Why did {name} moan?".format(name=name),
         f"{name} moaned because {task.worry_reason}. That worry made the task feel harder until the helper brought a calmer feeling."),
        ("What did the helper teach?",
         f"The helper pointed toward {helper.lesson.lower()} and the parent named the moral value: {task.moral_value}. That lesson turned the trouble into a gentle bedtime success."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    helper: HelperItem = f["helper"]
    task: TaskSpec = f["task"]
    qa = []
    qa.append(("What is a bedtime story?",
                "A bedtime story is a short, gentle story told at night to help someone feel calm and ready for sleep. It usually ends softly and safely."))
    qa.append(("What is a moral value?",
                "A moral value is a good quality people try to follow, like kindness, patience, or care. Stories often teach one by showing what choice is best."))
    qa.append(("What does a moon lamp do?",
                "A moon lamp gives off a soft light. Soft light can help a room feel peaceful at bedtime."))
    if helper.shiny:
        qa.append(("Why can a small light help at bedtime?",
                    "A small light helps because it makes dark corners easier to see without being too bright. That can make a child feel brave and calm."))
    if task.id == "find_book":
        qa.append(("Why do books get lost in a room?",
                    "Books can slide behind pillows or under blankets when a room is busy. A slow search works better than a rushed one."))
    return qa


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    for rid, room in world.rooms.items():
        bits = []
        if room.meters:
            bits.append(f"meters={dict(room.meters)}")
        if room.memes:
            bits.append(f"memes={dict(room.memes)}")
        lines.append(f"  {rid:8} (room   ) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
worry(R) :- room(R), tension(R,T), T >= 1.
mess(R) :- room(R), messiness(R,M), M >= 1.
kindness(C) :- child(C), lesson(C,L), L >= 1.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        for h in sorted(task.helpers):
            lines.append(asp.fact("task_helper", tid, h))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        if helper.sense >= SENSE_MIN:
            lines.append(asp.fact("sensible", hid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {hid for hid, h in HELPERS.items() if h.sense >= SENSE_MIN}:
        print("MISMATCH: ASP sensible helpers differ from Python.")
        rc = 1
    sample_params = CURATED[0]
    try:
        sample = generate(sample_params)
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as e:
        print(f"MISMATCH: generation smoke test failed: {e}")
        rc = 1
    else:
        print("OK: generation smoke test passed.")
    return rc


CURATED = [
    StoryParams("Mina", "girl", "mother", "bear", "bedroom", "tidy_toys", "little blanket"),
    StoryParams("Noah", "boy", "father", "starbot", "nursery", "find_book", "blue pillow"),
    StoryParams("Lia", "girl", "mother", "moonlamp", "attic", "settle_blanket", "soft quilt"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime storyworld: a moan, a minion-like helper, and a moral lesson.")
    ap.add_argument("--child", choices=["Mina", "Noah", "Lia"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--comfort", default=None)
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
              if (args.room is None or c[0] == args.room)
              and (args.task is None or c[1] == args.task)
              and (args.helper is None or c[2] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room_id, task_id, helper_id = rng.choice(sorted(combos))
    if not reasonableness_gate(room_id, task_id, helper_id):
        raise StoryError("That story choice is too weak for a bedtime lesson.")
    child_name = args.child or rng.choice(["Mina", "Noah", "Lia"])
    child_type = args.gender or rng.choice(["girl", "boy"])
    adult_type = args.adult or rng.choice(["mother", "father"])
    comfort_item = args.comfort or rng.choice(["little blanket", "blue pillow", "soft teddy"])
    return StoryParams(child_name, child_type, adult_type, helper_id, room_id, task_id, comfort_item)


def generate(params: StoryParams) -> StorySample:
    world = tell(ROOMS[params.room_id], TASKS[params.bedtime_task], HELPERS[params.helper_id],
                 params.child_name, params.child_type, params.adult_type, params.comfort_item)
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible helpers: " + ", ".join(asp_sensible()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.bedtime_task} with {p.helper_id} in {p.room_id}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
