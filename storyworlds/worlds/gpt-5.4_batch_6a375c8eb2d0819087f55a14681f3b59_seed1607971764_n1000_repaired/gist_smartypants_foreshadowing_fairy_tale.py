#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py
=======================================================================

A standalone fairy-tale-flavored story world about a child who tries to skip the
full instructions for a tiny magical task, boasts like a smartypants, and then
has to learn that the *gist* is not always enough.

The domain is intentionally small and constraint-checked: a village child is
asked to carry a charm through a place with a specific magical risk. A helper
gives clear advice and a protective item. If the child listens, the charm is
delivered safely. If the child ignores the warning and carries only the gist,
the charm falters and must be repaired before the ending can turn bright again.

Foreshadowing is built into the world state: the warning names the exact danger
that will later happen, and Q&A reads that trace back out of the model rather
than from the rendered English.

Run it
------
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py --route reed_bridge --charm dew_lantern
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py --route windy_hill --cover none
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py --all
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/gist_smartypants_foreshadowing_fairy_tale.py --verify
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "witch", "queen"}
        male = {"boy", "father", "man", "wizard", "king"}
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
class Charm:
    id: str
    label: str
    phrase: str
    purpose: str
    fragile_to: str
    consequence: str
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
class Route:
    id: str
    place: str
    hazard: str
    sign: str
    warning: str
    atmosphere: str
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
class Cover:
    id: str
    label: str
    phrase: str
    protects_from: set[str] = field(default_factory=set)
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
class Repair:
    id: str
    label: str
    phrase: str
    fixes: set[str] = field(default_factory=set)
    action_text: str = ""
    qa_text: str = ""
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


