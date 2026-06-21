#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py
==============================================================================

A standalone story world for a tiny pirate-style tale about a pretend ship, a
jar of marmalade, a sudden hailstorm, a broken promise, and reconciliation.

The world models a child-sized adventure with one clear tension:

- two children play pirates with a snack as their "treasure"
- one child grabs the marmalade after promising to share
- the other child feels hurt and storms off toward a risky place near the water
  during hail
- the first child must choose a real repair: apology alone is not enough unless
  they also bring cover and share the treasure
- if they make the right repair, the pair reconcile and finish their pirate game
  safely under shelter

The reasonableness gate enforces that:
- hail only creates this story when there is a reachable shelter
- reconciliation requires both an apology and a concrete repair
- some repairs are known but refused as too weak or thoughtless

Run it
------
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py --deck blanket_fort --repair umbrella_share
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py --repair shout_sorry
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/damn_marmalade_hail_reconciliation_pirate_tale.py --verify
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
class Theme:
    id: str
    scene: str
    rig: str
    titles: tuple[str, str]
    quest: str
    sendoff: str
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
class Deck:
    id: str
    label: str
    phrase: str
    slick: bool
    shelter: str
    sheltered: bool
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
class Treasure:
    id: str
    label: str
    phrase: str
    smear: str
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
class Weather:
    id: str
    label: str
    cry: str
    danger: int
    pelts: str
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
class Repair:
    id: str
    sense: int
    brings_cover: bool
    shares_treasure: bool
    kind: str
    text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_hail_fear(world: World) -> list[str]:
    out: list[str] = []
    weather = world.get("weather")
    if weather.meters["falling"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("hail_fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__hail__")
    return out


def _r_exposed_sting(world: World) -> list[str]:
    out: list[str] = []
    weather = world.get("weather")
    if weather.meters["falling"] < THRESHOLD:
        return out
    for kid in world.kids():
        if kid.meters["exposed"] < THRESHOLD:
            continue
        sig = ("sting", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.meters["stung"] += 1
        kid.memes["misery"] += 1
        out.append(f"{kid.id} ducked as little white stones of hail tapped at {kid.pronoun('possessive')} hood and sleeves.")
    return out


def _r_hurt_anger(world: World) -> list[str]:
    out: list[str] = []
    mate = world.get("mate")
    if mate.memes["hurt"] < THRESHOLD:
        return out
    sig = ("hurt_anger", mate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    mate.memes["anger"] += 1
    return out


def _r_reconcile(world: World) -> list[str]:
    captain = world.get("captain")
    mate = world.get("mate")
    if captain.memes["apology"] < THRESHOLD:
        return []
    if captain.memes["repair"] < THRESHOLD:
        return []
    if mate.memes["trust"] < THRESHOLD:
        return []
    sig = ("reconcile", captain.id, mate.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    captain.memes["reconciled"] += 1
    mate.memes["reconciled"] += 1
    captain.memes["guilt"] = 0.0
    mate.memes["hurt"] = 0.0
    mate.memes["anger"] = 0.0
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    return ["__reconciled__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hail_fear", tag="emotional", apply=_r_hail_fear),
    Rule(name="exposed_sting", tag="physical", apply=_r_exposed_sting),
    Rule(name="hurt_anger", tag="emotional", apply=_r_hurt_anger),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
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


def can_weather_story(deck: Deck, weather: Weather) -> bool:
    return weather.danger <= 1 or deck.sheltered


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def can_reconcile(repair: Repair, deck: Deck, weather: Weather) -> bool:
    if repair.sense < SENSE_MIN:
        return False
    if not repair.shares_treasure:
        return False
    if weather.danger >= 2 and not repair.brings_cover:
        return False
    if weather.danger >= 2 and not deck.sheltered:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for theme_id in THEMES:
        for deck_id, deck in DECKS.items():
            for treasure_id in TREASURES:
                for weather_id, weather in WEATHER.items():
                    if can_weather_story(deck, weather):
                        combos.append((theme_id, deck_id, treasure_id, weather_id))
    return combos


def predict_runoff(world: World, repair: Repair) -> dict:
    sim = world.copy()
    mate = sim.get("mate")
    weather = sim.get("weather")
    deck = sim.facts["deck_cfg"]
    mate.meters["exposed"] += 1
    if repair.brings_cover and deck.sheltered:
        mate.meters["exposed"] = 0.0
    if weather.danger >= 2:
        weather.meters["falling"] += 1
    propagate(sim, narrate=False)
    return {
        "stung": mate.meters["stung"] >= THRESHOLD,
        "fear": mate.memes["fear"],
    }


def play_setup(world: World, captain: Entity, mate: Entity, theme: Theme, deck: Deck, treasure: Treasure) -> None:
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    c_title, m_title = theme.titles
    world.say(
        f"One bright afternoon, {captain.id} and {mate.id} turned the room into {theme.scene}. "
        f"{theme.rig} On the middle cushion they set {treasure.phrase}, shining like pirate gold."
    )
    world.say(
        f'"{c_title} {captain.id} and {m_title} {mate.id}!" {captain.id} cried. '
        f'"Today we hunt {theme.quest} from {deck.phrase}."'
    )


def promise_share(world: World, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    captain.memes["promise"] += 1
    mate.memes["trust"] += 1
    world.say(
        f'{mate.id} pointed at {treasure.phrase}. "We share the treasure, right?" '
        f'"Right," said {captain.id}.'
    )


def grab_treasure(world: World, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    captain.memes["greed"] += 1
    captain.memes["guilt"] += 1
    mate.memes["hurt"] += 1
    world.say(
        f"But when the lid came off, the sweet smell of {treasure.label} rushed out. "
        f"{captain.id} dipped the spoon first, then scooped up too much and pulled the jar close."
    )
    world.say(
        f'A sticky stripe of {treasure.smear} shone at the corner of {captain.pronoun("possessive")} mouth. '
        f'"Just one more bite," {captain.pronoun()} muttered.'
    )
    world.say(
        f'{mate.id} stared. "You promised." Hurt rose fast in {mate.pronoun("possessive")} face.'
    )
    propagate(world, narrate=False)


def angry_word(world: World, mate: Entity) -> None:
    world.say(
        f'"Oh, damn this pirate trick," {mate.id} burst out, stamping one foot. '
        f'{mate.pronoun().capitalize()} did not mean a rude big-person curse. '
        f'It came out like one small angry spark from a hurt heart.'
    )


def storm_off(world: World, mate: Entity, deck: Deck) -> None:
    mate.meters["exposed"] += 1
    mate.memes["distance"] += 1
    world.say(
        f'{mate.id} snatched up the paper map and marched toward {deck.phrase}. '
        f'{mate.pronoun().capitalize()} wanted to be alone for a minute.'
    )


def hail_begins(world: World, weather: Weather) -> None:
    weather_ent = world.get("weather")
    weather_ent.meters["falling"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then came {weather.cry}. {weather.pelts} drummed on the window and the make-believe deck."
    )


def captain_realizes(world: World, captain: Entity, mate: Entity, deck: Deck, treasure: Treasure, repair: Repair) -> None:
    pred = predict_runoff(world, repair)
    world.facts["predicted_sting"] = pred["stung"]
    captain.memes["care"] += 1
    if pred["stung"]:
        extra = f" {mate.id} could get pelted if {captain.pronoun()} only shouted from far away."
    else:
        extra = ""
    world.say(
        f"{captain.id} looked at the spoon, at the jar, and then at {mate.id} near {deck.label}.{extra}"
    )


def attempt_repair(world: World, captain: Entity, mate: Entity, repair: Repair, deck: Deck, treasure: Treasure) -> None:
    captain.memes["apology"] += 1
    if repair.shares_treasure:
        captain.memes["repair"] += 1
        mate.memes["trust"] += 1
    if repair.brings_cover and deck.sheltered:
        mate.meters["exposed"] = 0.0
    world.say(repair.text.format(captain=captain.id, mate=mate.id, shelter=deck.shelter, treasure=treasure.label))
    propagate(world, narrate=False)


def reconcile_scene(world: World, captain: Entity, mate: Entity, theme: Theme, treasure: Treasure, deck: Deck) -> None:
    world.say(
        f"{mate.id}'s shoulders softened. {mate.pronoun().capitalize()} saw that {captain.id} was not only saying sorry but making things right."
    )
    world.say(
        f"Soon they sat together in {deck.shelter}, sharing the marmalade carefully on crackers while the hail clicked outside like tiny pebbles on a ship."
    )
    world.say(
        f"When the noise faded, the two pirates set out again, gentler than before, and {theme.sendoff}."
    )


def lonely_end(world: World, captain: Entity, mate: Entity, theme: Theme, deck: Deck) -> None:
    if mate.meters["stung"] >= THRESHOLD:
        world.say(
            f"{captain.id} brought {mate.id} back inside at last, but the game had gone flat. A sorry shouted too late did not warm the hurt place right away."
        )
    else:
        world.say(
            f"They both came in from {deck.phrase}, but the room felt quiet now. The ship was still there, yet the game could not sail until trust was mended."
        )
    world.say(
        f"That evening the pirate hats hung on their hooks, waiting for a kinder adventure another day."
    )


def tell(
    theme: Theme,
    deck: Deck,
    treasure: Treasure,
    weather: Weather,
    repair: Repair,
    captain_name: str = "Tom",
    captain_type: str = "boy",
    mate_name: str = "Lily",
    mate_type: str = "girl",
    parent_type: str = "mother",
    trait: str = "thoughtful",
    relation: str = "siblings",
    pet: str = "",
) -> World:
    world = World()
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_type,
        label=captain_name,
        role="captain",
        traits=["bold"],
        attrs={"name": captain_name, "relation": relation},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_type,
        label=mate_name,
        role="mate",
        traits=[trait],
        attrs={"name": mate_name, "relation": relation},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
        attrs={"pet": pet},
    ))
    weather_ent = world.add(Entity(id="weather", type="weather", label=weather.label))
    world.facts["deck_cfg"] = deck
    world.facts["treasure_cfg"] = treasure
    world.facts["weather_cfg"] = weather
    world.facts["theme_cfg"] = theme
    world.facts["repair_cfg"] = repair
    world.facts["parent_ent"] = parent
    world.facts["captain_ent"] = captain
    world.facts["mate_ent"] = mate

    play_setup(world, captain, mate, theme, deck, treasure)
    promise_share(world, captain, mate, treasure)

    world.para()
    grab_treasure(world, captain, mate, treasure)
    angry_word(world, mate)
    storm_off(world, mate, deck)

    world.para()
    hail_begins(world, weather)
    captain_realizes(world, captain, mate, deck, treasure, repair)
    attempt_repair(world, captain, mate, repair, deck, treasure)

    world.para()
    reconciled = captain.memes["reconciled"] >= THRESHOLD and mate.memes["reconciled"] >= THRESHOLD
    if reconciled:
        reconcile_scene(world, captain, mate, theme, treasure, deck)
    else:
        lonely_end(world, captain, mate, theme, deck)

    outcome = "reconciled" if reconciled else "unmended"
    world.facts.update(
        theme=theme,
        deck=deck,
        treasure=treasure,
        weather=weather,
        repair=repair,
        captain=captain,
        mate=mate,
        parent=parent,
        outcome=outcome,
        pet=pet,
        hail_fell=weather_ent.meters["falling"] >= THRESHOLD,
        mate_stung=mate.meters["stung"] >= THRESHOLD,
    )
    return world


THEMES = {
    "pirates": Theme(
        id="pirates",
        scene="a bright little sea of sofa-cushion waves",
        rig="A striped blanket was the sail, a cardboard tube was the spyglass, and a blue laundry basket by the wall was a tiny harbor.",
        titles=("Captain", "First Mate"),
        quest="the breakfast island treasure",
        sendoff="they sailed their cushion ship toward one last happy map mark",
    ),
    "corsairs": Theme(
        id="corsairs",
        scene="a windy hidden cove",
        rig="Two chairs became the mast, a broom was the oar, and a floor rug curled like a dark secret island.",
        titles=("Captain", "Scout"),
        quest="the orange-gold hoard",
        sendoff="they steered their brave little ship toward supper with smiling faces",
    ),
}

DECKS = {
    "window_seat": Deck(
        id="window_seat",
        label="the window seat",
        phrase="the window seat they called the upper deck",
        slick=False,
        shelter="the blanket cave under the table",
        sheltered=True,
        tags={"shelter", "window"},
    ),
    "blanket_fort": Deck(
        id="blanket_fort",
        label="the blanket fort roof",
        phrase="the blanket fort roof they called the crow's nest",
        slick=False,
        shelter="the fort's snug tunnel",
        sheltered=True,
        tags={"shelter", "fort"},
    ),
    "porch_rail": Deck(
        id="porch_rail",
        label="the porch rail",
        phrase="the porch rail they called the side deck",
        slick=True,
        shelter="the back-door mat just inside",
        sheltered=True,
        tags={"porch", "shelter"},
    ),
    "open_step": Deck(
        id="open_step",
        label="the back step",
        phrase="the back step they called the outer deck",
        slick=True,
        shelter="the kitchen doorway",
        sheltered=False,
        tags={"step"},
    ),
}

TREASURES = {
    "marmalade": Treasure(
        id="marmalade",
        label="marmalade",
        phrase="a small jar of marmalade",
        smear="orange marmalade",
        tags={"marmalade", "share_food"},
    ),
    "jam": Treasure(
        id="jam",
        label="berry jam",
        phrase="a little pot of berry jam",
        smear="purple jam",
        tags={"jam", "share_food"},
    ),
    "honey": Treasure(
        id="honey",
        label="honey",
        phrase="a little cup of honey",
        smear="golden honey",
        tags={"honey", "share_food"},
    ),
}

WEATHER = {
    "hail": Weather(
        id="hail",
        label="hail",
        cry="hail from a gray cloud",
        danger=2,
        pelts="Cold little bits of ice",
        tags={"hail", "storm"},
    ),
    "gust": Weather(
        id="gust",
        label="a sharp wind",
        cry="a sharp wind from the yard",
        danger=1,
        pelts="Dry leaves and cold air",
        tags={"wind"},
    ),
}

REPAIRS = {
    "umbrella_share": Repair(
        id="umbrella_share",
        sense=3,
        brings_cover=True,
        shares_treasure=True,
        kind="cover_and_share",
        text='"I was wrong," {captain} said, hurrying over with an umbrella in one hand and the jar in the other. "Come to {shelter}. We will share the {treasure}, and you can have the first sweet bite."',
        qa_text="brought cover, apologized, and shared the treasure fairly",
        tags={"umbrella", "share", "apology"},
    ),
    "coat_share": Repair(
        id="coat_share",
        sense=2,
        brings_cover=True,
        shares_treasure=True,
        kind="coat_and_share",
        text='{captain} ran to {mate}, wrapped {mate} in a warm coat, and said, "I am sorry. Let us go to {shelter} and split the {treasure} right down the middle."',
        qa_text="brought a warm coat, apologized, and split the treasure fairly",
        tags={"coat", "share", "apology"},
    ),
    "share_only": Repair(
        id="share_only",
        sense=1,
        brings_cover=False,
        shares_treasure=True,
        kind="share_only",
        text='{captain} held up the jar and called, "Sorry! You can have half!"',
        qa_text="offered to share, but did not bring cover",
        tags={"share", "apology"},
    ),
    "shout_sorry": Repair(
        id="shout_sorry",
        sense=1,
        brings_cover=False,
        shares_treasure=False,
        kind="words_only",
        text='{captain} stayed where {captain} was and shouted, "Sorry, {mate}!" through the noise.',
        qa_text="shouted sorry from far away",
        tags={"apology"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["thoughtful", "careful", "gentle", "steady", "cautious", "kind"]
PETS = ["the cat", "the puppy", "the little dog", "the kitten", ""]


@dataclass
class StoryParams:
    theme: str
    deck: str
    treasure: str
    weather: str
    repair: str
    captain_name: str
    captain_type: str
    mate_name: str
    mate_type: str
    parent: str
    trait: str
    relation: str = "siblings"
    pet: str = ""
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
    "hail": [(
        "What is hail?",
        "Hail is frozen rain that falls from the sky in little lumps of ice. It can sting when it hits, so people hurry to shelter."
    )],
    "marmalade": [(
        "What is marmalade?",
        "Marmalade is a sweet fruit spread, often made with oranges. People put it on bread or crackers."
    )],
    "share": [(
        "Why does sharing help after a quarrel?",
        "Sharing shows that you are thinking about the other person's feelings, not only your own. A fair action can help trust grow again."
    )],
    "apology": [(
        "What makes an apology feel real?",
        "A real apology uses honest words and also tries to repair the problem. It helps when a person changes what they do, not only what they say."
    )],
    "umbrella": [(
        "What does an umbrella do?",
        "An umbrella gives cover from rain or hail overhead. It helps keep drops and little bits of ice off your head and shoulders."
    )],
    "coat": [(
        "Why can a warm coat help in bad weather?",
        "A warm coat covers your body and keeps cold air and wet weather from bothering you so much. It can make it easier to get back to shelter calmly."
    )],
}
KNOWLEDGE_ORDER = ["hail", "marmalade", "share", "apology", "umbrella", "coat"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    treasure = f["treasure"]
    weather = f["weather"]
    deck = f["deck"]
    outcome = f["outcome"]
    base = (
        f'Write a pirate-style story for a 3-to-5-year-old that includes the words "damn", '
        f'"{treasure.id if treasure.id == "marmalade" else "marmalade"}", and "{weather.id if weather.id == "hail" else "hail"}".'
    )
    if outcome == "reconciled":
        return [
            base,
            f"Tell a gentle pirate game story where {captain.label} breaks a promise over sweet treasure, {mate.label} runs to {deck.label}, and real reconciliation comes when the apology includes a caring repair.",
            f"Write a child-facing story about two pretend pirates who quarrel over breakfast treasure during hail and then make up by sharing fairly under shelter.",
        ]
    return [
        base,
        f"Tell a pirate game story where {captain.label} says sorry after hurting {mate.label}, but the repair is too weak to mend trust during the storm.",
        f"Write a cautionary but gentle story showing that reconciliation needs more than words when someone has been hurt.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    treasure = f["treasure"]
    weather = f["weather"]
    deck = f["deck"]
    repair = f["repair"]
    relation = captain.attrs.get("relation", "friends")
    pair = pair_noun(captain, mate, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {captain.label} and {mate.label}, who were pretending to be pirates together. Their game turned serious when one promise about the treasure was broken."
        ),
        (
            "What was the treasure in their pirate game?",
            f"The treasure was {treasure.phrase}. It felt special because the children treated the sweet food like pirate gold in the middle of their game."
        ),
        (
            f"Why did {mate.label} get upset?",
            f"{mate.label} got upset because {captain.label} promised to share and then pulled the treasure close instead. The hurt came from the broken promise, not only from the missing bite."
        ),
    ]
    if f["hail_fell"]:
        qa.append((
            "What changed when the hail began?",
            f"The pretend quarrel suddenly had real weather in it. Hail started falling, so being alone out by {deck.label} was no longer just dramatic play but a small danger."
        ))
    if f["outcome"] == "reconciled":
        qa.append((
            f"How did {captain.label} make things right?",
            f"{captain.label} {repair.qa_text}. That worked because the apology matched the problem: {mate.label} needed fairness and care at the same time."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with reconciliation. The children shared the marmalade under shelter and went back to their pirate game more gently than before."
        ))
    else:
        if f["mate_stung"]:
            second = f"{mate.label} had already been pelted by the hail, which made the hurt feel bigger."
        else:
            second = f"The problem stayed because the repair did not truly answer what {mate.label} needed."
        qa.append((
            f"Why did the apology not fix everything right away?",
            f"The apology was too weak because it did not bring enough care, fairness, or shelter. {second}"
        ))
        qa.append((
            "How did the story end?",
            "It ended quietly, with the pirate game put away for now. The children were back inside, but trust still needed more time and kinder action."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = set()
    weather = world.facts["weather"]
    treasure = world.facts["treasure"]
    repair = world.facts["repair"]
    if "hail" in weather.tags:
        tags.add("hail")
    if treasure.id == "marmalade":
        tags.add("marmalade")
    tags |= {"share", "apology"}
    if "umbrella" in repair.tags:
        tags.add("umbrella")
    if "coat" in repair.tags:
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
        name = e.label or e.id
        lines.append(f"  {name:12} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="pirates",
        deck="blanket_fort",
        treasure="marmalade",
        weather="hail",
        repair="umbrella_share",
        captain_name="Tom",
        captain_type="boy",
        mate_name="Lily",
        mate_type="girl",
        parent="mother",
        trait="careful",
        relation="siblings",
        pet="the puppy",
    ),
    StoryParams(
        theme="corsairs",
        deck="window_seat",
        treasure="jam",
        weather="gust",
        repair="coat_share",
        captain_name="Mia",
        captain_type="girl",
        mate_name="Ben",
        mate_type="boy",
        parent="father",
        trait="gentle",
        relation="friends",
        pet="",
    ),
    StoryParams(
        theme="pirates",
        deck="porch_rail",
        treasure="marmalade",
        weather="hail",
        repair="share_only",
        captain_name="Sam",
        captain_type="boy",
        mate_name="Nora",
        mate_type="girl",
        parent="mother",
        trait="steady",
        relation="siblings",
        pet="the cat",
    ),
]


def explain_rejection(deck: Deck, weather: Weather) -> str:
    if weather.danger >= 2 and not deck.sheltered:
        return (
            f"(No story: {weather.label} is too sharp for {deck.phrase} because there is no good nearby shelter. "
            f"Pick a deck with cover, like a blanket fort or window seat.)"
        )
    return "(No story: this deck and weather do not make a reasonable scene.)"


def explain_repair(rid: str) -> str:
    repair = REPAIRS[rid]
    better = ", ".join(sorted(r.id for r in sensible_repairs()))
    return (
        f"(Refusing repair '{rid}': it is too weak for a reconciliation story here "
        f"(sense={repair.sense} < {SENSE_MIN}). Try: {better}.)"
    )


ASP_RULES = r"""
deck_weather_ok(D, W) :- deck(D), weather(W), weather_danger(W, X), X <= 1.
deck_weather_ok(D, W) :- deck(D), weather(W), weather_danger(W, X), X >= 2, sheltered(D).

valid(T, D, Tr, W) :- theme(T), deck_weather_ok(D, W), treasure(Tr).

sensible(R) :- repair(R), sense(R, S), sense_min(M), S >= M.

chosen_reconciled :- chosen_repair(R), sensible(R), shares_treasure(R),
                     chosen_weather(W), weather_danger(W, X), X <= 1.
chosen_reconciled :- chosen_repair(R), sensible(R), shares_treasure(R),
                     chosen_weather(W), weather_danger(W, X), X >= 2,
                     brings_cover(R), chosen_deck(D), sheltered(D).

outcome(reconciled) :- chosen_reconciled.
outcome(unmended) :- not chosen_reconciled.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for did, deck in DECKS.items():
        lines.append(asp.fact("deck", did))
        if deck.sheltered:
            lines.append(asp.fact("sheltered", did))
    for tr in TREASURES:
        lines.append(asp.fact("treasure", tr))
    for wid, weather in WEATHER.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("weather_danger", wid, weather.danger))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        if repair.brings_cover:
            lines.append(asp.fact("brings_cover", rid))
        if repair.shares_treasure:
            lines.append(asp.fact("shares_treasure", rid))
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
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_deck", params.deck),
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_repair", params.repair),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def outcome_of(params: StoryParams) -> str:
    if can_reconcile(REPAIRS[params.repair], DECKS[params.deck], WEATHER[params.weather]):
        return "reconciled"
    return "unmended"


def asp_verify() -> int:
    rc = 0
    cset, pset = set(asp_valid_combos()), set(valid_combos())
    if cset == pset:
        print(f"OK: gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    cs, ps = set(asp_sensible()), {r.id for r in sensible_repairs()}
    if cs == ps:
        print(f"OK: sensible repairs match ({sorted(cs)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: clingo={sorted(cs)} python={sorted(ps)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(30):
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
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke-test generation/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Pirate tale storyworld: broken sharing, hail, and reconciliation."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--deck", choices=DECKS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--weather", choices=WEATHER)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.deck and args.weather:
        if not can_weather_story(DECKS[args.deck], WEATHER[args.weather]):
            raise StoryError(explain_rejection(DECKS[args.deck], WEATHER[args.weather]))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(explain_repair(args.repair))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.deck is None or c[1] == args.deck)
        and (args.treasure is None or c[2] == args.treasure)
        and (args.weather is None or c[3] == args.weather)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, deck, treasure, weather = rng.choice(sorted(combos))
    repair = args.repair or rng.choice(sorted(r.id for r in sensible_repairs()))
    captain_name, captain_type = _pick_kid(rng)
    mate_name, mate_type = _pick_kid(rng, avoid=captain_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    relation = rng.choice(["siblings", "friends"])
    pet = rng.choice(PETS)
    return StoryParams(
        theme=theme,
        deck=deck,
        treasure=treasure,
        weather=weather,
        repair=repair,
        captain_name=captain_name,
        captain_type=captain_type,
        mate_name=mate_name,
        mate_type=mate_type,
        parent=parent,
        trait=trait,
        relation=relation,
        pet=pet,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        deck = DECKS[params.deck]
        treasure = TREASURES[params.treasure]
        weather = WEATHER[params.weather]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from None

    if not can_weather_story(deck, weather):
        raise StoryError(explain_rejection(deck, weather))

    world = tell(
        theme=theme,
        deck=deck,
        treasure=treasure,
        weather=weather,
        repair=repair,
        captain_name=params.captain_name,
        captain_type=params.captain_type,
        mate_name=params.mate_name,
        mate_type=params.mate_type,
        parent_type=params.parent,
        trait=params.trait,
        relation=params.relation,
        pet=params.pet,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (theme, deck, treasure, weather) combos:\n")
        for theme, deck, treasure, weather in combos:
            print(f"  {theme:8} {deck:13} {treasure:10} {weather}")
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
                f"### {p.captain_name} & {p.mate_name}: {p.treasure} on {p.deck} "
                f"({p.weather}, {p.repair}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
