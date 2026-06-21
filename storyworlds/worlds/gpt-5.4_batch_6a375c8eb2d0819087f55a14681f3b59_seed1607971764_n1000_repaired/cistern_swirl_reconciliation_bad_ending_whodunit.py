#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py
================================================================================

A standalone story world for a child-facing whodunit with an old cistern, a
mysterious loss, a mistaken accusation, a reconciliation, and a bad ending.

Premise
-------
Two children are playing detective near an old cistern when a treasured small
object goes missing. Each sees a suspicious clue and briefly suspects the other.
After they calm down and compare clues, they reconcile and solve the mystery:
the real "culprit" was not a person at all, but wind or a curious animal that
sent the object into the cistern, where the dark water's swirl carried it away.
They make up, but the object is lost for good.

The world model drives:
- where the children are,
- what object vanished,
- what cause moved it,
- which clues each child noticed,
- whether their argument delays the search,
- and why the ending is sad even after the friendship is repaired.

Run it
------
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py --item ribbon --cause wind
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py --item stone_badge
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/cistern_swirl_reconciliation_bad_ending_whodunit.py --verify
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
PATIENCE_START = 4.0
TRUST_START = 5.0
SAFE_DELAY = 0
LOSS_DELAY = 1


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
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    scene: str
    cistern_detail: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    material: str
    floatable: bool
    sinkable: bool
    precious: str
    wet_ruins: bool
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
    culprit_label: str
    kind: str
    can_push_light: bool
    can_grab_soft: bool
    leaves_tracks: bool
    leaves_feathers: bool
    leaves_fur: bool
    text_intro: str
    text_reveal: str
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


@dataclass
class Cover:
    id: str
    label: str
    keeps_out_animals: bool
    blocks_wind: bool
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"owner", "friend"}]

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


def _r_argument_hurts_trust(world: World) -> list[str]:
    out: list[str] = []
    owner = world.get("owner")
    friend = world.get("friend")
    if owner.memes["accusing"] >= THRESHOLD and friend.memes["accusing"] >= THRESHOLD:
        sig = ("argument",)
        if sig not in world.fired:
            world.fired.add(sig)
            owner.memes["hurt"] += 1
            friend.memes["hurt"] += 1
            owner.memes["trust"] -= 2
            friend.memes["trust"] -= 2
            world.facts["argument_happened"] = True
            out.append("__argument__")
    return out


def _r_delay_causes_loss(world: World) -> list[str]:
    item = world.get("item")
    cistern = world.get("cistern")
    if item.meters["in_cistern"] < THRESHOLD:
        return []
    if item.meters["delay"] < LOSS_DELAY:
        return []
    sig = ("lost",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["lost"] += 1
    cistern.meters["swirl"] += 1
    out = ["__lost__"]
    if item.meters["floatable"] >= THRESHOLD:
        item.meters["soaked"] += 1
    if item.meters["sinkable"] >= THRESHOLD:
        item.meters["sunk"] += 1
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="argument_hurts_trust", tag="social", apply=_r_argument_hurts_trust),
    Rule(name="delay_causes_loss", tag="physical", apply=_r_delay_causes_loss),
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


def object_can_fall_in(cause: Cause, item: Treasure) -> bool:
    if cause.kind == "wind":
        return item.floatable
    if cause.kind == "bird":
        return item.floatable or item.material in {"cloth", "paper"}
    if cause.kind == "cat":
        return item.floatable or item.material in {"cloth", "wood", "paper"}
    return False


def cover_allows_incident(cause: Cause, cover: Cover) -> bool:
    if cause.kind == "wind":
        return not cover.blocks_wind
    if cause.kind in {"bird", "cat"}:
        return not cover.keeps_out_animals
    return False


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for item_id, item in TREASURES.items():
            for cause_id, cause in CAUSES.items():
                for cover_id, cover in COVERS.items():
                    if object_can_fall_in(cause, item) and cover_allows_incident(cause, cover):
                        combos.append((setting_id, item_id, cause_id, cover_id))
    return sorted(combos)


def mystery_delay(argument: bool) -> int:
    return 1 if argument else 0


def outcome_of(params: "StoryParams") -> str:
    return "lost" if mystery_delay(params.argument) >= LOSS_DELAY else "saved"


def predict_loss(item: Treasure, cause: Cause, cover: Cover, argument: bool) -> dict:
    return {
        "incident": object_can_fall_in(cause, item) and cover_allows_incident(cause, cover),
        "lost": mystery_delay(argument) >= LOSS_DELAY,
    }


