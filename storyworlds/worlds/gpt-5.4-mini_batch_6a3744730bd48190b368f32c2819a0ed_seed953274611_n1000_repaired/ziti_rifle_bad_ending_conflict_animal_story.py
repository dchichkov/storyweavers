#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ziti_rifle_bad_ending_conflict_animal_story.py
===============================================================================

A standalone storyworld about animal friends, a shared bowl of ziti, and a rifle
that turns a small disagreement into a bad ending.

The world is deliberately tiny:
- two animal characters
- one food prize
- one dangerous rifle object
- a conflict that grows when the rifle is mishandled
- a bad ending where the food is ruined and the friends part upset

The prose is child-facing, but the situation is tense and ends badly on purpose.
It still follows the storyworld contract: typed entities, physical meters and
emotional memes, a Python reasonableness gate, an inline ASP twin, QA sets, and
the standard CLI modes.
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
SENSE_MIN = 2


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
    flammable: bool = False
    dangerous: bool = False
    edible: bool = False

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
        return self.label or self.type
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
    scene: str
    has_barn: bool = True
    has_table: bool = True
    has_lantern: bool = False
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
class Food:
    id: str
    label: str
    phrase: str
    plate: str
    serving: str
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
class Rifle:
    id: str
    label: str
    phrase: str
    location: str
    loud: str
    dangerous: bool = True
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


@dataclass
class StoryParams:
    place: str
    food: str
    rifle: str
    animal1: str
    animal1_type: str
    animal2: str
    animal2_type: str
    parent: str
    delay: int = 1
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
        clone.facts = copy.deepcopy(self.facts)
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


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    rifle = world.get("rifle")
    if rifle.meters["bang"] < THRESHOLD:
        return out
    sig = ("spook",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.characters():
        e.memes["fear"] += 1
        e.memes["conflict"] += 1
    out.append("__bang__")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    food = world.get("ziti")
    if food.meters["spilled"] < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    food.meters["ruined"] += 1
    out.append("The ziti slid all over the floor.")
    return out


CAUSAL_RULES = [Rule("spook", "social", _r_spook), Rule("spill", "physical", _r_spill)]


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


def hazard_at_risk(rifle: Rifle, food: Food) -> bool:
    return rifle.dangerous and food.edible


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for rid, rifle in RIFLES.items():
            for fid, food in FOODS.items():
                if hazard_at_risk(rifle, food):
                    combos.append((place, rid, fid))
    return combos


def fire_severity(delay: int) -> int:
    return 1 + delay


def is_contained(response: Response, delay: int) -> bool:
    return response.power >= fire_severity(delay)


def predict_badness(world: World) -> dict:
    sim = world.copy()
    _do_rifle(sim, narrate=False)
    return {
        "bang": sim.get("rifle").meters["bang"] >= THRESHOLD,
        "ruined": sim.get("ziti").meters["ruined"] >= THRESHOLD,
        "conflict": sum(e.memes["conflict"] for e in sim.characters()),
    }


def _do_rifle(world: World, narrate: bool = True) -> None:
    rifle = world.get("rifle")
    rifle.meters["bang"] += 1
    propagate(world, narrate=narrate)


def start(world: World, a: Entity, b: Entity, place: Place, food: Food, rifle: Rifle) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"At {place.label}, {a.id} and {b.id} were eating {food.phrase}. "
        f"{place.scene}"
    )
    world.say(f"They liked the warm smell of supper and the quiet evening air.")


def want(world: World, a: Entity, b: Entity, rifle: Rifle, food: Food) -> None:
    a.memes["want"] += 1
    world.say(
        f"Then {a.id} spotted {rifle.phrase} near the shed. "
        f'"Look at that," {a.id} said. "I can make a big noise!"'
    )
    world.say(
        f"{b.id} frowned at once. \"That is not a toy,\" {b.id} said. "
        f"\"And the {food.label} is right there.\""
    )


def argue(world: World, a: Entity, b: Entity) -> None:
    a.memes["defiance"] += 1
    b.memes["worry"] += 1
    world.say(
        f"{a.id} ignored the warning and grabbed the rifle anyway. "
        f"{b.id} grabbed {a.id}'s arm, and both of them started talking at once."
    )


def fire(world: World, rifle: Rifle, food: Food) -> None:
    _do_rifle(world)
    world.say(
        f"Bang! The rifle went off with a crack that shook the plates. "
        f"The loud sound made everyone jump."
    )
    food.meters["spilled"] += 1
    world.say(
        f"The bowl of {food.label} tipped over, and red sauce splashed across the floor."
    )


