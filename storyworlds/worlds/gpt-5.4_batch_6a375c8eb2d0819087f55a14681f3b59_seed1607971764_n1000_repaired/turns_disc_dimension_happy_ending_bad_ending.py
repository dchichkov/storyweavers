#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py
===========================================================================

A standalone story world for a tall-tale-flavored story about a child, an old
sky disc, and a windy dimension that should have been left alone.

This world rebuilds a simple source premise in simulation form:

    On a giant plain, a child climbs up to a strange old disc mounted on a post.
    The child gives it too many turns, and the disc opens a door to a wild
    dimension. Wind bursts out and snatches at the town. A grown-up or elder
    tries to fix the trouble. Sometimes the fix is quick enough for a happy
    ending. Sometimes the wind gets too big and the town loses something before
    everyone gets safe.

The domain is intentionally small and classical:
- typed entities with physical meters and emotional memes
- a short causal rule engine
- a reasonableness gate for valid disc/dimension combinations
- an inline ASP twin checked by --verify
- a tall-tale prose renderer driven by world state

Run it
------
    python storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py
    python storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py --all
    python storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py --qa --json
    python storyworlds/worlds/gpt-5.4/turns_disc_dimension_happy_ending_bad_ending.py --verify
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
    anchored: bool = False
    spinning: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "uncle": "uncle", "aunt": "aunt"}.get(
            self.type, self.type
        )
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
    scene: str
    landmark: str
    closing_image: str
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
class Disc:
    id: str
    label: str
    phrase: str
    mounted_on: str
    boast: str
    spin_sound: str
    wildness: int
    opens: str
    safe_turns: int = 1
    real_disc: bool = True
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
class Dimension:
    id: str
    label: str
    gust: str
    image: str
    threat: str
    loss: str
    ending_good: str
    affinity: set[str] = field(default_factory=set)
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


