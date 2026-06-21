#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/boondocks_coupe_humor_teamwork_nursery_rhyme.py
===============================================================================

A small storyworld about a dusty boondocks road, an old coupe, and a cheerful
jam-up that gets solved by teamwork and a little humor.

The domain is built to fit a nursery-rhyme feel:
- concrete, repeatable place and object choices
- a tiny cast with typed entities, physical meters, and emotional memes
- a state-driven turn where the car gets stuck or creaks apart
- a teamwork resolution with a comic beat and a bright ending image

The seed words boondocks and coupe are always present in the story.
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
HUMOR_MIN = 1.0
TEAMWORK_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def noun(self) -> str:
        return self.label or self.type
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
class Place:
    id: str
    label: str
    road: str
    detail: str
    mood: str
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
class Vehicle:
    id: str
    label: str
    phrase: str
    sound: str
    trouble: str
    rescue: str
    rolling: bool = False
    stuck: bool = False
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    comic: str
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
class TeamMove:
    id: str
    sense: int
    power: int
    text: str
    fail: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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


def _r_stuck(world: World) -> list[str]:
    out: list[str] = []
    coupe = world.get("coupe")
    if coupe.meters["stuck"] < THRESHOLD or coupe.stuck:
        return out
    sig = ("stuck", coupe.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    coupe.stuck = True
    for kid in world.characters():
        kid.memes["surprise"] += 1
    out.append("__stuck__")
    return out


def _r_laugh(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["joke"] < THRESHOLD:
            continue
        sig = ("laugh", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["joy"] += 1
        out.append(f"{kid.id} giggled at the silly old coupe.")
    return out


def _r_team(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.characters():
        if kid.memes["helped"] < THRESHOLD:
            continue
        sig = ("team", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["teamwork"] += 1
        out.append(f"{kid.id} pulled with steady hands.")
    return out


CAUSAL_RULES = [
    Rule("stuck", "physical", _r_stuck),
    Rule("laugh", "social", _r_laugh),
    Rule("team", "social", _r_team),
]


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


def stuck_risk(place: Place, vehicle: Vehicle) -> bool:
    return "road" in place.tags and "stuck" in vehicle.tags


def sensible_moves() -> list[TeamMove]:
    return [m for m in MOVES.values() if m.sense >= HUMOR_MIN]


def move_succeeds(move: TeamMove, vehicle: Vehicle) -> bool:
    return move.power >= 1 and not vehicle.stuck


def predict_problem(world: World, vehicle_id: str) -> dict:
    sim = world.copy()
    sim.get(vehicle_id).meters["stuck"] += 1
    propagate(sim, narrate=False)
    coupe = sim.get(vehicle_id)
    return {"stuck": coupe.stuck, "joy": sum(k.memes["joy"] for k in sim.characters())}


def ride_setup(world: World, kids: list[Entity], place: Place, vehicle: Vehicle) -> None:
    a, b = kids
    for kid in kids:
        kid.memes["joy"] += 1
    world.say(
        f"In the boondocks, where the dust went swish and sway, {a.id} and {b.id} "
        f"found an old coupe by the road one day."
    )
    world.say(
        f'{vehicle.phrase} it sat, and {vehicle.sound} it went, as if the car were '
        f'singing a tune to the fence-posts bent.'
    )
    world.say(
        f"{place.detail} made the lane look long and wide, and the children laughed "
        f"as they climbed inside."
    )


def trouble(world: World, driver: Entity, helper: Entity, place: Place, vehicle: Vehicle) -> None:
    driver.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.say(
        f"{driver.id} said, 'Let's roll down the road!' But the boondocks lane was "
        f"bumpy and rough, not smooth and broad."
    )
    world.say(
        f"{helper.id} bit {helper.pronoun('possessive')} lip and gave a wise little grin: "
        f'"That coupe sounds coughy. It might not go in."'
    )


def comic_warning(world: World, helper: Entity, vehicle: Vehicle) -> None:
    helper.memes["humor"] += 1
    world.say(
        f'{helper.id} tapped the hood and said, "If it grumbles like a bear, '
        f'we should not push it in our Sunday hair."'
    )
    world.say(
        f"Even the coupe gave a creak and a squeak, as if it knew it was cranky and weak."
    )


def do_stuck(world: World, vehicle: Vehicle) -> None:
    vehicle.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the coupe sank down with a clunk and a thud; one back wheel spun in the dust and mud."
    )


def teamwork(world: World, a: Entity, b: Entity, move: TeamMove, vehicle: Vehicle) -> None:
    a.memes["helped"] += 1
    b.memes["helped"] += 1
    world.say(
        f"{a.id} and {b.id} looked at each other and started to grin. "
        f'"{move.text}" they said, and the teamwork began.'
    )
    world.say(
        f"{a.id} pushed from the left, {b.id} pushed from the right, and the old coupe "
        f"wobbled and rocked with all of its might."
    )


def rescue(world: World, a: Entity, b: Entity, move: TeamMove, vehicle: Vehicle) -> None:
    vehicle.stuck = False
    vehicle.meters["stuck"] = 0
    a.memes["teamwork"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f"{move.text.capitalize()}, and at last the coupe popped free. "
        f"{move.action} it did, with a jolly little snee!"
    )
    world.say(
        f"Everyone laughed at the dusty old squeal, and the road felt bright as a toy wooden wheel."
    )


def ending(world: World, a: Entity, b: Entity, vehicle: Vehicle) -> None:
    world.say(
        f"So {a.id} and {b.id} waved to the boondocks trees, and the coupe rolled on "
        f"with a soft, merry breeze."
    )
    world.say(
        f"It was still an old coupe, a creaky old prance, but teamwork and humor had helped it dance."
    )


def tell(place: Place, vehicle: Vehicle, move: TeamMove,
         kid1: str = "Mia", kid2: str = "Ned",
         kid1_type: str = "girl", kid2_type: str = "boy") -> World:
    world = World()
    a = world.add(Entity(id=kid1, kind="character", type=kid1_type, role="helper"))
    b = world.add(Entity(id=kid2, kind="character", type=kid2_type, role="driver"))
    car = world.add(Entity(id="coupe", kind="thing", type="vehicle", label=vehicle.label))
    world.facts["place"] = place
    world.facts["vehicle"] = vehicle
    world.facts["move"] = move
    ride_setup(world, [a, b], place, vehicle)
    world.para()
    trouble(world, b, a, place, vehicle)
    comic_warning(world, a, vehicle)
    do_stuck(world, car)
    world.para()
    teamwork(world, a, b, move, car)
    rescue(world, a, b, move, car)
    ending(world, a, b, car)
    world.facts.update(kid1=a, kid2=b, stuck=car.stuck, rescued=not car.stuck)
    return world


@dataclass
class StoryParams:
    place: str
    vehicle: str
    move: str
    kid1: str
    kid2: str
    kid1_type: str
    kid2_type: str
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
    "boondocks_lane": Place(
        id="boondocks_lane",
        label="boondocks lane",
        road="the boondocks road",
        detail="The boondocks lane had a sleepy fence and a wobbly wooden gate",
        mood="dusty",
        tags={"road", "boondocks"},
    ),
    "country_dirt": Place(
        id="country_dirt",
        label="country dirt road",
        road="the country dirt road",
        detail="The country dirt road curled like a ribbon through the grass",
        mood="bouncy",
        tags={"road", "boondocks"},
    ),
}

VEHICLES = {
    "coupe": Vehicle(
        id="coupe",
        label="coupe",
        phrase="There was a little old coupe",
        sound="putt-putt",
        trouble="coughy",
        rescue="pop-free",
        tags={"coupe"},
    ),
    "little_coupe": Vehicle(
        id="little_coupe",
        label="little coupe",
        phrase="There was a little coupe",
        sound="vroom-zoom",
        trouble="snuffly",
        rescue="wiggle-free",
        tags={"coupe"},
    ),
}

MOVES = {
    "push_pull": TeamMove(
        id="push_pull",
        sense=2,
        power=1,
        text="You push, I pull",
        fail="they pushed and pulled but the car stayed still",
        tags={"teamwork", "humor"},
    ),
    "rock_and_roll": TeamMove(
        id="rock_and_roll",
        sense=2,
        power=1,
        text="Rock and roll, all in a row",
        fail="they rocked and rolled, but the wheels only burped",
        tags={"teamwork", "humor"},
    ),
    "tickle_and_push": TeamMove(
        id="tickle_and_push",
        sense=1,
        power=1,
        text="A tickle first, then a push",
        fail="they tickled and pushed, and the coupe only gave a sputter",
        tags={"teamwork", "humor"},
    ),
}

GIRL_NAMES = ["Mia", "Ada", "Nora", "Luna", "Ivy", "Zoe"]
BOY_NAMES = ["Ned", "Otto", "Finn", "Pip", "Rey", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for vehicle in VEHICLES:
            for move in MOVES:
                if stuck_risk(PLACES[place], VEHICLES[vehicle]):
                    combos.append((place, vehicle, move))
    return combos


def explain_rejection(place: Place, vehicle: Vehicle) -> str:
    if "road" not in place.tags:
        return "(No story: this place does not fit the boondocks road scene.)"
    if "coupe" not in vehicle.tags:
        return "(No story: the seed asks for a coupe, and this vehicle is not one.)"
    return "(No story: this combination does not create the right little jam-up.)"


def explain_move(rid: str) -> str:
    move = MOVES[rid]
    good = ", ".join(sorted(m.id for m in sensible_moves()))
    return f"(Refusing move '{rid}': the story wants a sensible teamwork move. Try: {good}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a nursery-rhyme style story that includes the words "boondocks" and "coupe".',
        f"Tell a funny teamwork tale where {f['kid1'].id} and {f['kid2'].id} help a coupe in the boondocks road.",
        f"Write a child-friendly rhyme where an old coupe gets stuck and two kids solve it together with humor.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["kid1"], f["kid2"]
    move = f["move"]
    vehicle = f["vehicle"]
    qa = [
        QAItem(
            question="What did the children find in the boondocks?",
            answer=f"They found an old coupe by the road. It was creaky and funny-looking, but it became the center of their little adventure.",
        ),
        QAItem(
            question="What problem happened to the coupe?",
            answer="The coupe got stuck in the rough road. Its wheel sank down in the dust, so it could not roll on by itself.",
        ),
        QAItem(
            question="How did the children fix the problem?",
            answer=f"They used teamwork: {move.text.lower()}. Together they pushed and pulled until the coupe popped free.",
        ),
    ]
    if f.get("stuck"):
        qa.append(
            QAItem(
                question="Why was the moment funny as well as tricky?",
                answer="The coupe made silly creaky sounds, and the children talked like a little rhyme. That kept the scary part light and cheerful.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is boondocks?",
            answer="Boondocks means a faraway country place. It is a dusty, quiet spot with roads that can be bumpy and old.",
        ),
        QAItem(
            question="What is a coupe?",
            answer="A coupe is a kind of small car with a neat roof and two doors, though a story can imagine any old coupe it likes.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together. Each helper adds a little strength, and the job gets done sooner.",
        ),
        QAItem(
            question="Why can humor help in a hard moment?",
            answer="Humor can make everyone feel braver and less tense. A small laugh can turn a sticky problem into something friendly and manageable.",
        ),
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="boondocks_lane", vehicle="coupe", move="push_pull", kid1="Mia", kid2="Ned", kid1_type="girl", kid2_type="boy"),
    StoryParams(place="country_dirt", vehicle="little_coupe", move="rock_and_roll", kid1="Ada", kid2="Finn", kid1_type="girl", kid2_type="boy"),
    StoryParams(place="boondocks_lane", vehicle="coupe", move="tickle_and_push", kid1="Nora", kid2="Pip", kid1_type="girl", kid2_type="boy"),
]


ASP_RULES = r"""
stuck_vehicle(V) :- vehicle(V), risk(V).
humor(M) :- move(M), sense(M, S), S >= sense_min.
teamwork(M) :- move(M), power(M, P), P >= 1.
valid(P, V, M) :- place(P), vehicle(V), move(M), risk(V), humor(M), teamwork(M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for vid, v in VEHICLES.items():
        lines.append(asp.fact("vehicle", vid))
        if "coupe" in v.tags:
            lines.append(asp.fact("risk", vid))
    for mid, m in MOVES.items():
        lines.append(asp.fact("move", mid))
        lines.append(asp.fact("sense", mid, m.sense))
        lines.append(asp.fact("power", mid, m.power))
    lines.append(asp.fact("sense_min", HUMOR_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP gate differs from valid_combos().")
    try:
        sample = generate(CURATED[0])
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generate() smoke test succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme storyworld about a boondocks coupe, humor, and teamwork.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vehicle", choices=VEHICLES)
    ap.add_argument("--move", choices=MOVES)
    ap.add_argument("--kid1")
    ap.add_argument("--kid2")
    ap.add_argument("--kid1-type", choices=["girl", "boy"])
    ap.add_argument("--kid2-type", choices=["girl", "boy"])
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
    if args.move and MOVES[args.move].sense < HUMOR_MIN:
        raise StoryError(explain_move(args.move))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.vehicle is None or c[1] == args.vehicle)
              and (args.move is None or c[2] == args.move)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, vehicle, move = rng.choice(sorted(combos))
    kid1_type = args.kid1_type or rng.choice(["girl", "boy"])
    kid2_type = args.kid2_type or ("boy" if kid1_type == "girl" else "girl")
    kid1_pool = GIRL_NAMES if kid1_type == "girl" else BOY_NAMES
    kid2_pool = GIRL_NAMES if kid2_type == "girl" else BOY_NAMES
    kid1 = args.kid1 or rng.choice(kid1_pool)
    kid2 = args.kid2 or rng.choice([n for n in kid2_pool if n != kid1] or kid2_pool)
    return StoryParams(place=place, vehicle=vehicle, move=move, kid1=kid1, kid2=kid2, kid1_type=kid1_type, kid2_type=kid2_type)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.vehicle not in VEHICLES or params.move not in MOVES:
        raise StoryError("Invalid params.")
    world = tell(PLACES[params.place], VEHICLES[params.vehicle], MOVES[params.move], params.kid1, params.kid2, params.kid1_type, params.kid2_type)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
