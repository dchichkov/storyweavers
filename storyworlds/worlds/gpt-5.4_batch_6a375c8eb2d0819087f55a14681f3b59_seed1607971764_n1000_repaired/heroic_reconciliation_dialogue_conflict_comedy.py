#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py
=============================================================================

A standalone story world about a silly, heroic pretend show almost falling apart
when two children quarrel over how the hero act should go. The world models
scarce props, hurt feelings, dialogue-based repairs, and a small comic middle
turn where the pretend city literally tips over because the children stop
working together.

Run it
------
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py --setting living_room --prop cape --conflict grabbing --fix make_copy
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py --prop helmet --fix make_copy
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py --all
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/heroic_reconciliation_dialogue_conflict_comedy.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    city_name: str
    materials: set[str] = field(default_factory=set)
    opening_detail: str = ""
    topple_detail: str = ""
    ending_image: str = ""
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
class Prop:
    id: str
    label: str
    phrase: str
    funny_detail: str
    copy_materials: set[str] = field(default_factory=set)
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
class ConflictMode:
    id: str
    label: str
    valid_fixes: set[str] = field(default_factory=set)
    first_line: str = ""
    second_line: str = ""
    effect: str = ""
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
class PeacePlan:
    id: str
    label: str
    kind: str
    needs_copy: bool = False
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"lead", "partner"}]


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


def _r_stall(world: World) -> list[str]:
    lead = world.get("lead")
    partner = world.get("partner")
    stage = world.get("stage")
    if stage.meters["stalled"] >= THRESHOLD:
        return []
    if (lead.memes["anger"] >= THRESHOLD or lead.memes["pride"] >= THRESHOLD) and (
        partner.memes["hurt"] >= THRESHOLD or partner.memes["anger"] >= THRESHOLD
    ):
        stage.meters["stalled"] += 1
        return ["__stall__"]
    return []


def _r_topple(world: World) -> list[str]:
    stage = world.get("stage")
    city = world.get("city")
    if stage.meters["stalled"] < THRESHOLD or city.meters["toppled"] >= THRESHOLD:
        return []
    city.meters["toppled"] += 1
    city.meters["messy"] += 1
    for kid in world.kids():
        kid.memes["embarrassment"] += 1
    return ["__topple__"]