def _r_portal_wind(world: World) -> list[str]:
    out: list[str] = []
    disc = world.get("disc")
    if disc.meters["portal_open"] < THRESHOLD:
        return out
    sig = ("portal_wind",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    square = world.get("square")
    square.meters["wind"] += disc.meters["turns"] + disc.meters["wildness"]
    square.meters["danger"] += 1
    for eid in ("hero", "helper"):
        if eid in world.entities:
            world.get(eid).memes["fear"] += 1
    out.append("__wind__")
    return out


def _r_loose_loss(world: World) -> list[str]:
    out: list[str] = []
    square = world.get("square")
    if square.meters["wind"] < 4:
        return out
    for ent in list(world.entities.values()):
        if ent.role != "loose":
            continue
        if ent.anchored:
            continue
        sig = ("loss", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["gone"] += 1
        out.append("__loss__")
    return out


CAUSAL_RULES = [
    Rule(name="portal_wind", tag="physical", apply=_r_portal_wind),
    Rule(name="loose_loss", tag="physical", apply=_r_loose_loss),
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
        for sent in produced:
            world.say(sent)
    return produced


def hazard_at_risk(disc: Disc, dimension: Dimension) -> bool:
    return disc.real_disc and dimension.id == disc.opens and disc.id in dimension.affinity


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def portal_severity(disc: Disc, turns: int, delay: int) -> int:
    return disc.wildness + turns + delay


def is_contained(response: Response, disc: Disc, turns: int, delay: int) -> bool:
    return response.power >= portal_severity(disc, turns, delay)


def predict_wind(world: World, turns: int) -> dict:
    sim = world.copy()
    _turn_disc(sim, turns=turns, narrate=False)
    square = sim.get("square")
    loss = any(e.meters["gone"] >= THRESHOLD for e in sim.entities.values() if e.role == "loose")
    return {
        "wind": square.meters["wind"],
        "danger": square.meters["danger"],
        "loss": loss,
    }


def _turn_disc(world: World, turns: int, narrate: bool = True) -> None:
    disc = world.get("disc")
    disc.spinning = True
    disc.meters["turns"] += float(turns)
    if turns > disc.attrs.get("safe_turns", 1):
        disc.meters["portal_open"] += 1
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, helper: Entity, place: Place, disc: Disc) -> None:
    hero.memes["joy"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"In {place.scene}, folks said even the fence posts stood taller than church steeples. "
        f"Right in the middle of it all stood {disc.phrase}, mounted on {disc.mounted_on}."
    )
    world.say(
        f"{hero.id} and {helper.id} had come to see it, and the old thing winked in the sun as if it knew a secret."
    )


def boast(world: World, hero: Entity, disc: Disc, turns: int) -> None:
    hero.memes["pride"] += 1
    world.say(
        f'"I bet I can give that {disc.label} {turns} turns before a grasshopper can blink," '
        f"{hero.id} said. {disc.boast}"
    )


def warning(world: World, helper: Entity, hero: Entity, dimension: Dimension, turns: int) -> None:
    pred = predict_wind(world, turns=turns)
    helper.memes["caution"] += 1
    world.facts["predicted_wind"] = pred["wind"]
    world.facts["predicted_loss"] = pred["loss"]
    world.say(
        f'{helper.id} squinted up at the disc. "Easy now," {helper.pronoun()} said. '
        f'"Too many turns can point that old disc at {dimension.label}. '
        f'Then {dimension.gust}, and a town can lose its hat before it finds its head."'
    )


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But tall-tale courage puffed up in {hero.id} like a parade balloon, and {hero.pronoun()} reached for the handle anyway."
    )


def portal_opens(world: World, hero: Entity, disc: Disc, dimension: Dimension, turns: int) -> None:
    _turn_disc(world, turns=turns, narrate=False)
    square = world.get("square")
    wind = int(square.meters["wind"])
    world.say(
        f"{disc.spin_sound} Around and around went the disc until the last turn clicked like a giant lock. "
        f"At once the air split open above the square, and {dimension.image} poured from {dimension.label}."
    )
    world.say(
        f"The wind came so hard it made the hitching rail groan and the weathercock bow. "
        f"In one breath, the whole town knew the day had gone crooked."
    )
    if wind >= 4:
        world.say(f"{dimension.threat}")


def cry_for_help(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(f'"{helper.id}!" {hero.id} shouted. "I turned it too far!"')


def rescue(world: World, helper: Entity, response: Response, place: Place, dimension: Dimension) -> None:
    disc = world.get("disc")
    square = world.get("square")
    disc.meters["portal_open"] = 0.0
    square.meters["wind"] = 0.0
    square.meters["danger"] = 0.0
    body = response.text.replace("{place}", place.landmark).replace("{dimension}", dimension.label)
    world.say(
        f"{helper.id} moved quicker than a lizard in skillet heat and {body}."
    )
    world.say(
        f"The rip in the air puckered shut, and the wild wind folded back into {dimension.label} as neat as a blanket on a bed."
    )


def lesson(world: World, helper: Entity, hero: Entity, disc: Disc) -> None:
    helper.memes["care"] += 1
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f'{helper.id} set a steady hand on {hero.id}\'s shoulder. "A thing can look lonely and still be powerful," '
        f'{helper.pronoun()} said. "Old magic asks for gentle hands, not bragging hands."'
    )
    world.say(
        f"{hero.id} nodded so hard {hero.pronoun('possessive')} hat brim bobbed. From then on, {hero.pronoun()} counted careful before touching the disc."
    )


def happy_ending(world: World, hero: Entity, helper: Entity, place: Place, dimension: Dimension) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"By sundown, the square was laughing again. {dimension.ending_good}"
    )
    world.say(
        f"{hero.id} watched the quiet sky over {place.closing_image} and thought that a day turned right felt bigger than any brag."
    )


def rescue_fail(world: World, helper: Entity, response: Response, dimension: Dimension) -> None:
    square = world.get("square")
    disc = world.get("disc")
    disc.meters["portal_open"] += 1
    square.meters["wind"] += 2
    square.meters["danger"] += 1
    propagate(world, narrate=False)
    body = response.fail.replace("{dimension}", dimension.label)
    world.say(f"{helper.id} {body}.")
    world.say("But the gusts only got meaner and louder, as if the sky itself had found a howl.")


