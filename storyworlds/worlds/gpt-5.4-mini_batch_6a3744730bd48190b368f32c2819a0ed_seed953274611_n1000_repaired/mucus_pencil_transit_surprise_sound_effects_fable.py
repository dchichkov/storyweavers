#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/mucus_pencil_transit_surprise_sound_effects_fable.py
=====================================================================================

A small fable-like storyworld about a child-sized transit mishap:
a rider carries a pencil, a sudden mucus problem changes the trip,
and a surprising sound-effect trick helps everyone finish the journey
with a wiser ending.

The world keeps to a tiny, classical shape:
- typed entities with physical meters and emotional memes
- a forward causal model that changes the prose
- a reasonableness gate
- an inline ASP twin for parity checks
- grounded prompts, grounded story QA, and world-knowledge QA

Seed words woven into the domain:
- mucus
- pencil
- transit

Style and instruments:
- fable
- surprise
- sound effects
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
BRAVERY_INIT = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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


@dataclass
class TransitRoute:
    id: str
    place: str
    vehicle: str
    stop: str
    ride_sound: str
    surprise_sound: str
    can_turn: bool
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    needs: str
    can_smear: bool = False
    can_mark: bool = False
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
class SoundTool:
    id: str
    label: str
    phrase: str
    sound: str
    helps: bool
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
class OutcomeRule:
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    rider = world.get("rider")
    if rider.meters["mucus"] < THRESHOLD:
        return out
    sig = ("mess", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.memes["embarrassment"] += 1
    rider.memes["fear"] += 1
    out.append("__sneeze__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    rider = world.get("rider")
    if rider.meters["mucus"] < THRESHOLD or rider.memes["surprise"] < THRESHOLD:
        return out
    sig = ("surprise", rider.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.memes["courage"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("mess", "social", _r_mess), Rule("surprise", "social", _r_surprise)]


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


def predict_trip(world: World, route: TransitRoute, pencil: ObjectCfg, sound: SoundTool) -> dict:
    sim = world.copy()
    sim.get("pencil").meters["marked"] += 1
    sim.get("rider").meters["mucus"] += 1
    if sound.helps:
        sim.get("rider").memes["surprise"] += 1
    propagate(sim, narrate=False)
    return {
        "messy": sim.get("rider").meters["mucus"] >= THRESHOLD,
        "courage": sim.get("rider").memes["courage"],
    }


def reasonableness_ok(route: TransitRoute, pencil: ObjectCfg) -> bool:
    return route.can_turn and pencil.can_mark


def sensible_tools() -> list[SoundTool]:
    return [t for t in SOUND_TOOLS.values() if t.helps]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for route_id, route in ROUTES.items():
        for pencil_id, pencil in OBJECTS.items():
            for sound_id, sound in SOUND_TOOLS.items():
                if reasonableness_ok(route, pencil) and sound.helps:
                    combos.append((route_id, pencil_id, sound_id))
    return combos


@dataclass
class StoryParams:
    route: str
    pencil: str
    sound: str
    rider_name: str
    rider_gender: str
    guide_name: str
    guide_gender: str
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


ROUTES = {
    "tram": TransitRoute(
        id="tram",
        place="the tram",
        vehicle="tram car",
        stop="the last hill stop",
        ride_sound="clang-clang",
        surprise_sound="psst!",
        can_turn=True,
        tags={"transit", "tram"},
    ),
    "bus": TransitRoute(
        id="bus",
        place="the bus",
        vehicle="bus",
        stop="the village gate",
        ride_sound="rumble-rumble",
        surprise_sound="psst!",
        can_turn=True,
        tags={"transit", "bus"},
    ),
}

OBJECTS = {
    "pencil": ObjectCfg(
        id="pencil",
        label="pencil",
        phrase="a small pencil",
        needs="mark the route",
        can_smear=True,
        can_mark=True,
        tags={"pencil"},
    ),
    "crayon": ObjectCfg(
        id="crayon",
        label="crayon",
        phrase="a wax crayon",
        needs="mark the route",
        can_smear=True,
        can_mark=True,
        tags={"pencil"},
    ),
}

SOUND_TOOLS = {
    "whistle": SoundTool(
        id="whistle",
        label="whistle",
        phrase="a little whistle",
        sound="tweet-tweet",
        helps=True,
        tags={"sound"},
    ),
    "drum": SoundTool(
        id="drum",
        label="drum",
        phrase="a tiny drum",
        sound="boom-boom",
        helps=True,
        tags={"sound"},
    ),
}

RESPONSES = {
    "wipe": OutcomeRule(
        id="wipe",
        sense=3,
        power=3,
        text="wiped the mucus away with a clean cloth and steadied the child's hand",
        fail="wiped at the mucus, but the ride was already too slippery and rushed",
        qa_text="wiped the mucus away with a clean cloth and steadied the child's hand",
        tags={"mucus"},
    ),
    "pause": OutcomeRule(
        id="pause",
        sense=3,
        power=2,
        text="asked the conductor to pause at the next stop, then helped the rider breathe slowly",
        fail="asked for a pause, but the transit kept rocking and the child still felt stuck",
        qa_text="asked the conductor to pause at the next stop and helped the rider breathe slowly",
        tags={"transit"},
    ),
}

GIRL_NAMES = ["Mina", "Tia", "Lena", "Nora", "Ivy", "Sara"]
BOY_NAMES = ["Oren", "Beni", "Luca", "Noam", "Pavel", "Eli"]
TRAITS = ["careful", "curious", "gentle", "steady", "thoughtful"]
SENSATIONS = ["soft", "sticky", "surprising", "bright"]


def tell(route: TransitRoute, pencil: ObjectCfg, sound: SoundTool, response: OutcomeRule,
         rider_name: str = "Mina", rider_gender: str = "girl",
         guide_name: str = "Aunt", guide_gender: str = "woman") -> World:
    world = World()
    rider = world.add(Entity(id="rider", kind="character", type=rider_gender, label=rider_name))
    guide = world.add(Entity(id="guide", kind="character", type=guide_gender, label=guide_name, role="guide"))
    pencil_ent = world.add(Entity(id="pencil", kind="thing", type="thing", label=pencil.label, tags=set(pencil.tags)))
    mucus_ent = world.add(Entity(id="mucus", kind="thing", type="thing", label="mucus", tags={"mucus"}))
    sound_ent = world.add(Entity(id="sound", kind="thing", type="thing", label=sound.label, tags=set(sound.tags)))

    rider.memes["duty"] = 1
    rider.memes["surprise"] = 1
    guide.memes["patience"] = 1

    world.say(
        f"On a bright morning, {rider.label_word} climbed onto {route.place} with "
        f"{pencil.phrase} tucked in a pocket. The {route.vehicle} went {route.ride_sound}, "
        f"and the little wheels sang like a row of pebbles."
    )
    world.say(
        f"{guide.label_word.capitalize()} said the ride would be simple: mark the stops, "
        f"count the turns, and arrive with a clear head."
    )

    world.para()
    world.say(
        f"But halfway to {route.stop}, {rider.label_word} felt a sudden tickle. "
        f"A bit of mucus sneaked out, and the pencil tip slipped right when it should have stayed neat."
    )
    rider.meters["mucus"] += 1
    rider.meters["pencil"] += 1
    rider.memes["surprise"] += 1
    predict_trip(world, route, pencil, sound)
    propagate(world, narrate=False)
    world.say(
        f'"{route.surprise_sound}" went the air, and {guide.label_word} turned at once. '
        f'"A surprise on a ride means we slow down," {guide.pronoun()} said.'
    )

    world.para()
    outcome = "contained"
    if response.sense < 3:
        raise StoryError("response is too weak for this small transit problem")
    if response.power >= 3:
        body = response.text
        world.say(
            f"{guide.label_word.capitalize()} {body}."
        )
        rider.meters["mucus"] = 0
        rider.memes["fear"] = 0
        rider.memes["joy"] += 1
        world.say(
            f"The train of stops felt easier after that. {rider.label_word} breathed out, "
            f"held the pencil straight again, and the transit windows flashed by like lanterns."
        )
        world.para()
        world.say(
            f"To turn the awkward moment into a lesson, {guide.label_word} taught a little fable: "
            f"when a ride gets messy, a calm answer and a kind helper keep the journey moving."
        )
    else:
        outcome = "failed"
        world.say(
            f"{guide.label_word.capitalize()} {response.fail}. The ride shook on, and the pencil scribble came out crooked."
        )
        world.say(
            f"Still, {guide.label_word} kept {rider.label_word} safe, and the two of them waited for the next stop."
        )

    world.facts.update(
        route=route,
        pencil_cfg=pencil,
        sound_cfg=sound,
        response=response,
        rider=rider,
        guide=guide,
        outcome=outcome,
        transit_sound=route.ride_sound,
        surprise_sound=route.surprise_sound,
        mucus_fixed=outcome == "contained",
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    route = f["route"]
    return [
        f'Write a short fable for a child that includes the words "mucus", "pencil", and "transit".',
        f"Tell a gentle transit fable where {f['rider'].label_word} has a mucus surprise on {route.place} and a kind guide helps.",
        f"Write a story with sound effects like {route.ride_sound} and {route.surprise_sound}, ending with a wise lesson about riding calmly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    rider = f["rider"]
    guide = f["guide"]
    route = f["route"]
    resp = f["response"]
    qa = [
        (f"Where did the story happen?",
         f"It happened on {route.place}, while the rider was traveling in a {route.vehicle}. The whole problem unfolded during transit, not at home."),
        (f"What caused the surprise?",
         f"A bit of mucus made the pencil slip at the wrong moment. That small accident turned an ordinary ride into a sudden surprise."),
        (f"What did the guide do?",
         f"{guide.label_word.capitalize()} responded calmly and {resp.qa_text}. That helped the child settle down and continue the trip safely."),
        (f"What was the lesson?",
         f"The lesson was that a small problem on transit needs a calm helper, not panic. A wise fable turns a messy moment into a better choice for next time."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    out = [
        ("What is mucus?",
         "Mucus is a slimy liquid in the nose and throat that helps catch dust and keep those places moist."),
        ("What is a pencil?",
         "A pencil is a tool for writing or drawing. It uses a thin mark-making core, so you can erase many pencil marks."),
        ("What is transit?",
         "Transit means traveling in a vehicle like a bus, tram, or train to go from one place to another."),
        ("What are sound effects?",
         "Sound effects are special words or sounds, like clang-clang or boom-boom, that help a story feel lively."),
    ]
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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(route="tram", pencil="pencil", sound="whistle", rider_name="Mina", rider_gender="girl",
                guide_name="Aunt", guide_gender="woman"),
    StoryParams(route="bus", pencil="crayon", sound="drum", rider_name="Oren", rider_gender="boy",
                guide_name="Uncle", guide_gender="man"),
]


def explain_rejection(route: TransitRoute, pencil: ObjectCfg) -> str:
    return (
        f"(No story: this transit scene does not fit the fable well enough. "
        f"The route must allow a small turn in the trip, and the pencil must be able to mark the route.)"
    )


def valid_story(route: TransitRoute, pencil: ObjectCfg, sound: SoundTool) -> bool:
    return route.can_turn and pencil.can_mark and sound.helps


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in ROUTES.items():
        lines.append(asp.fact("route", rid))
        if r.can_turn:
            lines.append(asp.fact("can_turn", rid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.can_mark:
            lines.append(asp.fact("can_mark", oid))
    for sid, s in SOUND_TOOLS.items():
        lines.append(asp.fact("sound_tool", sid))
        if s.helps:
            lines.append(asp.fact("helps", sid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R, O, S) :- route(R), object(O), sound_tool(S), can_turn(R), can_mark(O), helps(S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    p = set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if a - p:
            print("  only in clingo:", sorted(a - p))
        if p - a:
            print("  only in python:", sorted(p - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable-like transit storyworld with mucus, a pencil, and sound effects.")
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--pencil", choices=OBJECTS)
    ap.add_argument("--sound", choices=SOUND_TOOLS)
    ap.add_argument("--rider-name")
    ap.add_argument("--guide-name")
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
    route = args.route or rng.choice(sorted(ROUTES))
    pencil = args.pencil or rng.choice(sorted(OBJECTS))
    sound = args.sound or rng.choice(sorted(SOUND_TOOLS))
    if not valid_story(ROUTES[route], OBJECTS[pencil], SOUND_TOOLS[sound]):
        raise StoryError(explain_rejection(ROUTES[route], OBJECTS[pencil]))
    rider_gender = rng.choice(["girl", "boy"])
    guide_gender = rng.choice(["woman", "man"])
    rider_name = args.rider_name or rng.choice(GIRL_NAMES if rider_gender == "girl" else BOY_NAMES)
    guide_name = args.guide_name or rng.choice(["Aunt", "Uncle", "Friend", "Neighbor"])
    return StoryParams(
        route=route,
        pencil=pencil,
        sound=sound,
        rider_name=rider_name,
        rider_gender=rider_gender,
        guide_name=guide_name,
        guide_gender=guide_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES or params.pencil not in OBJECTS or params.sound not in SOUND_TOOLS:
        raise StoryError("invalid story parameters")
    world = tell(ROUTES[params.route], OBJECTS[params.pencil], SOUND_TOOLS[params.sound], RESPONSES["wipe"],
                 rider_name=params.rider_name, rider_gender=params.rider_gender,
                 guide_name=params.guide_name, guide_gender=params.guide_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible route/object/sound combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            params.seed = seed
            samples.append(sample)

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