def _r_hazard_hurts_charm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    charm = world.get("charm")
    route = world.get("route")
    cover = world.get("cover")
    if child.attrs.get("on_route") != route.id:
        return out
    if cover.attrs.get("protects", set()) and route.attrs.get("hazard") in cover.attrs.get("protects", set()):
        return out
    if route.attrs.get("hazard") != charm.attrs.get("fragile_to"):
        return out
    sig = ("hazard_hurts", route.id, charm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    charm.meters["faded"] += 1
    charm.meters["safe"] = 0.0
    child.memes["worry"] += 1
    out.append("__hazard__")
    return out


def _r_success_glow(world: World) -> list[str]:
    out: list[str] = []
    charm = world.get("charm")
    queen = world.get("queen")
    if charm.meters["delivered"] < THRESHOLD:
        return out
    if charm.meters["faded"] >= THRESHOLD:
        return out
    sig = ("glow", charm.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    queen.memes["relief"] += 1
    charm.meters["glowing"] += 1
    out.append("__glow__")
    return out


CAUSAL_RULES = [
    Rule(name="hazard_hurts_charm", tag="physical", apply=_r_hazard_hurts_charm),
    Rule(name="success_glow", tag="resolution", apply=_r_success_glow),
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


def cover_works(route: Route, charm: Charm, cover: Cover) -> bool:
    return route.hazard == charm.fragile_to and route.hazard in cover.protects_from


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for route_id, route in ROUTES.items():
        for charm_id, charm in CHARMS.items():
            for cover_id, cover in COVERS.items():
                for repair_id, repair in REPAIRS.items():
                    if route.hazard != charm.fragile_to:
                        continue
                    if not cover_works(route, charm, cover) and cover_id != "none":
                        continue
                    if route.hazard not in repair.fixes:
                        continue
                    combos.append((route_id, charm_id, cover_id, repair_id))
    return combos


def explain_rejection(route: Route, charm: Charm, cover: Cover, repair: Repair) -> str:
    if route.hazard != charm.fragile_to:
        return (
            f"(No story: {charm.label} is not threatened by {route.hazard}, so the warning would "
            f"not honestly foreshadow any real trouble on {route.place}.)"
        )
    if cover.id != "none" and not cover_works(route, charm, cover):
        return (
            f"(No story: {cover.label} does not protect {charm.label} from {route.hazard}. "
            f"The helper's advice must actually work.)"
        )
    if route.hazard not in repair.fixes:
        return (
            f"(No story: {repair.label} cannot mend harm caused by {route.hazard}, so the tale "
            f"would have no believable repair after the mistake.)"
        )
    return "(No story: this combination does not form a reasonable fairy tale.)"


def predict_hazard(world: World) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.attrs["on_route"] = "route"
    propagate(sim, narrate=False)
    charm = sim.get("charm")
    return {
        "faded": charm.meters["faded"] >= THRESHOLD,
        "hazard": sim.get("route").attrs.get("hazard", ""),
    }


def introduce(world: World, child: Entity, charm: Charm, queen: Entity, route: Route) -> None:
    world.say(
        f"Once, beside a silver wood, there lived a little {child.type} named {child.id} who loved to answer quickly."
    )
    world.say(
        f"One dawn, the {queen.label} placed {charm.phrase} in {child.id}'s hands and said it must reach the moonwell by way of {route.place}."
    )
    child.memes["pride"] += 1


def foreshadow(world: World, guide: Entity, child: Entity, route: Route, charm: Charm, cover: Cover) -> None:
    pred = predict_hazard(world)
    world.facts["predicted_hazard"] = pred["hazard"]
    world.facts["foreshadowed"] = pred["faded"]
    world.say(
        f'By the gate stood {guide.label}, who saw {route.sign}. "{route.warning}," {guide.pronoun()} said.'
    )
    if cover.id != "none":
        world.say(
            f'{guide.pronoun().capitalize()} offered {cover.phrase}. "Keep {charm.label} tucked inside, and it will stay bright."'
        )
    else:
        world.say(
            f'{guide.pronoun().capitalize()} had no proper wrapping to give, only a worried look and careful words.'
        )


def boast(world: World, child: Entity, guide: Entity, charm: Charm) -> None:
    child.memes["boast"] += 1
    world.say(
        f'{child.id} tossed {child.pronoun("possessive")} head and said, "I have the gist. I do not need every little rule."'
    )
    world.say(
        f'"Do not be such a smartypants," {guide.label} said gently. "Magic listens best to careful ears."'
    )


def choose_listen(world: World, child: Entity, cover: Cover, charm: Charm) -> None:
    child.memes["care"] += 1
    child.attrs["used_cover"] = True
    world.say(
        f"But as {child.id} looked at {charm.label}, the boasting words felt too sharp."
    )
    if cover.id != "none":
        world.say(
            f"{child.pronoun().capitalize()} wrapped the charm in {cover.label} and held it close."
        )
    else:
        world.say(
            f"{child.pronoun().capitalize()} slowed down, cupped the charm with both hands, and promised to mind each warning."
        )


def choose_ignore(world: World, child: Entity, charm: Charm) -> None:
    child.memes["defiance"] += 1
    child.attrs["used_cover"] = False
    world.say(
        f"{child.id} hurried on with only the gist in mind, feeling very grand and very sure."
    )


def cross_route(world: World, child: Entity, route: Route) -> None:
    child.attrs["on_route"] = "route"
    world.say(f"{route.atmosphere}")
    propagate(world, narrate=False)


def hazard_scene(world: World, child: Entity, route: Route, charm: Charm) -> None:
    world.say(
        f"Just as {guide_phrase(route)} had promised, the {route.hazard} found the charm."
    )
    world.say(
        f"{charm.phrase.capitalize()} {charm.consequence}, and {child.id} felt {child.pronoun('possessive')} brave smile slip away."
    )


def guide_phrase(route: Route) -> str:
    return {
        "mist": "mist by the reeds",
        "wind": "wind on the hill",
        "sparks": "sparks in the hollow",
    }.get(route.hazard, route.hazard)


def safe_arrival(world: World, child: Entity, queen: Entity, charm: Entity) -> None:
    charm.meters["delivered"] += 1
    charm.meters["safe"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {child.id} reached the moonwell, the charm still shone as clear as the first drop of morning."
    )
    world.say(
        f"The {queen.label} smiled, and silver light spread over the thirsty garden beds."
    )


def ask_help(world: World, child: Entity, guide: Entity) -> None:
    child.memes["humble"] += 1
    world.say(
        f'"Please," {child.id} said, turning back at once, "I thought being quick was the same as being wise. It was not."'
    )
    world.say(
        f"{guide.label} came along the path with steady steps, for kind helpers in fairy tales do not stay far away."
    )


def repair_charm(world: World, guide: Entity, child: Entity, charm: Entity, repair: Repair) -> None:
    charm.meters["faded"] = 0.0
    charm.meters["mended"] += 1
    charm.meters["delivered"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{guide.label} {repair.action_text}."
    )
    world.say(
        f"Little by little, the pale light gathered itself again inside the charm."
    )


def humbled_ending(world: World, child: Entity, queen: Entity, cover: Cover) -> None:
    world.say(
        f"When they reached the moonwell at last, the charm glowed again, though now {child.id} walked more slowly than before."
    )
    world.say(
        f'The {queen.label} thanked {child.id}, and {child.pronoun()} answered, "Next time I will listen to more than the gist."'
    )
    if cover.id != "none":
        world.say(
            f"From that day on, {child.id} never laughed at careful tools or called caution fussing again."
        )
    else:
        world.say(
            f"From that day on, {child.id} remembered that wise words can be a kind of shelter too."
        )


def tell(
    route: Route,
    charm_cfg: Charm,
    cover_cfg: Cover,
    repair_cfg: Repair,
    child_name: str = "Mira",
    child_gender: str = "girl",
    guide_type: str = "witch",
    queen_type: str = "queen",
    heed_warning: bool = False,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="child"))
    guide = world.add(Entity(id="guide", kind="character", type=guide_type, label="the mossy witch", role="guide"))
    queen = world.add(Entity(id="queen", kind="character", type=queen_type, label="moon-queen", role="queen"))
    charm = world.add(
        Entity(
            id="charm",
            kind="thing",
            type="charm",
            label=charm_cfg.label,
            attrs={"fragile_to": charm_cfg.fragile_to, "purpose": charm_cfg.purpose},
        )
    )
    route_ent = world.add(
        Entity(
            id="route",
            kind="thing",
            type="route",
            label=route.place,
            attrs={"hazard": route.hazard, "warning": route.warning},
        )
    )
    cover = world.add(
        Entity(
            id="cover",
            kind="thing",
            type="cover",
            label=cover_cfg.label,
            attrs={"protects": set(cover_cfg.protects_from)},
        )
    )

    child.attrs["used_cover"] = False
    child.attrs["on_route"] = ""
    charm.meters["safe"] = 1.0
    charm.meters["faded"] = 0.0
    charm.meters["delivered"] = 0.0
    queen.memes["relief"] = 0.0
    child.memes["worry"] = 0.0

    introduce(world, child, charm_cfg, queen, route)
    world.para()
    foreshadow(world, guide, child, route, charm_cfg, cover_cfg)
    boast(world, child, guide, charm_cfg)
    world.para()

    if heed_warning:
        choose_listen(world, child, cover_cfg, charm_cfg)
        cross_route(world, child, route)
        safe_arrival(world, child, queen, charm)
        outcome = "safe"
    else:
        choose_ignore(world, child, charm_cfg)
        cross_route(world, child, route)
        if charm.meters["faded"] >= THRESHOLD:
            hazard_scene(world, child, route, charm_cfg)
        world.para()
        ask_help(world, child, guide)
        repair_charm(world, guide, child, charm, repair_cfg)
        humbled_ending(world, child, queen, cover_cfg)
        outcome = "mended"

    world.facts.update(
        child=child,
        guide=guide,
        queen=queen,
        charm_cfg=charm_cfg,
        route_cfg=route,
        cover_cfg=cover_cfg,
        repair_cfg=repair_cfg,
        heed_warning=heed_warning,
        outcome=outcome,
        used_cover=child.attrs.get("used_cover", False),
        foreshadowed=world.facts.get("foreshadowed", False),
        hazard_happened=charm.meters["mended"] >= THRESHOLD or child.memes["worry"] >= THRESHOLD,
        charm_mended=charm.meters["mended"] >= THRESHOLD,
        charm_delivered=charm.meters["delivered"] >= THRESHOLD,
    )
    return world


CHARMS = {
    "dew_lantern": Charm(
        id="dew_lantern",
        label="dew lantern",
        phrase="a dew lantern in a shell of glass",
        purpose="to wake the sleeping lilies",
        fragile_to="mist",
        consequence="went cloudy and dim",
        tags={"lantern", "mist", "magic"},
    ),
    "star_letter": Charm(
        id="star_letter",
        label="star letter",
        phrase="a star letter folded from light",
        purpose="to carry a blessing to the moonwell",
        fragile_to="wind",
        consequence="fluttered loose and lost its shine",
        tags={"letter", "wind", "magic"},
    ),
    "ember_seed": Charm(
        id="ember_seed",
        label="ember seed",
        phrase="an ember seed wrapped in golden thread",
        purpose="to warm the orchard roots",
        fragile_to="sparks",
        consequence="crackled the wrong way and darkened",
        tags={"seed", "sparks", "magic"},
    ),
}

ROUTES = {
    "reed_bridge": Route(
        id="reed_bridge",
        place="the reed bridge",
        hazard="mist",
        sign="white mist curling above the river",
        warning="Mind the river mist, for it steals the shine from dew-made things",
        atmosphere="Across the reeds, cool mist rose in soft ropes and stroked the bridge rails like ghostly fingers",
        tags={"mist", "bridge"},
    ),
    "windy_hill": Route(
        id="windy_hill",
        place="the windy hill",
        hazard="wind",
        sign="the bent grass all leaning one way",
        warning="Mind the hill wind, for it loves to tease apart light things and carry them astray",
        atmosphere="Up on the hill, the wind came singing over the stones and tugged at sleeves, hems, and promises",
        tags={"wind", "hill"},
    ),
    "thorn_hollow": Route(
        id="thorn_hollow",
        place="the thorn hollow",
        hazard="sparks",
        sign="tiny orange pricks hopping among the roots",
        warning="Mind the thorn sparks, for they nip at ember-work and make it sulk",
        atmosphere="In the hollow, tiny sparks skipped from root to root like rude fireflies with sharp little tempers",
        tags={"sparks", "hollow"},
    ),
}

COVERS = {
    "wax_cloak": Cover(
        id="wax_cloak",
        label="waxed leaf-cloak",
        phrase="a waxed leaf-cloak",
        protects_from={"mist"},
        tags={"cover", "mist"},
    ),
    "ribbon_case": Cover(
        id="ribbon_case",
        label="ribbon case",
        phrase="a ribbon case lined with lambswool",
        protects_from={"wind"},
        tags={"cover", "wind"},
    ),
    "clay_cup": Cover(
        id="clay_cup",
        label="clay cup",
        phrase="a clay cup with a snug lid",
        protects_from={"sparks"},
        tags={"cover", "sparks"},
    ),
    "none": Cover(
        id="none",
        label="bare hands",
        phrase="bare hands",
        protects_from=set(),
        tags=set(),
    ),
}

REPAIRS = {
    "moon_drop": Repair(
        id="moon_drop",
        label="moon-drop spell",
        phrase="a moon-drop spell",
        fixes={"mist"},
        action_text="caught one moonlit tear from a fern and touched it to the cloudy glass",
        qa_text="used a moon-drop spell to clear the lantern again",
        tags={"repair", "mist"},
    ),
    "silver_knot": Repair(
        id="silver_knot",
        label="silver knot",
        phrase="a silver knot",
        fixes={"wind"},
        action_text="whispered a silver knot into the torn folds of light and tied them back together",
        qa_text="tied the star letter back together with a silver knot",
        tags={"repair", "wind"},
    ),
    "ash_song": Repair(
        id="ash_song",
        label="ash song",
        phrase="an ash song",
        fixes={"sparks"},
        action_text="sang an ash song so softly that the dark ember remembered how to glow the right way",
        qa_text="sang an ash song to set the ember seed right again",
        tags={"repair", "sparks"},
    ),
}

GIRL_NAMES = ["Mira", "Elin", "Tansy", "Poppy", "Nella", "Iris"]
BOY_NAMES = ["Rowan", "Tobin", "Alder", "Finn", "Bram", "Lio"]


@dataclass
class StoryParams:
    route: str
    charm: str
    cover: str
    repair: str
    name: str
    gender: str
    guide: str
    queen: str
    heed_warning: bool
    seed: Optional[int] = None
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


KNOWLEDGE = {
    "mist": [(
        "What is mist?",
        "Mist is a cloud very close to the ground, made of tiny drops of water. It can make things damp and hard to see."
    )],
    "wind": [(
        "What can wind do?",
        "Wind can push, tug, and carry light things away. Strong wind can make it hard to hold onto small objects."
    )],
    "sparks": [(
        "What is a spark?",
        "A spark is a tiny bright bit of fire or heat. Even a little spark can bother delicate things."
    )],
    "magic": [(
        "Why do fairy tales use careful rules for magic?",
        "Fairy-tale magic often works best when people listen closely and follow wise advice. The rules help show that care matters."
    )],
    "foreshadowing": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story hints early about something that will matter later. It helps the later event feel prepared instead of sudden."
    )],
    "humility": [(
        "Why is it better not to act like a smartypants?",
        "A smartypants acts as if already knowing everything, and that can block good advice. Humility leaves room to learn."
    )],
}
KNOWLEDGE_ORDER = ["mist", "wind", "sparks", "magic", "foreshadowing", "humility"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    route = f["route_cfg"]
    charm = f["charm_cfg"]
    if f["outcome"] == "safe":
        return [
            f'Write a fairy tale for ages 3 to 5 that includes the words "gist" and "smartypants". Use foreshadowing when a guide warns about {route.hazard}.',
            f"Tell a gentle fairy tale where {child.label} almost acts like a smartypants, then listens carefully and carries a {charm.label} safely across {route.place}.",
            f"Write a small magical story where the warning comes first, the danger is hinted at, and the child chooses wisdom over pride."
        ]
    return [
        f'Write a fairy tale for ages 3 to 5 that includes the words "gist" and "smartypants". Use foreshadowing so an early warning about {route.hazard} comes true later.',
        f"Tell a fairy tale where {child.label} says {child.pronoun('subject')} has the gist, ignores a guide, and then needs help repairing a {charm.label}.",
        f"Write a child-facing magical cautionary tale with a warm ending: pride causes a problem, but honesty and help mend it."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guide = f["guide"]
    queen = f["queen"]
    route = f["route_cfg"]
    charm = f["charm_cfg"]
    cover = f["cover_cfg"]
    repair = f["repair_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.label}, a child carrying the {charm.label}, and {guide.label}, who tried to help. The moon-queen also mattered because the charm was needed for {charm.purpose}."
        ),
        (
            f"What warning came before the trouble on {route.place}?",
            f"{guide.label.capitalize()} warned {child.label} about {route.hazard} before the journey began. That was foreshadowing, because the same danger mattered later on the path."
        ),
        (
            f"Why did {guide.label} call {child.label} a smartypants?",
            f"{child.label} acted as if only the gist was enough and did not need the full advice. The word fits because {child.pronoun('subject')} sounded proudly over-sure instead of careful."
        ),
    ]
    if f["outcome"] == "safe":
        out.append((
            f"How did {child.label} keep the {charm.label} safe?",
            f"{child.label} listened to the warning and used {cover.phrase}. Because the cover matched the danger from {route.hazard}, the charm stayed bright all the way to the moonwell."
        ))
        out.append((
            "How did the story end?",
            f"It ended happily, with the charm shining and the moon-queen smiling. The bright ending proves that careful listening changed what happened."
        ))
    else:
        out.append((
            f"What happened when {child.label} ignored the warning?",
            f"The {route.hazard} reached the {charm.label}, and it {charm.consequence}. That happened because {child.label} hurried on with only the gist and left the good advice unused."
        ))
        out.append((
            f"How was the {charm.label} fixed?",
            f"{guide.label.capitalize()} {repair.qa_text}. After that, the light gathered itself again, so the journey could still end well."
        ))
        out.append((
            f"What did {child.label} learn by the end?",
            f"{child.pronoun().capitalize()} learned that being quick is not the same as being wise. The ending changes because {child.pronoun('subject')} becomes honest, asks for help, and listens better."
        ))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["route_cfg"].tags) | set(f["charm_cfg"].tags) | {"foreshadowing", "humility"}
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="reed_bridge",
        charm="dew_lantern",
        cover="wax_cloak",
        repair="moon_drop",
        name="Mira",
        gender="girl",
        guide="witch",
        queen="queen",
        heed_warning=False,
    ),
    StoryParams(
        route="windy_hill",
        charm="star_letter",
        cover="ribbon_case",
        repair="silver_knot",
        name="Rowan",
        gender="boy",
        guide="witch",
        queen="queen",
        heed_warning=True,
    ),
    StoryParams(
        route="thorn_hollow",
        charm="ember_seed",
        cover="clay_cup",
        repair="ash_song",
        name="Tansy",
        gender="girl",
        guide="witch",
        queen="queen",
        heed_warning=False,
    ),
    StoryParams(
        route="reed_bridge",
        charm="dew_lantern",
        cover="none",
        repair="moon_drop",
        name="Finn",
        gender="boy",
        guide="witch",
        queen="queen",
        heed_warning=False,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld: a child carries a charm, pride meets a warning, and foreshadowed danger proves why care matters."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--heed-warning", action="store_true", help="choose the listening branch")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.charm and args.cover and args.repair:
        route = ROUTES[args.route]
        charm = CHARMS[args.charm]
        cover = COVERS[args.cover]
        repair = REPAIRS[args.repair]
        if (args.route, args.charm, args.cover, args.repair) not in valid_combos():
            raise StoryError(explain_rejection(route, charm, cover, repair))

    combos = [
        c for c in valid_combos()
        if (args.route is None or c[0] == args.route)
        and (args.charm is None or c[1] == args.charm)
        and (args.cover is None or c[2] == args.cover)
        and (args.repair is None or c[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    route_id, charm_id, cover_id, repair_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    heed_warning = bool(args.heed_warning) if args.heed_warning else rng.choice([False, True])
    return StoryParams(
        route=route_id,
        charm=charm_id,
        cover=cover_id,
        repair=repair_id,
        name=name,
        gender=gender,
        guide="witch",
        queen="queen",
        heed_warning=heed_warning,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        route = ROUTES[params.route]
        charm = CHARMS[params.charm]
        cover = COVERS[params.cover]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Unknown option: {err.args[0]})") from None

    if (params.route, params.charm, params.cover, params.repair) not in valid_combos():
        raise StoryError(explain_rejection(route, charm, cover, repair))

    world = tell(
        route=route,
        charm_cfg=charm,
        cover_cfg=cover,
        repair_cfg=repair,
        child_name=params.name,
        child_gender=params.gender,
        guide_type=params.guide,
        queen_type=params.queen,
        heed_warning=params.heed_warning,
    )
    child = world.get("child")
    child.label = params.name
    return StorySample(
        params=params,
        story=world.render().replace("child", params.name),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


ASP_RULES = r"""
hazard_match(R, C) :- route(R), charm(C), route_hazard(R, H), fragile_to(C, H).
cover_works(R, C, V) :- hazard_match(R, C), cover(V), route_hazard(R, H), protects(V, H).
repair_works(R, Y) :- route(R), repair(Y), route_hazard(R, H), fixes(Y, H).

valid(R, C, V, Y) :- hazard_match(R, C), repair_works(R, Y), cover_works(R, C, V).
valid(R, C, none, Y) :- hazard_match(R, C), repair_works(R, Y), cover(none).

hazard_happens :- chosen_route(R), chosen_charm(C), route_hazard(R, H), fragile_to(C, H),
                  chosen_cover(V), not protects(V, H), not heed_warning.
hazard_happens :- chosen_route(R), chosen_charm(C), route_hazard(R, H), fragile_to(C, H),
                  chosen_cover(none), not heed_warning.

outcome(safe) :- heed_warning.
outcome(mended) :- not heed_warning, hazard_happens.
#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("route_hazard", route_id, route.hazard))
    for charm_id, charm in CHARMS.items():
        lines.append(asp.fact("charm", charm_id))
        lines.append(asp.fact("fragile_to", charm_id, charm.fragile_to))
    for cover_id, cover in COVERS.items():
        lines.append(asp.fact("cover", cover_id))
        for hazard in sorted(cover.protects_from):
            lines.append(asp.fact("protects", cover_id, hazard))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for hazard in sorted(repair.fixes):
            lines.append(asp.fact("fixes", repair_id, hazard))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_route", params.route),
        asp.fact("chosen_charm", params.charm),
        asp.fact("chosen_cover", params.cover),
        asp.fact("chosen_repair", params.repair),
        ("heed_warning." if params.heed_warning else ""),
    ])
    model = asp.one_model(asp_program(extra))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "safe" if params.heed_warning else "mended"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for s in range(12):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print("Unexpected StoryError during resolve_params().")
            break

    mismatches = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, charm, cover, repair) combos:\n")
        for route, charm, cover, repair in combos:
            print(f"  {route:12} {charm:12} {cover:11} {repair}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.charm} on {p.route} ({'safe' if p.heed_warning else 'mended'})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