def alarm(world: World, parent: Entity) -> None:
    world.say(f'"{parent.id}!" {world.facts["animal2"].id} shouted for help.')


def fail_rescue(world: World, parent: Entity, response: Response, food: Food) -> None:
    food.meters["ruined"] += 1
    world.get("ziti").meters["spilled"] += 1
    body = response.fail.replace("{target}", food.label)
    world.say(f"{parent.label_word.capitalize()} ran over, but {body}.")
    world.say(
        "The sauce spread under the chair legs, and the good supper turned into a messy stain."
    )


def bad_ending(world: World, a: Entity, b: Entity, food: Food) -> None:
    a.memes["sad"] += 1
    b.memes["sad"] += 1
    world.say(
        f"The friends stopped smiling. Nobody ate the {food.label} after that, "
        f"and the table stayed messy and quiet."
    )
    world.say(
        f"By bedtime, {a.id} and {b.id} were still upset, and the whole barn smelled like spilled sauce."
    )


def tell(place: Place, food: Food, rifle: Rifle, response: Response,
         animal1: str = "Milo", animal1_type: str = "fox",
         animal2: str = "Pip", animal2_type: str = "raccoon",
         parent: str = "the farmer", delay: int = 1) -> World:
    world = World()
    a = world.add(Entity(id=animal1, kind="character", type=animal1_type, role="instigator"))
    b = world.add(Entity(id=animal2, kind="character", type=animal2_type, role="cautioner"))
    p = world.add(Entity(id="parent", kind="character", type="farmer", label=parent))
    z = world.add(Entity(id="ziti", type="food", label=food.label, edible=True))
    r = world.add(Entity(id="rifle", type="thing", label=rifle.label, dangerous=True))

    world.facts.update(animal1=a, animal2=b, parent=p, food=food, place=place, rifle=rifle,
                       response=response, delay=delay)

    start(world, a, b, place, food, rifle)
    world.para()
    want(world, a, b, rifle, food)
    argue(world, a, b)
    world.para()
    fire(world, rifle, food)
    alarm(world, p)
    world.para()
    if is_contained(response, delay):
        world.say("But in this world, no one could clean it in time.")
    else:
        fail_rescue(world, p, response, food)
    bad_ending(world, a, b, food)

    world.facts["outcome"] = "bad"
    world.facts["ruined"] = z.meters["ruined"] >= THRESHOLD
    return world


PLACES = {
    "barn": Place(id="barn", label="the barn", scene="The hay was soft, but the evening was getting chilly."),
    "kitchen": Place(id="kitchen", label="the farm kitchen", scene="The table was set, and the smell of supper filled the room."),
    "porch": Place(id="porch", label="the porch", scene="The porch light glowed, but the yard beyond it was dark."),
}

FOODS = {
    "ziti": Food(id="ziti", label="ziti", phrase="a big bowl of ziti", plate="the table", serving="the supper bowl", tags={"food", "ziti"}),
    "baked_ziti": Food(id="baked_ziti", label="ziti", phrase="a pan of baked ziti", plate="the table", serving="the baking dish", tags={"food", "ziti"}),
}

RIFLES = {
    "rifle": Rifle(id="rifle", label="rifle", phrase="an old rifle", location="by the shed", loud="bang", tags={"rifle", "danger"}),
    "hunting_rifle": Rifle(id="hunting_rifle", label="rifle", phrase="a hunting rifle", location="on the wall", loud="bang", tags={"rifle", "danger"}),
}

RESPONSES = {
    "cover": Response(id="cover", sense=2, power=1,
                      text="covered the bowl with a pan, but the noise and mess had already happened",
                      fail="covered the bowl too late",
                      qa_text="covered the bowl with a pan",
                      tags={"cover"}),
    "stomp": Response(id="stomp", sense=2, power=1,
                      text="stomped at the spill, but the sauce kept spreading",
                      fail="stomped at the spill, but it kept spreading",
                      qa_text="stomped at the spill",
                      tags={"stomp"}),
    "call": Response(id="call", sense=3, power=3,
                     text="called for help and shut the door, but the damage was already done",
                     fail="called for help, but the mess was already too big",
                     qa_text="called for help and shut the door",
                     tags={"call"}),
}