def loss_and_escape(world: World, hero: Entity, helper: Entity, dimension: Dimension, place: Place) -> None:
    hero.memes["fear"] += 1
    helper.memes["fear"] += 1
    lost_items = [e for e in world.entities.values() if e.role == "loose" and e.meters["gone"] >= THRESHOLD]
    if lost_items:
        item = lost_items[0].label
        world.say(
            f"{dimension.loss} The {item} went spinning over {place.landmark} and never came back."
        )
    world.say(
        f"{helper.id} snatched {hero.id} close and ducked behind the stone well until the worst of it passed. "
        f"Nobody was hurt, but the town looked as if a giant had shuffled it with one hand."
    )


def grim_lesson(world: World, hero: Entity, helper: Entity, disc: Disc, place: Place) -> None:
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    helper.memes["care"] += 1
    world.say(
        f'When the sky finally quieted, {helper.id} looked over the battered square and sighed. '
        f'"That disc will keep its secrets until grown hands mend the mount," {helper.pronoun()} said.'
    )
    world.say(
        f"{hero.id} never forgot that afternoon in {place.scene}. After that, whenever {hero.pronoun()} passed the disc, "
        f"{hero.pronoun()} tipped {hero.pronoun('possessive')} hat to it and kept both hands in {hero.pronoun('possessive')} pockets."
    )


def tell(
    place: Place,
    disc_cfg: Disc,
    dimension: Dimension,
    response: Response,
    *,
    hero_name: str = "Willa",
    hero_gender: str = "girl",
    helper_name: str = "Uncle Reed",
    helper_type: str = "uncle",
    turns: int = 2,
    delay: int = 0,
    loose_item: str = "laundry sheet",
) -> World:
    world = World()
    hero = world.add(Entity(id="hero", kind="character", type=hero_gender, label=hero_name, role="hero"))
    hero.id = hero_name
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    helper.id = helper_name
    square = world.add(Entity(id="square", type="place", label="the town square"))
    disc = world.add(
        Entity(
            id="disc",
            type="disc",
            label=disc_cfg.label,
            role="disc",
            attrs={"safe_turns": disc_cfg.safe_turns},
        )
    )
    disc.meters["wildness"] = float(disc_cfg.wildness)
    loose = world.add(Entity(id="loose", type="thing", label=loose_item, role="loose", anchored=False))
    world.facts["loose_item"] = loose_item
    world.facts["predicted_wind"] = 0
    world.facts["predicted_loss"] = False

    opening(world, hero, helper, place, disc_cfg)
    world.para()
    boast(world, hero, disc_cfg, turns)
    warning(world, helper, hero, dimension, turns)
    defy(world, hero)

    world.para()
    portal_opens(world, hero, disc_cfg, dimension, turns)
    cry_for_help(world, hero, helper)

    contained = is_contained(response, disc_cfg, turns, delay)
    severity = portal_severity(disc_cfg, turns, delay)
    disc.meters["severity"] = float(severity)

    world.para()
    if contained:
        rescue(world, helper, response, place, dimension)
        lesson(world, helper, hero, disc_cfg)
        world.para()
        happy_ending(world, hero, helper, place, dimension)
        outcome = "happy"
    else:
        rescue_fail(world, helper, response, dimension)
        loss_and_escape(world, hero, helper, dimension, place)
        grim_lesson(world, hero, helper, disc_cfg, place)
        outcome = "bad"

    world.facts.update(
        place=place,
        disc_cfg=disc_cfg,
        dimension=dimension,
        response=response,
        hero=hero,
        helper=helper,
        turns=turns,
        delay=delay,
        severity=severity,
        outcome=outcome,
        contained=contained,
        opened=disc.meters["portal_open"] >= THRESHOLD or outcome == "bad" or turns > disc_cfg.safe_turns,
    )
    return world


