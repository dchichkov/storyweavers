#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/typical_flashback_pirate_tale.py
=================================================================

A small standalone storyworld for a pirate tale with a flashback instrument.
The premise is typical for TinyStories-style adventure: a child crew faces a
simple problem, remembers an earlier lesson, and uses that memory to choose a
safer, kinder ending.

The world model keeps the story grounded in changing state:
- children have emotional memes and physical meters
- pirate props and treasures have properties and location
- a flashback can reveal an earlier clue that changes the current choice

The generated stories stay small and complete:
setup -> trouble -> flashback -> turn -> resolution.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    location: str = ""
    portable: bool = True
    valuable: bool = False
    wettable: bool = False
    helpful: bool = False
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
class Place:
    id: str
    label: str
    dark_spot: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
class PirateProp:
    id: str
    label: str
    phrase: str
    shines: bool = False
    helpful: bool = False
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
class FlashbackCue:
    id: str
    memory_line: str
    lesson: str
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


@dataclass
class Problem:
    id: str
    detail: str
    risk: str
    severity: int
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
        import copy as _copy

        clone = World()
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    prop: str
    problem: str
    response: str
    flashback: str
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


PLACES = {
    "dock": Place(
        id="dock",
        label="the old dock",
        dark_spot="the water under the dock",
        scene="a pirate ship made of crates and rope",
        affords={"rope", "map"},
    ),
    "cove": Place(
        id="cove",
        label="the quiet cove",
        dark_spot="the cave behind the rocks",
        scene="a sandy cove with shells for coins",
        affords={"rope", "map"},
    ),
}

PROPS = {
    "lantern": PirateProp(
        id="lantern",
        label="a lantern",
        phrase="a little lantern with a brass handle",
        shines=True,
        helpful=True,
        tags={"light"},
    ),
    "map": PirateProp(
        id="map",
        label="a map",
        phrase="a crinkly map with a red X",
        helpful=True,
        tags={"map"},
    ),
    "rope": PirateProp(
        id="rope",
        label="a rope",
        phrase="a coil of rope",
        helpful=False,
        tags={"rope"},
    ),
}

PROBLEMS = {
    "dark": Problem(
        id="dark",
        detail="it was too dark to see the treasure",
        risk="they might trip on the rocks",
        severity=1,
        tags={"dark"},
    ),
    "lost_key": Problem(
        id="lost_key",
        detail="the key to the treasure chest was missing",
        risk="they could not open the chest",
        severity=2,
        tags={"key"},
    ),
}

FLASHBACKS = {
    "candle_memory": FlashbackCue(
        id="candle_memory",
        memory_line="A few days ago, they had seen a candle tip and the smoke had scared everyone.",
        lesson="Fire was not a toy, and a safe light was better than a flame.",
        tags={"fire", "memory"},
    ),
    "storm_memory": FlashbackCue(
        id="storm_memory",
        memory_line="They remembered a stormy night when a lantern had helped them cross the hall.",
        lesson="A steady light can guide friends through the dark.",
        tags={"light", "memory"},
    ),
}

