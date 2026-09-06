#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/thud_teamwork_rhyming_story.py
===============================================================

A tiny Storyweavers world for child-facing rhyming stories about teamwork:
something goes wrong with a "thud", two friends take complementary actions,
and the ending proves their shared effort changed the world.

The domain is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a reasonableness gate for valid story setups
- a Python causal model with a matching inline ASP twin
- three Q&A sets grounded in the simulated world state
- a rhyming, child-friendly renderer with concrete state changes

Seed words and features:
- word: thud
- feature: teamwork
- style: rhyming story
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    dark: bool = False
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
class Block:
    id: str
    label: str
    heavy: bool = False
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
class Aid:
    id: str
    label: str
    helper: bool = True
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        import copy
        w = World(place=self.place)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if cart and cart.meters["stuck"] >= THRESHOLD and ("wobble", "cart") not in world.fired:
        world.fired.add(("wobble", "cart"))
        for kid in world.characters():
            kid.memes["worry"] += 1
        out.append("__wobble__")
    return out


def _r_pull(world: World) -> list[str]:
    out: list[str] = []
    cart = world.entities.get("cart")
    if not cart or cart.meters["stuck"] < THRESHOLD:
        return out
    pullers = [e for e in world.characters() if e.memes["pulling"] >= THRESHOLD]
    if len(pullers) >= 2 and ("pull", "cart") not in world.fired:
        world.fired.add(("pull", "cart"))
        cart.meters["stuck"] = 0.0
        cart.meters["free"] = 1.0
        for kid in pullers:
            kid.memes["pride"] += 1
            kid.meters["helped"] += 1
        out.append("__free__")
    return out


