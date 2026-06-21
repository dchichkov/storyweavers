#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py
====================================================================

A standalone story world about a small detective mystery before a preschool
graduation celebration: something for the grad parade goes missing, a child
detective follows a concrete clue, and the ending teaches honesty, calm
thinking, or careful responsibility.

The domain is intentionally small and constraint-checked. Not every missing-item
idea makes sense with every cause:

- a breeze can only carry light paper things,
- borrowing only makes sense for useful craft items,
- tucking something away only makes sense for pocket-sized keepsakes.

The story engine models typed entities with physical meters and emotional memes,
uses a tiny forward-chaining rule engine, renders prose from changing state, and
includes an inline ASP twin for its reasonableness gate and outcome model.

Run it
------
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py --place classroom --item tassel --cause blown
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py --item medal
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/grad_moral_value_rhyme_detective_story.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    portable: bool = True
    light: bool = False
    useful: bool = False
    pocketable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "teacher", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"teacher": "teacher", "mother": "mom", "father": "dad"}.get(self.type, self.type)
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
    hiding_spot: str
    breeze_spot: str
    rhyme_end: str
    affords: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    use_line: str
    clue_mark: str
    light: bool = False
    useful: bool = False
    pocketable: bool = False
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
class Cause:
    id: str
    label: str
    clue: str
    rhyme_a: str
    rhyme_b: str
    moral: str
    outcome: str
    needs: set[str] = field(default_factory=set)
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
class Helper:
    id: str
    label: str
    type: str
    prompt: str
    reassurance: str
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


