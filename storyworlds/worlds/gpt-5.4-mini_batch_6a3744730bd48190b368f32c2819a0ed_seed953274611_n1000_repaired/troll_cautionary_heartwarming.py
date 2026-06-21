#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/troll_cautionary_heartwarming.py
=================================================================

A tiny storyworld for a heartwarming cautionary tale about a troll who lives by
a bridge, a child who wants to help, and a safer choice that keeps everyone kind
and safe.

The world is intentionally small:
- A child sees a lonely troll near a bridge.
- The child is tempted to do something risky or unwise.
- A cautious helper warns them.
- A grown-up or safer plan turns the moment into warmth, not trouble.
- The ending image proves something changed: trust, food, light, or friendship.

This script follows the Storyweavers contract:
- standalone stdlib script
- typed entities with meters and memes
- Python reasonableness gate and inline ASP twin
- StoryParams, build_parser, resolve_params, generate, emit, main
- prompts, story-grounded QA, world-knowledge QA
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    friendly: bool = False
    hungry: bool = False
    hungry_for: str = ""
    risky: bool = False
    safe: bool = False

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "troll"}
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
    kind: str = "place"
    near_water: bool = False
    has_bridge: bool = False
    has_lantern_post: bool = False
    has_berries: bool = False
    has_rainbow_rocks: bool = False
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
class Want:
    id: str
    label: str
    risky: bool
    safe_alt: str
    reason: str
    consequence: str
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
class Help:
    id: str
    label: str
    sense: int
    kind: str
    text: str
    consequence: str
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
    child_name: str
    child_gender: str
    troll_name: str
    troll_tone: str
    want: str
    help: str
    seed: Optional[int] = None
    child_age: int = 6
    troll_lonely: bool = True
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
        self.place: Optional[Place] = None
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.place = copy.deepcopy(self.place)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
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


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("worry", 0.0) < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["caution"] = e.memes.get("caution", 0.0) + 1
        out.append("__worry__")
    return out


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes.get("kindness", 0.0) < THRESHOLD:
            continue
        sig = ("kindness", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hope"] = e.memes.get("hope", 0.0) + 1
        out.append("__hope__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("kindness", _r_kindness)]


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


def want_at_risk(want: Want) -> bool:
    return want.risky


def sensible_helps() -> list[Help]:
    return [h for h in HELPS.values() if h.sense >= SENSE_MIN]


def best_help() -> Help:
    return max(HELPS.values(), key=lambda h: h.sense)


def can_help(help_: Help, want: Want) -> bool:
    return help_.sense >= SENSE_MIN and (not want.risky or help_.kind in {"call_adult", "share_food", "lantern", "ask_name"})


def predict(world: World, want_id: str) -> dict:
    sim = world.copy()
    _do_want(sim, sim.get("child"), WANTS[want_id], narrate=False)
    return {"trouble": sim.get("child").meters.get("trouble", 0.0) >= THRESHOLD}


def _do_want(world: World, child: Entity, want: Want, narrate: bool = True) -> None:
    child.memes["want"] = child.memes.get("want", 0.0) + 1
    if want.risky:
        child.meters["trouble"] = child.meters.get("trouble", 0.0) + 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, troll: Entity, place: Place) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    troll.memes["lonely"] = troll.memes.get("lonely", 0.0) + (1 if troll.attrs.get("lonely") else 0)
    world.say(
        f"One chilly afternoon, {child.id} followed the path to {place.label}. "
        f"By the bridge, a troll sat with {troll.hungry_for or 'an empty basket'} and a sad, patient look."
    )
    world.say(
        f'The troll blinked up and said, "{troll.attrs.get("greeting", "Hello there")}, little one."'
    )


def temptation(world: World, child: Entity, want: Want, troll: Entity, place: Place) -> None:
    world.say(
        f"{child.id} noticed that {place.label} had {want.label}. It felt like a quick way to make the troll smile."
    )
    if want.risky:
        world.say(f'But {child.id} also knew it might be a bad idea.')
    child.memes["hope"] = child.memes.get("hope", 0.0) + 1


def warn(world: World, helper: Entity, child: Entity, want: Want, troll: Entity) -> None:
    helper.memes["caution"] = helper.memes.get("caution", 0.0) + 1
    pred = predict(world, want.id)
    world.facts["predicted_trouble"] = pred["trouble"]
    world.say(
        f'{helper.id} touched {child.pronoun("possessive")} sleeve. '
        f'"That is kind, but not safe," {helper.pronoun()} said. '
        f'"{want.reason}. We should choose a safer way."'
    )
    if pred["trouble"]:
        world.say(f"{helper.id} looked at the bridge and worried that trouble could start fast.")


def choose_safe(world: World, child: Entity, troll: Entity, want: Want, help_: Help) -> None:
    child.memes["caution"] = child.memes.get("caution", 0.0) + 1
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(
        f'{child.id} listened. Instead of {want.label.lower()}, {child.id} chose {want.safe_alt}.'
    )
    world.say(
        f'{help_.text}. The troll straightened up, a little surprised and a lot happier.'
    )


def resolve(world: World, child: Entity, troll: Entity, help_: Help, place: Place) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    troll.memes["hope"] = troll.memes.get("hope", 0.0) + 1
    troll.memes["grateful"] = troll.memes.get("grateful", 0.0) + 1
    world.say(
        f"{place.label} felt warmer after that. The troll shared a grin, and {child.id} laughed back."
    )
    world.say(
        f"By the end, the bridge was not scary anymore; it was just a place where a lonely troll had found a friend."
    )


def tell(params: StoryParams) -> World:
    if params.place not in PLACES or params.want not in WANTS or params.help not in HELPS:
        raise StoryError("Invalid story parameters.")
    place = PLACES[params.place]
    want = WANTS[params.want]
    help_ = HELPS[params.help]
    if not can_help(help_, want):
        raise StoryError(f"'{help_.id}' is too weak or mismatched for this story.")
    world = World()
    world.place = place
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_gender, role="child"))
    troll = world.add(
        Entity(
            id=params.troll_name,
            kind="character",
            type="troll",
            role="troll",
            friendly=True,
            hungry=True,
            hungry_for="some dinner",
            attrs={"lonely": params.troll_lonely, "greeting": "Oh, hello"},
        )
    )
    helper = world.add(Entity(id="Helper", kind="character", type="adult", role="helper"))

    setup(world, child, troll, place)
    world.para()
    temptation(world, child, want, troll, place)
    warn(world, helper, child, want, troll)
    world.para()
    choose_safe(world, child, troll, want, help_)
    resolve(world, child, troll, help_, place)

    world.facts.update(
        child=child,
        troll=troll,
        helper=helper,
        place=place,
        want=want,
        help=help_,
        outcome="safe",
    )
    return world


