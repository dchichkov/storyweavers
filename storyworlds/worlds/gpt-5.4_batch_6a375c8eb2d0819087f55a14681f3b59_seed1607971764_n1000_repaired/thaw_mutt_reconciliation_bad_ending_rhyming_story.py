#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py
================================================================================

A standalone story world about two children, a spring thaw, and a little mutt
on breaking ice. The children begin in a quarrel, reconcile in time to try
together, and still lose something dear in the dark water. The stories aim for
a gentle rhyming cadence while keeping the causal spine in world state.

Run it
------
    python storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py --place pond --mutt hungry --method branch
    python storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py --method step_on_ice
    python storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/thaw_mutt_reconciliation_bad_ending_rhyming_story.py --verify
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


# ---------------------------------------------------------------------------
# Entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        dog = {"dog", "mutt"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


# ---------------------------------------------------------------------------
# Domain knobs
# ---------------------------------------------------------------------------
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    water: str
    edge: str
    width: int
    thaw_force: int
    image: str
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
class MuttKind:
    id: str
    mood: str
    call: str
    lure: str
    bridge_ok: bool
    loop_ok: bool
    branch_ok: bool
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
class Prize:
    id: str
    label: str
    phrase: str
    lost_line: str
    material: str
    resilience: int
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
class Method:
    id: str
    sense: int
    reach: int
    speed: int
    text: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"child_a", "child_b"}]

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


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------
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


def _r_drift(world: World) -> list[str]:
    ice = world.get("ice")
    mutt = world.get("mutt")
    prize = world.get("prize")
    place = world.facts["place"]
    if ice.meters["thawing"] < THRESHOLD:
        return []
    sig = ("drift", int(ice.meters["drifting"]))
    if sig in world.fired:
        return []
    world.fired.add(sig)
    ice.meters["drifting"] += 1
    mutt.meters["distance"] += 1
    prize.meters["distance"] += 1
    prize.meters["danger"] += float(place.thaw_force)
    return ["__drift__"]