def _r_missing_worry(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    owner = world.get("owner")
    if item.meters["missing"] >= THRESHOLD and ("missing_worry", owner.id) not in world.fired:
        world.fired.add(("missing_worry", owner.id))
        owner.memes["worry"] += 1
        detective = world.get("detective")
        detective.memes["focus"] += 1
        out.append("__missing__")
    return out


def _r_clue_hope(world: World) -> list[str]:
    out: list[str] = []
    det = world.get("detective")
    if det.meters["clue_found"] >= THRESHOLD and ("clue_hope", det.id) not in world.fired:
        world.fired.add(("clue_hope", det.id))
        det.memes["hope"] += 1
        owner = world.get("owner")
        owner.memes["hope"] += 1
        out.append("__clue__")
    return out


def _r_return_relief(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    owner = world.get("owner")
    helper = world.get("helper")
    if item.meters["returned"] >= THRESHOLD and ("return_relief", owner.id) not in world.fired:
        world.fired.add(("return_relief", owner.id))
        item.meters["missing"] = 0.0
        owner.memes["worry"] = 0.0
        owner.memes["relief"] += 1
        helper.memes["pride"] += 1
        detective = world.get("detective")
        detective.memes["satisfaction"] += 1
        out.append("__returned__")
    return out


CAUSAL_RULES = [
    Rule(name="missing_worry", tag="emotional", apply=_r_missing_worry),
    Rule(name="clue_hope", tag="emotional", apply=_r_clue_hope),
    Rule(name="return_relief", tag="social", apply=_r_return_relief),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def cause_fits(item: MissingItem, place: Place, cause: Cause) -> bool:
    if cause.id not in place.affords:
        return False
    if "light" in cause.needs and not item.light:
        return False
    if "useful" in cause.needs and not item.useful:
        return False
    if "pocketable" in cause.needs and not item.pocketable:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id, item in ITEMS.items():
            for cause_id, cause in CAUSES.items():
                if cause_fits(item, place, cause):
                    combos.append((place_id, item_id, cause_id))
    return combos


def predict_outcome(cause: Cause) -> str:
    return cause.outcome


def start_mystery(world: World, detective: Entity, owner: Entity, place: Place, item: MissingItem) -> None:
    detective.memes["curiosity"] += 1
    owner.memes["pride"] += 1
    world.say(
        f"On grad morning, the room at {place.label} buzzed with little shoes, bright paper stars, "
        f"and soft practice songs. {place.scene}"
    )
    world.say(
        f"{owner.id} had been chosen to carry {item.phrase}, and {owner.pronoun()} kept checking it with a proud smile. "
        f"{item.use_line}"
    )
    world.say(
        f"{detective.id}, who loved detective games, straightened an imaginary coat collar and whispered, "
        f'"Detective {detective.id} is on the case."'
    )


def notice_loss(world: World, owner: Entity, item_ent: Entity, helper: Entity) -> None:
    item_ent.meters["missing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But when the class lined up, {owner.id} gave a small gasp. {item_ent.label.capitalize()} was gone."
    )
    world.say(
        f'"My {item_ent.label} was right here," {owner.id} said, with watery eyes. '
        f'{helper.label.capitalize()} bent down and said, "{helper.attrs["reassurance"]}"'
    )


def detective_vow(world: World, detective: Entity, helper: Entity) -> None:
    world.say(
        f'{helper.label.capitalize()} nodded to {detective.id}. "{helper.attrs["prompt"]}"'
    )
    world.say(
        f'{detective.id} pressed {detective.pronoun("possessive")} lips together and looked slowly around the room. '
        f'{detective.pronoun().capitalize()} decided not to blame anyone too fast.'
    )


def find_clue(world: World, detective: Entity, place: Place, item: MissingItem, cause: Cause) -> None:
    detective.meters["clue_found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Near {place.hiding_spot}, {detective.id} noticed {cause.clue}. It matched {item.clue_mark} on the missing {item.label}."
    )
    world.say(
        f'{detective.id} whispered a little clue rhyme: "{cause.rhyme_a} / {cause.rhyme_b}."'
    )
    world.facts["rhyme"] = f"{cause.rhyme_a} / {cause.rhyme_b}"


def solve_borrowed(world: World, detective: Entity, owner: Entity, helper: Entity, item_ent: Entity, item: MissingItem) -> None:
    friend = world.get("friend")
    friend.memes["guilt"] += 1
    world.say(
        f"The clue led to {friend.id}, who was hiding behind the art shelf with a torn paper banner and a glue stick."
    )
    world.say(
        f'"I borrowed the {item.label} to press this curl flat," {friend.id} admitted. '
        f'"I meant to bring it back, but then I got scared."'
    )
    item_ent.meters["returned"] += 1
    propagate(world, narrate=False)
    friend.memes["honesty"] += 1
    owner.memes["trust"] += 1
    world.say(
        f'{helper.label.capitalize()} held out a gentle hand. "{friend.id}, thank you for telling the truth. '
        f'Next time, ask first."'
    )
    world.say(
        f"{friend.id} returned the {item.label} to {owner.id}. {owner.id}'s shoulders loosened at once."
    )
    world.facts["lesson"] = "honesty"
    world.facts["culprit"] = friend.id


def solve_blown(world: World, detective: Entity, owner: Entity, helper: Entity, item_ent: Entity, place: Place, item: MissingItem) -> None:
    world.say(
        f"The clue led to the open window by {place.breeze_spot}. A tiny breeze kept fluttering the curtain there."
    )
    world.say(
        f"Behind a basket, {detective.id} spotted the missing {item.label}, folded where the air had whisked it away."
    )
    item_ent.meters["returned"] += 1
    propagate(world, narrate=False)
    owner.memes["care"] += 1
    world.say(
        f'{helper.label.capitalize()} smiled. "Good detective work. The wind was the trickster this time, not a person."'
    )
    world.say(
        f"{owner.id} hugged the {item.label} and decided to keep it tucked under a careful hand until the parade began."
    )
    world.facts["lesson"] = "carefulness"
    world.facts["culprit"] = "wind"


def solve_tucked(world: World, detective: Entity, owner: Entity, helper: Entity, item_ent: Entity, item: MissingItem) -> None:
    owner.memes["memory"] += 1
    world.say(
        f"The clue led back to {owner.id}, who suddenly patted {owner.pronoun('possessive')} own little pocket."
    )
    world.say(
        f'"Oh!" {owner.id} whispered. "I tucked the {item.label} away so it would not get bent, and then I forgot."'
    )
    item_ent.meters["returned"] += 1
    propagate(world, narrate=False)
    owner.memes["honesty"] += 1
    world.say(
        f'{helper.label.capitalize()} smiled warmly. "That was a careful idea, and telling us the truth helped fast."'
    )
    world.say(
        f"{detective.id} grinned. The case was solved not by blame, but by calm remembering."
    )
    world.facts["lesson"] = "truth_and_calm"
    world.facts["culprit"] = owner.id


def ending(world: World, detective: Entity, owner: Entity, helper: Entity, item: MissingItem, place: Place) -> None:
    detective.memes["joy"] += 1
    owner.memes["joy"] += 1
    world.say(
        f"Soon the music started, the children formed a neat line, and {owner.id} carried {item.phrase} with a steadier smile."
    )
    lesson = world.facts.get("lesson", "kindness")
    if lesson == "honesty":
        moral = "a true word mends trouble faster than a frightened lie"
    elif lesson == "carefulness":
        moral = "looking carefully can be kinder than guessing quickly"
    else:
        moral = "calm truth helps worried hearts settle down"
    world.say(
        f'{detective.id} murmured one last rhyme as the grad parade began: '
        f'"Look with care, be fair, be bright; / tell what\'s true and set things right."'
    )
    world.say(
        f"And under the paper stars at {place.label}, everyone remembered that {moral}."
    )


def tell(
    place: Place,
    item: MissingItem,
    cause: Cause,
    helper_cfg: Helper,
    detective_name: str = "Mina",
    detective_gender: str = "girl",
    owner_name: str = "Owen",
    owner_gender: str = "boy",
    friend_name: str = "Tess",
    friend_gender: str = "girl",
) -> World:
    world = World()
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=["observant", "gentle"],
    ))
    owner = world.add(Entity(
        id=owner_name,
        kind="character",
        type=owner_gender,
        role="owner",
        traits=["proud", "nervous"],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_gender,
        role="friend",
        traits=["helpful"],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_cfg.type,
        role="helper",
        label=helper_cfg.label,
        attrs={"prompt": helper_cfg.prompt, "reassurance": helper_cfg.reassurance},
    ))
    item_ent = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item.label,
        role="missing_item",
        owner=owner.id,
        light=item.light,
        useful=item.useful,
        pocketable=item.pocketable,
    ))

    world.facts.update(
        place=place,
        item_cfg=item,
        cause=cause,
        helper_cfg=helper_cfg,
        detective=detective,
        owner=owner,
        friend=friend,
        helper=helper,
        item=item_ent,
        clue_found=False,
        resolved=False,
        lesson="",
        culprit="",
    )

    start_mystery(world, detective, owner, place, item)
    world.para()
    notice_loss(world, owner, item_ent, helper)
    detective_vow(world, detective, helper)
    world.para()
    find_clue(world, detective, place, item, cause)

    if cause.id == "borrowed":
        solve_borrowed(world, detective, owner, helper, item_ent, item)
    elif cause.id == "blown":
        solve_blown(world, detective, owner, helper, item_ent, place, item)
    elif cause.id == "tucked":
        solve_tucked(world, detective, owner, helper, item_ent, item)
    else:
        raise StoryError(f"(Unknown cause '{cause.id}'.)")

    world.facts["clue_found"] = detective.meters["clue_found"] >= THRESHOLD
    world.facts["resolved"] = item_ent.meters["returned"] >= THRESHOLD
    world.para()
    ending(world, detective, owner, helper, item, place)
    return world