PLACES = {
    "prairie": Place(
        id="prairie",
        scene="a prairie so broad folks claimed the sunset had to gallop to cross it",
        landmark="the hitching rail",
        closing_image="the long gold grass",
        tags={"wind", "plain"},
    ),
    "mesa": Place(
        id="mesa",
        scene="a red mesa town where shadows stretched longer than wagon roads",
        landmark="the stone well",
        closing_image="the red cliffs",
        tags={"wind", "mesa"},
    ),
    "riverbend": Place(
        id="riverbend",
        scene="a riverbend settlement where even the cottonwoods leaned to hear a story",
        landmark="the ferry post",
        closing_image="the silver river",
        tags={"wind", "river"},
    ),
}

DISCS = {
    "thunder_disc": Disc(
        id="thunder_disc",
        label="thunder disc",
        phrase="a brass disc as wide as a wagon wheel",
        mounted_on="an iron post sunk deep in the square",
        boast="The handle on its side looked eager for trouble.",
        spin_sound="Whum-whum-whum!",
        wildness=2,
        opens="storm_dimension",
        safe_turns=1,
        real_disc=True,
        tags={"disc", "storm"},
    ),
    "tumble_disc": Disc(
        id="tumble_disc",
        label="tumble disc",
        phrase="a silver disc polished smooth by a hundred windy years",
        mounted_on="a cedar mast taller than the schoolhouse",
        boast="Its rim flashed like a fish scale every time the light hit it.",
        spin_sound="Zing-zing-zing!",
        wildness=1,
        opens="whistle_dimension",
        safe_turns=1,
        real_disc=True,
        tags={"disc", "wind"},
    ),
    "sun_marker": Disc(
        id="sun_marker",
        label="sun marker",
        phrase="a painted little disc no bigger than a supper plate",
        mounted_on="a porch post by the store",
        boast="It looked fancy, but it was only a weather sign.",
        spin_sound="Tik-tik-tik!",
        wildness=0,
        opens="none",
        safe_turns=99,
        real_disc=False,
        tags={"disc"},
    ),
}

DIMENSIONS = {
    "storm_dimension": Dimension(
        id="storm_dimension",
        label="the Stormy Seventh Dimension",
        gust="rain-cold gusts with thunder hiding inside them come charging out",
        image="a stack of purple clouds and silver wind",
        threat="Chickens skittered sideways, and every hat in town grabbed for the sky.",
        loss="A clapboard roof sheet tore loose like a playing card in a cyclone.",
        ending_good="The pump handle stopped rattling, the hats stayed put, and the clouds over the prairie minded their own business again.",
        affinity={"thunder_disc"},
        tags={"dimension", "storm"},
    ),
    "whistle_dimension": Dimension(
        id="whistle_dimension",
        label="the Whistling Ninth Dimension",
        gust="thin singing gusts sharp enough to peel laundry from a line come whirling out",
        image="blue air striped with shining wind",
        threat="Wash tubs scooted, doors banged, and the town flag stood straight as a broomstick.",
        loss="Three fence boards hopped away in a row as if they had grown legs.",
        ending_good="The line of sheets settled, the flag drooped like a tired bird, and the town could hear crickets again.",
        affinity={"tumble_disc"},
        tags={"dimension", "wind"},
    ),
    "none": Dimension(
        id="none",
        label="no dimension at all",
        gust="nothing but ordinary weather comes out",
        image="plain old sky and nothing more",
        threat="Nothing strange happened.",
        loss="Nothing was lost.",
        ending_good="Nothing changed.",
        affinity=set(),
        tags=set(),
    ),
}

