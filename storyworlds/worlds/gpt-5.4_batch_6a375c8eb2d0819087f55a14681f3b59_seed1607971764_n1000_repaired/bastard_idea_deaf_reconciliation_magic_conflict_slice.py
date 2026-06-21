#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py
====================================================================================

A standalone story world about a small household conflict: one child has a good
idea, another child rushes, something ordinary gets broken, and a gentle bit of
home magic helps them slow down, understand one another, and reconcile.

This world keeps the tone close to slice-of-life: supper, chores, cousins, a
grandmother's cupboard, and one small magical ritual. The seed words appear
naturally in the domain:
- "idea" is the missed plan that would have prevented the break.
- "deaf" describes the child whose signing is initially missed.
- "bastard" appears in the label on a harmless herb tin, "bastard balm",
  used in the grandmother's truth-steam charm.

Run it
------
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py --item paper_lantern --repair paper_paste
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py --bridge steam_window --place courtyard
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py --all
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bastard_idea_deaf_reconciliation_magic_conflict_slice.py --verify
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
    deaf: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "mother", "aunt"}
        male = {"boy", "man", "grandfather", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)
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
    task: str
    afford_bridges: set[str] = field(default_factory=set)
    ending_spot: str = ""
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
class ItemCfg:
    id: str
    label: str
    phrase: str
    material: str
    damage_word: str
    display_verb: str
    ending_image: str
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
class RepairSpell:
    id: str
    label: str
    fixes: str
    gesture: str
    result: str
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
class Bridge:
    id: str
    label: str
    intro: str
    reveal: str
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
    setting: Setting
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"rusher", "deaf_child"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        return World(
            setting=self.setting,
            entities=copy.deepcopy(self.entities),
            fired=set(self.fired),
            paragraphs=[[]],
            facts=copy.deepcopy(self.facts),
        )
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


