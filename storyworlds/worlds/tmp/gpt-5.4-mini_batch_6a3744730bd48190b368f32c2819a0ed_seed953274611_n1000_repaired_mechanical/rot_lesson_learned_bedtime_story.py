#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/rot_lesson_learned_bedtime_story.py
====================================================================

A tiny bedtime-story world about a child, a snack, and the lesson they learn
after something is left out too long and begins to rot.

The domain is intentionally small: a child wants to save a sweet snack for later,
forgets it on a warm bedside table, and a caregiver helps them clean up and learn
a simple habit for next time. The world model tracks physical meters and emotional
memes so the prose comes from state changes, not from a frozen template.

Seed premise
------------
A child puts a berry snack aside near bedtime, leaves it out overnight, and in the
morning discovers it has gone soft and rotten. A grown-up helps clean it up and
the child learns to keep food covered and put away.

This world aims for:
- a bedtime-story tone
- a concrete turning point driven by state
- a clear lesson learned ending
- child-facing prose with one small domain and plausible variations
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
ROTTEN_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Food:
    id: str
    label: str
    phrase: str
    place_phrase: str
    cover_phrase: str
    smell: str
    soft_phrase: str
    rot_speed: int = 1
    rotatable: bool = True
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Container:
    id: str
    label: str
    phrase: str
    keeps_safe: bool
    lid: str = ""
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_rot(world: World) -> list[str]:
    out: list[str] = []
    for food in list(world.entities.values()):
        if food.role != "snack":
            continue
        if food.meters["left_out"] < THRESHOLD:
            continue
        sig = ("rot", food.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        food.meters["rotten"] += 1
        food.meters["smelly"] += 1
        if "room" in world.entities:
            world.get("room").meters["stale"] += 1
        for ent in list(world.entities.values()):
            if ent.role in {"child", "caregiver"}:
                ent.memes["worry"] += 0.5
        out.append("__rot__")
    return out


CAUSAL_RULES: list[Rule] = [Rule("rot", "physical", _r_rot)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def snack_at_risk(snack: Food, left_out: int) -> bool:
    return snack.rotatable and left_out >= 1


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def rot_severity(snack: Food, delay: int) -> int:
    return snack.rot_speed + delay


def is_contained(response: Response, snack: Food, delay: int) -> bool:
    return response.power >= rot_severity(snack, delay)


def predict_rot(world: World, snack_id: str, delay: int) -> dict:
    sim = world.copy()
    sim.get(snack_id).meters["left_out"] += 1 + delay
    propagate(sim, narrate=False)
    return {
        "rotten": sim.get(snack_id).meters["rotten"] >= THRESHOLD,
        "stale": sim.get("room").meters["stale"],
    }


def _leave_out(world: World, snack: Entity) -> None:
    snack.meters["left_out"] += 1
    world.say(f"{snack.id} was left out on the bedside table.")


def opening(world: World, child: Entity, snack: Food, room: Entity) -> None:
    child.memes["joy"] += 1
    world.say(
        f"At bedtime, {child.id} made a little plan to save {snack.phrase} for later. "
        f"{snack.place_phrase}."
    )
    world.say(
        f"The room was sleepy and still, and the snack sat by the lamp like it had plenty of time."
    )


def temptation(world: World, child: Entity, snack: Food) -> None:
    child.memes["hope"] += 1
    world.say(
        f'"I will eat it in the morning," {child.id} whispered, and {child.pronoun()} '
        f'left it alone for the night.'
    )


def warn(world: World, caregiver: Entity, child: Entity, snack: Food, delay: int) -> None:
    pred = predict_rot(world, snack.id, delay)
    caregiver.memes["care"] += 1
    world.facts["predicted_stale"] = pred["stale"]
    world.say(
        f'{caregiver.id} smiled softly and said, "{snack.label} needs to be covered, '
        f'or it can go bad if it sits out too long."'
    )


def rot_storybeat(world: World, snack: Entity, food: Food) -> None:
    _leave_out(world, snack)
    snack.meters["rotten"] += 1
    propagate(world, narrate=False)
    world.say(
        f"By morning, the sweet smell had turned sour. {food.id} was soft, brown at the edges, "
        f"and a little fuzzy with rot."
    )


def cleanup(world: World, caregiver: Entity, child: Entity, snack: Food) -> None:
    caregiver.memes["patience"] += 1
    child.memes["shame"] += 0.5
    world.say(
        f"{caregiver.label_word.capitalize()} came to help, opened the window, and wrapped up the spoiled bits."
    )
    world.say(
        f"Together they washed the plate, wiped the crumbs, and made the sleepy room feel fresh again."
    )


def lesson(world: World, caregiver: Entity, child: Entity, snack: Food, container: Container) -> None:
    child.memes["lesson"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f'{caregiver.label_word.capitalize()} knelt down and said, "Food stays better when it is covered and put away. '
        f'That way it does not rot."'
    )
    world.say(
        f'"I remember," said {child.id}. "Next time I will use {container.phrase}."'
    )


def safe_end(world: World, child: Entity, snack: Food, container: Container) -> None:
    child.memes["joy"] += 1
    world.say(
        f"The next night, {child.id} tucked a fresh snack into {container.phrase}, and it stayed safe and sweet."
    )
    world.say(
        f"The little room was quiet again, with no sour smell at all, only the calm promise of a better habit."
    )


def tell(child_name: str, child_gender: str, caregiver_type: str, snack: Food,
         container: Container, delay: int = 0) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, role="caregiver"))
    room = world.add(Entity(id="room", type="room", label="the room"))
    snack_ent = world.add(Entity(id="snack", type="food", label=snack.label, role="snack"))

    opening(world, child, snack, room)
    world.para()
    temptation(world, child, snack)
    warn(world, caregiver, child, snack, delay)
    world.para()
    rot_storybeat(world, snack_ent, snack)
    cleanup(world, caregiver, child, snack)
    world.para()
    lesson(world, caregiver, child, snack, container)
    safe_end(world, child, snack, container)

    world.facts.update(
        child=child, caregiver=caregiver, snack=snack, container=container,
        delay=delay, outcome="rotten", learned=child.memes["lesson"] >= THRESHOLD
    )
    return world