def introduce(world: World, owner: Entity, friend: Entity, adult: Entity, item: Treasure) -> None:
    owner.memes["trust"] = TRUST_START
    friend.memes["trust"] = TRUST_START
    owner.memes["patience"] = PATIENCE_START
    friend.memes["patience"] = PATIENCE_START
    owner.memes["love_item"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"On a bright afternoon in {world.setting.place}, {owner.id} and {friend.id} played at being detectives. "
        f"{world.setting.scene}"
    )
    world.say(
        f"{owner.id} had brought {item.phrase}. {owner.pronoun('possessive').capitalize()} {adult.label_word} had given it to "
        f"{owner.pronoun('object')}, and {owner.pronoun()} liked to keep it close because {item.precious}."
    )


def set_scene(world: World, owner: Entity, friend: Entity, cover: Cover) -> None:
    world.say(
        f"Near them stood an old cistern. {world.setting.cistern_detail} Today its cover was {cover.label}."
    )
    world.say(
        f'"Let\'s solve a tiny mystery before snack," {friend.id} whispered, and both children tiptoed around the stones as if a real case were waiting.'
    )


def incident(world: World, owner: Entity, friend: Entity, item_cfg: Treasure, cause_cfg: Cause, cover_cfg: Cover) -> None:
    item = world.get("item")
    cistern = world.get("cistern")
    world.para()
    world.say(
        f"Then the case found them. {cause_cfg.text_intro} For one blink, no one noticed where {item_cfg.label} had gone."
    )
    item.meters["in_cistern"] += 1
    item.meters["delay"] = 0.0
    item.meters["floatable"] = 1.0 if item_cfg.floatable else 0.0
    item.meters["sinkable"] = 1.0 if item_cfg.sinkable else 0.0
    cistern.attrs["cover"] = cover_cfg.id
    world.facts["incident_happened"] = True
    if cause_cfg.leaves_tracks:
        world.facts["clue_ground"] = "tiny wet prints"
    elif cause_cfg.leaves_feathers:
        world.facts["clue_ground"] = "a loose gray feather"
    elif cause_cfg.leaves_fur:
        world.facts["clue_ground"] = "a soft orange hair"
    else:
        world.facts["clue_ground"] = "a damp mark"
    world.facts["clue_water"] = "a small swirl moving in the dark water"


def notice_absence(world: World, owner: Entity, friend: Entity, item_cfg: Treasure) -> None:
    owner.memes["worry"] += 1
    friend.memes["worry"] += 1
    world.say(
        f'{owner.id} looked down and gasped. "{item_cfg.label.capitalize()}! It was right here."'
    )
    world.say(
        f"{friend.id} knelt beside the stones and saw that something by the cistern had changed, but not what had done it."
    )


def accuse(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["accusing"] += 1
    friend.memes["accusing"] += 1
    owner.memes["patience"] -= 2
    friend.memes["patience"] -= 2
    world.get("item").meters["delay"] += 1
    propagate(world, narrate=False)
    world.para()
    world.say(
        f'"Did you hide it for the game?" {owner.id} asked, cheeks hot with worry.'
    )
    world.say(
        f'"No! I thought maybe you tucked it away yourself," {friend.id} answered. Their detective game turned sharp and unhappy for a moment.'
    )


def compare_clues(world: World, owner: Entity, friend: Entity) -> None:
    ground = world.facts["clue_ground"]
    water = world.facts["clue_water"]
    world.para()
    owner.memes["thinking"] += 1
    friend.memes["thinking"] += 1
    world.say(
        f"After a quiet breath, {owner.id} noticed {ground} near the stones, and {friend.id} noticed {water} inside the cistern."
    )
    world.say(
        f'"Wait," {friend.id} said softly. "If I had hidden it, why would there be {ground} there?"'
    )


def reconcile(world: World, owner: Entity, friend: Entity) -> None:
    owner.memes["accusing"] = 0.0
    friend.memes["accusing"] = 0.0
    owner.memes["hurt"] = max(0.0, owner.memes["hurt"] - 1.0)
    friend.memes["hurt"] = max(0.0, friend.memes["hurt"] - 1.0)
    owner.memes["trust"] += 2
    friend.memes["trust"] += 2
    owner.memes["love_friend"] += 1
    friend.memes["love_friend"] += 1
    world.say(
        f'{owner.id} swallowed hard. "I am sorry I blamed you."'
    )
    world.say(
        f'"I am sorry too," {friend.id} said, taking {owner.pronoun("possessive")} hand. "Let\'s be detectives together again."'
    )
    world.facts["reconciled"] = True


def solve_case(world: World, owner: Entity, friend: Entity, item_cfg: Treasure, cause_cfg: Cause) -> None:
    item = world.get("item")
    cistern = world.get("cistern")
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"Together they pieced it out at last. {cause_cfg.text_reveal}"
    )
    if item.meters["lost"] >= THRESHOLD:
        cistern.meters["deep"] += 1
        if item_cfg.floatable and not item_cfg.sinkable:
            world.say(
                f"They leaned over the rim and saw only a dark swirl below. {item_cfg.label.capitalize()} had been carried past the place their small hands could reach."
            )
        elif item_cfg.sinkable:
            world.say(
                f"They leaned over the rim and saw only a dark swirl and one last glimmer below. Then even that slipped out of sight."
            )
        else:
            world.say(
                f"They leaned over the rim and saw the water turning in a slow swirl. Whatever had happened, {item_cfg.label} was gone from easy reach."
            )
    else:
        world.say(
            f"Because they worked together quickly, they spotted {item_cfg.label} near the edge before the water could pull it away."
        )
    world.facts["culprit_solved"] = True