PLACES = {
    "bridge": Place(
        id="bridge",
        label="the old stone bridge",
        near_water=True,
        has_bridge=True,
        has_lantern_post=True,
        has_berries=True,
    ),
    "path": Place(
        id="path",
        label="the forest path",
        near_water=False,
        has_bridge=False,
        has_lantern_post=False,
        has_berries=True,
    ),
    "dock": Place(
        id="dock",
        label="the little dock by the pond",
        near_water=True,
        has_bridge=False,
        has_lantern_post=True,
        has_rainbow_rocks=True,
    ),
}

WANTS = {
    "feed": Want(
        id="feed",
        label="the troll with a cookie from home",
        risky=True,
        safe_alt="a shared snack with a grown-up",
        reason="A stranger, even a friendly troll, should not be fed with random food alone",
        consequence="the child could waste the snack or get too close to the water",
        tags={"food", "troll"},
    ),
    "cross": Want(
        id="cross",
        label="cross the bridge alone at dusk",
        risky=True,
        safe_alt="cross with the helper and the lantern",
        reason="The bridge is slippery when the light goes dim",
        consequence="a cautious helper can keep everyone steady",
        tags={"bridge", "dark"},
    ),
    "gift": Want(
        id="gift",
        label="leave shiny coins for the troll",
        risky=True,
        safe_alt="leave a note and a lantern-lit basket",
        reason="Shiny things can fall into the water and make a mess of the path",
        consequence="a safer gift can be just as kind",
        tags={"gift", "water"},
    ),
    "greet": Want(
        id="greet",
        label="shout hello from the middle of the bridge",
        risky=False,
        safe_alt="walk closer slowly and say hello kindly",
        reason="A calm hello is safer than startling anyone",
        consequence="kind words work better than loud ones",
        tags={"hello", "troll"},
    ),
}