def _r_break_tension(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["broken"] < THRESHOLD:
        return []
    sig = ("break_tension",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("room").meters["trouble"] += 1
    for kid in world.kids():
        kid.memes["worry"] += 1
    return []


def _r_ignored_hurt(world: World) -> list[str]:
    deaf_child = world.get("deaf_child")
    if deaf_child.memes["ignored"] < THRESHOLD:
        return []
    sig = ("ignored_hurt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    deaf_child.memes["hurt"] += 1
    world.get("rusher").memes["defensive"] += 1
    world.get("room").meters["tension"] += 1
    return []


def _r_reconcile(world: World) -> list[str]:
    if not world.facts.get("bridge_used"):
        return []
    if not world.facts.get("apology_given"):
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("deaf_child").memes["hurt"] = 0.0
    world.get("rusher").memes["defensive"] = 0.0
    for kid in world.kids():
        kid.memes["trust"] += 1
        kid.memes["relief"] += 1
    world.get("room").meters["tension"] = 0.0
    return []


def _r_mended_calm(world: World) -> list[str]:
    item = world.get("item")
    if item.meters["mended"] < THRESHOLD:
        return []
    sig = ("mended_calm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    item.meters["broken"] = 0.0
    item.meters["glow"] += 1
    world.get("room").meters["trouble"] = 0.0
    for kid in world.kids():
        kid.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="break_tension", tag="physical", apply=_r_break_tension),
    Rule(name="ignored_hurt", tag="social", apply=_r_ignored_hurt),
    Rule(name="reconcile", tag="social", apply=_r_reconcile),
    Rule(name="mended_calm", tag="magic", apply=_r_mended_calm),
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
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS: dict[str, Setting] = {
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        task="hanging a small light before supper",
        afford_bridges={"slate", "glow_ribbon", "steam_window"},
        ending_spot="over the supper table",
        tags={"home", "supper"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        task="putting something pretty near the front door",
        afford_bridges={"slate", "glow_ribbon", "steam_window"},
        ending_spot="by the front door",
        tags={"home", "visitors"},
    ),
    "courtyard": Setting(
        id="courtyard",
        place="the courtyard",
        task="getting ready for an evening snack outside",
        afford_bridges={"slate", "glow_ribbon"},
        ending_spot="above the little outdoor table",
        tags={"outside", "evening"},
    ),
}

ITEMS: dict[str, ItemCfg] = {
    "paper_lantern": ItemCfg(
        id="paper_lantern",
        label="paper lantern",
        phrase="a round paper lantern",
        material="paper",
        damage_word="tore along one side",
        display_verb="hung",
        ending_image="glowed like a small moon",
        tags={"paper_lantern", "paper"},
    ),
    "quilt": ItemCfg(
        id="quilt",
        label="quilt",
        phrase="a patchwork quilt",
        material="cloth",
        damage_word="split at one seam",
        display_verb="spread",
        ending_image="lay smooth and warm again",
        tags={"quilt", "cloth"},
    ),
    "teacup": ItemCfg(
        id="teacup",
        label="teacup",
        phrase="a painted teacup",
        material="ceramic",
        damage_word="chipped at the rim",
        display_verb="set",
        ending_image="held a quiet curl of tea steam",
        tags={"teacup", "ceramic", "tea"},
    ),
}

REPAIRS: dict[str, RepairSpell] = {
    "paper_paste": RepairSpell(
        id="paper_paste",
        label="paper-paste charm",
        fixes="paper",
        gesture="brushed a pearly paste across the torn place and tapped it twice",
        result="the thin paper knit itself flat again",
        qa_text="used a paper-paste charm to mend the torn paper",
        tags={"paper_magic", "repair_magic"},
    ),
    "silver_thread": RepairSpell(
        id="silver_thread",
        label="silver-thread spell",
        fixes="cloth",
        gesture="drew one shining thread through the seam without even needing a needle",
        result="the seam pulled snug and neat",
        qa_text="used a silver-thread spell to close the split seam",
        tags={"cloth_magic", "repair_magic"},
    ),
    "warm_glaze": RepairSpell(
        id="warm_glaze",
        label="warm-glaze whisper",
        fixes="ceramic",
        gesture="warmed the chipped edge with her hands until it shone the color of honey",
        result="the little chip smoothed over as if it had remembered its old shape",
        qa_text="used a warm-glaze whisper to smooth the chipped cup",
        tags={"ceramic_magic", "repair_magic"},
    ),
}

BRIDGES: dict[str, Bridge] = {
    "slate": Bridge(
        id="slate",
        label="kitchen slate",
        intro="set a little slate on the table and held out a piece of chalk",
        reveal="The chalk lines turned bright enough for everyone to follow the idea slowly.",
        tags={"writing", "communication"},
    ),
    "glow_ribbon": Bridge(
        id="glow_ribbon",
        label="glow ribbon",
        intro="looped a glow ribbon around their wrists so every careful hand-shape left a soft trail of light",
        reveal="The glowing trails made the signs easy to notice, and nobody had to guess anymore.",
        tags={"signs", "communication", "magic"},
    ),
    "steam_window": Bridge(
        id="steam_window",
        label="steam window",
        intro="breathed warm kettle steam across the window and invited them to trace their thoughts in the mist",
        reveal="Each traced line stayed shining in the fog long enough for both children to really look.",
        tags={"writing", "steam", "communication", "magic"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tess", "Nora", "June", "Ava", "Ruby", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Milo", "Sam", "Theo", "Ben"]
RELATIONS = ["siblings", "cousins"]


def repair_fits(item: ItemCfg, repair: RepairSpell) -> bool:
    return item.material == repair.fixes


def bridge_allowed(setting: Setting, bridge: Bridge) -> bool:
    return bridge.id in setting.afford_bridges


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for repair_id, repair in REPAIRS.items():
                for bridge_id, bridge in BRIDGES.items():
                    if repair_fits(item, repair) and bridge_allowed(setting, bridge):
                        out.append((place, item_id, repair_id, bridge_id))
    return out


@dataclass
class StoryParams:
    place: str
    item: str
    repair: str
    bridge: str
    deaf_name: str
    deaf_gender: str
    rusher_name: str
    rusher_gender: str
    elder_type: str
    relation: str
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


def predict_mend(world: World, repair_id: str) -> bool:
    sim = world.copy()
    item = sim.get("item")
    repair = REPAIRS[repair_id]
    if not repair_fits(ITEMS[sim.facts["item_cfg"].id], repair):
        return False
    item.meters["mended"] += 1
    propagate(sim, narrate=False)
    return item.meters["broken"] < THRESHOLD and item.meters["glow"] >= THRESHOLD


def setting_opening(setting: Setting) -> str:
    if setting.id == "kitchen":
        return "The window was pale with evening, and the house smelled faintly of rice and onions."
    if setting.id == "hallway":
        return "Shoes waited by the mat, and the narrow hall held the last gold of the day."
    return "The bricks still held a little warmth from the sun, and the air had started to cool."


def introduce(world: World, deaf_child: Entity, rusher: Entity, elder: Entity) -> None:
    relation = world.facts["relation"]
    kin = "siblings" if relation == "siblings" else "cousins"
    world.say(
        f"{deaf_child.id} and {rusher.id} were {kin} helping {elder.label_word} with {world.setting.task} in {world.setting.place}."
    )
    world.say(setting_opening(world.setting))
    world.say(
        f"{deaf_child.id} was deaf and quick with expressive hands, and {rusher.id} was the sort of child who reached for a job before the whole plan had been said."
    )


def setup_item(world: World, item_cfg: ItemCfg) -> None:
    elder = world.get("elder")
    world.say(
        f"{elder.label_word.capitalize()} brought out {item_cfg.phrase} and asked them to work together with gentle hands."
    )


def missed_idea(world: World, deaf_child: Entity, rusher: Entity, item_cfg: ItemCfg) -> None:
    deaf_child.memes["hope"] += 1
    world.facts["idea_source"] = deaf_child.id
    if item_cfg.id == "paper_lantern":
        idea = "tie the lower knot first so the lantern would stop spinning"
    elif item_cfg.id == "quilt":
        idea = "fold the heavy corner under before lifting it"
    else:
        idea = "set a towel down first and turn the cup by its saucer"
    world.facts["idea_text"] = idea
    world.say(
        f"{deaf_child.id} had an idea at once and began to sign it: {idea}."
    )
    world.say(
        f"But {rusher.id} was already moving. {rusher.pronoun().capitalize()} caught only the beginning, guessed wrong, and hurried ahead."
    )


def break_item(world: World, deaf_child: Entity, rusher: Entity, item_cfg: ItemCfg) -> None:
    item = world.get("item")
    item.meters["broken"] += 1
    item.meters["scar"] += 1
    deaf_child.memes["ignored"] += 1
    world.facts["break_cause"] = "rushing past the signed warning"
    propagate(world, narrate=False)
    world.say(
        f"In the next second, the {item_cfg.label} {item_cfg.damage_word}."
    )
    world.say(
        f'"I was trying to tell you!" {deaf_child.id} said, hands jumping fast with hurt.'
    )
    world.say(
        f'{rusher.id} flushed. "{rusher.pronoun("subject").capitalize()} thought you were saying hold it higher," {elder_said_name(world)} said a moment later, because {rusher.id} could not find a calmer answer right away.'
    )


def elder_said_name(world: World) -> str:
    return world.get("rusher").id


def conflict_beat(world: World, deaf_child: Entity, rusher: Entity) -> None:
    world.say(
        f"{deaf_child.id} looked away. Being missed felt worse than the broken thing, because the good idea had been there in time."
    )
    world.say(
        f"{rusher.id} stared at the floorboards and wished the room would stop feeling so tight."
    )


def truth_magic(world: World, elder: Entity, bridge_cfg: Bridge) -> None:
    world.facts["bridge_used"] = True
    world.say(
        f"{elder.label_word.capitalize()} did not scold either of them. Instead, {elder.pronoun()} opened the blue tin marked bastard balm and {bridge_cfg.intro}."
    )
    world.say(
        f'A pinch of the herb went into a cup of warm water, and the air filled with a fresh, green smell. "{elder.pronoun().capitalize()} only need the room to slow down," {elder.pronoun()} said.'
    )
    world.say(bridge_cfg.reveal)


def share_truth(world: World, deaf_child: Entity, rusher: Entity) -> None:
    world.facts["truth_seen"] = True
    idea = world.facts["idea_text"]
    deaf_child.memes["clarity"] += 1
    world.say(
        f"This time {rusher.id} watched properly. {deaf_child.id} signed the whole idea again, and it was simple: {idea}."
    )
    world.say(
        f"{rusher.id}'s face changed as soon as {rusher.pronoun()} understood that the warning had never been anger at all; it had been help."
    )


def apologize(world: World, deaf_child: Entity, rusher: Entity) -> None:
    world.facts["apology_given"] = True
    rusher.memes["sorry"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"I am sorry," {rusher.id} said. "I rushed, and I did not wait for your hands. Your idea was the better one."'
    )
    world.say(
        f"{deaf_child.id} let out a long breath and nodded. The room felt softer as soon as the apology landed."
    )


def mend(world: World, elder: Entity, item_cfg: ItemCfg, repair_cfg: RepairSpell) -> None:
    item = world.get("item")
    world.facts["repair_success"] = predict_mend(world, repair_cfg.id)
    world.say(
        f"{elder.label_word.capitalize()} touched the broken place and chose {repair_cfg.label}."
    )
    world.say(
        f"{elder.pronoun().capitalize()} {repair_cfg.gesture}, and {repair_cfg.result}."
    )
    item.meters["mended"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then {deaf_child_name(world)} and {rusher_name(world)} finished the job together, this time following the idea in the right order."
    )


def deaf_child_name(world: World) -> str:
    return world.get("deaf_child").id


def rusher_name(world: World) -> str:
    return world.get("rusher").id


def ending(world: World, item_cfg: ItemCfg, deaf_child: Entity, rusher: Entity, elder: Entity) -> None:
    world.say(
        f"When they were done, the {item_cfg.label} {item_cfg.ending_image} {world.setting.ending_spot}."
    )
    world.say(
        f"{rusher.id} answered {deaf_child.id} with a careful thank-you sign, and {deaf_child.id} smiled back."
    )
    world.say(
        f"{elder.label_word.capitalize()} went back to the evening's small work, and the house felt ordinary again in the good way."
    )


def tell(
    setting: Setting,
    item_cfg: ItemCfg,
    repair_cfg: RepairSpell,
    bridge_cfg: Bridge,
    deaf_name: str = "June",
    deaf_gender: str = "girl",
    rusher_name_value: str = "Eli",
    rusher_gender: str = "boy",
    elder_type: str = "grandmother",
    relation: str = "cousins",
) -> World:
    world = World(setting=setting)
    world.facts.update(
        bridge_used=False,
        apology_given=False,
        truth_seen=False,
        repair_success=False,
        relation=relation,
        item_cfg=item_cfg,
        repair_cfg=repair_cfg,
        bridge_cfg=bridge_cfg,
    )

    deaf_child = world.add(
        Entity(
            id=deaf_name,
            kind="character",
            type=deaf_gender,
            role="deaf_child",
            deaf=True,
            attrs={"relation": relation},
        )
    )
    rusher = world.add(
        Entity(
            id=rusher_name_value,
            kind="character",
            type=rusher_gender,
            role="rusher",
            attrs={"relation": relation},
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    world.add(Entity(id="room", type="room", label="the room"))
    world.add(
        Entity(
            id="item",
            type=item_cfg.id,
            label=item_cfg.label,
            attrs={"material": item_cfg.material},
        )
    )

    deaf_child.memes["trust"] = 1.0
    rusher.memes["trust"] = 1.0

    introduce(world, deaf_child, rusher, elder)
    setup_item(world, item_cfg)

    world.para()
    missed_idea(world, deaf_child, rusher, item_cfg)
    break_item(world, deaf_child, rusher, item_cfg)
    conflict_beat(world, deaf_child, rusher)

    world.para()
    truth_magic(world, elder, bridge_cfg)
    share_truth(world, deaf_child, rusher)
    apologize(world, deaf_child, rusher)

    world.para()
    mend(world, elder, item_cfg, repair_cfg)
    ending(world, item_cfg, deaf_child, rusher, elder)

    world.facts.update(
        deaf_child=deaf_child,
        rusher=rusher,
        elder=elder,
        item=world.get("item"),
        setting=setting,
        reconciled=deaf_child.memes["hurt"] < THRESHOLD and world.facts["apology_given"],
    )
    return world


KNOWLEDGE = {
    "deaf": [
        (
            "What does it mean if someone is deaf?",
            "A deaf person cannot hear, or cannot hear much, so they may use sign language, lip-reading, writing, or other ways to communicate. The important thing is to face them and give them time to see what you mean.",
        )
    ],
    "signs": [
        (
            "Why is it helpful to watch someone's hands when they are signing?",
            "Signing uses hand-shapes, movement, and facial expression to share meaning. If you rush or look away, you can miss important parts of what they are trying to say.",
        )
    ],
    "apology": [
        (
            "Why can an apology help after a mistake?",
            "A real apology tells the other person you understand the hurt and wish you had acted differently. That helps trust start growing again.",
        )
    ],
    "repair_magic": [
        (
            "What is mending magic in a story like this?",
            "Mending magic is a pretend, gentle kind of spell that fixes a small household thing like cloth, paper, or pottery. It works best when people also fix the hurt between them.",
        )
    ],
    "paper": [
        (
            "Why does paper tear easily?",
            "Paper is thin and light, so a quick pull can rip it. That is why paper things need slow hands.",
        )
    ],
    "cloth": [
        (
            "What is a seam?",
            "A seam is the line where pieces of cloth are joined together. If a seam splits, the cloth can come apart until someone sews or mends it.",
        )
    ],
    "ceramic": [
        (
            "Why do cups chip?",
            "Ceramic is hard, but it can still crack or chip if it knocks against something. Hard things can break when they hit in the wrong way.",
        )
    ],
    "writing": [
        (
            "Why can writing help people understand each other?",
            "Writing slows a thought down and holds it still for a moment. That can help everyone look carefully and understand the same idea.",
        )
    ],
    "steam": [
        (
            "What happens when warm steam touches a cool window?",
            "Tiny drops of water gather on the cool glass and make a misty layer. You can draw on that fog with a finger.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "deaf",
    "signs",
    "apology",
    "repair_magic",
    "paper",
    "cloth",
    "ceramic",
    "writing",
    "steam",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    deaf_child = f["deaf_child"]
    rusher = f["rusher"]
    item_cfg = f["item_cfg"]
    setting = f["setting"]
    return [
        f'Write a gentle slice-of-life story with a touch of magic about two children in {setting.place}, a broken {item_cfg.label}, and a missed idea that leads to reconciliation. Include the words "idea" and "deaf".',
        f"Tell a story where {deaf_child.id}, who is deaf, tries to warn {rusher.id} about a better plan, but {rusher.id} rushes and something household gets broken before they make peace.",
        'Write a small domestic fantasy where a grandmother uses a tin marked "bastard balm" to help two children slow down, understand each other, and mend both an object and a friendship.',
    ]


def pair_noun(relation: str, deaf_child: Entity, rusher: Entity) -> str:
    if relation == "siblings":
        if deaf_child.type == "girl" and rusher.type == "girl":
            return "two sisters"
        if deaf_child.type == "boy" and rusher.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two cousins"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    deaf_child = f["deaf_child"]
    rusher = f["rusher"]
    elder = f["elder"]
    item_cfg = f["item_cfg"]
    repair_cfg = f["repair_cfg"]
    bridge_cfg = f["bridge_cfg"]
    relation = f["relation"]
    pair = pair_noun(relation, deaf_child, rusher)
    idea = f["idea_text"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {deaf_child.id} and {rusher.id}, and their {elder.label_word} who helps them after a mistake. The story stays close to one small evening at home.",
        ),
        (
            f"What was {deaf_child.id}'s idea?",
            f"{deaf_child.id}'s idea was to {idea}. It was a careful plan that would have kept the {item_cfg.label} safe if {rusher.id} had waited to see it.",
        ),
        (
            f"Why did the fight start?",
            f"The fight started because {rusher.id} rushed ahead and missed the signed warning. Then the {item_cfg.label} was damaged, and {deaf_child.id} felt hurt because the good idea had been there in time.",
        ),
        (
            f"How did the magic help them understand each other?",
            f"{elder.label_word.capitalize()} used bastard balm and the {bridge_cfg.label} so the idea could be shared slowly and clearly. That mattered because the problem was not meanness alone; it was rushing and not really looking.",
        ),
        (
            f"What did {rusher.id} do to make things better?",
            f"{rusher.id} apologized and admitted that {deaf_child.id}'s idea was the better one. The apology softened the room first, and then they could work together again.",
        ),
        (
            f"How was the {item_cfg.label} fixed?",
            f"{elder.label_word.capitalize()} {repair_cfg.qa_text}. After that, the children finished the job in the right order, using the idea that had been missed before.",
        ),
        (
            "How did the story end?",
            f"It ended with the {item_cfg.label} safely in place and the children understanding each other again. The final image proves what changed: their hands slowed down, and the work became shared instead of tense.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    item_cfg = f["item_cfg"]
    bridge_cfg = f["bridge_cfg"]
    repair_cfg = f["repair_cfg"]
    tags: set[str] = {"deaf", "apology", "repair_magic"}
    if "communication" in bridge_cfg.tags:
        tags.add("signs")
    if "writing" in bridge_cfg.tags:
        tags.add("writing")
    if "steam" in bridge_cfg.tags:
        tags.add("steam")
    if item_cfg.material == "paper":
        tags.add("paper")
    if item_cfg.material == "cloth":
        tags.add("cloth")
    if item_cfg.material == "ceramic":
        tags.add("ceramic")
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
        if ent.deaf:
            bits.append("deaf=True")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="kitchen",
        item="paper_lantern",
        repair="paper_paste",
        bridge="steam_window",
        deaf_name="June",
        deaf_gender="girl",
        rusher_name="Eli",
        rusher_gender="boy",
        elder_type="grandmother",
        relation="cousins",
    ),
    StoryParams(
        place="hallway",
        item="quilt",
        repair="silver_thread",
        bridge="glow_ribbon",
        deaf_name="Milo",
        deaf_gender="boy",
        rusher_name="Ruby",
        rusher_gender="girl",
        elder_type="grandmother",
        relation="siblings",
    ),
    StoryParams(
        place="courtyard",
        item="teacup",
        repair="warm_glaze",
        bridge="slate",
        deaf_name="Nora",
        deaf_gender="girl",
        rusher_name="Finn",
        rusher_gender="boy",
        elder_type="grandmother",
        relation="cousins",
    ),
]


def explain_rejection(setting: Setting, item: ItemCfg, repair: RepairSpell, bridge: Bridge) -> str:
    if not repair_fits(item, repair):
        return (
            f"(No story: {repair.label} fixes {repair.fixes}, but the {item.label} is made of {item.material}. "
            f"The magic should suit the broken thing.)"
        )
    if not bridge_allowed(setting, bridge):
        allowed = ", ".join(sorted(setting.afford_bridges))
        return (
            f"(No story: {bridge.id} is not a good fit for {setting.place}. "
            f"That setting supports these communication bridges: {allowed}.)"
        )
    return "(No story: this combination is not reasonable.)"


ASP_RULES = r"""
repair_fits(I, R) :- item(I), repair(R), material(I, M), fixes(R, M).
bridge_ok(P, B)   :- setting(P), bridge(B), allows_bridge(P, B).

valid(P, I, R, B) :- setting(P), item(I), repair(R), bridge(B),
                     repair_fits(I, R), bridge_ok(P, B).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for bridge_id in sorted(setting.afford_bridges):
            lines.append(asp.fact("allows_bridge", place, bridge_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("material", item_id, item.material))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        lines.append(asp.fact("fixes", repair_id, repair.fixes))
    for bridge_id in BRIDGES:
        lines.append(asp.fact("bridge", bridge_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def _smoke_emit(sample: StorySample) -> None:
    if not sample.story or "idea" not in sample.story.lower() or "deaf" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story is missing expected seed words.")
    _ = sample.to_json()


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combo gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and serialized a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    rng = random.Random(123)
    parser = build_parser()
    try:
        for i in range(5):
            params = resolve_params(parser.parse_args([]), rng)
            params.seed = 123 + i
            sample = generate(params)
            _smoke_emit(sample)
        print("OK: random generation smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"RANDOM GENERATION FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a household disagreement, a deaf child with a good idea, and gentle magic that helps reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--bridge", choices=BRIDGES)
    ap.add_argument("--relation", choices=RELATIONS)
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle"], dest="elder_type")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.item and args.repair and args.bridge:
        setting = SETTINGS[args.place]
        item = ITEMS[args.item]
        repair = REPAIRS[args.repair]
        bridge = BRIDGES[args.bridge]
        if not (repair_fits(item, repair) and bridge_allowed(setting, bridge)):
            raise StoryError(explain_rejection(setting, item, repair, bridge))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.repair is None or combo[2] == args.repair)
        and (args.bridge is None or combo[3] == args.bridge)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, item_id, repair_id, bridge_id = rng.choice(sorted(combos))
    deaf_gender = rng.choice(["girl", "boy"])
    rusher_gender = rng.choice(["girl", "boy"])
    deaf_name = _pick_name(rng, deaf_gender)
    rusher_name = _pick_name(rng, rusher_gender, avoid=deaf_name)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    relation = args.relation or rng.choice(RELATIONS)

    return StoryParams(
        place=place,
        item=item_id,
        repair=repair_id,
        bridge=bridge_id,
        deaf_name=deaf_name,
        deaf_gender=deaf_gender,
        rusher_name=rusher_name,
        rusher_gender=rusher_gender,
        elder_type=elder_type,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    if params.bridge not in BRIDGES:
        raise StoryError(f"(Unknown bridge: {params.bridge})")
    if params.relation not in RELATIONS:
        raise StoryError(f"(Unknown relation: {params.relation})")

    setting = SETTINGS[params.place]
    item_cfg = ITEMS[params.item]
    repair_cfg = REPAIRS[params.repair]
    bridge_cfg = BRIDGES[params.bridge]
    if not (repair_fits(item_cfg, repair_cfg) and bridge_allowed(setting, bridge_cfg)):
        raise StoryError(explain_rejection(setting, item_cfg, repair_cfg, bridge_cfg))

    world = tell(
        setting=setting,
        item_cfg=item_cfg,
        repair_cfg=repair_cfg,
        bridge_cfg=bridge_cfg,
        deaf_name=params.deaf_name,
        deaf_gender=params.deaf_gender,
        rusher_name_value=params.rusher_name,
        rusher_gender=params.rusher_gender,
        elder_type=params.elder_type,
        relation=params.relation,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item, repair, bridge) combos:\n")
        for place, item, repair, bridge in combos:
            print(f"  {place:10} {item:14} {repair:14} {bridge}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.deaf_name} and {p.rusher_name}: {p.item} in {p.place} ({p.bridge}, {p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