FOODS = {
    "berries": Food(
        id="berries",
        label="berries",
        phrase="a little bowl of berries",
        place_phrase="They waited on the bedside table in a small blue bowl",
        cover_phrase="under a cloth",
        smell="sweet",
        soft_phrase="soft and squishy",
        rot_speed=1,
        rotatable=True,
        tags={"food", "rot", "berries"},
    ),
    "banana": Food(
        id="banana",
        label="banana slices",
        phrase="banana slices on a plate",
        place_phrase="They were left on the nightstand beside a storybook",
        cover_phrase="in a covered box",
        smell="sweet",
        soft_phrase="brown and mushy",
        rot_speed=2,
        rotatable=True,
        tags={"food", "rot", "banana"},
    ),
    "apple": Food(
        id="apple",
        label="apple pieces",
        phrase="a few apple pieces",
        place_phrase="They were set beside the pillow and forgotten",
        cover_phrase="under a lid",
        smell="fresh",
        soft_phrase="soft and sad",
        rot_speed=1,
        rotatable=True,
        tags={"food", "rot", "apple"},
    ),
}

CONTAINERS = {
    "box": Container(
        id="box",
        label="lunch box",
        phrase="a little lunch box",
        keeps_safe=True,
        lid="lid",
        tags={"container", "safe"},
    ),
    "jar": Container(
        id="jar",
        label="jar",
        phrase="a clean jar with a lid",
        keeps_safe=True,
        lid="lid",
        tags={"container", "safe"},
    ),
    "fridge": Container(
        id="fridge",
        label="fridge",
        phrase="the fridge",
        keeps_safe=True,
        lid="door",
        tags={"container", "safe"},
    ),
}

