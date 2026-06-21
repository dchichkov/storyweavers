#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py
=====================================================================================

A standalone story world for a tiny child-facing detective story domain built
around a missing object, a dazzling decoy that can mesmerize a young sleuth, a
wrong turn in the investigation, and a warm reconciliation after the truth is
found.

The source tale imagined from the seed:
---------------------------------------
Two children play detective when something important goes missing. One of them
gets distracted by a beautiful, glittering object and starts building a fancy
mystery too quickly. The other keeps following ordinary clues. When the real
cause is discovered, the first detective learns not to let a shiny idea replace
careful checking, apologizes, and the friends make up.

Run it
------
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py --setting library --item bookmark
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py --cause cat
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/mesmerize_lesson_learned_reconciliation_detective_story.py --verify
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
IMPULSE_INIT = 5.0
CAREFUL_TRAITS = {"careful", "patient", "steady", "methodical"}


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
        female = {"girl", "mother", "woman", "librarian", "baker", "teacher"}
        male = {"boy", "father", "man"}
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
class Setting:
    id: str
    place: str
    keeper_type: str
    keeper_label: str
    occasion: str
    affords: set[str] = field(default_factory=set)
    hideouts: set[str] = field(default_factory=set)
    items: set[str] = field(default_factory=set)
    decoys: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    need: str
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
class Decoy:
    id: str
    label: str
    phrase: str
    shine: str
    pull: int
    setting_tags: set[str] = field(default_factory=set)
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
    needs: set[str] = field(default_factory=set)
    hideout_tags: set[str] = field(default_factory=set)
    clue: str = ""
    move_text: str = ""
    found_text: str = ""
    lesson: str = ""
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
class Hideout:
    id: str
    label: str
    phrase: str
    found_text: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_mesmerized(world: World) -> list[str]:
    detective = world.get("detective")
    partner = world.get("partner")
    decoy = world.get("decoy")
    if decoy.meters["noticed"] < THRESHOLD:
        return []
    sig = ("mesmerized",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["wonder"] += decoy.attrs["pull"]
    if detective.memes["wonder"] >= partner.memes["careful"] + 2:
        detective.memes["rush"] += 1
        partner.memes["friction"] += 1
        return ["__rush__"]
    partner.memes["focus"] += 1
    return []


def _r_hidden_clue(world: World) -> list[str]:
    item = world.get("item")
    hideout = world.get("hideout")
    if item.meters["moved"] < THRESHOLD:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hideout.meters["clue_visible"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    detective = world.get("detective")
    partner = world.get("partner")
    if detective.memes["apology"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["trust"] += 1
    partner.memes["trust"] += 1
    detective.memes["lesson"] += 1
    partner.memes["relief"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="mesmerized", tag="emotional", apply=_r_mesmerized),
    Rule(name="hidden_clue", tag="physical", apply=_r_hidden_clue),
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


def initial_careful(trait: str) -> float:
    return 5.0 if trait in CAREFUL_TRAITS else 3.0


def combo_ok(setting: Setting, item: MissingItem, decoy: Decoy, cause: Cause, hideout: Hideout) -> bool:
    if item.id not in setting.items:
        return False
    if decoy.id not in setting.decoys:
        return False
    if cause.id not in setting.affords:
        return False
    if hideout.id not in setting.hideouts:
        return False
    if decoy.setting_tags and setting.id not in decoy.setting_tags:
        return False
    if cause.needs and not (item.tags & cause.needs):
        return False
    if cause.hideout_tags and not (hideout.tags & cause.hideout_tags):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    out: list[tuple[str, str, str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for iid, item in ITEMS.items():
            for did, decoy in DECOYS.items():
                for cid, cause in CAUSES.items():
                    for hid, hideout in HIDEOUTS.items():
                        if combo_ok(setting, item, decoy, cause, hideout):
                            out.append((sid, iid, did, cid, hid))
    return out


def outcome_of(params: "StoryParams") -> str:
    pull = DECOYS[params.decoy].pull
    careful = initial_careful(params.partner_trait)
    return "ruffled" if IMPULSE_INIT + pull > careful + 3 else "smooth"


def predict_outcome(world: World) -> dict:
    sim = world.copy()
    sim.get("decoy").meters["noticed"] += 1
    propagate(sim, narrate=False)
    return {
        "rush": sim.get("detective").memes["rush"] >= THRESHOLD,
        "wonder": sim.get("detective").memes["wonder"],
    }


def opening(world: World, detective: Entity, partner: Entity, keeper: Entity, item: MissingItem) -> None:
    world.say(
        f"On a bright morning in {world.setting.place}, {detective.id} and {partner.id} called "
        f"themselves the Maple Street Detectives. They were tiny, serious sleuths who liked "
        f"to notice what other people missed."
    )
    world.say(
        f"That day, {keeper.label_word} needed {item.phrase} because {item.need}. "
        f"But when the time came, {item.label} was gone."
    )


def assignment(world: World, keeper: Entity, detective: Entity, partner: Entity, item: MissingItem) -> None:
    world.say(
        f'"Please help me look," said {keeper.label_word}. "{item.label.capitalize()} does not just walk away."'
    )
    detective.memes["duty"] += 1
    partner.memes["duty"] += 1
    world.say(
        f'{detective.id} puffed up proudly. "{detective.id} is on the case," {detective.pronoun()} said, '
        f'and {partner.id} nodded and opened a little notebook.'
    )


def notice_decoy(world: World, detective: Entity, partner: Entity, decoy: Decoy) -> None:
    pred = predict_outcome(world)
    world.facts["predicted_rush"] = pred["rush"]
    world.get("decoy").meters["noticed"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then they saw {decoy.phrase}. {decoy.shine} It was the sort of thing that could "
        f"mesmerize anyone who stared too long."
    )
    if pred["rush"]:
        world.say(
            f"{detective.id} stopped so suddenly that {partner.id} nearly bumped into {detective.pronoun('object')}. "
            f'"Aha," {detective.pronoun()} whispered. "A glittering clue. This mystery is bigger than we thought."'
        )
    else:
        world.say(
            f"{detective.id} admired it for a second, but {partner.id} tapped the floor and pointed back to the search path."
        )


def theory_or_method(world: World, detective: Entity, partner: Entity, item: MissingItem) -> None:
    if detective.memes["rush"] >= THRESHOLD:
        detective.memes["certainty"] += 1
        world.say(
            f'"Someone clever must have hidden the {item.label}," {detective.id} said. '
            f'"I can feel a grand thief story starting."'
        )
        world.say(
            f'{partner.id} frowned. "{partner.id} said, '
            f'`Maybe we should follow the ordinary clues first.`"'
        )
        partner.memes["hurt"] += 1
    else:
        world.say(
            f'{partner.id} crouched down and said, "Shiny things are interesting, but they are not always the answer." '
            f'{detective.id} agreed and looked for plain clues instead.'
        )


def move_item(world: World, cause: Cause, item: MissingItem, hideout: Hideout) -> None:
    ent = world.get("item")
    ent.meters["moved"] += 1
    ent.meters["hidden"] += 1
    world.say(cause.move_text.format(item=item.label, hideout=hideout.phrase))
    world.facts["clue_text"] = cause.clue
    world.facts["movement_text"] = cause.move_text.format(item=item.label, hideout=hideout.phrase)
    propagate(world, narrate=False)


def search(world: World, detective: Entity, partner: Entity, cause: Cause, hideout: Hideout, item: MissingItem) -> None:
    world.say(
        f"{partner.id} looked lower. {cause.clue} That small clue pointed straight toward {hideout.phrase}."
    )
    if detective.memes["rush"] >= THRESHOLD:
        world.say(
            f"{detective.id} blinked, looked where {partner.id} was pointing, and felt the fancy thief story shrink at once."
        )
    else:
        world.say(
            f"{detective.id} saw it too, and the two detectives hurried together toward {hideout.phrase}."
        )
    world.get("item").meters["found"] += 1
    world.get("item").meters["hidden"] = 0.0
    world.say(
        f"There was the {item.label}: {hideout.found_text} {cause.found_text}"
    )


def apology(world: World, detective: Entity, partner: Entity, item: MissingItem) -> None:
    if detective.memes["rush"] >= THRESHOLD:
        detective.memes["remorse"] += 1
        detective.memes["apology"] += 1
        propagate(world, narrate=False)
        world.say(
            f'"I was chasing the sparkliest idea instead of the truest one," {detective.id} said quietly. '
            f'"I should have listened when you asked me to check the real clues."'
        )
        world.say(
            f'{partner.id} gave a small nod. "You listened now," {partner.pronoun()} said. '
            f'"And we found the {item.label} together."'
        )
    else:
        detective.memes["apology"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{detective.id} grinned at {partner.id}. "Good thing we kept our heads," {detective.pronoun()} said.'
        )


def lesson_and_ending(world: World, detective: Entity, partner: Entity, keeper: Entity, item: MissingItem) -> None:
    keeper.memes["relief"] += 1
    if world.facts["outcome"] == "ruffled":
        world.say(
            f"{keeper.label_word.capitalize()} thanked them both and tucked {item.label} safely back where it belonged."
        )
        world.say(
            f"{detective.id} learned that a clue does not become true just because it sparkles. "
            f"The best detectives look twice, listen to their partners, and let ordinary facts lead the way."
        )
        world.say(
            f"Then {detective.id} and {partner.id} bumped shoulders, opened the notebook together, and walked on side by side, "
            f"ready for their next case with kinder voices and steadier eyes."
        )
    else:
        world.say(
            f"{keeper.label_word.capitalize()} thanked them both, and the little mystery was solved before anyone had to worry much."
        )
        world.say(
            f"The children still learned something important: even when a shiny thing catches the eye, good detectives stay calm and keep following the facts."
        )
        world.say(
            f"With that, {detective.id} and {partner.id} marched off together, pretending the sunlit floor was another case file waiting to be read."
        )


def tell(
    setting: Setting,
    item: MissingItem,
    decoy: Decoy,
    cause: Cause,
    hideout: Hideout,
    *,
    detective_name: str = "Nora",
    detective_type: str = "girl",
    partner_name: str = "Ben",
    partner_type: str = "boy",
    partner_trait: str = "careful",
) -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_type,
        role="detective",
        traits=["bold"],
        label=detective_name,
    ))
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_type,
        role="partner",
        traits=[partner_trait],
        label=partner_name,
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=setting.keeper_type,
        role="keeper",
        label=setting.keeper_label,
    ))
    item_ent = world.add(Entity(
        id="item",
        type="item",
        label=item.label,
        tags=set(item.tags),
    ))
    decoy_ent = world.add(Entity(
        id="decoy",
        type="decoy",
        label=decoy.label,
        tags=set(decoy.tags),
        attrs={"pull": decoy.pull},
    ))
    hideout_ent = world.add(Entity(
        id="hideout",
        type="place",
        label=hideout.label,
        tags=set(hideout.tags),
    ))
    detective.memes["impulse"] = IMPULSE_INIT
    detective.memes["trust"] = 3.0
    partner.memes["careful"] = initial_careful(partner_trait)
    partner.memes["trust"] = 3.0
    item_ent.meters["moved"] = 0.0
    decoy_ent.meters["noticed"] = 0.0
    hideout_ent.meters["clue_visible"] = 0.0
    world.facts["setting"] = setting
    world.facts["item_cfg"] = item
    world.facts["decoy_cfg"] = decoy
    world.facts["cause_cfg"] = cause
    world.facts["hideout_cfg"] = hideout

    opening(world, detective, partner, keeper, item)
    assignment(world, keeper, detective, partner, item)

    world.para()
    notice_decoy(world, detective, partner, decoy)
    theory_or_method(world, detective, partner, item)

    world.para()
    move_item(world, cause, item, hideout)
    search(world, detective, partner, cause, hideout, item)

    world.para()
    world.facts["outcome"] = "ruffled" if detective.memes["rush"] >= THRESHOLD else "smooth"
    apology(world, detective, partner, item)
    lesson_and_ending(world, detective, partner, keeper, item)

    world.facts.update(
        detective=detective,
        partner=partner,
        keeper=keeper,
        item=item_ent,
        decoy=decoy_ent,
        hideout=hideout_ent,
        rushed=detective.memes["rush"] >= THRESHOLD,
        found=item_ent.meters["found"] >= THRESHOLD,
        reconciled=detective.memes["lesson"] >= THRESHOLD or detective.memes["apology"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "library": Setting(
        id="library",
        place="the town library",
        keeper_type="librarian",
        keeper_label="the librarian",
        occasion="story hour",
        affords={"draft", "cart"},
        hideouts={"atlas_shelf", "book_drop", "reading_basket"},
        items={"bookmark", "clue_sheet"},
        decoys={"sun_catcher", "music_box"},
    ),
    "theater": Setting(
        id="theater",
        place="the little community theater",
        keeper_type="teacher",
        keeper_label="the drama teacher",
        occasion="curtain call",
        affords={"fan", "costume_rack"},
        hideouts={"costume_trunk", "velvet_curtain", "prop_box"},
        items={"brooch", "stage_key"},
        decoys={"mirror_mobile", "spotlight_glass"},
    ),
    "bakery": Setting(
        id="bakery",
        place="the warm corner bakery",
        keeper_type="baker",
        keeper_label="the baker",
        occasion="the morning rush",
        affords={"tray", "cat"},
        hideouts={"mixing_bowl", "flour_sack", "receipt_drawer"},
        items={"recipe_card", "gold_token"},
        decoys={"sugar_spinner", "cookie_tin"},
    ),
}

ITEMS = {
    "bookmark": MissingItem(
        id="bookmark",
        label="brass bookmark",
        phrase="the brass bookmark with the moon on top",
        need="story hour was about to begin",
        tags={"small", "metal", "shiny"},
    ),
    "clue_sheet": MissingItem(
        id="clue_sheet",
        label="clue sheet",
        phrase="the clue sheet for the treasure game",
        need="the children needed it to start the game",
        tags={"paper", "light", "flat"},
    ),
    "brooch": MissingItem(
        id="brooch",
        label="star brooch",
        phrase="the star brooch for the lead costume",
        need="the play was almost ready for curtain call",
        tags={"small", "wearable", "shiny"},
    ),
    "stage_key": MissingItem(
        id="stage_key",
        label="stage key",
        phrase="the little stage key on a blue ribbon",
        need="the prop cabinet had to be opened before the show",
        tags={"small", "metal", "shiny"},
    ),
    "recipe_card": MissingItem(
        id="recipe_card",
        label="recipe card",
        phrase="the recipe card with the cinnamon buns on it",
        need="the baker was about to mix the next batch",
        tags={"paper", "flat", "light"},
    ),
    "gold_token": MissingItem(
        id="gold_token",
        label="gold token",
        phrase="the gold token for the lucky muffin prize",
        need="a child winner would arrive any minute",
        tags={"small", "metal", "shiny"},
    ),
}

DECOYS = {
    "sun_catcher": Decoy(
        id="sun_catcher",
        label="sun-catcher",
        phrase="a rainbow sun-catcher in the window",
        shine="Colored light danced over the shelves in tiny moving diamonds.",
        pull=3,
        setting_tags={"library"},
        tags={"light", "window"},
    ),
    "music_box": Decoy(
        id="music_box",
        label="music box",
        phrase="a silver music box on the return desk",
        shine="Its lid winked and turned softly, as if it knew a secret.",
        pull=2,
        setting_tags={"library"},
        tags={"silver", "spinning"},
    ),
    "mirror_mobile": Decoy(
        id="mirror_mobile",
        label="mirror mobile",
        phrase="a hanging mirror mobile above the stage",
        shine="It tossed little sparks of light over the curtains and seats.",
        pull=3,
        setting_tags={"theater"},
        tags={"light", "hanging"},
    ),
    "spotlight_glass": Decoy(
        id="spotlight_glass",
        label="spotlight glass",
        phrase="a round piece of colored spotlight glass near the wings",
        shine="It glowed red and gold like a tiny piece of sunset.",
        pull=2,
        setting_tags={"theater"},
        tags={"glass", "light"},
    ),
    "sugar_spinner": Decoy(
        id="sugar_spinner",
        label="sugar spinner",
        phrase="a little sugar spinner turning in the front window",
        shine="Threads of sugar flashed in the sun like a tiny carnival wheel.",
        pull=3,
        setting_tags={"bakery"},
        tags={"spinning", "window"},
    ),
    "cookie_tin": Decoy(
        id="cookie_tin",
        label="cookie tin",
        phrase="a polished cookie tin shaped like a castle",
        shine="Its shiny sides gleamed so brightly they almost seemed to wink.",
        pull=2,
        setting_tags={"bakery"},
        tags={"tin", "shiny"},
    ),
}

CAUSES = {
    "draft": Cause(
        id="draft",
        label="a draft",
        needs={"paper", "light", "flat"},
        hideout_tags={"catch"},
        clue="A corner of paper was peeking out where the air had pushed it.",
        move_text="A sneaky draft from an open window had lifted the {item} and slipped it toward {hideout}.",
        found_text="It had not been stolen at all; the moving air had simply carried it there.",
        lesson="follow the plain trail before the dramatic one",
        tags={"wind", "air"},
    ),
    "cart": Cause(
        id="cart",
        label="a rolling cart",
        needs={"small", "metal", "shiny"},
        hideout_tags={"catch"},
        clue="A fresh little scrape on the floor showed where something had been nudged along.",
        move_text="A rolling library cart had bumped the {item} and nudged it toward {hideout}.",
        found_text="It had slid there when the cart rattled past.",
        lesson="objects can move for ordinary reasons",
        tags={"wheels"},
    ),
    "fan": Cause(
        id="fan",
        label="a rehearsal fan",
        needs={"light", "wearable", "small", "flat", "shiny"},
        hideout_tags={"soft"},
        clue="A ribbon end was stirring where the air from the fan still reached.",
        move_text="During rehearsal, a whirring fan had blown the {item} toward {hideout}.",
        found_text="The fan had done the mischief all by itself.",
        lesson="check the room before inventing a villain",
        tags={"air", "stage"},
    ),
    "costume_rack": Cause(
        id="costume_rack",
        label="a costume rack",
        needs={"wearable", "small", "shiny"},
        hideout_tags={"soft"},
        clue="A loose thread glittered where a sleeve had snagged something on the way by.",
        move_text="A swaying costume rack had caught the {item} and carried it toward {hideout}.",
        found_text="The rack had snared it for one clumsy moment and dropped it there.",
        lesson="watch what brushes past in a busy room",
        tags={"clothes", "stage"},
    ),
    "tray": Cause(
        id="tray",
        label="a baking tray",
        needs={"paper", "flat", "small", "metal"},
        hideout_tags={"kitchen"},
        clue="A neat line in the flour showed where something flat had slid underneath.",
        move_text="A baking tray had pushed the {item} across the counter and toward {hideout}.",
        found_text="It had been hidden by kitchen bustle, not by a crook.",
        lesson="busy hands can move things without meaning to",
        tags={"kitchen"},
    ),
    "cat": Cause(
        id="cat",
        label="the bakery cat",
        needs={"small", "shiny", "metal"},
        hideout_tags={"kitchen"},
        clue="Tiny paw prints dusted with flour led away from the counter.",
        move_text="The bakery cat had batted the {item} playfully and sent it toward {hideout}.",
        found_text="The cat had treated it like a toy and tucked it out of sight.",
        lesson="mischief is not the same as stealing",
        tags={"animal", "kitchen"},
    ),
}

HIDEOUTS = {
    "atlas_shelf": Hideout(
        id="atlas_shelf",
        label="atlas shelf",
        phrase="the bottom atlas shelf",
        found_text="It was lying behind a row of heavy books on the bottom atlas shelf.",
        tags={"catch", "shelf"},
    ),
    "book_drop": Hideout(
        id="book_drop",
        label="book drop",
        phrase="the indoor book drop",
        found_text="It was resting beside the soft flap of the indoor book drop.",
        tags={"catch", "slot"},
    ),
    "reading_basket": Hideout(
        id="reading_basket",
        label="reading basket",
        phrase="the wicker reading basket",
        found_text="It had slipped down into the wicker reading basket beside the beanbags.",
        tags={"catch", "basket"},
    ),
    "costume_trunk": Hideout(
        id="costume_trunk",
        label="costume trunk",
        phrase="the open costume trunk",
        found_text="It was tucked in the folds inside the open costume trunk.",
        tags={"soft", "box"},
    ),
    "velvet_curtain": Hideout(
        id="velvet_curtain",
        label="velvet curtain",
        phrase="the thick velvet curtain",
        found_text="It was caught in a heavy fold of the thick velvet curtain.",
        tags={"soft", "fabric"},
    ),
    "prop_box": Hideout(
        id="prop_box",
        label="prop box",
        phrase="the painted prop box",
        found_text="It had dropped into the painted prop box beside a toy crown.",
        tags={"soft", "box"},
    ),
    "mixing_bowl": Hideout(
        id="mixing_bowl",
        label="mixing bowl",
        phrase="the stack of mixing bowls",
        found_text="It was hidden under the lip of the stack of mixing bowls.",
        tags={"kitchen", "bowl"},
    ),
    "flour_sack": Hideout(
        id="flour_sack",
        label="flour sack",
        phrase="the flour sack by the wall",
        found_text="It was peeking from the fold of the flour sack by the wall.",
        tags={"kitchen", "soft"},
    ),
    "receipt_drawer": Hideout(
        id="receipt_drawer",
        label="receipt drawer",
        phrase="the little receipt drawer",
        found_text="It had slid into the little receipt drawer under the counter.",
        tags={"kitchen", "box"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Zoe", "Clara", "Ruby"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Noah", "Finn", "Theo", "Eli"]
TRAITS = ["careful", "patient", "steady", "methodical", "curious", "brisk"]


@dataclass
class StoryParams:
    setting: str
    item: str
    decoy: str
    cause: str
    hideout: str
    detective_name: str
    detective_type: str
    partner_name: str
    partner_type: str
    partner_trait: str
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
    "detective": [(
        "What does a detective do?",
        "A detective looks for clues and asks what really happened. Good detectives do not guess too fast; they check the facts."
    )],
    "mesmerize": [(
        "What does mesmerize mean?",
        "Mesmerize means to hold someone's attention so strongly that they keep staring or listening. A dazzling thing can mesmerize you and make it harder to notice everything else."
    )],
    "clue": [(
        "What is a clue?",
        "A clue is a small sign that helps you figure something out. It might be a footprint, a scrape mark, or something out of place."
    )],
    "draft": [(
        "What can a draft do to a light piece of paper?",
        "A draft is moving air, and it can push or lift a light piece of paper. That is why papers near a window sometimes slide away."
    )],
    "cat": [(
        "Why do cats bat small shiny things?",
        "Cats often swipe at little moving or shiny things because those things seem playful to them. They are not trying to solve a mystery; they are just being cats."
    )],
    "fan": [(
        "How can a fan move small objects?",
        "A fan blows air, and that moving air can push ribbons, papers, and other light objects. If something is loose, it may slide or flutter away."
    )],
    "reconcile": [(
        "What does it mean to reconcile after an argument?",
        "To reconcile means to make peace again after feelings were hurt. People listen, apologize, and choose to be kind to each other again."
    )],
}
KNOWLEDGE_ORDER = ["detective", "mesmerize", "clue", "draft", "fan", "cat", "reconcile"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    item = f["item_cfg"]
    return [
        f'Write a child-friendly detective story set in {setting.place} where two young sleuths search for a missing {item.label} and include the word "mesmerize".',
        f"Tell a gentle mystery in which one child detective is distracted by something dazzling, but the partners learn to trust real clues and make up in the end.",
        f"Write a short detective-style story with a lesson learned and reconciliation after a missing object is found for an important moment.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    partner = f["partner"]
    keeper = f["keeper"]
    item_cfg = f["item_cfg"]
    decoy = f["decoy_cfg"]
    cause = f["cause_cfg"]
    hideout = f["hideout_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two child detectives, {detective.id} and {partner.id}, who try to help {keeper.label_word} find a missing {item_cfg.label}. They want to solve the mystery before {item_cfg.need}."
        ),
        (
            f"Why did the missing {item_cfg.label} matter?",
            f"It mattered because {item_cfg.need}. The search felt urgent, so the children hurried to solve the case."
        ),
        (
            f"What almost distracted {detective.id} from the real mystery?",
            f"{decoy.phrase.capitalize()} almost distracted {detective.id}. It was so dazzling it could mesmerize a person and make a fancy idea seem more important than a plain clue."
        ),
        (
            f"How did {partner.id} help solve the case?",
            f"{partner.id} kept looking for ordinary signs instead of chasing the sparkliest theory. {partner.pronoun().capitalize()} noticed that {cause.clue.lower()}, and that clue led them to {hideout.phrase}."
        ),
        (
            f"Where was the {item_cfg.label}, and how did it get there?",
            f"The {item_cfg.label} was at {hideout.phrase}. {cause.found_text}."
        ),
    ]
    if f["outcome"] == "ruffled":
        qa.append((
            f"What lesson did {detective.id} learn?",
            f"{detective.id} learned that a mystery should be solved with careful facts, not with the most glittering guess. Listening to a partner can save the whole case from going the wrong way."
        ))
        qa.append((
            f"How did {detective.id} and {partner.id} reconcile?",
            f"{detective.id} admitted that the shiny idea had pulled {detective.pronoun('object')} away from the real clues and apologized. {partner.id} accepted that apology, and they went back to working side by side."
        ))
    else:
        qa.append((
            "What lesson did the detectives learn?",
            f"They learned that even an exciting-looking clue should be checked calmly. Real detectives stay friends by listening to each other and following the facts together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "mesmerize", "clue", "reconcile"}
    cause = world.facts["cause_cfg"]
    if cause.id == "draft":
        tags.add("draft")
    if cause.id == "fan":
        tags.add("fan")
    if cause.id == "cat":
        tags.add("cat")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="library",
        item="bookmark",
        decoy="sun_catcher",
        cause="cart",
        hideout="atlas_shelf",
        detective_name="Nora",
        detective_type="girl",
        partner_name="Ben",
        partner_type="boy",
        partner_trait="careful",
    ),
    StoryParams(
        setting="library",
        item="clue_sheet",
        decoy="music_box",
        cause="draft",
        hideout="reading_basket",
        detective_name="Mia",
        detective_type="girl",
        partner_name="Theo",
        partner_type="boy",
        partner_trait="patient",
    ),
    StoryParams(
        setting="theater",
        item="brooch",
        decoy="mirror_mobile",
        cause="costume_rack",
        hideout="costume_trunk",
        detective_name="Ella",
        detective_type="girl",
        partner_name="Max",
        partner_type="boy",
        partner_trait="curious",
    ),
    StoryParams(
        setting="theater",
        item="stage_key",
        decoy="spotlight_glass",
        cause="fan",
        hideout="velvet_curtain",
        detective_name="Leo",
        detective_type="boy",
        partner_name="Ruby",
        partner_type="girl",
        partner_trait="steady",
    ),
    StoryParams(
        setting="bakery",
        item="gold_token",
        decoy="sugar_spinner",
        cause="cat",
        hideout="flour_sack",
        detective_name="Clara",
        detective_type="girl",
        partner_name="Finn",
        partner_type="boy",
        partner_trait="methodical",
    ),
]


def explain_rejection(setting: Optional[str], item: Optional[str], decoy: Optional[str],
                      cause: Optional[str], hideout: Optional[str]) -> str:
    parts = []
    if setting and item and item not in SETTINGS[setting].items:
        parts.append(f"{ITEMS[item].label} does not belong in the {setting} cases")
    if setting and decoy and decoy not in SETTINGS[setting].decoys:
        parts.append(f"{DECOYS[decoy].label} is not part of the {setting} scene")
    if setting and cause and cause not in SETTINGS[setting].affords:
        parts.append(f"{CAUSES[cause].label} is not a plausible mover in the {setting}")
    if setting and hideout and hideout not in SETTINGS[setting].hideouts:
        parts.append(f"{HIDEOUTS[hideout].label} is not a plausible hiding place in the {setting}")
    if item and cause and not (ITEMS[item].tags & CAUSES[cause].needs):
        parts.append(f"{CAUSES[cause].label} would not normally move a {ITEMS[item].label}")
    if cause and hideout and not (HIDEOUTS[hideout].tags & CAUSES[cause].hideout_tags):
        parts.append(f"{CAUSES[cause].label} would not usually send something to {HIDEOUTS[hideout].label}")
    if not parts:
        return "(No valid combination matches the given options.)"
    return "(No story: " + "; ".join(parts) + ".)"


ASP_RULES = r"""
combo_ok(S, I, D, C, H) :-
    setting(S), item(I), decoy(D), cause(C), hideout(H),
    setting_item(S, I), setting_decoy(S, D), affords(S, C), setting_hideout(S, H),
    cause_needs(C, T), item_tag(I, T),
    cause_hideout(C, HT), hideout_tag(H, HT).

pull(D, P) :- decoy_pull(D, P).
careful_value(T, 5) :- careful_trait(T).
careful_value(T, 3) :- trait(T), not careful_trait(T).

ruffled(D, T) :- pull(D, P), careful_value(T, C), impulse_init(I), I + P > C + 3.
smooth(D, T) :- pull(D, P), careful_value(T, C), impulse_init(I), I + P <= C + 3.

outcome(ruffled) :- chosen_decoy(D), chosen_trait(T), ruffled(D, T).
outcome(smooth)  :- chosen_decoy(D), chosen_trait(T), smooth(D, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for iid in sorted(setting.items):
            lines.append(asp.fact("setting_item", sid, iid))
        for did in sorted(setting.decoys):
            lines.append(asp.fact("setting_decoy", sid, did))
        for cid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, cid))
        for hid in sorted(setting.hideouts):
            lines.append(asp.fact("setting_hideout", sid, hid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", iid, tag))
    for did, decoy in DECOYS.items():
        lines.append(asp.fact("decoy", did))
        lines.append(asp.fact("decoy_pull", did, decoy.pull))
    for cid, cause in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        for tag in sorted(cause.needs):
            lines.append(asp.fact("cause_needs", cid, tag))
        for tag in sorted(cause.hideout_tags):
            lines.append(asp.fact("cause_hideout", cid, tag))
    for hid, hideout in HIDEOUTS.items():
        lines.append(asp.fact("hideout", hid))
        for tag in sorted(hideout.tags):
            lines.append(asp.fact("hideout_tag", hid, tag))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    lines.append(asp.fact("impulse_init", int(IMPULSE_INIT)))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show combo_ok/5."))
    return sorted(set(asp.atoms(model, "combo_ok")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_decoy", params.decoy),
        asp.fact("chosen_trait", params.partner_trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for seed in range(50):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(p)
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
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generate/emit passed.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective, a dazzling decoy, and a gentle mystery with lesson learned and reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--decoy", choices=DECOYS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--partner-trait", choices=TRAITS, dest="partner_trait")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program (facts + inline rules)")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.item and args.decoy and args.cause and args.hideout:
        if not combo_ok(
            SETTINGS[args.setting],
            ITEMS[args.item],
            DECOYS[args.decoy],
            CAUSES[args.cause],
            HIDEOUTS[args.hideout],
        ):
            raise StoryError(explain_rejection(args.setting, args.item, args.decoy, args.cause, args.hideout))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.item is None or combo[1] == args.item)
        and (args.decoy is None or combo[2] == args.decoy)
        and (args.cause is None or combo[3] == args.cause)
        and (args.hideout is None or combo[4] == args.hideout)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.setting, args.item, args.decoy, args.cause, args.hideout))

    setting, item, decoy, cause, hideout = rng.choice(sorted(combos))
    detective_name, detective_type = _pick_name(rng)
    partner_name, partner_type = _pick_name(rng, avoid=detective_name)
    partner_trait = args.partner_trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        item=item,
        decoy=decoy,
        cause=cause,
        hideout=hideout,
        detective_name=detective_name,
        detective_type=detective_type,
        partner_name=partner_name,
        partner_type=partner_type,
        partner_trait=partner_trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        item = ITEMS[params.item]
        decoy = DECOYS[params.decoy]
        cause = CAUSES[params.cause]
        hideout = HIDEOUTS[params.hideout]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]}.)") from None
    if not combo_ok(setting, item, decoy, cause, hideout):
        raise StoryError(explain_rejection(params.setting, params.item, params.decoy, params.cause, params.hideout))
    world = tell(
        setting,
        item,
        decoy,
        cause,
        hideout,
        detective_name=params.detective_name,
        detective_type=params.detective_type,
        partner_name=params.partner_name,
        partner_type=params.partner_type,
        partner_trait=params.partner_trait,
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
        print(asp_program("", "#show combo_ok/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, item, decoy, cause, hideout) combos:\n")
        for combo in combos:
            print("  " + "  ".join(combo))
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
            header = f"### {p.setting}: {p.item}, {p.decoy}, {p.cause}, {outcome_of(p)}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