def bad_ending(world: World, owner: Entity, friend: Entity, adult: Entity, item_cfg: Treasure) -> None:
    item = world.get("item")
    owner.memes["sadness"] += 1
    friend.memes["sadness"] += 1
    adult.memes["comfort"] += 1
    world.para()
    world.say(
        f"{adult.label_word.capitalize()} came when they called and peered into the cistern, but the water was too deep and the stones were too slippery for a child-sized rescue."
    )
    if item_cfg.wet_ruins:
        world.say(
            f"{owner.id} knew that even if {item_cfg.label} ever came up again, the water would spoil it. The case was solved, but the treasure was still lost."
        )
    else:
        world.say(
            f"{owner.id} knew they would not get {item_cfg.label} back that day. The case was solved, but the treasure was still lost."
        )
    world.say(
        f"{friend.id} stood shoulder to shoulder with {owner.id}, and neither let go of the other's hand. They had found the truth, but too late to change the ending."
    )
    item.meters["unrecovered"] += 1
    world.facts["ending"] = "bad"


def hopeful_ending(world: World, owner: Entity, friend: Entity, item_cfg: Treasure) -> None:
    owner.memes["relief"] += 1
    friend.memes["relief"] += 1
    world.para()
    world.say(
        f"Together they hooked a long stick under {item_cfg.label} and pulled it back before the water could take it. The mystery ended with wet sleeves and relieved smiles."
    )
    world.say(
        f"From then on, they kept their clues and their treasures farther from the cistern, and they trusted each other first."
    )
    world.facts["ending"] = "saved"