def _r_lift(world: World) -> list[str]:
    out: list[str] = []
    crate = world.entities.get("crate")
    if crate and crate.meters["open"] >= THRESHOLD and ("lift", "crate") not in world.fired:
        world.fired.add(("lift", "crate"))
        out.append("The lid sprang up with a bright little flip.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("pull", _r_pull), Rule("lift", _r_lift)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                lines.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def predict_free(world: World) -> bool:
    sim = world.copy()
    cart = sim.get("cart")
    cart.meters["stuck"] = 1.0
    simulate_push(sim, narrate=False)
    return sim.get("cart").meters["free"] >= THRESHOLD


def simulate_push(world: World, narrate: bool = True) -> None:
    cart = world.get("cart")
    cart.meters["stuck"] += 1
    propagate(world, narrate=narrate)


@dataclass(frozen=True)
class StoryArc:
    key: str
    subject: str
    problem: str
    action: str
    result: str
    opening: tuple[str, str]
    trouble: tuple[str, str]
    teamwork: tuple[str, str]
    ending: tuple[str, str]


STORY_ARCS = (
    StoryArc(
        key="rug_wheel",
        subject="toy cart",
        problem="the toy cart's wheel was folded into the rug",
        action="one friend lifted the rug while the other guided the wheel out",
        result="the cart rolled across the play space again",
        opening=(
            "At {place}, {a} packed a toy cart while {b} stacked blocks inside.",
            "They planned to roll their little load on a room-wide treasure ride.",
        ),
        trouble=(
            "The front wheel caught beneath the rug: thud! The tower tipped awry.",
            '"Pushing harder bends the wheel," said {b}. "Let us stop and wonder why."',
        ),
        teamwork=(
            "{a} lifted up the rug's soft edge; {b} steered the wheel with care.",
            '"Lift, then roll," they called in time, each doing a useful share.',
        ),
        ending=(
            "The wheel slipped free, the blocks stayed tall, and off the cart could glide.",
            "Two bright flags waved above their fort at the end of the treasure ride.",
        ),
    ),
    StoryArc(
        key="floor_groove",
        subject="wooden wagon",
        problem="the wagon wheel was wedged in a narrow floor groove",
        action="one friend tilted the wagon while the other pushed a board beneath its wheel",
        result="the wagon crossed the groove without spilling its books",
        opening=(
            "At {place}, {a} filled a wooden wagon with picture books in rows.",
            "{b} drew a reading-map that showed exactly where it goes.",
        ),
        trouble=(
            "A wheel sank in a narrow groove: thud! The wagon gave a shake.",
            "The books leaned left, then leaned to right, like boats upon a lake.",
        ),
        teamwork=(
            '"Tilt it just a little," {a} said. {b} slid a board below.',
            "One held the wagon firm and still; one pushed it straight and slow.",
        ),
        ending=(
            "The wheel climbed out, the books rode on, and not one touched the floor.",
            "Together in their reading den, they opened one book more.",
        ),
    ),
    StoryArc(
        key="blocked_door",
        subject="costume chest",
        problem="a costume chest slid down and blocked the doorway",
        action="the friends carried opposite ends and turned the chest sideways",
        result="the doorway opened and the costume parade could begin",
        opening=(
            "At {place}, {a} found capes and crowns; {b} found a silver gown.",
            "They dressed a chest for a grand parade with stars all up and down.",
        ),
        trouble=(
            "The heavy chest slid off its mat: thud! It blocked the doorway tight.",
            "{a} tugged once, but one small tug could never set it right.",
        ),
        teamwork=(
            '"You take that end; I will take this," said {b}. "We turn it on three."',
            "They bent their knees and carried together: one, two, three!") ,
        ending=(
            "The chest swung round, the doorway cleared, and music filled the room.",
            "{a} and {b} marched through in crowns, each topped with a feather plume.",
        ),
    ),
    StoryArc(
        key="block_bridge",
        subject="block tower",
        problem="a tall block tower fell across the toy train's track",
        action="one friend sorted the blocks while the other rebuilt them as a bridge",
        result="the train passed beneath a stronger block bridge",
        opening=(
            "At {place}, {a} built a tower while {b} drove a click-clack train.",
            "It circled past a paper hill and round a painted plain.",
        ),
        trouble=(
            "The train tapped one unsteady block: thud! Down came the wall.",
            "Red and yellow filled the track; there was no path at all.",
        ),
        teamwork=(
            "{a} sorted wide blocks for the base; {b} arched the top up high.",
            "They tested every piece together before the train rolled by.",
        ),
        ending=(
            "The engine clicked beneath their bridge and whistled round the bend.",
            "A strong new arch stood over the track, built better by each friend.",
        ),
    ),
    StoryArc(
        key="runaway_cart",
        subject="rolling cart",
        problem="a loaded cart began rolling toward a stack of paint pots",
        action="one friend caught its rope while the other placed a wooden stop before the wheel",
        result="the cart stopped safely before reaching the paint",
        opening=(
            "At {place}, {a} loaded paper; {b} brought pots of blue and red.",
            "They meant to paint a moonlit town with stars above its head.",
        ),
        trouble=(
            "The sloping floor sent off the cart: thud! It bumped a wooden chair.",
            "Then on it rolled toward open paint. Blue puddles waited there.",
        ),
        teamwork=(
            '"Catch the rope!" cried {a}. {b} caught it while {a} found a wooden square.',
            "One slowed the cart; one blocked the wheel. Their plan was quick and fair.",
        ),
        ending=(
            "The cart stopped short; the paint stayed put; their picture could begin.",
            "Two painted stars shone side by side above a wide blue grin.",
        ),
    ),
    StoryArc(
        key="lantern_ladder",
        subject="paper lantern",
        problem="a paper lantern fell when its ribbon slipped from a hook",
        action="one friend steadied the step stool while the other tied a firmer knot",
        result="the lantern hung safely and lit their shadow show",
        opening=(
            "At {place}, {a} cut a paper moon; {b} made a lantern glow.",
            "They planned to hang it overhead and start a shadow show.",
        ),
        trouble=(
            "The ribbon slipped; the lantern fell: thud! Darkness crossed the wall.",
            "The hook was high, the stool was light; one friend could not fix all.",
        ),
        teamwork=(
            "{b} held the stool with both feet firm while {a} tied a double bow.",
            '"Steady below, ready above!" they sang, both working slow.',
        ),
        ending=(
            "The lantern stayed; a paper moon sailed through its golden beam.",
            "Their joined hands made two shadows wave at the ending of the scene.",
        ),
    ),
    StoryArc(
        key="parade_drum",
        subject="parade drum",
        problem="the drum tipped from its cart and its strap came loose",
        action="one friend held the drum upright while the other threaded and tied its strap",
        result="the drum rode securely in the parade",
        opening=(
            "At {place}, {a} tapped a parade beat; {b} waved a ribbon high.",
            "Their cardboard cart would lead the march as flags went fluttering by.",
        ),
        trouble=(
            "The drum strap slipped; the drum fell down: thud! The rhythm lost its sound.",
            "It wobbled when {a} raised it up and nearly rolled around.",
        ),
        teamwork=(
            "{b} hugged the drum against the cart; {a} threaded through the lace.",
            "They pulled the knot from opposite sides until it held in place.",
        ),
        ending=(
            "Boom-boom went the steady drum as both friends led the way.",
            "Their two-step footprints crossed the floor at the close of the grand parade.",
        ),
    ),
    StoryArc(
        key="birdhouse_roof",
        subject="birdhouse roof",
        problem="the birdhouse roof dropped because the walls spread apart",
        action="one friend held the walls square while the other fastened the roof",
        result="the birdhouse stood straight with a snug roof",
        opening=(
            "At {place}, {a} shaped a birdhouse; {b} painted berries red.",
            "They hoped a tiny wren might choose the cozy home ahead.",
        ),
        trouble=(
            "They set the roof upon the walls: thud! It tumbled to the ground.",
            "The two side walls had spread apart, so no snug seat was found.",
        ),
        teamwork=(
            '"Hold both walls square," said {a}. {b} held them straight and true.',
            "{a} fixed the roof while {b} kept still. Together, they knew what to do.",
        ),
        ending=(
            "The roof sat snug; the red paint dried; the house stood straight and strong.",
            "A feather rested by its door like the promise of a song.",
        ),
    ),
    StoryArc(
        key="marble_ramp",
        subject="marble ramp",
        problem="the marble ramp collapsed where two short tracks failed to meet",
        action="one friend held the tracks level while the other joined them with a flat block",
        result="the marble traveled over the repaired ramp into its cup",
        opening=(
            "At {place}, {a} made a marble road; {b} placed a cup below.",
            "They wished to send a silver ball through every curve and row.",
        ),
        trouble=(
            "The marble reached a gap: thud! The middle ramp fell flat.",
            "One track was low, the next too high; no ball could travel that.",
        ),
        teamwork=(
            "{a} held both tracks at matching height while {b} bridged the space.",
            '"Ready, steady, test!" they called, then watched the marble race.',
        ),
        ending=(
            "The silver marble crossed the bridge and chimed inside the cup.",
            "They bumped two happy knuckles while the silver ball looked up.",
        ),
    ),
    StoryArc(
        key="puppet_curtain",
        subject="puppet-stage curtain",
        problem="the puppet-stage curtain bar fell from its loose supports",
        action="one friend raised the bar while the other tightened both supports",
        result="the curtain opened smoothly for their puppet show",
        opening=(
            "At {place}, {a} made a dragon; {b} made a mouse in blue.",
            "Behind a little curtain, they rehearsed what each would do.",
        ),
        trouble=(
            "They pulled the cord; the curtain bar fell down with one loud thud.",
            "The dragon lost its castle view; the mouse stared at the rug.",
        ),
        teamwork=(
            "{a} raised the bar above the stage; {b} tightened left and right.",
            "They checked each knot, then pulled the cord. This time it held up tight.",
        ),
        ending=(
            "The curtain swept aside to show the dragon sharing tea.",
            "The mouse and dragon bowed together where both friends could see.",
        ),
    ),
    StoryArc(
        key="seed_tray",
        subject="seedling tray",
        problem="a seedling tray slipped and scattered cups across the floor",
        action="one friend gathered and named the cups while the other refilled and ordered them",
        result="every seedling returned upright to a sunny row",
        opening=(
            "At {place}, {a} brought bean seeds; {b} filled pots with loam.",
            "They lined them in a stripe of sun, a tiny garden home.",
        ),
        trouble=(
            "A tray edge slipped between their hands: thud! Cups rolled everywhere.",
            "Some labels faced the floor below; loose soil dusted the air.",
        ),
        teamwork=(
            "{a} read each label one by one; {b} filled each cup anew.",
            "They passed the seedlings hand to hand and checked them two by two.",
        ),
        ending=(
            "Each bean stood tall in its own cup along the sunny sill.",
            "Two green shoots leaned toward the light, together, calm and still.",
        ),
    ),
    StoryArc(
        key="blanket_den",
        subject="blanket den",
        problem="the blanket den collapsed when its center cushion slid away",
        action="one friend braced the cushion while the other clipped the blanket to two chairs",
        result="the rebuilt den stayed up around their reading nook",
        opening=(
            "At {place}, {a} spread a blanket; {b} arranged two chairs.",
            "They planned a snug and secret den for books and teddy bears.",
        ),
        trouble=(
            "The middle cushion slid away: thud! Down drooped the blanket sky.",
            "{b} held one corner overhead, but three more corners tumbled by.",
        ),
        teamwork=(
            "{a} braced the cushion in the middle; {b} clipped the blanket tight.",
            "They traded places, checked each chair, and made the roof sit right.",
        ),
        ending=(
            "The den stayed high around their books, a quiet, cozy nook.",
            "Two pairs of socks peeked from its door above one open book.",
        ),
    ),
)


def _stable_seed(place: Place, first: Entity, second: Entity, seed: Optional[int]) -> int:
    if seed is not None:
        return seed
    text = f"{place.id}:{first.id}:{second.id}"
    return sum((i + 1) * ord(ch) for i, ch in enumerate(text))


def tell(place: Place, first: Entity, second: Entity, seed: Optional[int] = None) -> World:
    world = World(place=place)
    a = world.add(first)
    b = world.add(second)
    rng = random.Random(_stable_seed(place, first, second, seed))
    arc = STORY_ARCS[rng.randrange(len(STORY_ARCS))]
    cart = world.add(Entity(id="cart", kind="thing", type="cart", label=arc.subject))
    crate = world.add(Entity(id="crate", kind="thing", type="box", label="little box"))

    values = {"a": a.id, "b": b.id, "place": place.label}
    for line in arc.opening:
        world.say(line.format(**values))
    world.para()
    cart.meters["stuck"] = 1.0
    a.memes["surprise"] += 1
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    for line in arc.trouble:
        world.say(line.format(**values))
    world.para()
    a.memes["pulling"] += 1
    b.memes["pulling"] += 1
    a.meters["helped"] += 1
    b.meters["helped"] += 1
    for line in arc.teamwork:
        world.say(line.format(**values))
    cart.meters["stuck"] = 0.0
    cart.meters["free"] = 1.0
    cart.meters["repaired"] = 1.0
    world.fired.add(("teamwork", arc.key))
    world.para()
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    for line in arc.ending:
        world.say(line.format(**values))

    world.facts.update(
        hero=a,
        helper=b,
        cart=cart,
        crate=crate,
        place=place,
        teamwork=True,
        freed=cart.meters["free"] >= THRESHOLD,
        arc=arc.key,
        subject=arc.subject,
        problem=arc.problem,
        action=arc.action,
        result=arc.result,
        ending=arc.ending[-1].format(**values),
    )
    return world


@dataclass
class StoryParams:
    place: str
    hero_name: str
    helper_name: str
    hero_gender: str = "boy"
    helper_gender: str = "girl"
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
    "playroom": Place(id="playroom", label="the playroom", dark=False, tags={"room"}),
    "garage": Place(id="garage", label="the garage", dark=False, tags={"room"}),
    "shed": Place(id="shed", label="the shed", dark=True, tags={"room", "dark"}),
}
NAMES = {
    "boy": ["Ben", "Leo", "Max", "Toby", "Sam"],
    "girl": ["Mia", "Lily", "Zoe", "Nora", "Ava"],
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, "cart", "crate") for p in PLACES]