CAUSAL_RULES = [
    Rule(name="stall", tag="social", apply=_r_stall),
    Rule(name="topple", tag="physical", apply=_r_topple),
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
        for item in produced:
            if item == "__topple__":
                world.say(world.setting.topple_detail)
    return produced


def copy_possible(setting: Setting, prop: Prop) -> bool:
    return bool(setting.materials & prop.copy_materials)


def valid_combo(setting_id: str, prop_id: str, conflict_id: str, fix_id: str) -> bool:
    if setting_id not in SETTINGS or prop_id not in PROPS or conflict_id not in CONFLICTS or fix_id not in FIXES:
        return False
    setting = SETTINGS[setting_id]
    prop = PROPS[prop_id]
    conflict = CONFLICTS[conflict_id]
    fix = FIXES[fix_id]
    if fix_id not in conflict.valid_fixes:
        return False
    if fix.needs_copy and not copy_possible(setting, prop):
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for prop_id in PROPS:
            for conflict_id in CONFLICTS:
                for fix_id in FIXES:
                    if valid_combo(setting_id, prop_id, conflict_id, fix_id):
                        out.append((setting_id, prop_id, conflict_id, fix_id))
    return out


def predict_topple(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.get("city").meters["toppled"] >= THRESHOLD


def introduce(world: World, lead: Entity, partner: Entity, setting: Setting, prop: Prop) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
        kid.memes["hope"] += 1
    world.say(
        f"After lunch, {lead.id} and {partner.id} turned {setting.place} into {setting.city_name}. "
        f"{setting.opening_detail}"
    )
    world.say(
        f"They were planning a heroic rescue show for the family, and the best prop of all was {prop.phrase}. "
        f"{prop.funny_detail}"
    )


def assign_roles(world: World, lead: Entity, partner: Entity, prop: Prop) -> None:
    world.say(
        f'"I can be the hero who swings in first," {lead.id} said. '
        f'"And I can do the giant rescue speech," {partner.id} said.'
    )
    world.say(f"For one happy minute, the whole game seemed ready to sparkle around the {prop.label}.")


def start_conflict(world: World, lead: Entity, partner: Entity, prop: Prop, conflict: ConflictMode) -> None:
    if conflict.id == "grabbing":
        lead.memes["anger"] += 1
        partner.memes["anger"] += 1
        world.get("prop").meters["rumpled"] += 1
        world.say(
            f'{lead.id} grabbed for the {prop.label} at the same moment {partner.id} did. '
            f'{conflict.first_line}'
        )
        world.say(conflict.second_line)
    elif conflict.id == "bragging":
        lead.memes["pride"] += 1
        partner.memes["hurt"] += 1
        world.say(
            f'{lead.id} puffed up very tall and said, {conflict.first_line}'
        )
        world.say(conflict.second_line)
    else:
        lead.memes["pride"] += 1
        partner.memes["hurt"] += 1
        world.say(
            f'{lead.id} kept talking over every idea. {conflict.first_line}'
        )
        world.say(conflict.second_line)

    if predict_topple(world):
        world.facts["predicted_topple"] = True
    propagate(world, narrate=True)
    if world.get("city").meters["toppled"] >= THRESHOLD:
        world.facts["turn_happened"] = True
        world.say(conflict.effect)


def repair_take_turns(world: World, lead: Entity, partner: Entity, prop: Prop) -> None:
    world.get("stage").meters["stalled"] = 0.0
    for kid in (lead, partner):
        kid.memes["relief"] += 1
        kid.memes["cooperation"] += 1
        kid.memes["anger"] = 0.0
    world.say(
        f'{partner.id} took a breath first. "We can both be heroes," {partner.pronoun()} said. '
        f'"You wear the {prop.label} for the first rescue, and then I wear it for the second."'
    )
    world.say(
        f'{lead.id} blinked, then nodded. "Two rescues are funnier than one," {lead.pronoun()} said, '
        f'and the quarrel loosened like a knot coming undone.'
    )
    world.facts["repair_method"] = "turns"


def repair_team_up(world: World, lead: Entity, partner: Entity, prop: Prop) -> None:
    world.get("stage").meters["stalled"] = 0.0
    for kid in (lead, partner):
        kid.memes["relief"] += 1
        kid.memes["cooperation"] += 1
        kid.memes["hurt"] = 0.0
        kid.memes["anger"] = 0.0
    lead.memes["kindness"] += 1
    partner.memes["kindness"] += 1
    world.say(
        f'{lead.id} looked at the crooked city and at {partner.id}\'s face. '
        f'"I was acting too big," {lead.pronoun()} admitted. "I want you on my team."'
    )
    world.say(
        f'{partner.id} answered right away. "Then let\'s do the rescue together. '
        f'You wear the {prop.label}, and I\'ll be the map-reader with the loudest warning voice."'
    )
    world.say(
        f'That made {lead.id} laugh. "A heroic hero needs a heroic helper," {lead.pronoun()} said.'
    )
    world.facts["repair_method"] = "team"


def repair_make_copy(world: World, lead: Entity, partner: Entity, setting: Setting, prop: Prop) -> None:
    world.get("stage").meters["stalled"] = 0.0
    for kid in (lead, partner):
        kid.memes["relief"] += 1
        kid.memes["cooperation"] += 1
        kid.memes["anger"] = 0.0
        kid.memes["hurt"] = 0.0
    material = sorted(setting.materials & prop.copy_materials)[0]
    copy_prop = world.add(
        Entity(
            id="copy_prop",
            type="prop",
            label=f"second {prop.label}",
            phrase=f"a second {prop.label}",
            attrs={"material": material},
            tags=set(prop.tags),
        )
    )
    copy_prop.meters["made"] += 1
    world.get("prop").meters["shared"] += 1
    world.say(
        f'{lead.id} rubbed the back of {lead.pronoun("possessive")} neck. "I don\'t want the show to stay grumpy," '
        f'{lead.pronoun()} said.'
    )
    world.say(
        f'{partner.id} spotted the {material} nearby and gasped. "Wait! We can make a second {prop.label}." '
        f'Together they folded, tucked, and tied until the room had not one but two ridiculous hero props.'
    )
    world.say(
        f'Soon they were both laughing so hard that the new {prop.label} almost fell sideways too.'
    )
    world.facts["repair_method"] = "copy"
    world.facts["copy_material"] = material


def rebuild(world: World, lead: Entity, partner: Entity) -> None:
    city = world.get("city")
    if city.meters["toppled"] >= THRESHOLD:
        city.meters["toppled"] = 0.0
        city.meters["rebuilt"] += 1
        world.say(
            f"First they set the city upright again, shelf by shelf and box by box, while both of them kept talking kindly."
        )


def finale(world: World, lead: Entity, partner: Entity, setting: Setting, prop: Prop, fix: PeacePlan) -> None:
    for kid in (lead, partner):
        kid.memes["joy"] += 1
        kid.memes["love"] += 1
    stage = world.get("stage")
    stage.meters["ready"] += 1
    method = world.facts.get("repair_method")
    if method == "turns":
        world.say(
            f'{lead.id} made the first rescue with the {prop.label}, diving over a pillow mountain to save the stuffed mayor. '
            f'Then {partner.id} took the {prop.label} and rescued the rubber duck from the cookie tin jail.'
        )
    elif method == "team":
        world.say(
            f'{lead.id} struck a brave pose in the {prop.label} while {partner.id} shouted directions so dramatically '
            f'that even the hallway echoed back. The rescue worked much better once both voices were part of it.'
        )
    else:
        material = world.facts.get("copy_material", "paper")
        world.say(
            f'With one {prop.label} each, they marched side by side through the city, saving the stuffed mayor and a spoon '
            f'that had somehow become a very worried moon. The homemade copy wobbled a little, which only made it funnier.'
        )
        world.facts["ending_material"] = material
    world.say(setting.ending_image)
    world.facts["reconciled"] = True


def tell(
    setting: Setting,
    prop: Prop,
    conflict: ConflictMode,
    fix: PeacePlan,
    lead_name: str = "Mia",
    lead_gender: str = "girl",
    partner_name: str = "Ben",
    partner_gender: str = "boy",
) -> World:
    world = World(setting)
    lead = world.add(
        Entity(
            id=lead_name,
            kind="character",
            type=lead_gender,
            role="lead",
            traits=["dramatic"],
            attrs={},
        )
    )
    partner = world.add(
        Entity(
            id=partner_name,
            kind="character",
            type=partner_gender,
            role="partner",
            traits=["quick"],
            attrs={},
        )
    )
    stage = world.add(
        Entity(
            id="stage",
            type="stage",
            label="the stage",
            attrs={},
        )
    )
    city = world.add(
        Entity(
            id="city",
            type="city",
            label=setting.city_name,
            attrs={},
        )
    )
    prop_ent = world.add(
        Entity(
            id="prop",
            type="prop",
            label=prop.label,
            phrase=prop.phrase,
            attrs={},
            tags=set(prop.tags),
        )
    )
    city.meters["upright"] = 1.0
    stage.meters["stalled"] = 0.0
    stage.meters["ready"] = 0.0
    prop_ent.meters["rumpled"] = 0.0
    world.facts.update(
        setting=setting,
        prop_cfg=prop,
        conflict=conflict,
        fix=fix,
        lead=lead,
        partner=partner,
        prop=prop_ent,
        turn_happened=False,
        predicted_topple=False,
        reconciled=False,
    )

    introduce(world, lead, partner, setting, prop)
    assign_roles(world, lead, partner, prop)

    world.para()
    start_conflict(world, lead, partner, prop, conflict)

    world.para()
    if fix.id == "take_turns":
        repair_take_turns(world, lead, partner, prop)
    elif fix.id == "team_up":
        repair_team_up(world, lead, partner, prop)
    else:
        repair_make_copy(world, lead, partner, setting, prop)
    rebuild(world, lead, partner)
    world.para()
    finale(world, lead, partner, setting, prop, fix)
    return world


SETTINGS = {
    "living_room": Setting(
        id="living_room",
        place="the living room",
        city_name="Cardboard City",
        materials={"paper", "towel"},
        opening_detail="A row of couch cushions became rooftops, a laundry basket became a volcano, and a spoon stood up in a mug as the city's silver moon.",
        topple_detail="Just then one shoebox tower leaned, wobbled twice, and folded into the volcano basket with a very tired flop.",
        ending_image="By the end, the family was laughing, and the once-wobbly city looked proud again under the lamp light.",
        tags={"cardboard", "teamwork"},
    ),
    "hallway": Setting(
        id="hallway",
        place="the hallway",
        city_name="Cape Corner",
        materials={"paper"},
        opening_detail="Shoes became mountain caves along the wall, a blanket bridge crossed the rug, and the umbrella stand was promoted to a very serious castle.",
        topple_detail="Then the blanket bridge slid off the rug and the castle of shoes clapped shut with a silly thump.",
        ending_image="Soon the hallway sounded less like a quarrel and more like a parade, with feet pattering and giggles bouncing off the walls.",
        tags={"parade", "teamwork"},
    ),
    "backyard": Setting(
        id="backyard",
        place="the backyard",
        city_name="Chalk Rescue Town",
        materials=set(),
        opening_detail="Chalk roads curled across the stones, a flowerpot became the mayor's tower, and a garden shovel was announced as the emergency rocket.",
        topple_detail="A chalk sign tipped over the flowerpot, and even the rocket shovel looked embarrassed to be part of the mess.",
        ending_image="When the show finally worked, the chalk town glowed in the late sun and both children bowed so low they almost toppled again.",
        tags={"chalk", "teamwork"},
    ),
}

PROPS = {
    "cape": Prop(
        id="cape",
        label="cape",
        phrase="the only red cape",
        funny_detail="It was so shiny and swishy that even walking to the sofa made a person feel three inches taller.",
        copy_materials={"towel"},
        tags={"cape", "heroic"},
    ),
    "badge": Prop(
        id="badge",
        label="badge",
        phrase="the only gold-paper badge",
        funny_detail="It was really a circle of glitter paper with tape on the back, but it looked important enough to boss around the curtains.",
        copy_materials={"paper"},
        tags={"badge", "heroic"},
    ),
    "helmet": Prop(
        id="helmet",
        label="helmet",
        phrase="the only brave-looking helmet",
        funny_detail="It made whoever wore it sound a little echoey, which somehow made every line twice as serious and three times as funny.",
        copy_materials=set(),
        tags={"helmet", "heroic"},
    ),
}

CONFLICTS = {
    "grabbing": ConflictMode(
        id="grabbing",
        label="grabbing the same prop",
        valid_fixes={"take_turns", "make_copy"},
        first_line='"Mine first!" "No, mine first!"',
        second_line="The prop twisted between their hands, and the rescue show stopped before the rescue had even started.",
        effect="For a moment they both stared at the mess, because it is hard to look heroic while standing in the middle of your own flop.",
        tags={"sharing", "conflict"},
    ),
    "bragging": ConflictMode(
        id="bragging",
        label="one child bragging too much",
        valid_fixes={"team_up", "make_copy"},
        first_line='"I should do the whole rescue myself, because I am the most heroic one here."',
        second_line="That made the room go quiet in the wrong way. The game did not feel sparkly anymore; it felt squashed.",
        effect="The fallen city made the brag sound even sillier, which was useful, because silly moments are good at popping proud balloons.",
        tags={"apology", "conflict"},
    ),
    "interrupting": ConflictMode(
        id="interrupting",
        label="talking over every idea",
        valid_fixes={"team_up"},
        first_line='Every time {partner} opened {poss} mouth, another speech zoomed in first.',
        second_line="Soon nobody knew the rescue plan, because one voice had become too big and the other had become too small.",
        effect="The flop in the middle of the set proved what the arguing voices already knew: a rescue show cannot be rescued by only one mouth.",
        tags={"dialogue", "conflict"},
    ),
}

FIXES = {
    "take_turns": PeacePlan(
        id="take_turns",
        label="take turns with the prop",
        kind="turns",
        needs_copy=False,
        tags={"sharing", "dialogue"},
    ),
    "team_up": PeacePlan(
        id="team_up",
        label="talk, apologize, and split the jobs",
        kind="team",
        needs_copy=False,
        tags={"dialogue", "apology", "teamwork"},
    ),
    "make_copy": PeacePlan(
        id="make_copy",
        label="make a second silly version",
        kind="copy",
        needs_copy=True,
        tags={"craft", "dialogue", "sharing"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Ruby", "Nora", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Finn", "Theo", "Sam", "Jack", "Noah"]


@dataclass
class StoryParams:
    setting: str
    prop: str
    conflict: str
    fix: str
    lead_name: str
    lead_gender: str
    partner_name: str
    partner_gender: str
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
    "cape": [
        (
            "What is a cape?",
            "A cape is a piece of cloth that hangs from your shoulders. In pretend play, it can make someone feel brave and dramatic, even though it is really just cloth.",
        )
    ],
    "badge": [
        (
            "What is a badge?",
            "A badge is a sign that shows a role or job. In pretend play, a paper badge can help children imagine they are rescuers, helpers, or guards.",
        )
    ],
    "helmet": [
        (
            "What is a helmet for in real life?",
            "A real helmet protects your head. In games, children sometimes use a costume helmet to pretend, but a real safety helmet is for keeping people safer.",
        )
    ],
    "sharing": [
        (
            "What does taking turns mean?",
            "Taking turns means one person uses something first and another person uses it after. It helps people share when there is only one of something.",
        )
    ],
    "dialogue": [
        (
            "What is dialogue?",
            "Dialogue means people talking and listening to each other. Good dialogue helps solve problems because everyone gets a turn to say what they mean.",
        )
    ],
    "apology": [
        (
            "What is an apology?",
            "An apology is when you say you are sorry for something hurtful and try to make it better. A real apology helps feelings begin to mend.",
        )
    ],
    "teamwork": [
        (
            "Why is teamwork useful?",
            "Teamwork helps people do a job together instead of pulling in different directions. When people cooperate, the work often becomes easier and more fun.",
        )
    ],
    "craft": [
        (
            "Why do people make a copy in a craft project?",
            "Making a copy can solve a sharing problem when there is only one object. If the materials are safe and simple, a homemade second version can help everyone join in.",
        )
    ],
    "cardboard": [
        (
            "Why do cardboard towers fall over easily?",
            "Cardboard boxes are light, so they can wobble if nobody steadies them. That is why pretend cities made from boxes need careful hands.",
        )
    ],
    "chalk": [
        (
            "What is chalk used for outside?",
            "Sidewalk chalk is used for drawing on stone or pavement. It washes away later, so it is good for temporary pictures and games.",
        )
    ],
    "parade": [
        (
            "What is a parade?",
            "A parade is when people move along together in a cheerful line. They might wave, march, play music, or show costumes.",
        )
    ],
}
KNOWLEDGE_ORDER = ["cape", "badge", "helmet", "sharing", "dialogue", "apology", "teamwork", "craft", "cardboard", "chalk", "parade"]


CURATED = [
    StoryParams(
        setting="living_room",
        prop="cape",
        conflict="grabbing",
        fix="make_copy",
        lead_name="Mia",
        lead_gender="girl",
        partner_name="Ben",
        partner_gender="boy",
    ),
    StoryParams(
        setting="hallway",
        prop="badge",
        conflict="bragging",
        fix="team_up",
        lead_name="Theo",
        lead_gender="boy",
        partner_name="Lily",
        partner_gender="girl",
    ),
    StoryParams(
        setting="backyard",
        prop="helmet",
        conflict="grabbing",
        fix="take_turns",
        lead_name="Ava",
        lead_gender="girl",
        partner_name="Max",
        partner_gender="boy",
    ),
    StoryParams(
        setting="living_room",
        prop="badge",
        conflict="interrupting",
        fix="team_up",
        lead_name="Noah",
        lead_gender="boy",
        partner_name="Ruby",
        partner_gender="girl",
    ),
    StoryParams(
        setting="hallway",
        prop="badge",
        conflict="grabbing",
        fix="make_copy",
        lead_name="Ella",
        lead_gender="girl",
        partner_name="Finn",
        partner_gender="boy",
    ),
]


def explain_rejection(setting_id: str, prop_id: str, conflict_id: str, fix_id: str) -> str:
    if setting_id not in SETTINGS:
        return f"(No story: unknown setting '{setting_id}'.)"
    if prop_id not in PROPS:
        return f"(No story: unknown prop '{prop_id}'.)"
    if conflict_id not in CONFLICTS:
        return f"(No story: unknown conflict '{conflict_id}'.)"
    if fix_id not in FIXES:
        return f"(No story: unknown fix '{fix_id}'.)"
    setting = SETTINGS[setting_id]
    prop = PROPS[prop_id]
    conflict = CONFLICTS[conflict_id]
    fix = FIXES[fix_id]
    if fix_id not in conflict.valid_fixes:
        return (
            f"(No story: '{fix_id}' does not honestly solve the conflict '{conflict_id}'. "
            f"This quarrel needs a different kind of repair.)"
        )
    if fix.needs_copy and not copy_possible(setting, prop):
        mats = ", ".join(sorted(setting.materials)) if setting.materials else "no handy craft materials"
        needed = ", ".join(sorted(prop.copy_materials)) if prop.copy_materials else "no simple copy material"
        return (
            f"(No story: {setting.place} has {mats}, but a second {prop.label} would need {needed}. "
            f"A copy fix only works when the setting really has materials for it.)"
        )
    return "(No story: this combination is unreasonable.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    prop = f["prop_cfg"]
    conflict = f["conflict"]
    setting = f["setting"]
    fix = f["fix"]
    return [
        f'Write a short comedy for a 3-to-5-year-old that includes the word "heroic" and shows two children having a conflict during pretend play.',
        f"Tell a funny story where {lead.id} and {partner.id} turn {setting.place} into a rescue stage, quarrel over a {prop.label}, and reconcile through dialogue.",
        f"Write a child-facing story where the conflict is {conflict.label}, the repair is {fix.label}, and the ending proves the children can play together again.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    lead = f["lead"]
    partner = f["partner"]
    prop = f["prop_cfg"]
    setting = f["setting"]
    conflict = f["conflict"]
    fix = f["fix"]
    repair_method = f.get("repair_method", "")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {lead.id} and {partner.id}, two children making a funny heroic rescue show together. They turn {setting.place} into a pretend city and try to be the stars of it.",
        ),
        (
            "What caused the problem?",
            f"The problem started because the conflict was {conflict.label} and the children stopped working together. Their feelings got in the way of the game, so the show stalled instead of sparkling.",
        ),
        (
            "What happened in the middle of the story when they argued?",
            f"The pretend city toppled over while they were upset with each other. That silly flop showed them that the game needed both of them, not just louder arguing.",
        ),
    ]
    if repair_method == "turns":
        qa.append(
            (
                "How did they make peace?",
                f"They used dialogue to agree on taking turns with the {prop.label}. One child spoke first about a fair plan, and the other child accepted it, so the conflict could soften into cooperation.",
            )
        )
    elif repair_method == "team":
        qa.append(
            (
                "How did they reconcile after the conflict?",
                f"They talked honestly, and {lead.id} admitted the problem instead of pretending nothing was wrong. Then they split the jobs in a way that made both children important, which turned hurt feelings into teamwork.",
            )
        )
    else:
        material = f.get("copy_material", "something nearby")
        qa.append(
            (
                "How did they solve the sharing problem?",
                f"They used dialogue and made a second silly version of the {prop.label} from {material}. That worked because the new copy gave both children a way back into the game at the same time.",
            )
        )
    qa.append(
        (
            "How do you know the ending is happy?",
            f"The children finish the show together and laugh again, which proves the quarrel has changed into reconciliation. The final rescue works because they are cooperating instead of fighting.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["prop_cfg"].tags)
    tags |= set(f["fix"].tags)
    tags |= set(f["setting"].tags)
    tags |= set(f["conflict"].tags)
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
copy_possible(S, P) :- material(S, M), copy_material(P, M).

valid(S, P, C, F) :- setting(S), prop(P), conflict(C), fix(F),
                     works_for(F, C), not requires_copy(F).

valid(S, P, C, F) :- setting(S), prop(P), conflict(C), fix(F),
                     works_for(F, C), requires_copy(F), copy_possible(S, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for material in sorted(setting.materials):
            lines.append(asp.fact("material", sid, material))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        for material in sorted(prop.copy_materials):
            lines.append(asp.fact("copy_material", pid, material))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        if fix.needs_copy:
            lines.append(asp.fact("requires_copy", fid))
    for cid, conflict in CONFLICTS.items():
        for fid in sorted(conflict.valid_fixes):
            lines.append(asp.fact("works_for", fid, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        random_case = resolve_params(build_parser().parse_args([]), random.Random(17))
        smoke_cases.append(random_case)
    except StoryError as err:
        rc = 1
        print("SMOKE FAIL: resolve_params() crashed on defaults:", err)

    for idx, params in enumerate(smoke_cases, 1):
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("generated empty story")
            emit(sample, trace=False, qa=False, header=f"### smoke {idx}")
        except Exception as err:
            rc = 1
            print(f"SMOKE FAIL on case {idx}: {err}")

    if rc == 0:
        print("OK: smoke generation succeeded.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a heroic pretend show, a comic conflict, and a dialogue-based reconciliation."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--lead")
    ap.add_argument("--partner")
    ap.add_argument("--lead-gender", choices=["girl", "boy"])
    ap.add_argument("--partner-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, prop, conflict, fix) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.prop and args.conflict and args.fix:
        if not valid_combo(args.setting, args.prop, args.conflict, args.fix):
            raise StoryError(explain_rejection(args.setting, args.prop, args.conflict, args.fix))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.prop is None or combo[1] == args.prop)
        and (args.conflict is None or combo[2] == args.conflict)
        and (args.fix is None or combo[3] == args.fix)
    ]
    if not combos:
        setting = args.setting or next(iter(SETTINGS))
        prop = args.prop or next(iter(PROPS))
        conflict = args.conflict or next(iter(CONFLICTS))
        fix = args.fix or next(iter(FIXES))
        raise StoryError(explain_rejection(setting, prop, conflict, fix))

    setting_id, prop_id, conflict_id, fix_id = rng.choice(sorted(combos))
    lead_gender = args.lead_gender or rng.choice(["girl", "boy"])
    partner_gender = args.partner_gender or rng.choice(["girl", "boy"])
    lead_name = args.lead or _pick_name(rng, lead_gender)
    partner_name = args.partner or _pick_name(rng, partner_gender, avoid=lead_name)
    return StoryParams(
        setting=setting_id,
        prop=prop_id,
        conflict=conflict_id,
        fix=fix_id,
        lead_name=lead_name,
        lead_gender=lead_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def _conflict_with_names(conflict: ConflictMode, partner: Entity) -> ConflictMode:
    if conflict.id != "interrupting":
        return conflict
    return ConflictMode(
        id=conflict.id,
        label=conflict.label,
        valid_fixes=set(conflict.valid_fixes),
        first_line=conflict.first_line.format(partner=partner.id, poss=partner.pronoun("possessive")),
        second_line=conflict.second_line,
        effect=conflict.effect,
        tags=set(conflict.tags),
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.setting, params.prop, params.conflict, params.fix):
        raise StoryError(explain_rejection(params.setting, params.prop, params.conflict, params.fix))

    setting = SETTINGS[params.setting]
    prop = PROPS[params.prop]
    conflict = CONFLICTS[params.conflict]
    fix = FIXES[params.fix]
    partner_stub = Entity(id=params.partner_name, kind="character", type=params.partner_gender, role="partner")
    conflict = _conflict_with_names(conflict, partner_stub)

    world = tell(
        setting=setting,
        prop=prop,
        conflict=conflict,
        fix=fix,
        lead_name=params.lead_name,
        lead_gender=params.lead_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
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
        print(f"{len(combos)} compatible (setting, prop, conflict, fix) combos:\n")
        for setting, prop, conflict, fix in combos:
            print(f"  {setting:12} {prop:7} {conflict:11} {fix}")
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
            header = f"### {p.lead_name} & {p.partner_name}: {p.prop}, {p.conflict}, {p.fix} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