PLACES = {
    "classroom": Place(
        id="classroom",
        label="the sunny classroom",
        scene="A paper banner said GRAD DAY, and the block corner had been turned into a tiny stage.",
        hiding_spot="the art shelf",
        breeze_spot="the reading rug",
        rhyme_end="room",
        affords={"borrowed", "tucked", "blown"},
        tags={"school", "classroom"},
    ),
    "hallway": Place(
        id="hallway",
        label="the long school hallway",
        scene="Gold stars hung from the wall, and every little cap looked ready for a parade.",
        hiding_spot="the cubby bench",
        breeze_spot="the door to the playground",
        rhyme_end="hall",
        affords={"blown", "tucked"},
        tags={"school", "hallway"},
    ),
    "music_room": Place(
        id="music_room",
        label="the music room",
        scene="Chairs waited in tidy rows, and a piano gleamed beside the practice risers.",
        hiding_spot="the instrument shelf",
        breeze_spot="the tall fan",
        rhyme_end="tune",
        affords={"borrowed", "tucked"},
        tags={"school", "music"},
    ),
}

ITEMS = {
    "badge": MissingItem(
        id="badge",
        label="grad badge",
        phrase="the shiny grad badge",
        use_line="It had a bright clip and a little star in the middle.",
        clue_mark="a silver clip line",
        light=False,
        useful=False,
        pocketable=True,
        tags={"badge", "grad"},
    ),
    "tassel": MissingItem(
        id="tassel",
        label="blue tassel",
        phrase="the soft blue tassel for the grad cap",
        use_line="Its silky threads swayed whenever anyone walked by.",
        clue_mark="a loose blue thread",
        light=True,
        useful=False,
        pocketable=True,
        tags={"tassel", "grad", "cap"},
    ),
    "song_card": MissingItem(
        id="song_card",
        label="song card",
        phrase="the little song card for the grad song",
        use_line="The class needed it to remember the last rhyming line.",
        clue_mark="a crease in one corner",
        light=True,
        useful=True,
        pocketable=True,
        tags={"song", "card", "grad"},
    ),
    "medal": MissingItem(
        id="medal",
        label="gold medal",
        phrase="the gold medal for the grad parade",
        use_line="It had a thick ribbon and made a soft clink against a shirt.",
        clue_mark="a ribbon wrinkle",
        light=False,
        useful=False,
        pocketable=False,
        tags={"medal", "grad"},
    ),
}