GIRL_NAMES = ["Mia", "Luna", "Nina", "Rose"]
BOY_NAMES = ["Milo", "Pip", "Finn", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with ziti, a rifle, conflict, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--rifle", choices=RIFLES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--animal1")
    ap.add_argument("--animal1-type")
    ap.add_argument("--animal2")
    ap.add_argument("--animal2-type")
    ap.add_argument("--parent")
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
    if args.food and args.rifle:
        if not hazard_at_risk(RIFLES[args.rifle], FOODS[args.food]):
            raise StoryError("No story: the rifle and the food do not make a believable conflict.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              if args.rifle is None or c[1] == args.rifle
              if args.food is None or c[2] == args.food]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place_id, rifle_id, food_id = rng.choice(sorted(combos))
    place = PLACES[place_id]
    rifle = RIFLES[rifle_id]
    food = FOODS[food_id]
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    a_name = args.animal1 or rng.choice(GIRL_NAMES + BOY_NAMES)
    b_name = args.animal2 or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != a_name])
    a_type = args.animal1_type or rng.choice(["fox", "raccoon", "mouse", "bear"])
    b_type = args.animal2_type or rng.choice([t for t in ["fox", "raccoon", "mouse", "bear"] if t != a_type])
    parent = args.parent or "the farmer"
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place=place.id, food=food.id, rifle=rifle.id,
                       animal1=a_name, animal1_type=a_type,
                       animal2=b_name, animal2_type=b_type,
                       parent=parent, delay=delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write an animal story that includes the words "ziti" and "rifle" and ends badly after a fight.',
        f"Tell a tense barnyard story where {f['animal1'].id} and {f['animal2'].id} argue over {f['food'].label} and an old rifle.",
        f"Write a short animal story with conflict, spilled dinner, and the word {f['food'].label}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["animal1"]
    b = f["animal2"]
    p = f["parent"]
    food = f["food"]
    rifle = f["rifle"]
    qa = [
        ("Who are the story about?",
         f"It is about {a.id} and {b.id}, two animals who were trying to share supper. The farmer was nearby when the trouble started."),
        ("What did they have for supper?",
         f"They had {food.phrase}. It was warm and ready before the argument began."),
        ("What caused the conflict?",
         f"{a.id} wanted to show off the {rifle.label}, while {b.id} knew it was dangerous. That disagreement turned a quiet meal into a fight."),
        ("How did the story end?",
         f"It ended badly. The rifle made a loud bang, the {food.label} spilled, and nobody got to enjoy supper."),
    ]
    if f.get("ruined"):
        qa.append((
            "What happened to the ziti?",
            f"The ziti was ruined. Sauce and noodles spilled across the floor, so the meal could not be saved."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ziti", "rifle", "conflict", "bad_ending"}
    out = []
    for tag in tags:
        if tag == "ziti":
            out.append(("What is ziti?", "Ziti is a kind of pasta, often served with sauce and baked in a warm dish."))
        elif tag == "rifle":
            out.append(("What is a rifle?", "A rifle is a dangerous weapon that can make a very loud bang. Children and animals should stay far away from it."))
        elif tag == "conflict":
            out.append(("What is a conflict?", "A conflict is a disagreement or fight. It can make a story tense and can hurt feelings if nobody calms down."))
        elif tag == "bad_ending":
            out.append(("What is a bad ending?", "A bad ending is when the trouble does not turn out well. Something gets broken, ruined, or lost by the end."))
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
        if e.flammable:
            bits.append("flammable")
        if e.dangerous:
            bits.append("dangerous")
        if e.edible:
            bits.append("edible")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(R, F) :- dangerous(R), edible(F).
valid(P, R, F) :- place(P), rifle(R), food(F), hazard(R, F).
outcome(bad) :- valid(_, _, _).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.edible:
            lines.append(asp.fact("edible", fid))
    for rid, r in RIFLES.items():
        lines.append(asp.fact("rifle", rid))
        if r.dangerous:
            lines.append(asp.fact("dangerous", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos.")
        rc = 1
    # smoke test ordinary generation
    try:
        p = resolve_params(argparse.Namespace(place=None, food=None, rifle=None, response=None,
                                              animal1=None, animal1_type=None, animal2=None,
                                              animal2_type=None, parent=None, delay=None),
                           random.Random(7))
        s = generate(p)
        _ = s.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("food", FOODS), ("rifle", RIFLES), ("response", RESPONSES)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], FOODS[params.food], RIFLES[params.rifle], RESPONSES[params.response],
                 params.animal1, params.animal1_type, params.animal2, params.animal2_type, params.parent, params.delay)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [
            generate(StoryParams(place="barn", food="ziti", rifle="rifle",
                                 animal1="Milo", animal1_type="fox",
                                 animal2="Pip", animal2_type="raccoon",
                                 parent="the farmer", delay=1))
        ]
    else:
        seen = set()
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
        header = "### bad ending animal story" if args.all else (f"### variant {i + 1}" if len(samples) > 1 else "")
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