def tell(
    setting: Setting,
    item_cfg: Treasure,
    cause_cfg: Cause,
    cover_cfg: Cover,
    owner_name: str = "Mara",
    owner_gender: str = "girl",
    friend_name: str = "Jules",
    friend_gender: str = "boy",
    adult_type: str = "aunt",
    argument: bool = True,
) -> World:
    world = World(setting)
    owner = world.add(Entity(id=owner_name, kind="character", type=owner_gender, role="owner"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend"))
    adult = world.add(Entity(id="Adult", kind="character", type=adult_type, role="adult", label="the grown-up"))
    cistern = world.add(Entity(id="cistern", kind="thing", type="cistern", label="cistern"))
    item = world.add(Entity(id="item", kind="thing", type=item_cfg.id, label=item_cfg.label))
    world.facts.update(
        owner=owner,
        friend=friend,
        adult=adult,
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        cover_cfg=cover_cfg,
        setting=setting,
        argument_planned=argument,
        clue_ground="",
        clue_water="",
        argument_happened=False,
        reconciled=False,
        culprit_solved=False,
        ending="",
    )

    introduce(world, owner, friend, adult, item_cfg)
    set_scene(world, owner, friend, cover_cfg)
    incident(world, owner, friend, item_cfg, cause_cfg, cover_cfg)
    notice_absence(world, owner, friend, item_cfg)
    if argument:
        accuse(world, owner, friend)
    compare_clues(world, owner, friend)
    reconcile(world, owner, friend)
    solve_case(world, owner, friend, item_cfg, cause_cfg)
    if item.meters["lost"] >= THRESHOLD:
        bad_ending(world, owner, friend, adult, item_cfg)
    else:
        hopeful_ending(world, owner, friend, item_cfg)

    world.facts.update(
        outcome=world.facts["ending"],
        lost=item.meters["lost"] >= THRESHOLD,
        unrecovered=item.meters["unrecovered"] >= THRESHOLD,
        item=item,
        cistern=cistern,
    )
    return world


SETTINGS = {
    "courtyard": Setting(
        id="courtyard",
        place="the old courtyard behind the bakery",
        scene="Warm bricks glowed in the sun, and ivy made little shadows on the wall.",
        cistern_detail="Its round stones were cool and dark, and the iron ring on the lid was worn smooth.",
        tags={"courtyard", "cistern"},
    ),
    "vicarage_garden": Setting(
        id="vicarage_garden",
        place="the quiet garden beside the vicarage",
        scene="Pear leaves whispered overhead, and a narrow path curled between mint and marigolds.",
        cistern_detail="The old cistern sat beside the herb bed, half hidden by leaves and old stone.",
        tags={"garden", "cistern"},
    ),
    "school_yard": Setting(
        id="school_yard",
        place="the little school yard after lessons",
        scene="A chalk line still showed on the ground, and the last sun touched the fence.",
        cistern_detail="At the far edge stood a brick cistern with a mossy rim and deep, echoing water.",
        tags={"school", "cistern"},
    ),
}

TREASURES = {
    "ribbon": Treasure(
        id="ribbon",
        label="blue ribbon",
        phrase="a blue ribbon from the spring fair",
        material="cloth",
        floatable=True,
        sinkable=False,
        precious="it reminded her of a happy day",
        wet_ruins=True,
        tags={"ribbon", "cloth"},
    ),
    "note": Treasure(
        id="note",
        label="folded note",
        phrase="a folded note with a secret poem inside",
        material="paper",
        floatable=True,
        sinkable=False,
        precious="it held words she wanted to keep",
        wet_ruins=True,
        tags={"paper", "note"},
    ),
    "wooden_star": Treasure(
        id="wooden_star",
        label="wooden star",
        phrase="a small wooden star painted gold",
        material="wood",
        floatable=True,
        sinkable=False,
        precious="her grandfather had carved it by hand",
        wet_ruins=False,
        tags={"wood", "star"},
    ),
    "stone_badge": Treasure(
        id="stone_badge",
        label="stone badge",
        phrase="a smooth stone badge with a tiny painted crown",
        material="stone",
        floatable=False,
        sinkable=True,
        precious="she had worked hard to paint it herself",
        wet_ruins=False,
        tags={"stone", "badge"},
    ),
}

CAUSES = {
    "wind": Cause(
        id="wind",
        culprit_label="the wind",
        kind="wind",
        can_push_light=True,
        can_grab_soft=False,
        leaves_tracks=False,
        leaves_feathers=False,
        leaves_fur=False,
        text_intro="A quick wind skipped across the yard and flicked at loose things on the stones.",
        text_reveal="The children saw that the wind must have whisked the treasure over the crooked edge and into the cistern.",
        qa_text="The wind pushed it into the cistern",
        tags={"wind", "nonhuman"},
    ),
    "jackdaw": Cause(
        id="jackdaw",
        culprit_label="a jackdaw",
        kind="bird",
        can_push_light=False,
        can_grab_soft=True,
        leaves_tracks=False,
        leaves_feathers=True,
        leaves_fur=False,
        text_intro="A black jackdaw flapped down to the rim, pecked once, and sprang away in a rustle of wings.",
        text_reveal="The children realized the jackdaw had snatched at the treasure, dropped it, and knocked it into the cistern.",
        qa_text="A jackdaw pecked at it and knocked it into the cistern",
        tags={"bird", "nonhuman"},
    ),
    "cat": Cause(
        id="cat",
        culprit_label="the bakery cat",
        kind="cat",
        can_push_light=False,
        can_grab_soft=True,
        leaves_tracks=True,
        leaves_feathers=False,
        leaves_fur=True,
        text_intro="The bakery cat slipped past the flower pots, batted at something bright, and darted off again.",
        text_reveal="The children understood that the bakery cat had played with the treasure and flicked it into the cistern.",
        qa_text="The bakery cat batted it into the cistern",
        tags={"cat", "nonhuman"},
    ),
}

COVERS = {
    "ajar_grate": Cover(
        id="ajar_grate",
        label="slightly ajar",
        keeps_out_animals=False,
        blocks_wind=False,
        tags={"open", "unsafe"},
    ),
    "slat_lid": Cover(
        id="slat_lid",
        label="a little crooked",
        keeps_out_animals=False,
        blocks_wind=False,
        tags={"crooked", "unsafe"},
    ),
    "open_ring": Cover(
        id="open_ring",
        label="propped open on its iron ring",
        keeps_out_animals=False,
        blocks_wind=False,
        tags={"open", "unsafe"},
    ),
    "heavy_lid": Cover(
        id="heavy_lid",
        label="shut tight and heavy",
        keeps_out_animals=True,
        blocks_wind=True,
        tags={"safe"},
    ),
}

GIRL_NAMES = ["Mara", "Ivy", "Nora", "Lina", "Tessa", "Rose", "Mina", "Clara"]
BOY_NAMES = ["Jules", "Finn", "Theo", "Leo", "Owen", "Max", "Ned", "Eli"]


@dataclass
class StoryParams:
    setting: str
    item: str
    cause: str
    cover: str
    owner_name: str
    owner_gender: str
    friend_name: str
    friend_gender: str
    adult: str
    argument: bool = True
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
    "cistern": [
        (
            "What is a cistern?",
            "A cistern is a big container that stores water. Old cisterns can be deep and dark, so children should stay back and tell a grown-up if something falls in.",
        )
    ],
    "swirl": [
        (
            "What is a swirl in water?",
            "A swirl is water turning in a round, circling motion. That moving water can carry small things away from the edge.",
        )
    ],
    "wind": [
        (
            "Can wind move light things?",
            "Yes. Wind can push light things like paper or ribbon if they are loose and not being held.",
        )
    ],
    "bird": [
        (
            "Why might a bird peck at a shiny or soft thing?",
            "Some birds are curious about small objects and may peck or tug at them. That can make the object fall or move somewhere unexpected.",
        )
    ],
    "cat": [
        (
            "Why do cats bat at small objects?",
            "Cats often play with little moving or dangling things. A quick paw tap can send an object skittering away.",
        )
    ],
    "apology": [
        (
            "What does it mean to reconcile after an argument?",
            "To reconcile means to make peace again after being upset. People do that by telling the truth, listening, and saying they are sorry.",
        )
    ],
    "clues": [
        (
            "What is a clue in a mystery?",
            "A clue is a small sign that helps you figure out what happened. Good detectives look carefully before they blame anyone.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cistern", "swirl", "wind", "bird", "cat", "clues", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    item_cfg = f["item_cfg"]
    cause_cfg = f["cause_cfg"]
    return [
        f'Write a short child-friendly whodunit that includes the words "cistern" and "swirl". Two children should lose {item_cfg.phrase}, suspect each other, then reconcile after studying the clues.',
        f"Tell a gentle mystery about {owner.id} and {friend.id} near an old cistern, where the apparent culprit is really {cause_cfg.culprit_label}, and the truth comes too late for a happy ending.",
        "Write a story with reconciliation and a bad ending, where solving the mystery fixes the friendship but cannot bring back the lost treasure.",
    ]


def pair_noun(owner: Entity, friend: Entity) -> str:
    if owner.type == "girl" and friend.type == "girl":
        return "two friends"
    if owner.type == "boy" and friend.type == "boy":
        return "two friends"
    return "two friends"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    owner = f["owner"]
    friend = f["friend"]
    adult = f["adult"]
    item_cfg = f["item_cfg"]
    cause_cfg = f["cause_cfg"]
    cover_cfg = f["cover_cfg"]
    ground = f["clue_ground"]
    water = f["clue_water"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(owner, friend)}, {owner.id} and {friend.id}, who were playing detective near an old cistern. It also includes {owner.id}'s {adult.label_word}, who comes when the children call for help.",
        ),
        (
            f"What went missing?",
            f"{owner.id}'s {item_cfg.label} went missing beside the cistern. It mattered because {item_cfg.precious}.",
        ),
        (
            "Why did the children first suspect each other?",
            f"They were frightened and saw that the treasure had vanished all at once, so each child guessed the other might be playing a trick. Their worry made them speak before they had compared the clues.",
        ),
        (
            "What clues helped solve the mystery?",
            f"They found {ground} near the stones and noticed {water} in the cistern. Those clues showed that something had gone into the water, and that neither child had simply hidden it.",
        ),
        (
            "How did the children reconcile?",
            f"{owner.id} apologized for blaming {friend.id}, and {friend.id} apologized too. They took each other's hand and decided to be detectives together again.",
        ),
    ]
    if f["outcome"] == "bad":
        qa.append(
            (
                f"Who was the real culprit, and why was the ending still sad?",
                f"The real culprit was {cause_cfg.culprit_label}. {cause_cfg.qa_text}, but the argument delayed the children, so by the time they understood the truth, the cistern's swirl had already carried the treasure beyond reach.",
            )
        )
        qa.append(
            (
                "Could the grown-up fix everything?",
                f"No. {adult.label_word.capitalize()} could comfort them and look into the cistern, but the water was too deep and the opening was unsafe for a child-sized rescue. The friendship was repaired, but the lost object did not come back.",
            )
        )
    else:
        qa.append(
            (
                "Why were they able to save the treasure?",
                "They compared clues quickly and worked together instead of arguing. That let them reach the object before the moving water could pull it farther away.",
            )
        )
    qa.append(
        (
            f"Why did the cistern matter in the mystery?",
            f"The cistern was where the treasure fell, and the dark water with its swirl changed a small mistake into a real loss. The old opening was especially risky because its cover was {cover_cfg.label}.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"cistern", "swirl", "clues", "apology"}
    cause_cfg = world.facts["cause_cfg"]
    if cause_cfg.kind == "wind":
        tags.add("wind")
    elif cause_cfg.kind == "bird":
        tags.add("bird")
    elif cause_cfg.kind == "cat":
        tags.add("cat")
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
            shown = {k: v for k, v in e.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    facts = {
        k: v
        for k, v in world.facts.items()
        if k
        not in {
            "owner",
            "friend",
            "adult",
            "item",
            "cistern",
            "item_cfg",
            "cause_cfg",
            "cover_cfg",
            "setting",
        }
    }
    lines.append(f"  facts: {facts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="courtyard",
        item="ribbon",
        cause="cat",
        cover="ajar_grate",
        owner_name="Mara",
        owner_gender="girl",
        friend_name="Jules",
        friend_gender="boy",
        adult="aunt",
        argument=True,
    ),
    StoryParams(
        setting="vicarage_garden",
        item="note",
        cause="wind",
        cover="open_ring",
        owner_name="Ivy",
        owner_gender="girl",
        friend_name="Theo",
        friend_gender="boy",
        adult="uncle",
        argument=True,
    ),
    StoryParams(
        setting="school_yard",
        item="wooden_star",
        cause="jackdaw",
        cover="slat_lid",
        owner_name="Clara",
        owner_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        adult="mother",
        argument=True,
    ),
    StoryParams(
        setting="courtyard",
        item="stone_badge",
        cause="cat",
        cover="ajar_grate",
        owner_name="Nora",
        owner_gender="girl",
        friend_name="Max",
        friend_gender="boy",
        adult="father",
        argument=True,
    ),
]


def explain_rejection(item: Treasure, cause: Cause, cover: Cover) -> str:
    if not object_can_fall_in(cause, item):
        return (
            f"(No story: {cause.culprit_label} would not plausibly send {item.label} into the cistern. "
            f"Pick a lighter or easier-to-bat object.)"
        )
    if not cover_allows_incident(cause, cover):
        return (
            f"(No story: a cover that is {cover.label} would stop {cause.culprit_label} from causing the accident, "
            f"so there is no honest mystery here.)"
        )
    return "(No story: this combination does not make a plausible cistern mystery.)"


ASP_RULES = r"""
can_fall_in(Cause, Item) :- cause_kind(Cause, wind), item_floatable(Item).
can_fall_in(Cause, Item) :- cause_kind(Cause, bird), item_floatable(Item).
can_fall_in(Cause, Item) :- cause_kind(Cause, bird), item_material(Item, cloth).
can_fall_in(Cause, Item) :- cause_kind(Cause, bird), item_material(Item, paper).
can_fall_in(Cause, Item) :- cause_kind(Cause, cat), item_floatable(Item).
can_fall_in(Cause, Item) :- cause_kind(Cause, cat), item_material(Item, cloth).
can_fall_in(Cause, Item) :- cause_kind(Cause, cat), item_material(Item, wood).
can_fall_in(Cause, Item) :- cause_kind(Cause, cat), item_material(Item, paper).

cover_allows(Cause, Cover) :- cause_kind(Cause, wind), cover_blocks_wind(Cover, 0).
cover_allows(Cause, Cover) :- cause_kind(Cause, bird), cover_keeps_out_animals(Cover, 0).
cover_allows(Cause, Cover) :- cause_kind(Cause, cat), cover_keeps_out_animals(Cover, 0).

valid(Setting, Item, Cause, Cover) :-
    setting(Setting), treasure(Item), cause(Cause), cover(Cover),
    can_fall_in(Cause, Item), cover_allows(Cause, Cover).

delay(1) :- argument(true).
delay(0) :- not argument(true).

outcome(lost) :- delay(D), loss_delay(L), D >= L.
outcome(saved) :- delay(D), loss_delay(L), D < L.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        if t.floatable:
            lines.append(asp.fact("item_floatable", tid))
        lines.append(asp.fact("item_material", tid, t.material))
    for cid, c in CAUSES.items():
        lines.append(asp.fact("cause", cid))
        lines.append(asp.fact("cause_kind", cid, c.kind))
    for lid, c in COVERS.items():
        lines.append(asp.fact("cover", lid))
        lines.append(asp.fact("cover_keeps_out_animals", lid, 1 if c.keeps_out_animals else 0))
        lines.append(asp.fact("cover_blocks_wind", lid, 1 if c.blocks_wind else 0))
    lines.append(asp.fact("loss_delay", LOSS_DELAY))
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
            asp.fact("argument", "true" if params.argument else "false"),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a child-friendly cistern whodunit with reconciliation and a bad ending."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=TREASURES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--owner-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--owner-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument(
        "--argument",
        dest="argument",
        action="store_true",
        help="force the children to accuse each other first (default: random/usually true)",
    )
    ap.add_argument(
        "--no-argument",
        dest="argument",
        action="store_false",
        help="skip the accusation delay so they may save the object",
    )
    ap.set_defaults(argument=None)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.cause and args.cover:
        item = TREASURES[args.item]
        cause = CAUSES[args.cause]
        cover = COVERS[args.cover]
        if not (object_can_fall_in(cause, item) and cover_allows_incident(cause, cover)):
            raise StoryError(explain_rejection(item, cause, cover))

    combos = [
        c
        for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.item is None or c[1] == args.item)
        and (args.cause is None or c[2] == args.cause)
        and (args.cover is None or c[3] == args.cover)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, item_id, cause_id, cover_id = rng.choice(combos)
    owner_gender = args.owner_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    owner_name = args.owner_name or _pick_name(rng, owner_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=owner_name)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    argument = args.argument if args.argument is not None else True
    return StoryParams(
        setting=setting_id,
        item=item_id,
        cause=cause_id,
        cover=cover_id,
        owner_name=owner_name,
        owner_gender=owner_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult=adult,
        argument=argument,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.item not in TREASURES:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.cover not in COVERS:
        raise StoryError(f"(Unknown cover: {params.cover})")

    item_cfg = TREASURES[params.item]
    cause_cfg = CAUSES[params.cause]
    cover_cfg = COVERS[params.cover]
    if not (object_can_fall_in(cause_cfg, item_cfg) and cover_allows_incident(cause_cfg, cover_cfg)):
        raise StoryError(explain_rejection(item_cfg, cause_cfg, cover_cfg))

    world = tell(
        setting=SETTINGS[params.setting],
        item_cfg=item_cfg,
        cause_cfg=cause_cfg,
        cover_cfg=cover_cfg,
        owner_name=params.owner_name,
        owner_gender=params.owner_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult,
        argument=params.argument,
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
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_set - py:
            print("  only in clingo:", sorted(asp_set - py))
        if py - asp_set:
            print("  only in python:", sorted(py - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            p = resolve_params(build_parser().parse_args([]), random.Random(seed))
            p.seed = seed
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"Resolve failed for seed {seed}.")
    bad = 0
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("empty story")
        print("OK: smoke-test generation succeeded.")
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
        print(f"{len(combos)} valid (setting, item, cause, cover) combos:\n")
        for setting_id, item_id, cause_id, cover_id in combos:
            print(f"  {setting_id:15} {item_id:12} {cause_id:8} {cover_id}")
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
            header = f"### {p.owner_name} & {p.friend_name}: {p.item} / {p.cause} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