CAUSES = {
    "borrowed": Cause(
        id="borrowed",
        label="borrowed by a classmate",
        clue="a dab of glue and a bent bit of paper",
        rhyme_a="Glue on blue, a clue in view",
        rhyme_b="Ask, don't take, for goodness' sake",
        moral="Ask before borrowing and tell the truth quickly.",
        outcome="confession",
        needs={"useful"},
        tags={"honesty", "borrowing"},
    ),
    "blown": Cause(
        id="blown",
        label="blown away by a breeze",
        clue="a tiny trail leading toward moving air",
        rhyme_a="Flutter, mutter, near the shutter",
        rhyme_b="Follow air with patient care",
        moral="Look carefully before blaming somebody.",
        outcome="found",
        needs={"light"},
        tags={"care", "wind"},
    ),
    "tucked": Cause(
        id="tucked",
        label="tucked away and forgotten",
        clue="a small bulge in a pocket or cubby",
        rhyme_a="Pocket bump, don't just jump",
        rhyme_b="Think it through; truth helps too",
        moral="Stay calm and tell the truth about mistakes.",
        outcome="remembered",
        needs={"pocketable"},
        tags={"truth", "memory"},
    ),
}

HELPERS = {
    "teacher": Helper(
        id="teacher",
        label="the teacher",
        type="teacher",
        prompt="Use your eyes first, not your guesses.",
        reassurance="We can solve this together, one clue at a time.",
        tags={"teacher"},
    ),
    "mom": Helper(
        id="mom",
        label="mom",
        type="mother",
        prompt="Start with what you know, then follow the clue.",
        reassurance="Take a breath. We will look carefully.",
        tags={"parent"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Ava", "Nora", "Ruby", "Zoe", "Ella"]
BOY_NAMES = ["Owen", "Max", "Leo", "Sam", "Finn", "Noah", "Eli", "Ben"]


@dataclass
class StoryParams:
    place: str
    item: str
    cause: str
    helper: str
    detective: str
    detective_gender: str
    owner: str
    owner_gender: str
    friend: str
    friend_gender: str
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
    "grad": [
        (
            "What does grad mean?",
            "Grad is a short way to say graduation or graduate. It can mean a child is celebrating finishing one school step and moving to the next one."
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a small sign or tag that shows a role or a special day. People clip or pin it on so others can see it."
        )
    ],
    "tassel": [
        (
            "What is a tassel on a cap?",
            "A tassel is a bunch of hanging threads on a cap. It swings when you move and is often used on graduation hats."
        )
    ],
    "song": [
        (
            "Why do children use song cards?",
            "Song cards help children remember the words in order. They are useful when a group is singing together."
        )
    ],
    "borrowing": [
        (
            "What should you do before borrowing something?",
            "You should ask first and wait for the owner to say yes. Asking shows respect and helps everyone trust each other."
        )
    ],
    "honesty": [
        (
            "Why is honesty important when you make a mistake?",
            "Honesty helps people solve the problem faster. It also shows that you are trying to be brave and fair."
        )
    ],
    "wind": [
        (
            "How can wind move light things?",
            "Moving air can push light paper or soft threads across a room. That is why light things can slide or flutter away."
        )
    ],
    "care": [
        (
            "Why is it good to look carefully before blaming someone?",
            "Looking carefully helps you notice the real cause of a problem. That keeps you from hurting someone's feelings with a wrong guess."
        )
    ],
    "truth": [
        (
            "Why does telling the truth help in a mystery?",
            "Telling the truth gives everyone the facts they need. Then the problem can be fixed instead of growing bigger."
        )
    ],
}

KNOWLEDGE_ORDER = ["grad", "badge", "tassel", "song", "borrowing", "honesty", "wind", "care", "truth"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    item = f["item_cfg"]
    cause = f["cause"]
    detective = f["detective"]
    owner = f["owner"]
    lesson = cause.moral
    return [
        f'Write a short detective story for a 3-to-5-year-old about a missing {item.label} on grad day. Include a rhyming clue and a gentle moral.',
        f"Tell a child-friendly mystery where {detective.id} helps {owner.id} find a lost {item.label} at {place.label}, and the solution teaches that {lesson.lower()}",
        f'Write a simple detective-style story with rhyme where a little grad celebration is saved because someone follows clues calmly and kindly.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    owner = f["owner"]
    helper = f["helper"]
    item = f["item_cfg"]
    cause = f["cause"]
    culprit = f.get("culprit", "")
    lesson = f.get("lesson", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a little detective, and {owner.id}, whose {item.label} went missing on grad day. {helper.label.capitalize()} helped them stay calm while they looked."
        ),
        (
            f"What went missing before the grad parade?",
            f"{owner.id}'s {item.label} went missing just when the children were getting ready to line up. That missing item is what turned the morning into a mystery."
        ),
        (
            f"How did {detective.id} start solving the mystery?",
            f"{detective.id} looked for a clue instead of blaming someone right away. That careful choice helped {detective.pronoun('object')} notice what really pointed to the answer."
        ),
        (
            "What was the rhyming clue?",
            f'The clue rhyme was "{f.get("rhyme", "")}". The rhyme helped the detective remember where to look next.'
        ),
    ]
    if cause.id == "borrowed":
        qa.append(
            (
                f"Why did the missing {item.label} matter so much?",
                f"It mattered because {owner.id} needed the {item.label} for the grad celebration. When it disappeared, {owner.id} felt worried and the parade could not start the same way."
            )
        )
        qa.append(
            (
                "How was the mystery solved?",
                f"{culprit} admitted borrowing the {item.label} and returned it. The problem ended when the truth was told, because honesty made fixing the mistake simple."
            )
        )
    elif cause.id == "blown":
        qa.append(
            (
                "Was someone secretly taking the missing item?",
                f"No. The clue showed that moving air had blown the {item.label} away, so nobody had been sneaky at all. Looking carefully kept the children from making an unfair guess."
            )
        )
        qa.append(
            (
                "How was the mystery solved?",
                f"{detective.id} followed the clue toward the moving air and found the {item.label} hidden by the breeze. The careful search solved the case and brought relief to {owner.id}."
            )
        )
    else:
        qa.append(
            (
                f"Why did {owner.id} not know where the {item.label} was?",
                f"{owner.id} had tucked it away to keep it safe and then forgot about it. The mystery ended when calm remembering and truthful talking brought the answer back."
            )
        )
        qa.append(
            (
                "How was the mystery solved?",
                f"The clue led back to {owner.id}, who remembered where the {item.label} had been tucked. Telling the truth right away helped everyone stop worrying."
            )
        )
    if lesson == "honesty":
        ending = "the children learned to ask before borrowing and to tell the truth quickly"
    elif lesson == "carefulness":
        ending = "the children learned to look carefully before blaming anybody"
    else:
        ending = "the children learned that calm truth can solve a mistake"
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that {ending}. The case is solved gently because kindness and truth work better than blame."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"grad"} | set(f["item_cfg"].tags) | set(f["cause"].tags)
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
        bits: list[str] = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        attrs = {k: v for k, v in e.attrs.items() if v}
        if attrs:
            bits.append(f"attrs={attrs}")
        flags = [name for name, on in (("light", e.light), ("useful", e.useful), ("pocketable", e.pocketable)) if on]
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="classroom",
        item="song_card",
        cause="borrowed",
        helper="teacher",
        detective="Mina",
        detective_gender="girl",
        owner="Owen",
        owner_gender="boy",
        friend="Tess",
        friend_gender="girl",
    ),
    StoryParams(
        place="hallway",
        item="tassel",
        cause="blown",
        helper="teacher",
        detective="Leo",
        detective_gender="boy",
        owner="Ruby",
        owner_gender="girl",
        friend="Max",
        friend_gender="boy",
    ),
    StoryParams(
        place="classroom",
        item="badge",
        cause="tucked",
        helper="mom",
        detective="Ava",
        detective_gender="girl",
        owner="Ben",
        owner_gender="boy",
        friend="Lila",
        friend_gender="girl",
    ),
    StoryParams(
        place="music_room",
        item="song_card",
        cause="borrowed",
        helper="teacher",
        detective="Nora",
        detective_gender="girl",
        owner="Sam",
        owner_gender="boy",
        friend="Zoe",
        friend_gender="girl",
    ),
    StoryParams(
        place="hallway",
        item="badge",
        cause="tucked",
        helper="mom",
        detective="Finn",
        detective_gender="boy",
        owner="Ella",
        owner_gender="girl",
        friend="Ava",
        friend_gender="girl",
    ),
]


def explain_rejection(item: MissingItem, place: Place, cause: Cause) -> str:
    if cause.id not in place.affords:
        return f"(No story: {place.label} does not suit the cause '{cause.id}'. Pick a place where that kind of mystery could happen.)"
    if "light" in cause.needs and not item.light:
        return f"(No story: a breeze can only carry a light item, and the {item.label} is too heavy in this world.)"
    if "useful" in cause.needs and not item.useful:
        return f"(No story: borrowing only makes sense for an item someone could use, and the {item.label} is not that kind of tool here.)"
    if "pocketable" in cause.needs and not item.pocketable:
        return f"(No story: tucking something away only works for a pocket-sized item, and the {item.label} is not one.)"
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: StoryParams) -> str:
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    return predict_outcome(CAUSES[params.cause])