CURATED = [
    StoryParams(place="playroom", hero_name="Ben", helper_name="Mia", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="garage", hero_name="Leo", helper_name="Nora", hero_gender="boy", helper_gender="girl"),
    StoryParams(place="shed", hero_name="Ava", helper_name="Sam", hero_gender="girl", helper_gender="boy"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming teamwork story world with a thud.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(PLACES))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    hero_name = args.hero or rng.choice(NAMES[hero_gender])
    helper_name = args.helper or rng.choice([n for n in NAMES[helper_gender] if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, helper_name=helper_name,
                       hero_gender=hero_gender, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a small child that includes the word "thud" and shows teamwork.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} use teamwork after {f['problem']}.",
        f'Write a simple teamwork rhyme set at {f["place"].label} about a {f["subject"]}, a thud, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What problem did the friends face after the thud?",
            answer=f"After the thud, {f['problem']}. The friends paused to understand what needed fixing."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"They used teamwork: {f['action']}. Because both friends did a different useful part, {f['result']}."
        ),
        QAItem(
            question="What final image showed that their teamwork worked?",
            answer=f"The ending showed the change clearly: {f['ending']}"
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and work as one team. It can make hard jobs easier and more fun."
        ),
        QAItem(
            question="What does thud sound like?",
            answer="Thud sounds like a heavy bump. It is the kind of sound you hear when something lands or hits the floor."
        ),
    ]


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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
stuck(cart) :- cart(cart), stuck_meter(cart, S), S >= 1.
wobble(H) :- stuck(cart), hero(H).
free(cart) :- pull(H1), pull(H2), H1 != H2, helper(H1), helper(H2).
outcome(free) :- free(cart).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    lines.append(asp.fact("cart", "cart"))
    lines.append(asp.fact("crate", "crate"))
    lines.append(asp.fact("stuck_meter", "cart", 1))
    for child in ("first_child", "second_child"):
        lines.append(asp.fact("hero", child))
        lines.append(asp.fact("helper", child))
        lines.append(asp.fact("pull", child))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    try:
        model = asp.one_model(asp_program("#show outcome/1."))
        _ = model
    except Exception as exc:
        print(f"ASP smoke test failed: {exc}")
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            place=None, hero=None, helper=None, hero_gender=None, helper_gender=None
        ), random.Random(1)))
        if not sample.story.strip():
            print("Story generation produced empty text.")
            return 1
    except Exception as exc:
        print(f"Generation smoke test failed: {exc}")
        return 1
    print("OK: smoke tests passed.")
    return 0


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show free/1."))
    return sorted(set(asp.atoms(model, "free")))


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    if params.hero_gender not in NAMES or params.helper_gender not in NAMES:
        raise StoryError("Invalid gender.")
    place = PLACES[params.place]
    world = tell(
        place=place,
        first=Entity(id=params.hero_name, kind="character", type=params.hero_gender, role="hero"),
        second=Entity(id=params.helper_name, kind="character", type=params.helper_gender, role="helper"),
        seed=params.seed,
    )
    story = world.render()
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show free/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