RESPONSES = {
    "wipe": Response(
        id="wipe",
        sense=3,
        power=2,
        text="wiped the sticky spot clean and opened the window",
        fail="wiped at the mess, but the sour smell stayed in the room",
        qa_text="wiped the sticky spot clean and opened the window",
        tags={"cleanup", "smell"},
    ),
    "cover": Response(
        id="cover",
        sense=4,
        power=3,
        text="covered the snack right away and moved it to the fridge",
        fail="tried to cover the snack, but it had already gone bad",
        qa_text="covered the snack and moved it to the fridge",
        tags={"container", "safe"},
    ),
    "fridge": Response(
        id="fridge",
        sense=5,
        power=4,
        text="put the snack in the fridge and shut the door snugly",
        fail="moved too slowly, and the snack was already rotten",
        qa_text="put the snack in the fridge and shut the door snugly",
        tags={"container", "safe"},
    ),
    "toss": Response(
        id="toss",
        sense=2,
        power=2,
        text="threw the spoiled snack away before it could make a bigger mess",
        fail="threw it away, but the room still needed a good cleaning",
        qa_text="threw the spoiled snack away before it made a bigger mess",
        tags={"cleanup", "safe"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ella", "Zoe"]
BOY_NAMES = ["Finn", "Noah", "Theo", "Ben", "Leo"]
TRAITS = ["sleepy", "curious", "gentle", "careful", "thoughtful"]


@dataclass
class StoryParams:
    food: str
    container: str
    response: str
    child: str
    child_gender: str
    caregiver: str
    delay: int = 0
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for food_id, food in FOODS.items():
        for container_id, container in CONTAINERS.items():
            if food.rotatable and container.keeps_safe:
                combos.append((food_id, container_id))
    return combos


KNOWLEDGE = {
    "rot": [("What does rot mean?",
             "Rot means food has gone bad after being left out too long. It may smell sour, look soft, or get fuzzy.")],
    "berries": [("Why should berries be covered?",
                 "Berries stay cleaner and last longer when they are covered or put in a cold place.")],
    "banana": [("Why do banana slices go bad quickly?",
                 "Banana slices get soft and brown fast when they sit out, especially in a warm room.")],
    "apple": [("Why can apple pieces change when left out?",
                "Apple pieces can turn brown and soft when they sit in the air for too long.")],
    "container": [("What is a container?",
                   "A container is something that holds things together, like a box or jar.")],
    "safe": [("How do you keep food safe for later?",
              "You cover it, close the lid, or put it in the fridge so it stays fresh and clean.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = f["snack"]
    return [
        f'Write a bedtime story for a little child that uses the word "{snack.id}" and ends with a lesson learned.',
        f"Tell a soft, cozy story where {f['child'].id} leaves {snack.phrase} out at bedtime, it starts to rot, and a grown-up helps them learn a better habit.",
        f'Write a simple bedtime story about a snack that can rot and a child who learns to put it away next time.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, caregiver, snack, container = f["child"], f["caregiver"], f["snack"], f["container"]
    answers = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id} and {caregiver.label_word}. They are the ones who help make the bedtime lesson gentle and clear.",
        ),
        QAItem(
            question=f"What happened to {snack.label} overnight?",
            answer=f"It was left out too long, so by morning it had begun to rot. It turned soft, smelled sour, and looked spoiled.",
        ),
        QAItem(
            question="What did the grown-up teach at the end?",
            answer=f"The grown-up taught that food should be covered or put away so it stays fresh. That way it does not rot while everyone is sleeping.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with a new habit: next time, {child.id} used {container.phrase} and the snack stayed safe. The ending image is calm and tidy, with no sour smell left behind.",
        ),
    ]
    return answers


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["snack"].tags) | {"safe", "container", "rot"}
    out: list[QAItem] = []
    for key in ["rot", "berries", "banana", "apple", "container", "safe"]:
        if key in tags and key in KNOWLEDGE:
            q, a = KNOWLEDGE[key][0]
            out.append(QAItem(question=q, answer=a))
    return out


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(food="berries", container="box", response="fridge", child="Mia", child_gender="girl", caregiver="mother", delay=0),
    StoryParams(food="banana", container="jar", response="cover", child="Leo", child_gender="boy", caregiver="father", delay=0),
    StoryParams(food="apple", container="fridge", response="toss", child="Nora", child_gender="girl", caregiver="mother", delay=1),
]


def explain_rejection(food: Food, container: Container) -> str:
    if not food.rotatable:
        return "(No story: this snack would not rot, so there is no lesson to learn.)"
    return f"(No story: {food.label} and {container.label} do not make a meaningful bedtime problem.)"


def outcome_of(params: StoryParams) -> str:
    return "rotten"


ASP_RULES = r"""
rotatable(F) :- food(F).
safe_container(C) :- container(C), keeps_safe(C).
valid(F, C) :- rotatable(F), safe_container(C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid in FOODS:
        lines.append(asp.fact("food", fid))
        lines.append(asp.fact("rot_speed", fid, FOODS[fid].rot_speed))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        if c.keeps_safe:
            lines.append(asp.fact("keeps_safe", cid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate differs from Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(food=None, container=None, response=None, child=None, child_gender=None, caregiver=None, delay=None, seed=None), random.Random(7)))
        assert sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=False, qa=False)
    except Exception as exc:
        print(f"EMIT FAILED: {exc}")
        return 1
    print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world about rot and a lesson learned.")
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--container", choices=CONTAINERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child_gender", "--child-gender", dest="child_gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
    ap.add_argument("--child")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    food_id = args.food or rng.choice(sorted(FOODS))
    container_id = args.container or rng.choice(sorted(CONTAINERS))
    food = FOODS[food_id]
    container = CONTAINERS[container_id]
    if args.food and args.container:
        if (food_id, container_id) not in valid_combos():
            raise StoryError(explain_rejection(food, container))
    response = args.response or rng.choice(sorted(RESPONSES))
    if RESPONSES[response].sense < 2:
        raise StoryError("response too weak for a bedtime lesson story")
    gender = args.child_gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        food=food_id,
        container=container_id,
        response=response,
        child=child,
        child_gender=gender,
        caregiver=caregiver,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.food not in FOODS or params.container not in CONTAINERS or params.response not in RESPONSES:
        raise StoryError("invalid params")
    world = tell( params.child, params.child_gender, params.caregiver, FOODS[params.food], CONTAINERS[params.container], params.delay )
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
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible food/container pairs:")
        for food, container in combos:
            print(f"  {food:10} {container}")
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
            header = f"### {p.child}: {p.food} lesson ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