def _r_sadness(world: World) -> list[str]:
    prize = world.get("prize")
    if prize.meters["lost"] < THRESHOLD:
        return []
    out: list[str] = []
    for kid in world.kids():
        sig = ("sad", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["grief"] += 1
        out.append("__grief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="drift", tag="physical", apply=_r_drift),
    Rule(name="sadness", tag="emotional", apply=_r_sadness),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------------
def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def rescue_possible(place: Place, mutt: MuttKind, method: Method) -> bool:
    if method.reach < place.width:
        return False
    if method.id == "biscuit_bridge":
        return mutt.bridge_ok
    if method.id == "coat_loop":
        return mutt.loop_ok
    if method.id == "branch":
        return mutt.branch_ok
    return False


def toy_lost(place: Place, prize: Prize, delay: int) -> bool:
    return place.thaw_force + delay > prize.resilience


def rescue_success(place: Place, mutt: MuttKind, method: Method, delay: int) -> bool:
    if not rescue_possible(place, mutt, method):
        return False
    return method.speed + max(0, 2 - delay) >= 2


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for mutt_id, mk in MUTTS.items():
            for prize_id in PRIZES:
                for method_id, method in METHODS.items():
                    if method.sense >= SENSE_MIN and rescue_possible(place, mk, method):
                        combos.append((place_id, mutt_id, prize_id, method_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    place = PLACES[params.place]
    mutt = MUTTS[params.mutt]
    prize = PRIZES[params.prize]
    method = METHODS[params.method]
    rescued = rescue_success(place, mutt, method, params.delay)
    lost = toy_lost(place, prize, params.delay)
    if rescued and lost:
        return "mutt_saved_prize_lost"
    if rescued and not lost:
        return "mutt_saved_prize_kept"
    if not rescued and lost:
        return "mutt_gone_prize_lost"
    return "mutt_gone_prize_kept"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). A thawing edge needs a safer plan. "
        f"Try one of: {better}.)"
    )


def explain_combo(place: Place, mutt: MuttKind, method: Method) -> str:
    if method.reach < place.width:
        return (
            f"(No story: {method.id.replace('_', ' ')} cannot reach across {place.label}. "
            f"The water is too wide for that rescue.)"
        )
    return (
        f"(No story: a {mutt.mood} mutt would not come by {method.id.replace('_', ' ')} "
        f"at {place.label}. Pick a method the dog would trust.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def _thaw_step(world: World) -> None:
    world.get("ice").meters["thawing"] += 1
    propagate(world, narrate=False)


def predict(world: World, delay: int) -> dict:
    sim = world.copy()
    for _ in range(delay + 1):
        _thaw_step(sim)
    prize = sim.get("prize")
    mutt = sim.get("mutt")
    return {
        "prize_danger": prize.meters["danger"],
        "distance": mutt.meters["distance"],
    }


def setup_scene(world: World, a: Entity, b: Entity, prize: Entity, place: Place) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    prize.attrs["owned_by"] = f"{a.id} and {b.id}"
    world.say(
        f"At {place.label}, where the last white ridges turned to drip and thaw, "
        f"{a.id} and {b.id} came out to play beneath a silver sky so pale and slow."
    )
    world.say(
        f"They pulled {prize.phrase} through slush by the {place.edge}, "
        f"and the day felt thin and bright at the ragged winter's edge."
    )


def quarrel(world: World, a: Entity, b: Entity, prize: Prize) -> None:
    a.memes["anger"] += 1
    b.memes["anger"] += 1
    a.memes["apart"] += 1
    b.memes["apart"] += 1
    world.say(
        f'But soon they snapped, "It is my turn!" and "No, it is mine!" with hot little heat; '
        f'one tugged at the {prize.label}, one stamped two soggy feet.'
    )
    world.say(
        f"So back to back they stood in gloom, each nursing cross and pout, "
        f"and neither heard the tiny splash of trouble slipping out."
    )


def mutt_appears(world: World, mutt: Entity, place: Place, prize: Prize, mk: MuttKind) -> None:
    mutt.memes["fear"] += 1
    world.say(
        f"Out on a crust of broken ice there shivered a small gray mutt, "
        f"with {mk.call} by his nose while dark water licked and cut."
    )
    world.say(
        f"The {prize.label} bumped beside him near the place where the ice ran low; "
        f"the thaw had tugged them from the bank and set them both adrift to go."
    )


def blame(world: World, a: Entity, b: Entity, prize: Prize) -> None:
    world.say(
        f'"You pulled too hard!" cried {a.id}. "You let it slide!" cried {b.id} in turn. '
        f"The water made a grinding song while both small faces burned."
    )


def soften(world: World, a: Entity, b: Entity, delay: int, place: Place) -> None:
    pred = predict(world, delay)
    world.facts["predicted_danger"] = pred["prize_danger"]
    a.memes["worry"] += 1
    b.memes["worry"] += 1
    world.say(
        f"Then {a.id} heard the mutt cry out, a thin and frightened peep, "
        f"and saw the blacker water where the thaw had bitten deep."
    )
    world.say(
        f'"This is too big for blame," said {a.id}. "{b.id}, I was mean to shout." '
        f'"I was mean too," said {b.id}, and the hard old quarrel started out.'
    )
    if pred["prize_danger"] >= place.thaw_force:
        world.say(
            f"They knew each wasted heartbeat let the cold dark water tug more free; "
            f"what drifted now would not wait long beside the trembling tree."
        )


def reconcile(world: World, a: Entity, b: Entity) -> None:
    for kid in (a, b):
        kid.memes["anger"] = 0.0
        kid.memes["apart"] = 0.0
        kid.memes["trust"] += 1
        kid.memes["love"] += 1
    world.say(
        f"So palm met palm and eyes met eyes; their sorry words rang true, "
        f"and two small hearts that had been split beat steadier as they grew."
    )


def attempt_rescue(world: World, a: Entity, b: Entity, mk: MuttKind, method: Method) -> None:
    world.say(
        f"Together then they tried {method.text}, each doing just a part; "
        f"one lent quick hands, one lent a voice, and both lent all their heart."
    )
    if method.id == "biscuit_bridge":
        world.say(
            f"Crumb by crumb they made a trail and called in patient tone, "
            f"for a hungry mutt will trust a path when fear must walk alone."
        )
    elif method.id == "coat_loop":
        world.say(
            f"They knotted sleeves into a loop and held it low and wide, "
            f"so a dog could nose the cloth and find a safer side."
        )
    elif method.id == "branch":
        world.say(
            f"They laid a willow branch ahead like a narrow, muddy street, "
            f"and coaxed the mutt to test the path with shaking little feet."
        )


def resolve_rescue(
    world: World,
    a: Entity,
    b: Entity,
    mutt: Entity,
    prize_ent: Entity,
    place: Place,
    prize: Prize,
    method: Method,
    delay: int,
) -> None:
    for _ in range(delay + 1):
        _thaw_step(world)

    rescued = rescue_success(place, MUTTS[world.facts["mutt_cfg"].id], method, delay)
    lost = toy_lost(place, prize, delay)

    if rescued:
        mutt.meters["safe"] += 1
        mutt.memes["fear"] = 0.0
        mutt.memes["trust"] += 1
        world.say(
            f"At last the mutt came scrambling in with muddy paws and racing chest, "
            f"and tucked his nose by {b.id}'s wet coat hem as if that side felt best."
        )
    else:
        mutt.meters["gone"] += 1
        mutt.memes["fear"] += 1
        world.say(
            f"But the mutt gave one scared backward jump; the ice spun thin and wild, "
            f"and off beyond the reeds he rode from every calling child."
        )

    if lost:
        prize_ent.meters["lost"] += 1
        prize_ent.meters["safe"] = 0.0
        propagate(world, narrate=False)
        world.say(
            f"Then {prize.lost_line} It dipped once low, then slipped from sight, "
            f"and took their game into the night."
        )
    else:
        prize_ent.meters["safe"] += 1
        world.say(
            f"The {prize.label} snagged on reeds at last and shivered near the shore, "
            f"still sodden, still a sorry thing, but not yet lost for evermore."
        )

    world.facts["rescued"] = rescued
    world.facts["lost"] = lost
    world.facts["outcome"] = outcome_of(world.facts["params"])


def ending(world: World, a: Entity, b: Entity, mutt: Entity, prize: Prize) -> None:
    rescued = world.facts["rescued"]
    lost = world.facts["lost"]
    if rescued and lost:
        world.say(
            f"No cheer rose bright as song that day; the ending ached and stayed, "
            f"for though the mutt walked home with them, the {prize.label} was not saved."
        )
        world.say(
            f"But {a.id} and {b.id} walked side by side, one hand in fur, one hand in hand; "
            f"their quarrel sank where the water sank, and sorrow taught them where to stand."
        )
    elif not rescued and lost:
        world.say(
            f"So there they stood with joined-up hands, too late beside the flow; "
            f"the mutt was gone, the {prize.label} was gone, and the sky hung dull and low."
        )
        world.say(
            f"Still {a.id} and {b.id} did not part. They wept, then stayed together there, "
            f"for after bitter words were mended, grief became the thing to share."
        )
    elif rescued and not lost:
        world.say(
            f"The mutt was safe and the prize was wet, yet all their laughter came out slow; "
            f"for after anger, even a saved thing wears a softer glow."
        )
    else:
        world.say(
            f"The bank grew still; they held each other while the water dragged below, "
            f"and knew some losses answer sorrow with the saddest kind of no."
        )


def tell(
    place: Place,
    mutt_cfg: MuttKind,
    prize_cfg: Prize,
    method: Method,
    child_a_name: str = "Mira",
    child_a_gender: str = "girl",
    child_b_name: str = "Ben",
    child_b_gender: str = "boy",
    parent_type: str = "mother",
    delay: int = 1,
) -> World:
    world = World()
    a = world.add(Entity(id=child_a_name, kind="character", type=child_a_gender, role="child_a"))
    b = world.add(Entity(id=child_b_name, kind="character", type=child_b_gender, role="child_b"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    mutt = world.add(Entity(id="mutt", kind="character", type="mutt", role="mutt", label="the mutt"))
    ice = world.add(Entity(id="ice", type="ice", label="the ice"))
    prize_ent = world.add(Entity(id="prize", type="prize", label=prize_cfg.label))

    ice.meters["thawing"] = 0.0
    ice.meters["drifting"] = 0.0
    mutt.meters["distance"] = 0.0
    prize_ent.meters["distance"] = 0.0
    prize_ent.meters["danger"] = 0.0
    prize_ent.meters["lost"] = 0.0
    prize_ent.meters["safe"] = 0.0
    mutt.meters["safe"] = 0.0
    mutt.meters["gone"] = 0.0

    world.facts.update(
        place=place,
        mutt_cfg=mutt_cfg,
        prize_cfg=prize_cfg,
        method=method,
        params=None,
        rescued=False,
        lost=False,
        outcome="",
        parent=parent,
    )

    setup_scene(world, a, b, prize_ent, place)
    quarrel(world, a, b, prize_cfg)
    world.para()
    mutt_appears(world, mutt, place, prize_cfg, mutt_cfg)
    blame(world, a, b, prize_cfg)
    world.para()
    soften(world, a, b, delay, place)
    reconcile(world, a, b)
    attempt_rescue(world, a, b, mutt_cfg, method)
    world.para()
    resolve_rescue(world, a, b, mutt, prize_ent, place, prize_cfg, method, delay)
    ending(world, a, b, mutt, prize_cfg)

    world.facts.update(
        child_a=a,
        child_b=b,
        mutt=mutt,
        prize=prize_ent,
        ice=ice,
        reconciled=a.memes["love"] >= THRESHOLD and b.memes["love"] >= THRESHOLD,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "pond": Place(
        id="pond",
        label="the pond edge",
        water="pond water",
        edge="bank",
        width=2,
        thaw_force=2,
        image="brown reeds and a glazed gray rim",
        tags={"thaw", "ice", "pond"},
    ),
    "creek": Place(
        id="creek",
        label="the creek bend",
        water="creek water",
        edge="muddy bend",
        width=3,
        thaw_force=3,
        image="a quick dark ribbon under rotten ice",
        tags={"thaw", "ice", "creek"},
    ),
    "ditch": Place(
        id="ditch",
        label="the lane-side ditch",
        water="ditch water",
        edge="grassy lip",
        width=1,
        thaw_force=2,
        image="thin water under grass and broken skim",
        tags={"thaw", "ice", "ditch"},
    ),
}

MUTTS = {
    "hungry": MuttKind(
        id="hungry",
        mood="hungry",
        call="a biscuit smell",
        lure="food",
        bridge_ok=True,
        loop_ok=True,
        branch_ok=True,
        tags={"mutt", "dog", "hunger"},
    ),
    "timid": MuttKind(
        id="timid",
        mood="timid",
        call="a soft scared whine",
        lure="soft voices",
        bridge_ok=False,
        loop_ok=False,
        branch_ok=True,
        tags={"mutt", "dog", "fear"},
    ),
    "friendly": MuttKind(
        id="friendly",
        mood="friendly",
        call="a hopeful little wag",
        lure="kind voices",
        bridge_ok=True,
        loop_ok=True,
        branch_ok=True,
        tags={"mutt", "dog"},
    ),
}

PRIZES = {
    "sled": Prize(
        id="sled",
        label="sled",
        phrase="their red little sled",
        lost_line="Then the red sled spun in a crooked round and the black water took its red.",
        material="painted wood",
        resilience=1,
        tags={"sled", "toy"},
    ),
    "boat": Prize(
        id="boat",
        label="boat",
        phrase="their carved toy boat on a string",
        lost_line="Then the toy boat kissed one cold whirl and the string went slack instead.",
        material="wood and string",
        resilience=2,
        tags={"boat", "toy"},
    ),
    "drum": Prize(
        id="drum",
        label="drum",
        phrase="their small tin drum with the blue stripe round",
        lost_line="Then the tin drum bobbed with a hollow hum and sank with a little dread.",
        material="tin",
        resilience=1,
        tags={"drum", "toy"},
    ),
}

METHODS = {
    "branch": Method(
        id="branch",
        sense=3,
        reach=3,
        speed=2,
        text="a willow branch laid from the bank",
        qa_text="used a long willow branch from the bank",
        tags={"branch", "safe_rescue"},
    ),
    "biscuit_bridge": Method(
        id="biscuit_bridge",
        sense=3,
        reach=2,
        speed=1,
        text="a biscuit trail over the safest broken crust",
        qa_text="made a biscuit trail to lure the mutt back",
        tags={"biscuit", "safe_rescue"},
    ),
    "coat_loop": Method(
        id="coat_loop",
        sense=2,
        reach=2,
        speed=1,
        text="their sleeves knotted into a coat-loop",
        qa_text="knotted their coats into a long loop",
        tags={"coat", "safe_rescue"},
    ),
    "step_on_ice": Method(
        id="step_on_ice",
        sense=1,
        reach=1,
        speed=1,
        text="stepping onto the thawing ice by themselves",
        qa_text="stepped onto the thawing ice",
        tags={"unsafe"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Tess", "Nina", "Ruby", "Clara", "Ivy", "May"]
BOY_NAMES = ["Ben", "Noah", "Eli", "Finn", "Theo", "Sam", "Jude", "Max"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mutt: str
    prize: str
    method: str
    child_a_name: str
    child_a_gender: str
    child_b_name: str
    child_b_gender: str
    parent: str
    delay: int = 1
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
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


KNOWLEDGE = {
    "thaw": [
        (
            "What is a thaw?",
            "A thaw is when frozen ice or snow starts to melt because the air gets warmer. When a thaw begins, ice can turn weak, wet, and slippery."
        )
    ],
    "ice": [
        (
            "Why is thawing ice dangerous?",
            "Thawing ice can look solid even when it has gone thin and weak. That means it can crack, drift, or break under weight."
        )
    ],
    "mutt": [
        (
            "What is a mutt?",
            "A mutt is a dog whose family is a mix of different kinds of dogs. People often use the word for a scruffy mixed-breed dog."
        )
    ],
    "branch": [
        (
            "Why can a long branch help rescue an animal near water?",
            "A long branch lets you reach from a safer place instead of stepping into danger. It can give the animal a path or something steady to follow."
        )
    ],
    "biscuit": [
        (
            "Why might food help lure a hungry dog?",
            "A hungry dog may follow a safe trail of food when it is too scared to come for voices alone. The smell gives the dog a reason to move toward help."
        )
    ],
    "coat": [
        (
            "Why is a coat-loop safer than stepping onto thin ice?",
            "A coat-loop keeps people on the bank while they reach farther. Staying off the weak ice lowers the chance of anyone else slipping into danger."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means people stop fighting and make peace again. It often starts with saying sorry and choosing to work together."
        )
    ],
}

KNOWLEDGE_ORDER = ["thaw", "ice", "mutt", "branch", "biscuit", "coat", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    place = f["place"]
    prize = f["prize_cfg"]
    method = f["method"]
    return [
        f'Write a rhyming story for a 3-to-5-year-old that includes the words "thaw" and "mutt". Two children quarrel, reconcile, and face a sad ending by {place.label}.',
        f"Tell a gentle but unhappy spring story where {a.id} and {b.id} stop fighting so they can help a mutt on thawing ice, but they still lose their {prize.label}.",
        f"Write a child-facing poem-story about reconciliation after blame, using {method.id.replace('_', ' ')} as the rescue method and ending with a bittersweet walk home.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child_a"]
    b = f["child_b"]
    prize_cfg = f["prize_cfg"]
    place = f["place"]
    method = f["method"]
    mutt_cfg = f["mutt_cfg"]
    rescued = f["rescued"]
    lost = f["lost"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id}, two children by {place.label}, and a little mutt on breaking ice. Their shared {prize_cfg.label} is part of the trouble too."
        ),
        (
            "Why were the children upset at the beginning?",
            f"They were quarreling over the {prize_cfg.label} and each wanted to be right. That fight left them facing away from each other just as the danger began."
        ),
        (
            "Why was the mutt in danger?",
            f"The mutt was stranded on weak ice during a thaw. As the ice broke and drifted, the cold water could carry him farther from the bank."
        ),
        (
            "How did the children reconcile?",
            f"{a.id} and {b.id} stopped blaming each other and said they were sorry. After that, they worked together instead of pulling apart."
        ),
    ]
    if rescued:
        qa.append(
            (
                "How did they help the mutt?",
                f"They {method.qa_text}. That worked because a {mutt_cfg.mood} mutt could trust that kind of help while the children stayed on the bank."
            )
        )
    else:
        qa.append(
            (
                "Did their plan save the mutt?",
                f"No. They had reconciled and tried together, but the mutt drifted away before the plan could bring him back. The thaw made the danger move faster than they could fix."
            )
        )
    if lost:
        qa.append(
            (
                f"Why did they lose the {prize_cfg.label}?",
                f"They spent precious time fighting before they worked together, and the thaw kept pulling at the ice. By the time they tried to help, the water had already dragged the {prize_cfg.label} beyond saving."
            )
        )
    qa.append(
        (
            "Why is the ending sad even after they made peace?",
            f"The children did mend their hearts, but reconciliation could not undo what the thaw had already taken. In this story, being kind again helps them face the loss together, not erase it."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"thaw", "ice", "mutt", "reconciliation"}
    method = world.facts["method"]
    if "branch" in method.tags:
        tags.add("branch")
    if "biscuit" in method.tags:
        tags.add("biscuit")
    if "coat" in method.tags:
        tags.add("coat")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="pond",
        mutt="hungry",
        prize="sled",
        method="branch",
        child_a_name="Mira",
        child_a_gender="girl",
        child_b_name="Ben",
        child_b_gender="boy",
        parent="mother",
        delay=1,
    ),
    StoryParams(
        place="ditch",
        mutt="friendly",
        prize="boat",
        method="coat_loop",
        child_a_name="Lena",
        child_a_gender="girl",
        child_b_name="Noah",
        child_b_gender="boy",
        parent="father",
        delay=1,
    ),
    StoryParams(
        place="creek",
        mutt="timid",
        prize="drum",
        method="branch",
        child_a_name="Ruby",
        child_a_gender="girl",
        child_b_name="Eli",
        child_b_gender="boy",
        parent="mother",
        delay=2,
    ),
    StoryParams(
        place="pond",
        mutt="hungry",
        prize="boat",
        method="biscuit_bridge",
        child_a_name="Ivy",
        child_a_gender="girl",
        child_b_name="Finn",
        child_b_gender="boy",
        parent="father",
        delay=1,
    ),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% sensible methods
sensible(M) :- method(M), sense(M,S), sense_min(N), S >= N.

% compatibility gate
rescue_possible(P, K, M) :- place(P), mutt(K), method(M),
                            reach(M, R), width(P, W), R >= W,
                            M = branch, branch_ok(K).
rescue_possible(P, K, M) :- place(P), mutt(K), method(M),
                            reach(M, R), width(P, W), R >= W,
                            M = biscuit_bridge, bridge_ok(K).
rescue_possible(P, K, M) :- place(P), mutt(K), method(M),
                            reach(M, R), width(P, W), R >= W,
                            M = coat_loop, loop_ok(K).

valid(P, K, Z, M) :- place(P), mutt(K), prize(Z), sensible(M), rescue_possible(P, K, M).

% outcome
rescued :- chosen_place(P), chosen_mutt(K), chosen_method(M), delay(D),
           rescue_possible(P, K, M), speed(M, S), S + (2 - D) >= 2.
lost :- chosen_place(P), chosen_prize(Z), delay(D),
        thaw_force(P, F), resilience(Z, R), F + D > R.

outcome(mutt_saved_prize_lost) :- rescued, lost.
outcome(mutt_saved_prize_kept) :- rescued, not lost.
outcome(mutt_gone_prize_lost) :- not rescued, lost.
outcome(mutt_gone_prize_kept) :- not rescued, not lost.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("width", place_id, place.width))
        lines.append(asp.fact("thaw_force", place_id, place.thaw_force))
    for mutt_id, mk in MUTTS.items():
        lines.append(asp.fact("mutt", mutt_id))
        if mk.bridge_ok:
            lines.append(asp.fact("bridge_ok", mutt_id))
        if mk.loop_ok:
            lines.append(asp.fact("loop_ok", mutt_id))
        if mk.branch_ok:
            lines.append(asp.fact("branch_ok", mutt_id))
    for prize_id, prize in PRIZES.items():
        lines.append(asp.fact("prize", prize_id))
        lines.append(asp.fact("resilience", prize_id, prize.resilience))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("sense", method_id, method.sense))
        lines.append(asp.fact("reach", method_id, method.reach))
        lines.append(asp.fact("speed", method_id, method.speed))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_mutt", params.mutt),
            asp.fact("chosen_prize", params.prize),
            asp.fact("chosen_method", params.method),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    c_sens = set(asp_sensible())
    p_sens = {m.id for m in sensible_methods()}
    if c_sens == p_sens:
        print(f"OK: sensible methods match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for s in range(120):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated an empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: two children reconcile during a thaw to help a mutt, "
        "but the ending stays sad. Unspecified choices are randomized with a seed."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mutt", choices=MUTTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="extra wasted beats before the rescue works or fails")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    if args.place and args.mutt and args.method:
        place = PLACES[args.place]
        mutt = MUTTS[args.mutt]
        method = METHODS[args.method]
        if not rescue_possible(place, mutt, method):
            raise StoryError(explain_combo(place, mutt, method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.mutt is None or combo[1] == args.mutt)
        and (args.prize is None or combo[2] == args.prize)
        and (args.method is None or combo[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, mutt_id, prize_id, method_id = rng.choice(sorted(combos))
    child_a_name, child_a_gender = _pick_child(rng)
    child_b_name, child_b_gender = _pick_child(rng, avoid=child_a_name)
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])

    return StoryParams(
        place=place_id,
        mutt=mutt_id,
        prize=prize_id,
        method=method_id,
        child_a_name=child_a_name,
        child_a_gender=child_a_gender,
        child_b_name=child_b_name,
        child_b_gender=child_b_gender,
        parent=parent,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.mutt not in MUTTS:
        raise StoryError(f"(Unknown mutt kind: {params.mutt})")
    if params.prize not in PRIZES:
        raise StoryError(f"(Unknown prize: {params.prize})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")

    place = PLACES[params.place]
    mutt = MUTTS[params.mutt]
    prize = PRIZES[params.prize]
    method = METHODS[params.method]

    if method.sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))
    if not rescue_possible(place, mutt, method):
        raise StoryError(explain_combo(place, mutt, method))

    world = tell(
        place=place,
        mutt_cfg=mutt,
        prize_cfg=prize,
        method=method,
        child_a_name=params.child_a_name,
        child_a_gender=params.child_a_gender,
        child_b_name=params.child_b_name,
        child_b_gender=params.child_b_gender,
        parent_type=params.parent,
        delay=params.delay,
    )
    world.facts["params"] = params
    world.facts["outcome"] = outcome_of(params)

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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible methods: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, mutt, prize, method) combos:\n")
        for place, mutt, prize, method in combos:
            print(f"  {place:7} {mutt:8} {prize:6} {method}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = (
                f"### {p.child_a_name} & {p.child_b_name}: {p.mutt} mutt at {p.place} "
                f"with {p.method} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
