#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py
==================================================================

A standalone story world for a heartwarming moral tale about a child who finds
something lost, feels a troublesome pull to keep it, and then chooses honesty
and kindness instead.

The domain is deliberately small and classical:
- a child finds a lost item in a place
- the item belongs to another child or family
- there is a reasonable clue for finding the owner
- the finder imagines keeping it, sees that this would leave someone sad,
  and decides to return it
- the ending image shows trust and warmth growing from an honest choice

Run it
------
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py --place library --item scarf --clue name_tag
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py --place beach --item lunchbox
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py --all
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/troublesome_moral_value_heartwarming.py --verify
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    # physical + emotional axes
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "librarian_woman", "seller_woman"}
        male = {"boy", "father", "man", "groundskeeper_man", "lifeguard_man", "vendor_man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {"mother": "mom", "father": "dad"}
        return mapping.get(self.type, self.label or self.type)
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
    opening: str
    afford_clues: set[str] = field(default_factory=set)
    helper_label: str = ""
    helper_type: str = ""
    helper_action: str = ""
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
class LostItem:
    id: str
    label: str
    phrase: str
    shine: str
    owner_need: str
    clue_modes: set[str] = field(default_factory=set)
    temptation: int = 1
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
class Clue:
    id: str
    label: str
    direct: bool
    find_text: str
    use_text: str
    reunion_text: str
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
class Trait:
    id: str
    opening: str
    empathy: int
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
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_missing_item(world: World) -> list[str]:
    owner = world.get("owner")
    item = world.get("item")
    if item.owner != owner.id:
        sig = ("missing", item.id)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["worry"] += 1
    return []


def _r_empathy(world: World) -> list[str]:
    finder = world.get("finder")
    owner = world.get("owner")
    if owner.memes["worry"] < THRESHOLD:
        return []
    sig = ("empathy", finder.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    finder.memes["empathy"] += world.facts.get("trait_empathy", 1)
    finder.memes["guilt"] += 1
    return []


def _r_returned(world: World) -> list[str]:
    item = world.get("item")
    finder = world.get("finder")
    owner = world.get("owner")
    if item.owner != owner.id:
        return []
    sig = ("returned", item.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    owner.memes["relief"] += 1
    owner.memes["joy"] += 1
    finder.memes["relief"] += 1
    finder.memes["pride"] += 1
    finder.memes["temptation"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_item", tag="social", apply=_r_missing_item),
    Rule(name="empathy", tag="social", apply=_r_empathy),
    Rule(name="returned", tag="social", apply=_r_returned),
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
                produced.extend(out)
            elif any(sig[0] == rule.name for sig in world.fired):
                changed = True
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_clue(place: Place, item: LostItem, clue: Clue) -> bool:
    return clue.id in place.afford_clues and clue.id in item.clue_modes


def direct_return(clue: Clue) -> bool:
    return clue.direct


def explain_rejection(place: Place, item: LostItem, clue: Clue) -> str:
    return (
        f"(No story: {clue.label} is not a reasonable way to return {item.phrase} at "
        f"{place.label}. Pick a clue that the place supports and that the item can carry.)"
    )


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for clue_id, clue in CLUES.items():
                if valid_clue(place, item, clue):
                    out.append((place_id, item_id, clue_id))
    return sorted(out)


def predict_keep(world: World) -> dict:
    sim = world.copy()
    finder = sim.get("finder")
    owner = sim.get("owner")
    item = sim.get("item")
    item.owner = None
    finder.memes["temptation"] = world.get("finder").memes["temptation"]
    propagate(sim, narrate=False)
    sad = owner.memes["worry"] >= THRESHOLD and item.owner != owner.id
    guilt = sad and finder.memes["empathy"] + finder.memes["guilt"] >= THRESHOLD
    return {"owner_still_sad": sad, "finder_feels_bad": guilt}


def introduce(world: World, finder: Entity, place: Place) -> None:
    world.say(
        f"One soft afternoon, {finder.id} walked through {place.label}. "
        f"{place.opening}"
    )
    world.say(
        f"{finder.pronoun().capitalize()} was a {next((t for t in finder.traits if t), 'gentle')} "
        f"little {finder.type} who liked noticing small things other people missed."
    )


def discover(world: World, finder: Entity, item_cfg: LostItem, item: Entity) -> None:
    item.meters["found"] += 1
    finder.memes["wonder"] += 1
    finder.memes["temptation"] += float(item_cfg.temptation)
    world.say(
        f"Near a bench, {finder.pronoun()} spotted {item_cfg.phrase}. "
        f"It {item_cfg.shine}, and no one nearby seemed to be holding it."
    )
    world.say(
        f"{finder.id} picked it up carefully. A troublesome little thought whispered "
        f"that such a lovely thing might be fun to keep."
    )


def admire(world: World, finder: Entity, item_cfg: LostItem) -> None:
    if item_cfg.temptation >= 3:
        wish = "for many, many days"
    elif item_cfg.temptation == 2:
        wish = "for a while"
    else:
        wish = "for a moment"
    world.say(
        f"{finder.pronoun().capitalize()} imagined taking it home and enjoying it {wish}. "
        f"For one quiet breath, keeping it felt easier than asking whose it was."
    )


def notice_loss(world: World, owner: Entity, item_cfg: LostItem) -> None:
    world.say(
        f"Then {finder_name(world)} heard a small voice nearby. {owner.id} was looking around "
        f"with worried eyes because {owner.pronoun('possessive')} {item_cfg.label} was missing."
    )
    world.say(
        f"{owner.pronoun().capitalize()} needed it {item_cfg.owner_need}, and the sight of that worried face "
        f"made the moment feel different."
    )


def conscience(world: World, finder: Entity, clue: Clue) -> None:
    pred = predict_keep(world)
    world.facts["pred_owner_sad"] = pred["owner_still_sad"]
    world.facts["pred_finder_bad"] = pred["finder_feels_bad"]
    if pred["owner_still_sad"]:
        world.say(
            f"{finder.id} hugged the found thing against {finder.pronoun('possessive')} chest and felt a tight pinch inside. "
            f"Keeping it would leave someone else sad, and that troublesome feeling would stay."
        )
    else:
        world.say(
            f"{finder.id} paused and thought carefully about what to do next."
        )
    if clue.direct:
        world.say(
            f"Then {clue.find_text}, which gave {finder.pronoun('object')} a gentle, honest path to follow."
        )
    else:
        world.say(
            f"{clue.find_text.capitalize()}, so {finder.pronoun()} knew help could lead the way."
        )


def ask_helper(world: World, helper: Entity, clue: Clue, place: Place) -> None:
    world.say(
        f"{helper.label.capitalize()} saw the careful look on the child's face and came over. "
        f'"We can help," {helper.pronoun()} said. "{place.helper_action}."'
    )
    world.say(clue.use_text)


def decide_return(world: World, finder: Entity) -> None:
    finder.memes["honesty"] += 1
    finder.memes["kindness"] += 1
    world.say(
        f'"This belongs to somebody," {finder.id} said at last. '
        f'"I want to give it back."'
    )


def reunite(world: World, finder: Entity, owner: Entity, item: Entity, clue: Clue) -> None:
    item.owner = owner.id
    item.meters["returned"] += 1
    propagate(world, narrate=False)
    world.say(clue.reunion_text.format(owner=owner.id, finder=finder.id, item=item.label))
    world.say(
        f"{owner.id}'s face changed at once from worry to relief. "
        f"{finder.id} felt the tight little knot inside loosen."
    )


def moral_close(world: World, finder: Entity, owner: Entity, helper: Entity, item_cfg: LostItem, place: Place) -> None:
    owner.memes["trust"] += 1
    finder.memes["warmth"] += 1
    world.say(
        f'{owner.id} held the {item_cfg.label} close and said, "Thank you for being honest." '
        f"{helper.label.capitalize()} smiled too, as if the whole place had grown kinder."
    )
    world.say(
        f"{owner.id} shared a small happy thing with {finder.id} -- a grin, a grateful squeeze of the hand, "
        f"and room beside {owner.pronoun('object')} to stay for a while."
    )
    world.say(
        f"By the time the sun leaned low over {place.label}, the found thing was back where it belonged, "
        f"and two children felt bigger-hearted than before."
    )


def finder_name(world: World) -> str:
    return world.get("finder").id


def tell(
    place: Place,
    item_cfg: LostItem,
    clue: Clue,
    finder_name_value: str = "Mila",
    finder_gender: str = "girl",
    owner_name_value: str = "Noah",
    owner_gender: str = "boy",
    parent_type: str = "mother",
    trait: Trait = Trait(id="gentle", opening="gentle", empathy=2),
) -> World:
    world = World(place)
    finder = world.add(Entity(
        id=finder_name_value,
        kind="character",
        type=finder_gender,
        label=finder_name_value,
        role="finder",
        traits=[trait.opening],
    ))
    owner = world.add(Entity(
        id=owner_name_value,
        kind="character",
        type=owner_gender,
        label=owner_name_value,
        role="owner",
        traits=["worried"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=place.helper_type,
        label=place.helper_label,
        role="helper",
        traits=["calm"],
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label=parent_type,
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type=item_cfg.id,
        label=item_cfg.label,
        owner=None,
        tags=set(item_cfg.tags),
    ))

    world.facts["trait_empathy"] = trait.empathy
    world.facts["direct"] = clue.direct
    world.facts["clue"] = clue
    world.facts["item_cfg"] = item_cfg
    world.facts["place_cfg"] = place
    world.facts["trait"] = trait
    world.facts["parent"] = parent

    introduce(world, finder, place)
    discover(world, finder, item_cfg, item)
    admire(world, finder, item_cfg)

    world.para()
    propagate(world, narrate=False)
    notice_loss(world, owner, item_cfg)
    conscience(world, finder, clue)
    decide_return(world, finder)

    world.para()
    if clue.direct:
        world.say(clue.use_text)
    else:
        ask_helper(world, helper, clue, place)
    reunite(world, finder, owner, item, clue)

    world.para()
    moral_close(world, finder, owner, helper, item_cfg, place)

    world.facts.update(
        finder=finder,
        owner=owner,
        helper=helper,
        item=item,
        returned=item.owner == owner.id,
        outcome="direct" if clue.direct else "helped",
        honest=finder.memes["honesty"] >= THRESHOLD,
    )
    return world


PLACES = {
    "park": Place(
        id="park",
        label="the park",
        opening="Leaves made bright patches on the path, and children were laughing near the swings.",
        afford_clues={"name_tag", "announcement", "whistle"},
        helper_label="the groundskeeper",
        helper_type="groundskeeper_man",
        helper_action="I can ask around from the path",
        tags={"park"},
    ),
    "library": Place(
        id="library",
        label="the library",
        opening="The room was full of warm lamp light and the hush of turning pages.",
        afford_clues={"name_tag", "announcement"},
        helper_label="the librarian",
        helper_type="librarian_woman",
        helper_action="I can make a kind little announcement",
        tags={"library"},
    ),
    "beach": Place(
        id="beach",
        label="the beach",
        opening="Small waves folded onto the sand, and towels fluttered in the breeze.",
        afford_clues={"announcement", "whistle"},
        helper_label="the lifeguard",
        helper_type="lifeguard_man",
        helper_action="I can call out from the tall chair",
        tags={"beach"},
    ),
    "market": Place(
        id="market",
        label="the market square",
        opening="Baskets of fruit glowed red and gold, and friendly voices floated between the stalls.",
        afford_clues={"name_tag", "announcement"},
        helper_label="the fruit seller",
        helper_type="seller_woman",
        helper_action="I can ask the families by the stalls",
        tags={"market"},
    ),
}

ITEMS = {
    "scarf": LostItem(
        id="scarf",
        label="scarf",
        phrase="a soft striped scarf",
        shine="looked cozy and bright in the afternoon light",
        owner_need="to stay warm on the walk home",
        clue_modes={"name_tag", "announcement"},
        temptation=1,
        tags={"clothing", "lost_property"},
    ),
    "lunchbox": LostItem(
        id="lunchbox",
        label="lunchbox",
        phrase="a shiny little lunchbox with painted cherries on the lid",
        shine="clicked softly when it moved and smelled faintly of apples",
        owner_need="for supper and for the note tucked inside",
        clue_modes={"name_tag", "announcement"},
        temptation=2,
        tags={"food", "lost_property"},
    ),
    "puppy": LostItem(
        id="puppy",
        label="puppy",
        phrase="a fluffy puppy with one floppy ear",
        shine="wagged its tail and pressed close as if it hoped for help",
        owner_need="to feel safe and not be alone",
        clue_modes={"whistle", "announcement"},
        temptation=3,
        tags={"animal", "lost_pet"},
    ),
    "toy_bag": LostItem(
        id="toy_bag",
        label="toy bag",
        phrase="a little cloth bag full of toy blocks",
        shine="made a cheerful clack when it bumped against a shoe",
        owner_need="for the game they had been building",
        clue_modes={"name_tag", "announcement"},
        temptation=2,
        tags={"toys", "lost_property"},
    ),
}

CLUES = {
    "name_tag": Clue(
        id="name_tag",
        label="a name tag",
        direct=True,
        find_text="a neat little name tag was sewn inside",
        use_text="Inside was a name, written carefully enough for the child to read. That made it possible to ask the right family, one by one, until the answer came.",
        reunion_text="{owner} hurried over and said, \"That's my {item}!\" {finder} placed it into {owner}'s waiting hands.",
        tags={"names", "returning"},
    ),
    "announcement": Clue(
        id="announcement",
        label="a public announcement",
        direct=False,
        find_text="there was no clear name on it",
        use_text="Together they asked in warm, steady voices whose missing thing it might be, and the question traveled farther than one child could reach alone.",
        reunion_text="A voice answered from across the way. \"My {item}!\" cried {owner}, hurrying over while {finder} held it out with both hands.",
        tags={"helpers", "returning"},
    ),
    "whistle": Clue(
        id="whistle",
        label="a familiar call",
        direct=False,
        find_text="the little creature kept lifting its head as if listening for someone it already loved",
        use_text="The helper gave a clear call, and everyone paused to listen. A reply came back at once, full of relief and hope.",
        reunion_text="{owner} came running at the sound, and the {item} scrambled happily toward {owner}. {finder} laughed and stepped back so they could be together again.",
        tags={"pets", "helpers"},
    ),
}

TRAITS = {
    "gentle": Trait(id="gentle", opening="gentle", empathy=2, tags={"kindness"}),
    "thoughtful": Trait(id="thoughtful", opening="thoughtful", empathy=2, tags={"honesty"}),
    "tender": Trait(id="tender", opening="tender-hearted", empathy=3, tags={"kindness"}),
    "curious": Trait(id="curious", opening="curious", empathy=1, tags={"learning"}),
}

GIRL_NAMES = ["Mila", "Lina", "Nora", "Ava", "Lucy", "Ivy", "Ella", "Ruby"]
BOY_NAMES = ["Noah", "Ben", "Theo", "Max", "Finn", "Leo", "Owen", "Sam"]


@dataclass
class StoryParams:
    place: str
    item: str
    clue: str
    finder_name: str
    finder_gender: str
    owner_name: str
    owner_gender: str
    parent: str
    trait: str
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


def pair_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def outcome_of(params: StoryParams) -> str:
    clue = CLUES[params.clue]
    return "direct" if clue.direct else "helped"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    finder = f["finder"]
    item_cfg = f["item_cfg"]
    place = f["place_cfg"]
    clue = f["clue"]
    if clue.direct:
        return [
            f'Write a heartwarming story for a 3-to-5-year-old where a child finds {item_cfg.phrase} in {place.label} and chooses honesty over keeping it.',
            f'Write a gentle moral story that includes the word "troublesome" and shows {finder.id} returning a lost {item_cfg.label} after noticing a clue.',
            f"Tell a story where doing the right thing makes two children feel warmer inside than owning the lost thing ever could.",
        ]
    return [
        f'Write a heartwarming story for a 3-to-5-year-old where a child finds {item_cfg.phrase} in {place.label} and asks for help to return it.',
        f'Write a gentle moral story that includes the word "troublesome" and shows {finder.id} choosing honesty and kindness when a lost {item_cfg.label} is found.',
        f"Tell a story where a child returns something precious to its owner and ends the day with new trust and friendship.",
    ]


KNOWLEDGE = {
    "lost_property": [
        (
            "What should you do if you find something that belongs to someone else?",
            "You should try to return it or give it to a trusted grown-up who can help. Keeping it would leave the owner sad, and giving it back is the honest thing to do.",
        )
    ],
    "lost_pet": [
        (
            "What should you do if you find a lost pet?",
            "Stay calm and get a grown-up to help. A lost pet is usually scared, and the safest goal is to help it get back to its family.",
        )
    ],
    "names": [
        (
            "Why is a name tag helpful?",
            "A name tag tells you who something belongs to. That makes it easier to return the item kindly and quickly.",
        )
    ],
    "helpers": [
        (
            "Why can a helper make a hard problem easier?",
            "A helper can ask more people or speak more loudly and calmly than one child alone. That gives kindness a better chance to reach the right person.",
        )
    ],
    "honesty": [
        (
            "What is honesty?",
            "Honesty means telling the truth and doing what is right, even when another choice looks easier. It helps people trust you.",
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness means caring about how someone else feels and choosing to help. A kind choice can make a worried heart feel safe again.",
        )
    ],
    "pets": [
        (
            "Why do pets come when they hear a familiar voice or whistle?",
            "Pets learn the sounds of the people who care for them. A familiar call helps them know where safety and love are.",
        )
    ],
}
KNOWLEDGE_ORDER = ["lost_property", "lost_pet", "names", "helpers", "honesty", "kindness", "pets"]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    finder = f["finder"]
    owner = f["owner"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    place = f["place_cfg"]
    clue = f["clue"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {finder.id}, who found a lost {item_cfg.label}, and {owner.id}, who was missing it. The story also includes {helper.label}, who helped the honest choice grow easier.",
        ),
        (
            f"What did {finder.id} find?",
            f"{finder.id} found {item_cfg.phrase} in {place.label}. At first it looked so nice that keeping it felt tempting for a moment.",
        ),
        (
            f"Why did keeping the {item_cfg.label} feel wrong?",
            f"Keeping it would have left {owner.id} sad and still searching. When {finder.id} saw that someone needed it {item_cfg.owner_need}, the troublesome thought about keeping it no longer felt good.",
        ),
    ]
    if clue.direct:
        out.append(
            (
                f"How did {finder.id} know how to return the {item_cfg.label}?",
                f"{clue.find_text.capitalize()}, so there was a clear path to the owner. That clue turned honesty from a feeling into an action {finder.id} could take.",
            )
        )
    else:
        out.append(
            (
                f"Why did {finder.id} ask {helper.label} for help?",
                f"There was no simple name to follow, so {finder.id} needed a bigger, calmer voice. {helper.label.capitalize()} helped the search reach farther, and that is what brought the owner back.",
            )
        )
    out.append(
        (
            "How did the story end?",
            f"It ended with the {item_cfg.label} back where it belonged and worried feelings turning into relief. {finder.id} learned that honesty and kindness can make a day feel warmer than keeping a found thing.",
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set(f["item_cfg"].tags) | set(f["clue"].tags) | set(f["trait"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:16}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="library",
        item="scarf",
        clue="name_tag",
        finder_name="Mila",
        finder_gender="girl",
        owner_name="Noah",
        owner_gender="boy",
        parent="mother",
        trait="thoughtful",
        seed=1,
    ),
    StoryParams(
        place="park",
        item="toy_bag",
        clue="announcement",
        finder_name="Finn",
        finder_gender="boy",
        owner_name="Ruby",
        owner_gender="girl",
        parent="father",
        trait="gentle",
        seed=2,
    ),
    StoryParams(
        place="beach",
        item="puppy",
        clue="whistle",
        finder_name="Ella",
        finder_gender="girl",
        owner_name="Leo",
        owner_gender="boy",
        parent="mother",
        trait="tender",
        seed=3,
    ),
    StoryParams(
        place="market",
        item="lunchbox",
        clue="announcement",
        finder_name="Ben",
        finder_gender="boy",
        owner_name="Ivy",
        owner_gender="girl",
        parent="father",
        trait="curious",
        seed=4,
    ),
]


ASP_RULES = r"""
valid(Place, Item, Clue) :- place(Place), item(Item), clue(Clue),
                            affords(Place, Clue), supports(Item, Clue).

direct(Clue) :- clue_direct(Clue).

outcome(direct) :- chosen_clue(C), direct(C).
outcome(helped) :- chosen_clue(C), not direct(C).

#show valid/3.
#show outcome/1.
#show direct/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue_id in sorted(place.afford_clues):
            lines.append(asp.fact("affords", pid, clue_id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for clue_id in sorted(item.clue_modes):
            lines.append(asp.fact("supports", iid, clue_id))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        if clue.direct:
            lines.append(asp.fact("clue_direct", cid))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("chosen_clue", params.clue)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Heartwarming moral storyworld: a child finds a lost thing, feels a troublesome temptation, and chooses honesty."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--finder-gender", choices=["girl", "boy"])
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.clue:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        clue = CLUES[args.clue]
        if not valid_clue(place, item, clue):
            raise StoryError(explain_rejection(place, item, clue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.clue is None or combo[2] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, clue_id = rng.choice(combos)
    finder_gender = args.finder_gender or rng.choice(["girl", "boy"])
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    finder_name = pair_name(rng, finder_gender)
    owner_name = pair_name(rng, owner_gender, avoid=finder_name)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(sorted(TRAITS))
    return StoryParams(
        place=place_id,
        item=item_id,
        clue=clue_id,
        finder_name=finder_name,
        finder_gender=finder_gender,
        owner_name=owner_name,
        owner_gender=owner_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        item = ITEMS[params.item]
        clue = CLUES[params.clue]
        trait = TRAITS[params.trait]
    except KeyError as exc:
        raise StoryError(f"(Invalid story parameter: {exc.args[0]})") from None

    if not valid_clue(place, item, clue):
        raise StoryError(explain_rejection(place, item, clue))

    world = tell(
        place=place,
        item_cfg=item,
        clue=clue,
        finder_name_value=params.finder_name,
        finder_gender=params.finder_gender,
        owner_name_value=params.owner_name,
        owner_gender=params.owner_gender,
        parent_type=params.parent,
        trait=trait,
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


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid_combos() matches ASP ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in asp:", sorted(asp_valid - py_valid))

    cases = list(CURATED)
    for seed in range(25):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("(Smoke test failed: generated story was empty.)")
        print("OK: smoke test generation succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, item, clue) combos:\n")
        for place, item, clue in combos:
            print(f"  {place:8} {item:10} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.finder_name}: {p.item} at {p.place} via {p.clue} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