HELPS = {
    "lantern": Help(
        id="lantern",
        label="the lantern",
        sense=3,
        kind="lantern",
        text="The helper lit the lantern and held it low so the child could see the troll's smile",
        consequence="light made the bridge feel safe",
        tags={"light", "bridge"},
    ),
    "call_adult": Help(
        id="call_adult",
        label="calling a grown-up",
        sense=3,
        kind="call_adult",
        text="The helper called a grown-up, and together they made a safer plan",
        consequence="asking for help kept everyone calm",
        tags={"adult", "safety"},
    ),
    "share_food": Help(
        id="share_food",
        label="a shared snack picnic",
        sense=3,
        kind="share_food",
        text="The helper unpacked a small snack to share on a blanket far from the water",
        consequence="sharing food made the troll feel welcomed",
        tags={"food", "kindness"},
    ),
    "note": Help(
        id="note",
        label="a note with a picture",
        sense=2,
        kind="ask_name",
        text="The helper handed the child a crayon note with a drawing of a smiling troll",
        consequence="a note can say hello without crowding anyone",
        tags={"note", "kindness"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Ava", "Nora", "Ella"]
BOY_NAMES = ["Finn", "Leo", "Max", "Theo", "Owen"]
TROLL_NAMES = ["Moss", "Bracken", "Puddle", "Stone", "Hob"]
TROLL_TONES = ["gentle", "shy", "gruff", "soft-spoken"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for wid, want in WANTS.items():
            if not want_at_risk(want):
                continue
            for hid, help_ in HELPS.items():
                if can_help(help_, want):
                    combos.append((pid, wid, hid))
    return combos


def explain_rejection(want: Want, help_: Help) -> str:
    return (
        f"(No story: the choice '{help_.label}' does not fit the cautionary turn for "
        f"'{want.label}'. This world needs a safer, kind way that truly helps.)"
    )


def explain_help(help_id: str) -> str:
    h = HELPS[help_id]
    if h.sense < SENSE_MIN:
        return f"(Refusing help '{help_id}': it is too weak.)"
    return ""


ASP_RULES = r"""
risky_want(W) :- want(W), risky(W).
sensible_help(H) :- help(H), sense(H, S), sense_min(M), S >= M.
valid(P, W, H) :- place(P), want(W), risky_want(W), help(H), sensible_help(H).
safe_story(P, W, H) :- valid(P, W, H).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for wid, w in WANTS.items():
        lines.append(asp.fact("want", wid))
        if w.risky:
            lines.append(asp.fact("risky", wid))
    for hid, h in HELPS.items():
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))

    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, child_name=None, child_gender=None, troll_name=None,
            troll_tone=None, want=None, help=None, seed=None, child_age=None, troll_lonely=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # noqa: BLE001
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary heartwarming troll story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--help", dest="help_choice", choices=HELPS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--troll-name")
    ap.add_argument("--troll-tone", choices=TROLL_TONES)
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
    want_id = args.want or rng.choice(list(WANTS))
    help_id = args.help_choice or rng.choice(list(HELPS))
    if want_id not in WANTS or help_id not in HELPS:
        raise StoryError("Invalid choice.")
    if not can_help(HELPS[help_id], WANTS[want_id]):
        raise StoryError(explain_rejection(WANTS[want_id], HELPS[help_id]))
    place = args.place or rng.choice(list(PLACES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    troll_name = args.troll_name or rng.choice(TROLL_NAMES)
    troll_tone = args.troll_tone or rng.choice(TROLL_TONES)
    return StoryParams(
        place=place,
        child_name=child_name,
        child_gender=child_gender,
        troll_name=troll_name,
        troll_tone=troll_tone,
        want=want_id,
        help=help_id,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    want = f["want"]
    place = f["place"]
    return [
        f'Write a heartwarming cautionary story containing the word "troll" set at {place.label}.',
        f"Tell a gentle story where {child.id} wants to {want.label.lower()}, but a cautious helper suggests a safer way.",
        f"Write a child-friendly story about a troll who seems a little lonely, and a kind child who chooses the safer choice.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    troll = f["troll"]
    helper = f["helper"]
    want = f["want"]
    place = f["place"]
    help_ = f["help"]
    return [
        ("Who is the story about?",
         f"It is about {child.id}, {troll.id} the troll, and {helper.id}. They meet near {place.label}."),
        ("What was the risky choice?",
         f"{child.id} wanted to {want.label.lower()}. That seemed kind, but it was not the safest way to help."),
        ("How did they solve the problem?",
         f"They chose {help_.label} instead. That gave them a safer way to be kind without making trouble."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place = f["place"]
    want = f["want"]
    help_ = f["help"]
    out = [
        ("What is a troll?",
         "A troll is a fairy-tale creature. In this story, the troll is gentle and lonely, not scary."),
    ]
    if place.near_water:
        out.append(("Why should you be careful near water at a bridge?",
                     "Bridges near water can be slippery, so it is safer to walk slowly and stay with a grown-up."))
    if want.risky:
        out.append(("Why is it not always safe to give food to a stranger?",
                     "Even kind gifts should be shared carefully, because you need to know who the person is and how to help safely."))
    if help_.kind == "lantern":
        out.append(("What does a lantern do?",
                     "A lantern gives steady light without needing a flame you have to hold in your hand."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bridge", child_name="Lily", child_gender="girl", troll_name="Moss", troll_tone="gentle", want="feed", help="lantern"),
    StoryParams(place="dock", child_name="Finn", child_gender="boy", troll_name="Stone", troll_tone="soft-spoken", want="gift", help="call_adult"),
    StoryParams(place="path", child_name="Mia", child_gender="girl", troll_name="Bracken", troll_tone="shy", want="cross", help="note"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.want not in WANTS or params.help not in HELPS:
        raise StoryError("Invalid params.")
    world = tell(params)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, w, h in combos:
            print(p, w, h)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