RESPONSES = {
    "reverse_latch": Response(
        id="reverse_latch",
        sense=3,
        power=5,
        text="caught the spinning handle with a leather glove, gave the disc one careful turn back, and dropped the iron latch across it",
        fail="caught the handle and tried to turn the disc back from {dimension}, but the gusts jerked it free again",
        qa_text="turned the disc back and latched it shut",
        tags={"latch", "disc"},
    ),
    "anchor_chain": Response(
        id="anchor_chain",
        sense=3,
        power=4,
        text="flung a mule chain over the handle, braced both boots, and hauled the disc backward until the rip in the air shrank closed",
        fail="threw a chain over the handle, but even with both boots dug in the wind from {dimension} pulled harder",
        qa_text="hauled the disc backward with a chain until the portal shut",
        tags={"chain", "disc"},
    ),
    "blanket_throw": Response(
        id="blanket_throw",
        sense=2,
        power=2,
        text="threw a heavy horse blanket over the disc and pinned it still long enough to push it back to center",
        fail="threw a blanket over the disc, but the wind from {dimension} whipped it away like a napkin",
        qa_text="covered the disc with a heavy blanket and pushed it back to center",
        tags={"blanket", "disc"},
    ),
    "shout_at_it": Response(
        id="shout_at_it",
        sense=1,
        power=1,
        text="shouted at the disc until the whole square rang",
        fail="shouted at the disc, but shouting never yet taught wind any manners",
        qa_text="shouted at the disc",
        tags={"bad_idea"},
    ),
}

