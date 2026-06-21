#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py
====================================================================================

A standalone storyworld for a tiny detective-story domain: during a castle
renovation, something important seems to go missing, tempers rise, and a child
detective solves the case by noticing a clue, tracing the object's safe move,
and helping people reconcile.

Required seed words appear naturally in the stories:
- king
- variable
- renovate

The world model tracks:
- physical meters: dust, moved, hidden, found, danger_to_item
- emotional memes: worry, suspicion, trust, relief, apology, pride, kindness

The core tension is not a crime by a villain but a mistaken suspicion during a
busy renovation. The "detective story" feel comes from scene clues, witness
beliefs, a reasoned search, and a reveal. The "Reconciliation" feature is
modeled directly: the ending depends on whether the detective gets both adults
to compare notes and apologize after the item is found.

Run it
------
    python storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py
    python storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py --trace --qa
    python storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py --asp
    python storyworlds/worlds/gpt-5.4/king_variable_renovate_reconciliation_detective_story.py --verify
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
    tags: set[str] = field(default_factory=set)
    movable: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "builder_woman", "librarian"}
        male = {"boy", "father", "man", "king", "builder_man", "steward"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title(self) -> str:
        if self.type == "king":
            return "the king"
        return self.label or self.id
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Site:
    id: str
    label: str
    phrase: str
    detail: str
    risky_work: str
    dust_word: str
    safe_storages: set[str] = field(default_factory=set)
    item_tags: set[str] = field(default_factory=set)
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
class MissingItem:
    id: str
    label: str
    phrase: str
    plural: bool = False
    fragile: bool = False
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Storage:
    id: str
    label: str
    phrase: str
    protective: bool
    fits_tags: set[str] = field(default_factory=set)
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
    text: str
    points_to: str
    variable_wording: str
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


def _r_risk_to_item(world: World) -> list[str]:
    out: list[str] = []
    site = world.get("site")
    item = world.get("item")
    if item.meters["at_worksite"] < THRESHOLD:
        return out
    sig = ("risk_to_item",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["danger_to_item"] += 1
    king = world.get("King")
    king.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_suspicion_hurts_trust(world: World) -> list[str]:
    out: list[str] = []
    builder = world.get("Builder")
    steward = world.get("Steward")
    if builder.memes["suspected"] < THRESHOLD and steward.memes["suspected"] < THRESHOLD:
        return out
    sig = ("suspicion_hurts_trust",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    builder.memes["trust"] -= 1
    steward.memes["trust"] -= 1
    builder.memes["hurt"] += 1
    steward.memes["hurt"] += 1
    out.append("__trust__")
    return out


def _r_compare_notes_finds_item(world: World) -> list[str]:
    out: list[str] = []
    item = world.get("item")
    if world.facts.get("notes_compared") is not True:
        return out
    if item.meters["hidden"] < THRESHOLD:
        return out
    sig = ("compare_notes_finds_item",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["found"] += 1
    item.meters["hidden"] = 0.0
    king = world.get("King")
    detective = world.get("Detective")
    builder = world.get("Builder")
    steward = world.get("Steward")
    for ent in (king, detective, builder, steward):
        ent.memes["relief"] += 1
    out.append("__found__")
    return out


def _r_apology_restores_trust(world: World) -> list[str]:
    out: list[str] = []
    builder = world.get("Builder")
    steward = world.get("Steward")
    if builder.memes["apology"] < THRESHOLD or steward.memes["apology"] < THRESHOLD:
        return out
    sig = ("apology_restores_trust",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    builder.memes["trust"] += 2
    steward.memes["trust"] += 2
    builder.memes["hurt"] = 0.0
    steward.memes["hurt"] = 0.0
    out.append("__reconcile__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="risk_to_item", tag="physical", apply=_r_risk_to_item),
    Rule(name="suspicion_hurts_trust", tag="social", apply=_r_suspicion_hurts_trust),
    Rule(name="compare_notes_finds_item", tag="epistemic", apply=_r_compare_notes_finds_item),
    Rule(name="apology_restores_trust", tag="social", apply=_r_apology_restores_trust),
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


def compatible_move(site: Site, item: MissingItem, storage: Storage) -> bool:
    return (
        storage.id in site.safe_storages
        and bool(item.tags & site.item_tags)
        and bool(item.tags & storage.fits_tags)
        and storage.protective
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for site_id, site in SITES.items():
        for item_id, item in ITEMS.items():
            for storage_id, storage in STORAGES.items():
                for clue_id, clue in CLUES.items():
                    if clue.points_to != storage_id:
                        continue
                    if compatible_move(site, item, storage):
                        combos.append((site_id, item_id, storage_id, clue_id))
    return combos


def predict_found_if_notes_shared(site: Site, item: MissingItem, storage: Storage, compare_notes: bool) -> bool:
    return compatible_move(site, item, storage) and compare_notes


def predict_outcome(compare_notes: bool, encourage_apology: bool) -> str:
    if compare_notes and encourage_apology:
        return "reconciled"
    if compare_notes:
        return "solved"
    return "blamed"


def introduce(world: World, detective: Entity, king: Entity, site: Site, item: MissingItem) -> None:
    world.say(
        f"In the old castle, {site.phrase} was full of ladders, cloth sheets, and the tap-tap of workers trying to renovate the room before moonrise."
    )
    world.say(
        f"{king.title.capitalize()} wanted {item.phrase} ready for the evening ceremony, and {detective.id}, the smallest detective in the castle, liked mysteries almost as much as warm honey cakes."
    )
    world.say(site.detail)


def establish_missing(world: World, king: Entity, item: MissingItem, builder: Entity, steward: Entity) -> None:
    king.memes["worry"] += 1
    builder.memes["trust"] += 1
    steward.memes["trust"] += 1
    world.say(
        f"Then {king.title} looked at the velvet stand and blinked. {item.phrase.capitalize()} was gone."
    )
    world.say(
        f'"Where is it?" asked the king. {builder.id} looked at {steward.id}, and {steward.id} looked right back.'
    )


def show_suspicion(world: World, builder: Entity, steward: Entity, site: Site) -> None:
    builder.memes["suspected"] += 1
    steward.memes["suspected"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{builder.id} brushed {site.dust_word} from {builder.pronoun("possessive")} sleeves. "I moved only the work cloths," {builder.pronoun()} said.'
    )
    world.say(
        f'"And I moved only the royal papers," said {steward.id}. The room felt smaller when the two grown-ups stopped trusting each other.'
    )


def inspect_scene(world: World, detective: Entity, clue: Clue, site: Site) -> None:
    detective.memes["focus"] += 1
    world.say(
        f"{detective.id} did not shout. {detective.pronoun().capitalize()} walked in a slow circle, noticing the quiet things detectives notice: {clue.text}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} whispered that every renovation has one variable, and today's variable was where frightened helpers had tucked precious things to keep them clean."
    )


def infer_move(world: World, item: Entity, clue: Clue, site: Site, storage: Storage) -> None:
    item.meters["at_worksite"] += 1
    propagate(world, narrate=False)
    world.say(
        f"That clue did not look like a thief's clue. It looked like a careful clue. If dust and dripping plaster were falling in {site.label}, someone sensible would have moved the treasure somewhere safer."
    )
    world.say(
        f'"The mark points to {storage.phrase}," said {world.get("Detective").id}. "Someone hid it to protect it, not to keep it forever."'
    )


def search_storage(world: World, detective: Entity, storage: Storage, item: Entity, compare_notes: bool) -> None:
    if compare_notes:
        world.facts["notes_compared"] = True
        propagate(world, narrate=False)
        world.say(
            f"{detective.id} asked {world.get('Builder').id} and {world.get('Steward').id} to stop arguing and share what each of them had done. One had seen the chalk mark. The other had seen the extra key. Put together, the story finally made sense."
        )
        world.say(
            f"They hurried to {storage.phrase}, lifted the lid, and there lay the missing thing, safe from dust."
        )
    else:
        world.say(
            f"{detective.id} hurried to {storage.phrase}, but without the two grown-ups comparing notes, there were too many boxes and too many doors. The clue stayed only half-understood."
        )


def reveal_and_lesson(world: World, king: Entity, item_cfg: MissingItem, storage: Storage, site: Site) -> None:
    world.say(
        f'{king.title.capitalize()} let out a long breath. "{item_cfg.phrase.capitalize()} was hidden there because the hall was being renovated," {king.pronoun()} said. "That was caution, not stealing."'
    )
    world.say(
        f"The mystery was smaller now, but the hurt in the room was still real."
    )


def encourage_reconciliation(world: World, detective: Entity, builder: Entity, steward: Entity, encourage_apology: bool) -> None:
    if encourage_apology:
        builder.memes["apology"] += 1
        steward.memes["apology"] += 1
        builder.memes["kindness"] += 1
        steward.memes["kindness"] += 1
        propagate(world, narrate=False)
        world.say(
            f'{detective.id} folded {detective.pronoun("possessive")} hands. "A good detective solves the missing thing," {detective.pronoun()} said, "but a better one also mends the people."'
        )
        world.say(
            f'{builder.id} looked at {steward.id}. "I am sorry I blamed you," {builder.pronoun()} said. {steward.id} nodded. "I am sorry too. I should have spoken sooner."'
        )
    else:
        world.say(
            f"{detective.id} had solved where the item was, but the grown-ups were still standing stiff as broomsticks, each waiting for the other to soften first."
        )


def happy_ending(world: World, king: Entity, detective: Entity, item_cfg: MissingItem, site: Site) -> None:
    king.memes["pride"] += 1
    detective.memes["pride"] += 1
    world.say(
        f"{king.title.capitalize()} placed {item_cfg.phrase} back where it belonged and thanked everyone for protecting the castle while they renovate it."
    )
    world.say(
        f"Then {builder_name(world)} and {steward_name(world)} carried a table together instead of from opposite corners, and the room no longer felt like a courtroom. By supper, the castle glowed with fresh plaster, and the little detective smiled because the case had ended with truth and reconciliation."
    )


def plain_solved_ending(world: World, king: Entity, detective: Entity, item_cfg: MissingItem) -> None:
    king.memes["pride"] += 1
    detective.memes["pride"] += 1
    world.say(
        f"{king.title.capitalize()} put {item_cfg.phrase} back on its stand and thanked {detective.id} for sharp eyes and a calm mind."
    )
    world.say(
        f"But when the torches were lit, {builder_name(world)} and {steward_name(world)} still worked in silence. The mystery was solved, though the room did not feel fully warm again."
    )


def sadder_ending(world: World, king: Entity, detective: Entity, storage: Storage) -> None:
    king.memes["worry"] += 1
    detective.memes["resolve"] += 1
    world.say(
        f"{king.title.capitalize()} saw that the clue pointed somewhere important, but not enough had been shared to finish the puzzle before the ceremony bell rang."
    )
    world.say(
        f"So the case slept for one night. {detective.id} promised to return in the morning, when cooler heads could open {storage.phrase} properly and the angry voices might at last turn into helpful ones."
    )


def builder_name(world: World) -> str:
    return world.get("Builder").id


def steward_name(world: World) -> str:
    return world.get("Steward").id


def tell(
    site: Site,
    item_cfg: MissingItem,
    storage: Storage,
    clue: Clue,
    detective_name: str = "Mira",
    detective_type: str = "girl",
    builder_name_value: str = "Rowan",
    builder_type: str = "builder_man",
    steward_name_value: str = "Hale",
    steward_type: str = "steward",
    compare_notes: bool = True,
    encourage_apology: bool = True,
) -> World:
    world = World()
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_type, role="detective", label=detective_name))
    king = world.add(Entity(id="King", kind="character", type="king", role="king", label="the king"))
    builder = world.add(Entity(id=builder_name_value, kind="character", type=builder_type, role="builder", label=builder_name_value))
    steward = world.add(Entity(id=steward_name_value, kind="character", type=steward_type, role="steward", label=steward_name_value))
    site_ent = world.add(Entity(id="site", kind="thing", type="room", label=site.label))
    item = world.add(Entity(id="item", kind="thing", type="item", label=item_cfg.label, movable=True, fragile=item_cfg.fragile, tags=set(item_cfg.tags)))

    world.facts["notes_compared"] = False
    world.facts["site_cfg"] = site
    world.facts["item_cfg"] = item_cfg
    world.facts["storage_cfg"] = storage
    world.facts["clue_cfg"] = clue
    world.facts["compare_notes"] = compare_notes
    world.facts["encourage_apology"] = encourage_apology

    item.meters["hidden"] += 1
    item.meters["moved"] += 1

    introduce(world, detective, king, site, item_cfg)
    establish_missing(world, king, item_cfg, builder, steward)

    world.para()
    show_suspicion(world, builder, steward, site)
    inspect_scene(world, detective, clue, site)
    infer_move(world, item, clue, site, storage)

    world.para()
    search_storage(world, detective, storage, item, compare_notes)
    if item.meters["found"] >= THRESHOLD:
        reveal_and_lesson(world, king, item_cfg, storage, site)
        world.para()
        encourage_reconciliation(world, detective, builder, steward, encourage_apology)
        world.para()
        if encourage_apology:
            happy_ending(world, king, detective, item_cfg, site)
            outcome = "reconciled"
        else:
            plain_solved_ending(world, king, detective, item_cfg)
            outcome = "solved"
    else:
        world.para()
        sadder_ending(world, king, detective, storage)
        outcome = "blamed"

    world.facts.update(
        detective=detective,
        king=king,
        builder=builder,
        steward=steward,
        item=item,
        site=site_ent,
        found=item.meters["found"] >= THRESHOLD,
        outcome=outcome,
        reconciled=builder.memes["trust"] > 0 and steward.memes["trust"] > 0 and builder.memes["apology"] >= THRESHOLD and steward.memes["apology"] >= THRESHOLD,
    )
    return world


SITES = {
    "throne_room": Site(
        id="throne_room",
        label="the throne room",
        phrase="the throne room",
        detail="Fresh gold paint shone on one wall, while another wall hid behind sheets because the stone trim still needed careful work.",
        risky_work="fresh paint and moving ladders",
        dust_word="gold dust",
        safe_storages={"cedar_chest", "map_cabinet"},
        item_tags={"paper", "ceremony", "fabric"},
        tags={"castle", "renovation"},
    ),
    "west_library": Site(
        id="west_library",
        label="the west library",
        phrase="the west library",
        detail="Half the shelves had been emptied so the workers could mend the cracked ceiling, and soft gray dust lay where sunbeams touched it.",
        risky_work="falling dust and ceiling repair",
        dust_word="gray dust",
        safe_storages={"map_cabinet", "cedar_chest"},
        item_tags={"paper", "seal", "ceremony"},
        tags={"library", "renovation"},
    ),
    "music_gallery": Site(
        id="music_gallery",
        label="the music gallery",
        phrase="the music gallery",
        detail="New boards waited by the wall, and the old floor gave tiny squeaks whenever a ladder was moved across it.",
        risky_work="loose boards and sanding",
        dust_word="sawdust",
        safe_storages={"cedar_chest", "locked_drawer"},
        item_tags={"fabric", "seal", "ceremony"},
        tags={"gallery", "renovation"},
    ),
}

ITEMS = {
    "royal_letter": MissingItem(
        id="royal_letter",
        label="royal letter",
        phrase="the royal letter",
        fragile=True,
        tags={"paper", "ceremony"},
    ),
    "blue_ribbon_plan": MissingItem(
        id="blue_ribbon_plan",
        label="blue ribbon plan",
        phrase="the blue ribbon plan",
        fragile=False,
        tags={"paper"},
    ),
    "wax_seal_box": MissingItem(
        id="wax_seal_box",
        label="wax seal box",
        phrase="the wax seal box",
        fragile=True,
        tags={"seal", "ceremony"},
    ),
    "silk_banner": MissingItem(
        id="silk_banner",
        label="silk banner",
        phrase="the silk banner",
        fragile=False,
        tags={"fabric", "ceremony"},
    ),
}

STORAGES = {
    "cedar_chest": Storage(
        id="cedar_chest",
        label="cedar chest",
        phrase="the cedar chest by the wall",
        protective=True,
        fits_tags={"fabric", "ceremony"},
        tags={"storage", "chest"},
    ),
    "map_cabinet": Storage(
        id="map_cabinet",
        label="map cabinet",
        phrase="the flat map cabinet",
        protective=True,
        fits_tags={"paper", "seal"},
        tags={"storage", "cabinet"},
    ),
    "locked_drawer": Storage(
        id="locked_drawer",
        label="locked drawer",
        phrase="the locked drawer under the music stand",
        protective=True,
        fits_tags={"seal", "paper", "ceremony"},
        tags={"storage", "drawer"},
    ),
    "open_shelf": Storage(
        id="open_shelf",
        label="open shelf",
        phrase="the open shelf near the ladder",
        protective=False,
        fits_tags={"paper", "fabric", "seal", "ceremony"},
        tags={"storage", "shelf"},
    ),
}

CLUES = {
    "chalk_arrow": Clue(
        id="chalk_arrow",
        label="chalk arrow",
        text="a pale chalk arrow on the floor trim, almost rubbed away by busy boots",
        points_to="cedar_chest",
        variable_wording="The arrow had looked different from one angle to another, a variable little mark that only a patient eye would trust.",
        tags={"clue", "chalk"},
    ),
    "dust_free_square": Clue(
        id="dust_free_square",
        label="dust-free square",
        text="a clean square in the dust where a flat drawer had recently been opened",
        points_to="map_cabinet",
        variable_wording="The shape seemed to change with the light, a variable patch in the dust.",
        tags={"clue", "dust"},
    ),
    "extra_key": Clue(
        id="extra_key",
        label="extra key",
        text="a brass key tied with blue thread and hanging behind a music stand",
        points_to="locked_drawer",
        variable_wording="The key winked in and out of sight, a variable glint each time the sheet cloth moved.",
        tags={"clue", "key"},
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Nora", "Tessa", "Ivy", "June"]
BOY_NAMES = ["Owen", "Finn", "Milo", "Theo", "Evan", "Jules"]
BUILDER_NAMES = ["Rowan", "Bram", "Edda", "Pella"]
STEWARD_NAMES = ["Hale", "Cedric", "Iris", "Maren"]


@dataclass
class StoryParams:
    site: str
    item: str
    storage: str
    clue: str
    detective_name: str
    detective_gender: str
    builder_name: str
    builder_gender: str
    steward_name: str
    steward_gender: str
    compare_notes: bool = True
    encourage_apology: bool = True
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
    "renovation": [
        (
            "What does renovate mean?",
            "To renovate means to fix, mend, or improve an old place so it is safe and fresh again. Workers may move things away from dust, paint, or falling plaster while they do it."
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective notices clues and asks careful questions to figure out what really happened. A good detective tries to understand people as well as puzzles."
        )
    ],
    "king": [
        (
            "What is a king?",
            "A king is a ruler in a kingdom. In stories, a king often cares for the castle and the people who live there."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you solve a mystery. A footprint, a key, or a mark in dust can all be clues."
        )
    ],
    "reconciliation": [
        (
            "What is reconciliation?",
            "Reconciliation means people stop fighting and become friendly again after hurt feelings or a misunderstanding. It often begins with truth, listening, and an apology."
        )
    ],
    "storage": [
        (
            "Why do people move things during repairs?",
            "People move important things during repairs so dust, paint, or falling bits do not ruin them. Moving something for safety is different from stealing it."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "king", "renovation", "storage", "reconciliation"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    item_cfg = f["item_cfg"]
    site = f["site_cfg"]
    outcome = f["outcome"]
    if outcome == "reconciled":
        ending = "and ends with the adults apologizing and working together again"
    elif outcome == "solved":
        ending = "and ends with the mystery solved, though the hurt feelings are slower to heal"
    else:
        ending = "and ends with the mystery only partly solved for now"
    return [
        f'Write a child-friendly detective story about a king, a castle room being renovated, and a missing object. Include the words "king", "variable", and "renovate".',
        f"Tell a gentle mystery where {detective.id} notices clues in {site.label} and traces the missing {item_cfg.label} to a safe hiding place, {ending}.",
        f"Write a short castle mystery in which a missing treasure causes blame, but the detective learns that careful listening can matter as much as finding the clue."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    king = f["king"]
    builder = f["builder"]
    steward = f["steward"]
    item_cfg = f["item_cfg"]
    site = f["site_cfg"]
    storage = f["storage_cfg"]
    clue = f["clue_cfg"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {king.title}, {detective.id} the young detective, and two grown-ups named {builder.id} and {steward.id}. They were all caught in a mystery during work in {site.label}."
        ),
        (
            f"Why did everyone worry when {item_cfg.phrase} went missing?",
            f"They needed it for the king's ceremony, and the room was busy with renovation work. Dust, tools, and moving ladders made it easy to fear the item had been lost or taken."
        ),
        (
            f"What clue helped {detective.id} understand the mystery?",
            f"{detective.id} noticed {clue.text}. That clue suggested the item had been moved carefully toward {storage.label}, not stolen in a rush."
        ),
    ]

    if f["found"]:
        qa.append(
            (
                f"How did {detective.id} solve the case?",
                f"{detective.id} asked the grown-ups to compare what each of them had seen, and the two half-clues fit together. Then they searched {storage.phrase} and found {item_cfg.phrase} safe inside."
            )
        )
    else:
        qa.append(
            (
                f"Why was the mystery not fully solved that night?",
                f"The clue pointed in the right direction, but the adults did not share enough information to finish the puzzle. Without both notes together, the detective could only see half the pattern."
            )
        )

    if outcome == "reconciled":
        qa.append(
            (
                "How did reconciliation happen at the end?",
                f"After the item was found, {detective.id} reminded the adults that solving a mystery should also mend hurt feelings. {builder.id} and {steward.id} apologized to each other, so the room became calm as well as truthful."
            )
        )
    elif outcome == "solved":
        qa.append(
            (
                "Did finding the object fix every problem?",
                f"No. The object was found, but {builder.id} and {steward.id} were still upset with each other. The case was solved, yet the people in it were not fully mended."
            )
        )
    else:
        qa.append(
            (
                "What did the ending show about blame?",
                f"It showed that blame can grow faster than understanding when people are upset. The detective knew the answer would come sooner once everyone listened instead of accusing."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"detective", "clue", "king", "renovation", "storage"}
    if world.facts.get("outcome") == "reconciled":
        tags.add("reconciliation")
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} found={world.facts.get('found')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        site="west_library",
        item="royal_letter",
        storage="map_cabinet",
        clue="dust_free_square",
        detective_name="Mira",
        detective_gender="girl",
        builder_name="Rowan",
        builder_gender="boy",
        steward_name="Hale",
        steward_gender="boy",
        compare_notes=True,
        encourage_apology=True,
    ),
    StoryParams(
        site="music_gallery",
        item="wax_seal_box",
        storage="locked_drawer",
        clue="extra_key",
        detective_name="Owen",
        detective_gender="boy",
        builder_name="Edda",
        builder_gender="girl",
        steward_name="Iris",
        steward_gender="girl",
        compare_notes=True,
        encourage_apology=False,
    ),
    StoryParams(
        site="throne_room",
        item="silk_banner",
        storage="cedar_chest",
        clue="chalk_arrow",
        detective_name="Nora",
        detective_gender="girl",
        builder_name="Bram",
        builder_gender="boy",
        steward_name="Maren",
        steward_gender="girl",
        compare_notes=False,
        encourage_apology=False,
    ),
]


def explain_rejection(site: Site, item: MissingItem, storage: Storage, clue: Clue) -> str:
    if clue.points_to != storage.id:
        return (
            f"(No story: the clue '{clue.id}' points to {clue.points_to}, not to {storage.id}. "
            f"The mystery needs a clue that honestly leads to the chosen hiding place.)"
        )
    if storage.id not in site.safe_storages:
        return (
            f"(No story: {storage.label} is not a sensible safe place for valuables during work in {site.label}. "
            f"Choose a storage place the workers would really use while they renovate.)"
        )
    if not storage.protective:
        return (
            f"(No story: {storage.label} does not protect the missing item from dust and work. "
            f"The hiding place must be a safer place than the worksite.)"
        )
    return (
        f"(No story: {item.phrase} does not fit the kinds of things usually protected in {storage.label} during work in {site.label}. "
        f"Pick a more plausible item or storage place.)"
    )


ASP_RULES = r"""
compatible_move(Site, Item, Storage) :-
    site(Site), item(Item), storage(Storage),
    safe_storage(Site, Storage),
    protective(Storage),
    item_tag(Item, Tag),
    site_item_tag(Site, Tag),
    storage_fits(Storage, Tag).

valid(Site, Item, Storage, Clue) :-
    clue_points_to(Clue, Storage),
    compatible_move(Site, Item, Storage).

found_if_notes_shared(Site, Item, Storage) :-
    compatible_move(Site, Item, Storage),
    compare_notes.

outcome(reconciled) :- compare_notes, encourage_apology.
outcome(solved) :- compare_notes, not encourage_apology.
outcome(blamed) :- not compare_notes.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for site_id, site in SITES.items():
        lines.append(asp.fact("site", site_id))
        for storage_id in sorted(site.safe_storages):
            lines.append(asp.fact("safe_storage", site_id, storage_id))
        for tag in sorted(site.item_tags):
            lines.append(asp.fact("site_item_tag", site_id, tag))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        for tag in sorted(item.tags):
            lines.append(asp.fact("item_tag", item_id, tag))
    for storage_id, storage in STORAGES.items():
        lines.append(asp.fact("storage", storage_id))
        if storage.protective:
            lines.append(asp.fact("protective", storage_id))
        for tag in sorted(storage.fits_tags):
            lines.append(asp.fact("storage_fits", storage_id, tag))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("clue_points_to", clue_id, clue.points_to))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("compare_notes") if params.compare_notes else "",
            asp.fact("encourage_apology") if params.encourage_apology else "",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Castle detective storyworld: a king, a renovation, a missing object, and a chance for reconciliation."
    )
    ap.add_argument("--site", choices=SITES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--storage", choices=STORAGES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--compare-notes", choices=["yes", "no"])
    ap.add_argument("--encourage-apology", choices=["yes", "no"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combinations from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.site and args.item and args.storage and args.clue:
        site = SITES[args.site]
        item = ITEMS[args.item]
        storage = STORAGES[args.storage]
        clue = CLUES[args.clue]
        if not compatible_move(site, item, storage) or clue.points_to != storage.id:
            raise StoryError(explain_rejection(site, item, storage, clue))

    combos = [
        combo
        for combo in valid_combos()
        if (args.site is None or combo[0] == args.site)
        and (args.item is None or combo[1] == args.item)
        and (args.storage is None or combo[2] == args.storage)
        and (args.clue is None or combo[3] == args.clue)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    site_id, item_id, storage_id, clue_id = rng.choice(sorted(combos))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    detective_name = rng.choice(GIRL_NAMES if detective_gender == "girl" else BOY_NAMES)

    builder_gender = rng.choice(["girl", "boy"])
    builder_name = rng.choice([n for n in BUILDER_NAMES if n != detective_name])
    steward_gender = rng.choice(["girl", "boy"])
    steward_name = rng.choice([n for n in STEWARD_NAMES if n not in {detective_name, builder_name}])

    compare_notes = {"yes": True, "no": False}.get(args.compare_notes, rng.choice([True, False]))
    if not compare_notes:
        encourage_apology = False
    else:
        encourage_apology = {"yes": True, "no": False}.get(args.encourage_apology, rng.choice([True, False]))

    return StoryParams(
        site=site_id,
        item=item_id,
        storage=storage_id,
        clue=clue_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        builder_name=builder_name,
        builder_gender=builder_gender,
        steward_name=steward_name,
        steward_gender=steward_gender,
        compare_notes=compare_notes,
        encourage_apology=encourage_apology,
    )


def _builder_type(gender: str) -> str:
    return "builder_woman" if gender == "girl" else "builder_man"


def _steward_type(gender: str) -> str:
    return "librarian" if gender == "girl" else "steward"


def generate(params: StoryParams) -> StorySample:
    try:
        site = SITES[params.site]
        item = ITEMS[params.item]
        storage = STORAGES[params.storage]
        clue = CLUES[params.clue]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not compatible_move(site, item, storage) or clue.points_to != storage.id:
        raise StoryError(explain_rejection(site, item, storage, clue))

    world = tell(
        site=site,
        item_cfg=item,
        storage=storage,
        clue=clue,
        detective_name=params.detective_name,
        detective_type=params.detective_gender,
        builder_name_value=params.builder_name,
        builder_type=_builder_type(params.builder_gender),
        steward_name_value=params.steward_name,
        steward_type=_steward_type(params.steward_gender),
        compare_notes=params.compare_notes,
        encourage_apology=params.encourage_apology,
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

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: valid_combos() matches ASP ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"resolve_params failed unexpectedly for seed {seed}")
            break

    mismatches = 0
    for p in cases:
        py = predict_outcome(p.compare_notes, p.encourage_apology)
        asp_val = asp_outcome(p)
        if py != asp_val:
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches ASP on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(cases[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story.")
        emit(sample, trace=False, qa=False, header="-- smoke test --")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (site, item, storage, clue) combos:\n")
        for site_id, item_id, storage_id, clue_id in combos:
            print(f"  {site_id:13} {item_id:16} {storage_id:12} {clue_id}")
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
            header = f"### {p.site}: {p.item} via {p.storage} ({predict_outcome(p.compare_notes, p.encourage_apology)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