RESPONSES = {
    "wait_and_listen": Response(
        id="wait_and_listen",
        sense=3,
        power=3,
        text="held the lantern up, waited, and listened until they found the right path",
        fail="looked around in a panic, but the dark stayed confusing",
        qa_text="held the lantern up and listened until the path made sense",
        tags={"light"},
    ),
    "make_brave_choice": Response(
        id="make_brave_choice",
        sense=3,
        power=2,
        text="remembered the lesson and chose the safe lantern instead of guessing",
        fail="tried to guess their way through, but that did not help",
        qa_text="remembered the lesson and chose the safe lantern",
        tags={"light", "memory"},
    ),
    "rush_ahead": Response(
        id="rush_ahead",
        sense=1,
        power=1,
        text="ran ahead with a shout",
        fail="ran ahead and got more mixed up",
        qa_text="ran ahead",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Leo", "Sam", "Finn"]
TRAITS = ["curious", "careful", "brave", "playful", "clever"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in PLACES:
        for problem in PROBLEMS:
            for flashback in FLASHBACKS:
                for response in RESPONSES:
                    if response == "rush_ahead":
                        continue
                    combos.append((place, problem, flashback, response))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.flashback not in FLASHBACKS:
        raise StoryError("Unknown flashback cue.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < 2:
        raise StoryError("That response is too careless for a child-friendly pirate tale.")


def _predict(world: World, place: Place, problem: Problem) -> bool:
    return problem.id == "dark" and "light" in place.affords


def tell(world: World, place: Place, hero: Entity, friend: Entity, parent: Entity,
         prop: Entity, problem: Problem, flashback: FlashbackCue, response: Response) -> World:
    hero.memes["curiosity"] += 1
    friend.memes["joy"] += 1

    world.say(
        f"{hero.id} and {friend.id} made a typical pirate game at {place.label}. "
        f"{place.scene}."
    )
    world.say(
        f"They were searching for treasure, but {problem.detail}."
    )
    world.para()

    if _predict(world, place, problem):
        world.say(
            f'{friend.id} pointed at the dark spot. "We need light," {friend.pronoun()} said.'
        )
        world.say(
            f"{hero.id} frowned and then remembered something old: {flashback.memory_line}"
        )
        hero.memes["memory"] += 1
        hero.memes["caution"] += 1
        world.say(f"The flashback gave {hero.id} a better idea: {flashback.lesson}")

        if response.sense >= 2:
            world.para()
            if response.power >= problem.severity:
                world.say(
                    f"{parent.label_word.capitalize()} came over and {response.text}."
                )
                prop.meters["useful"] += 1
                friend.memes["relief"] += 1
                hero.memes["pride"] += 1
                world.say(
                    f"At last, the pirates saw the chest, and the lantern glowed like a tiny star."
                )
                world.say(
                    f"{hero.id} and {friend.id} smiled, because the flashback had helped them choose well."
                )
            else:
                world.say(
                    f"{parent.label_word.capitalize()} came over and {response.fail}."
                )
                world.say(
                    f"They still had to step back from the rocks, but they stayed safe and tried again later."
                )
                friend.memes["worry"] += 1
    else:
        world.say(f"They went on, but the place did not give them a safe path.")
        world.say(f"The flashback still helped {hero.id} slow down and think.")
        world.para()
        world.say(
            f"{parent.label_word.capitalize()} smiled and said they could look again in the morning."
        )

    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        prop=prop,
        place=place,
        problem=problem,
        flashback=flashback,
        response=response,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a pirate tale for a young child that includes the word "typical" and uses a flashback.',
        f"Tell a pirate story where {f['hero'].id} remembers an earlier lesson before choosing what to do in the dark.",
        f"Write a short adventure where a flashback helps {f['hero'].id} and {f['friend'].id} find treasure safely.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    flashback: FlashbackCue = f["flashback"]
    problem: Problem = f["problem"]
    response: Response = f["response"]
    parent: Entity = f["parent"]
    place: Place = f["place"]
    return [
        QAItem(
            question="Who are the story about?",
            answer=f"The story is about {hero.id} and {friend.id}, who were playing pirates at {place.label}. {parent.label_word.capitalize()} was nearby to help if needed.",
        ),
        QAItem(
            question="What was the problem in the story?",
            answer=f"The problem was that {problem.detail}. That made the treasure hard to find until they found a safer way forward.",
        ),
        QAItem(
            question="Why did the flashback matter?",
            answer=f"The flashback mattered because {flashback.memory_line.lower()} {flashback.lesson} It helped {hero.id} stop and make a careful choice instead of rushing ahead.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} and {friend.id} choosing {response.qa_text}. The dark place became manageable, and the pirates felt proud of their choice.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened earlier. It helps explain why a character makes a choice now.",
        ),
        QAItem(
            question="Why can a lantern be useful on a pirate adventure?",
            answer="A lantern gives steady light in the dark. That helps pirates see where they are going without guessing.",
        ),
        QAItem(
            question="What does it mean when a story says something is typical?",
            answer="Typical means ordinary or normal for that kind of thing. It tells you the story is starting with a familiar kind of event.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.location:
            parts.append(f"location={e.location}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    lines.append("  fired rules: " + ", ".join(sorted({n for n, *_ in world.fired})))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in PLACES[pid].affords:
            lines.append(asp.fact("affords", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("severity", pid, PROBLEMS[pid].severity))
    for fid in FLASHBACKS:
        lines.append(asp.fact("flashback", fid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pr, F, R) :- place(P), problem(Pr), flashback(F), response(R), sense(R,S), S >= 2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid-combos disagree.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, hero=None, hero_gender=None, friend=None, friend_gender=None,
            parent=None, prop=None, problem=None, response=None, flashback=None
        ), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        ok = False
        print(f"MISMATCH: smoke test failed: {exc}")
    if ok:
        print("OK: ASP parity and smoke test passed.")
        return 0
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny pirate tale with a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--flashback", choices=FLASHBACKS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    choices = [c for c in valid_combos()
               if (args.place is None or c[0] == args.place)
               and (args.problem is None or c[1] == args.problem)
               and (args.flashback is None or c[2] == args.flashback)
               and (args.response is None or c[3] == args.response)]
    if not choices:
        raise StoryError("No valid combination matches the given options.")
    place, problem, flashback, response = rng.choice(choices)
    hero_gender = rng.choice(["girl", "boy"])
    friend_gender = "boy" if hero_gender == "girl" else "girl"
    hero = args.name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice([n for n in (BOY_NAMES + GIRL_NAMES) if n != hero])
    parent = rng.choice(["mother", "father"])
    prop = rng.choice(list(PROPS))
    return StoryParams(
        place=place,
        hero=hero,
        hero_gender=hero_gender,
        friend=friend,
        friend_gender=friend_gender,
        parent=parent,
        prop=prop,
        problem=problem,
        response=response,
        flashback=flashback,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.problem not in PROBLEMS:
        raise StoryError("Unknown problem.")
    if params.flashback not in FLASHBACKS:
        raise StoryError("Unknown flashback.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    reasonableness_gate(params)

    world = World()
    place = PLACES[params.place]
    problem = PROBLEMS[params.problem]
    flashback = FLASHBACKS[params.flashback]
    response = RESPONSES[params.response]

    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    parent = world.add(Entity(id=params.parent.capitalize(), kind="character", type="mother" if params.parent == "mother" else "father", role="parent"))
    prop = world.add(Entity(id=PROPS[params.prop].label, kind="thing", type="tool", label=PROPS[params.prop].label, helpful=PROPS[params.prop].helpful))
    prop.location = place.label

    world.say(f"{hero.id} and {friend.id} were having a typical pirate day at {place.label}.")
    world.say(f"{place.scene} They searched for treasure and laughed like little captains.")
    world.para()
    world.say(f"But {problem.detail}.")
    world.say(f"That meant {problem.risk}.")
    world.para()
    world.say(f"Then {hero.id} remembered an earlier moment.")
    world.say(f"{flashback.memory_line}")
    world.say(f"{flashback.lesson}")
    world.para()
    if response.sense >= 2:
        if response.power >= problem.severity:
            world.say(f"{parent.label_word.capitalize()} came over and {response.text}.")
            prop.meters["useful"] += 1
            hero.memes["relief"] += 1
            friend.memes["relief"] += 1
            world.say(f"At last, the pirates found the way, and the lantern glow made the rocks look kind.")
            world.say(f"{hero.id} smiled because the flashback had turned a worry into a safe plan.")
        else:
            world.say(f"{parent.label_word.capitalize()} came over and {response.fail}.")
            world.say("They backed up and tried again later, now slower and wiser.")
    world.facts.update(
        hero=hero,
        friend=friend,
        parent=parent,
        prop=prop,
        place=place,
        problem=problem,
        flashback=flashback,
        response=response,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
    StoryParams(
        place="dock",
        hero="Mia",
        hero_gender="girl",
        friend="Tom",
        friend_gender="boy",
        parent="mother",
        prop="lantern",
        problem="dark",
        response="wait_and_listen",
        flashback="storm_memory",
    ),
    StoryParams(
        place="cove",
        hero="Ben",
        hero_gender="boy",
        friend="Nora",
        friend_gender="girl",
        parent="father",
        prop="map",
        problem="lost_key",
        response="make_brave_choice",
        flashback="candle_memory",
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
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
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