ASP_RULES = r"""
% reasonableness gate
fits(Item, Cause) :- item(Item), cause(Cause), needs(Cause, light), light(Item).
fits(Item, Cause) :- item(Item), cause(Cause), needs(Cause, useful), useful(Item).
fits(Item, Cause) :- item(Item), cause(Cause), needs(Cause, pocketable), pocketable(Item).
fits(Item, Cause) :- item(Item), cause(Cause), no_needs(Cause).

valid(Place, Item, Cause) :- place(Place), item(Item), cause(Cause), affords(Place, Cause), cause_ok(Item, Cause).
cause_ok(Item, Cause) :- cause(Cause), no_needs(Cause), item(Item).
cause_ok(Item, Cause) :- cause(Cause), needs(Cause, light), light(Item).
cause_ok(Item, Cause) :- cause(Cause), needs(Cause, useful), useful(Item).
cause_ok(Item, Cause) :- cause(Cause), needs(Cause, pocketable), pocketable(Item).

outcome(confession) :- chosen_cause(borrowed).
outcome(found) :- chosen_cause(blown).
outcome(remembered) :- chosen_cause(tucked).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for cause_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, cause_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        if item.light:
            lines.append(asp.fact("light", item_id))
        if item.useful:
            lines.append(asp.fact("useful", item_id))
        if item.pocketable:
            lines.append(asp.fact("pocketable", item_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        if not cause.needs:
            lines.append(asp.fact("no_needs", cause_id))
        for need in sorted(cause.needs):
            lines.append(asp.fact("needs", cause_id, need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_cause", params.cause)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    test_cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            test_cases.append(params)
        except StoryError:
            rc = 1
            print(f"Random resolve failed unexpectedly at seed {seed}.")
            break

    bad = 0
    for params in test_cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(test_cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(test_cases)} outcome cases differ.")

    try:
        sample = generate(CURATED[0])
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a gentle grad-day detective mystery with rhyme and a moral."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    candidates = [n for n in pool if n not in avoid]
    return rng.choice(candidates)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.cause:
        place = PLACES[args.place]
        item = ITEMS[args.item]
        cause = CAUSES[args.cause]
        if not cause_fits(item, place, cause):
            raise StoryError(explain_rejection(item, place, cause))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, cause_id = rng.choice(sorted(combos))
    helper_id = args.helper or rng.choice(sorted(HELPERS.keys()))
    detective_gender = rng.choice(["girl", "boy"])
    owner_gender = rng.choice(["girl", "boy"])
    friend_gender = rng.choice(["girl", "boy"])
    used: set[str] = set()
    detective = _pick_name(rng, detective_gender, used)
    used.add(detective)
    owner = _pick_name(rng, owner_gender, used)
    used.add(owner)
    friend = _pick_name(rng, friend_gender, used)
    return StoryParams(
        place=place_id,
        item=item_id,
        cause=cause_id,
        helper=helper_id,
        detective=detective,
        detective_gender=detective_gender,
        owner=owner,
        owner_gender=owner_gender,
        friend=friend,
        friend_gender=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause '{params.cause}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")

    place = PLACES[params.place]
    item = ITEMS[params.item]
    cause = CAUSES[params.cause]
    helper = HELPERS[params.helper]

    if not cause_fits(item, place, cause):
        raise StoryError(explain_rejection(item, place, cause))

    world = tell(
        place=place,
        item=item,
        cause=cause,
        helper_cfg=helper,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        owner_name=params.owner,
        owner_gender=params.owner_gender,
        friend_name=params.friend,
        friend_gender=params.friend_gender,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, cause) combos:\n")
        for place, item, cause in combos:
            print(f"  {place:11} {item:10} {cause}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.detective}: {p.item} at {p.place} ({p.cause})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