GIRL_NAMES = ["Willa", "Maisie", "Ruby", "Clara", "Nell", "Dora", "Mabel", "June"]
BOY_NAMES = ["Jeb", "Cal", "Toby", "Wade", "Hank", "Eli", "Beau", "Silas"]
HELPERS = [
    ("Uncle Reed", "uncle"),
    ("Aunt May", "aunt"),
    ("Dad", "father"),
    ("Mom", "mother"),
]
LOOSE_ITEMS = ["laundry sheet", "hay hat", "tin sign", "feed sack"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for disc_id, disc in DISCS.items():
            for dim_id, dimension in DIMENSIONS.items():
                if hazard_at_risk(disc, dimension):
                    combos.append((place_id, disc_id, dim_id))
    return combos


@dataclass
class StoryParams:
    place: str
    disc: str
    dimension: str
    response: str
    turns: int
    delay: int
    hero_name: str
    hero_gender: str
    helper_name: str
    helper_type: str
    loose_item: str
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


KNOWLEDGE = {
    "disc": [
        (
            "What is a disc?",
            "A disc is a round flat object, like a big coin or a wheel face. In this story it is a special round thing that can turn.",
        )
    ],
    "dimension": [
        (
            "What is a dimension in a story?",
            "In a story, a dimension can mean another strange place with its own rules. It is like a faraway world you cannot usually step into.",
        )
    ],
    "storm": [
        (
            "Why is strong wind dangerous?",
            "Strong wind can shove people, pull loose things away, and break parts of buildings. That is why grown-ups hurry to get everyone safe when a wild wind starts.",
        )
    ],
    "wind": [
        (
            "What does wind do to loose things?",
            "Wind pushes on anything not tied down. Light things like hats, sheets, and signs can blow away first.",
        )
    ],
    "latch": [
        (
            "What does a latch do?",
            "A latch holds something in place so it cannot swing or turn easily. It is a simple way to keep a moving thing shut.",
        )
    ],
    "chain": [
        (
            "Why would a chain help hold something still?",
            "A chain is strong and hard to tear. If you hook it around something, it can help a person pull or hold against a strong force.",
        )
    ],
    "blanket": [
        (
            "Can a heavy blanket stop everything blowing away?",
            "A heavy blanket can cover something for a moment, but it is not stronger than a very big wind. It helps best with small trouble, not giant trouble.",
        )
    ],
}
KNOWLEDGE_ORDER = ["disc", "dimension", "storm", "wind", "latch", "chain", "blanket"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    disc = f["disc_cfg"]
    dimension = f["dimension"]
    hero = f["hero"]
    helper = f["helper"]
    outcome = f["outcome"]
    base = (
        f'Write a tall tale for a 3-to-5-year-old that uses the words "turns", "disc", '
        f'and "dimension", set in {place.scene}, where a child turns a magical disc too far.'
    )
    if outcome == "happy":
        return [
            base,
            f"Tell a tall, windy story where {hero.id} gives the {disc.label} too many turns, opens {dimension.label}, and {helper.id} saves the day with a calm fix.",
            f"Write a playful frontier story with a happy ending where a wild dimension opens over a town square, but a grown-up shuts it before the town loses anything important.",
        ]
    return [
        base,
        f"Tell a tall-tale warning story where {hero.id} turns the {disc.label} too far, the wind from {dimension.label} gets stronger than the fix, and the town loses something before everyone gets safe.",
        f"Write a big windy story with a bad ending that stays child-safe: the magic trouble is not stopped in time, something blows away, and the child learns to leave old magic alone.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    disc = f["disc_cfg"]
    dimension = f["dimension"]
    response = f["response"]
    place = f["place"]
    turns = f["turns"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who wanted to show off with an old {disc.label}, and {helper.id}, who understood the danger better. They were in {place.scene}.",
        ),
        (
            f"Why did {helper.id} warn {hero.id} before the disc spun?",
            f"{helper.id} warned {hero.id} because too many turns could point the disc at {dimension.label}. In this story, that would let wild wind burst into town.",
        ),
        (
            f"What happened when {hero.id} gave the disc {turns} turns?",
            f"The old disc opened a rip toward {dimension.label}, and fierce wind came pouring out. The trouble started because {turns} turns were more than the disc could safely take.",
        ),
    ]
    if f["outcome"] == "happy":
        body = response.qa_text
        qa.append(
            (
                f"How did {helper.id} stop the trouble?",
                f"{helper.id} {body}. That worked because the fix was strong enough to beat the wind before it grew worse.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended happily. The portal shut, the town settled down, and {hero.id} learned to treat old magic gently instead of showing off.",
            )
        )
    else:
        qa.append(
            (
                f"Why could {helper.id} not stop the bad wind in time?",
                f"{helper.id} tried, but the fix was too weak for such a strong opening to {dimension.label}. Because the wind stayed loose, something in town was blown away before the sky calmed.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended sadly but safely. Nobody was hurt, yet the town lost something to the wind, and {hero.id} learned that bragging with strange power can bring real trouble.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["disc_cfg"].tags) | set(f["dimension"].tags)
    if f["outcome"] == "happy":
        tags |= set(f["response"].tags)
    else:
        tags |= set(f["response"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if e.anchored:
            bits.append("anchored=True")
        if e.spinning:
            bits.append("spinning=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="prairie",
        disc="thunder_disc",
        dimension="storm_dimension",
        response="reverse_latch",
        turns=2,
        delay=0,
        hero_name="Willa",
        hero_gender="girl",
        helper_name="Uncle Reed",
        helper_type="uncle",
        loose_item="hay hat",
    ),
    StoryParams(
        place="mesa",
        disc="tumble_disc",
        dimension="whistle_dimension",
        response="anchor_chain",
        turns=3,
        delay=0,
        hero_name="Cal",
        hero_gender="boy",
        helper_name="Aunt May",
        helper_type="aunt",
        loose_item="laundry sheet",
    ),
    StoryParams(
        place="riverbend",
        disc="thunder_disc",
        dimension="storm_dimension",
        response="blanket_throw",
        turns=3,
        delay=1,
        hero_name="Ruby",
        hero_gender="girl",
        helper_name="Dad",
        helper_type="father",
        loose_item="tin sign",
    ),
    StoryParams(
        place="prairie",
        disc="tumble_disc",
        dimension="whistle_dimension",
        response="blanket_throw",
        turns=2,
        delay=0,
        hero_name="Jeb",
        hero_gender="boy",
        helper_name="Mom",
        helper_type="mother",
        loose_item="feed sack",
    ),
]


def explain_rejection(disc: Disc, dimension: Dimension) -> str:
    if not disc.real_disc:
        return (
            f"(No story: the {disc.label} is only a marker and does not open any portal, "
            f"so there is no real danger, turn, or ending to tell.)"
        )
    if dimension.id != disc.opens:
        return (
            f"(No story: the {disc.label} does not point at {dimension.label}. "
            f"Pick the matching dimension for that disc.)"
        )
    if disc.id not in dimension.affinity:
        return (
            f"(No story: {dimension.label} is not the kind of place this disc can open.)"
        )
    return "(No story: this disc and dimension do not make a reasonable tale together.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    disc = DISCS[params.disc]
    response = RESPONSES[params.response]
    return "happy" if is_contained(response, disc, params.turns, params.delay) else "bad"


ASP_RULES = r"""
hazard(D, M) :- real_disc(D), opens(D, M), affinity(M, D).
valid(P, D, M) :- place(P), disc(D), dimension(M), hazard(D, M).

sensible(R) :- response(R), sense(R, S), sense_min(Min), S >= Min.

severity(W + T + Dly) :- chosen_disc(D), wildness(D, W), turns(T), delay(Dly).
contained :- chosen_response(R), power(R, P), severity(S), P >= S.

outcome(happy) :- contained.
outcome(bad) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for did, disc in DISCS.items():
        lines.append(asp.fact("disc", did))
        if disc.real_disc:
            lines.append(asp.fact("real_disc", did))
        lines.append(asp.fact("opens", did, disc.opens))
        lines.append(asp.fact("wildness", did, disc.wildness))
    for mid, dimension in DIMENSIONS.items():
        lines.append(asp.fact("dimension", mid))
        for a in sorted(dimension.affinity):
            lines.append(asp.fact("affinity", mid, a))
    for rid, resp in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, resp.sense))
        lines.append(asp.fact("power", rid, resp.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_disc", params.disc),
            asp.fact("chosen_response", params.response),
            asp.fact("turns", params.turns),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens, p_sens = set(asp_sensible()), {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    parser = build_parser()
    cases = list(CURATED)
    for s in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: too many turns on a strange disc open a wild dimension."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--disc", choices=DISCS)
    ap.add_argument("--dimension", choices=DIMENSIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--turns", type=int, choices=[2, 3], help="how many turns the hero gives the disc")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long before the helper gets control")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=[h[1] for h in HELPERS])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.disc and args.dimension:
        disc = DISCS[args.disc]
        dimension = DIMENSIONS[args.dimension]
        if not hazard_at_risk(disc, dimension):
            raise StoryError(explain_rejection(disc, dimension))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        c
        for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.disc is None or c[1] == args.disc)
        and (args.dimension is None or c[2] == args.dimension)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, disc, dimension = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    turns = args.turns if args.turns is not None else rng.choice([2, 3])
    delay = args.delay if args.delay is not None else rng.choice([0, 1, 2])
    gender = args.gender or rng.choice(["girl", "boy"])
    hero_name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_pool = [h for h in HELPERS if args.helper is None or h[1] == args.helper]
    helper_name, helper_type = rng.choice(helper_pool)
    loose_item = rng.choice(LOOSE_ITEMS)
    return StoryParams(
        place=place,
        disc=disc,
        dimension=dimension,
        response=response,
        turns=turns,
        delay=delay,
        hero_name=hero_name,
        hero_gender=gender,
        helper_name=helper_name,
        helper_type=helper_type,
        loose_item=loose_item,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.disc not in DISCS:
        raise StoryError(f"(Unknown disc: {params.disc})")
    if params.dimension not in DIMENSIONS:
        raise StoryError(f"(Unknown dimension: {params.dimension})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    disc = DISCS[params.disc]
    dimension = DIMENSIONS[params.dimension]
    response = RESPONSES[params.response]

    if not hazard_at_risk(disc, dimension):
        raise StoryError(explain_rejection(disc, dimension))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        PLACES[params.place],
        disc,
        dimension,
        response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        turns=params.turns,
        delay=params.delay,
        loose_item=params.loose_item,
    )
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, disc, dimension) combos:\n")
        for place, disc, dimension in combos:
            print(f"  {place:10} {disc:14} {dimension}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
                f"### {p.hero_name}: {p.disc} -> {p.dimension} "
                f"({p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
