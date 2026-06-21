#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py
================================================================================

A standalone story world about a child detective learning that a decent
detective checks facts before blaming anyone.

The tiny domain:
- A child is playing detective after a small treasured object goes missing.
- A first clue points toward an innocent suspect.
- The detective feels tempted to accuse too quickly.
- A careful check reveals the real cause.
- The ending is either an averted accusation or a repaired mistake with an apology.

This world keeps the tone child-facing and concrete, but the style leans gently
toward detective fiction: clues, suspects, a notebook, a magnifying glass, and
quiet inner monologue.

Run it
------
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --setting classroom --clue glitter --cause spill
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --cause squirrel
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --all
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --trace
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --json
    python storyworlds/worlds/gpt-5.4/decent_inner_monologue_cautionary_detective_story.py --verify
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
CAREFUL_TRAITS = {"patient", "careful", "fair", "thoughtful", "decent"}


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
        female = {"girl", "mother", "woman", "teacher"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "teacher": "teacher"}.get(self.type, self.type)
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
    nook: str
    keeper_type: str
    keeper_label: str
    surface: str
    ambience: str
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
class MissingThing:
    id: str
    label: str
    phrase: str
    special: str
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
    found_text: str
    points_to_role: str
    suspect_line: str
    thought_line: str
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
class Cause:
    id: str
    label: str
    reveal_text: str
    location_text: str
    trace_text: str
    true_role: str
    needs_method: str
    happy_end: str
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
class CheckMethod:
    id: str
    label: str
    action_text: str
    discover_text: str
    power_roles: set[str] = field(default_factory=set)
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


def _r_hurt_from_blame(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    if detective.meters["accused"] < THRESHOLD:
        return []
    sig = ("hurt_from_blame", suspect.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    suspect.memes["hurt"] += 1
    detective.memes["guilt"] += 1
    return ["__hurt__"]


def _r_relief_after_truth(world: World) -> list[str]:
    detective = world.get("detective")
    suspect = world.get("suspect")
    if world.facts.get("truth_found") != 1:
        return []
    sig = ("relief_after_truth", detective.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    detective.memes["relief"] += 1
    suspect.memes["relief"] += 1
    return ["__relief__"]


CAUSAL_RULES = [
    Rule(name="hurt_from_blame", tag="social", apply=_r_hurt_from_blame),
    Rule(name="relief_after_truth", tag="social", apply=_r_relief_after_truth),
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
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def clue_matches_cause(clue: Clue, cause: Cause) -> bool:
    return clue.points_to_role != cause.true_role


def method_finds_cause(method: CheckMethod, cause: Cause) -> bool:
    return cause.needs_method == method.id and cause.true_role in method.power_roles


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for thing_id in MISSING_THINGS:
            for clue_id, clue in CLUES.items():
                for cause_id, cause in CAUSES.items():
                    if not clue_matches_cause(clue, cause):
                        continue
                    for method_id, method in METHODS.items():
                        if method_finds_cause(method, cause):
                            combos.append((setting_id, thing_id, clue_id, cause_id, method_id))
    return combos


def careful_threshold(trait: str) -> int:
    return 3 if trait in CAREFUL_TRAITS else 1


def would_accuse(trait: str, helper_support: int) -> bool:
    return careful_threshold(trait) + helper_support < 4


def predict_hurt(world: World) -> dict:
    sim = world.copy()
    sim.get("detective").meters["accused"] += 1
    propagate(sim, narrate=False)
    return {
        "suspect_hurt": sim.get("suspect").memes["hurt"] >= THRESHOLD,
        "detective_guilt": sim.get("detective").memes["guilt"] >= THRESHOLD,
    }


def introduce(world: World, detective: Entity, helper: Entity, keeper: Entity,
              thing: MissingThing) -> None:
    detective.memes["curious"] += 1
    detective.memes["pride"] += 1
    world.say(
        f"After morning play, {detective.id} set up a tiny detective office in {world.setting.place}. "
        f"{world.setting.ambience} {detective.pronoun().capitalize()} had a stubby pencil, a notebook, "
        f"and a magnifying glass that made every speck look important."
    )
    world.say(
        f"In the middle of the desk sat {thing.phrase}. {detective.id} loved it because {thing.special}."
    )
    world.say(
        f'"Casebook ready," {detective.id} whispered. In {detective.pronoun("possessive")} head, '
        f'{detective.pronoun()} added, "A decent detective notices the small things."'
    )


def vanish(world: World, detective: Entity, helper: Entity, keeper: Entity,
           thing: MissingThing) -> None:
    thing_ent = world.get("missing")
    thing_ent.meters["missing"] += 1
    detective.memes["alarm"] += 1
    world.say(
        f"But when {detective.id} turned to show {helper.id} one shiny page, {thing.label} was gone."
    )
    world.say(
        f'{detective.id} stared at the empty {world.setting.surface}. '
        f'In a small, fast thought, {detective.pronoun()} told {detective.pronoun("object")}, '
        f'"Something happened in this room, and I am going to solve it."'
    )


def find_clue(world: World, detective: Entity, clue: Clue) -> None:
    world.facts["first_clue"] = clue.id
    world.say(
        f"Near {world.setting.nook}, {detective.id} found {clue.found_text}. "
        f"{clue.suspect_line}"
    )
    world.say(
        f'Inside, {detective.pronoun()} thought, "{clue.thought_line}"'
    )


def helper_warning(world: World, detective: Entity, helper: Entity, suspect: Entity) -> None:
    pred = predict_hurt(world)
    world.facts["predicted_hurt"] = int(pred["suspect_hurt"])
    helper.memes["care"] += 1
    extra = " and squeezed the little notebook shut for a moment" if pred["suspect_hurt"] else ""
    world.say(
        f'{helper.id} looked at {detective.id}{extra}. "{suspect.id} might not have done it," '
        f'{helper.pronoun()} said. "A clue is not the same as proof."'
    )


def accuse(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    detective.meters["accused"] += 1
    detective.memes["certainty"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{detective.id} marched over to {suspect.id}. "{clue.label.capitalize()}! '
        f'That means you took it," {detective.pronoun()} said.'
    )
    if suspect.memes["hurt"] >= THRESHOLD:
        world.say(
            f"{suspect.id}'s face fell. {suspect.pronoun().capitalize()} had only come to help, "
            f"and now {suspect.pronoun()} looked as if a door had shut inside {suspect.pronoun('object')}."
        )


def pause_instead(world: World, detective: Entity, helper: Entity) -> None:
    detective.memes["care"] += 1
    detective.memes["restraint"] += 1
    world.say(
        f"{detective.id} took one breath, then another. In {detective.pronoun('possessive')} mind, "
        f"{detective.pronoun()} changed the case note from blame to question."
    )
    world.say(
        f'"I need one more clue before I talk big," {detective.pronoun()} murmured.'
    )


def investigate(world: World, detective: Entity, helper: Entity, method: CheckMethod,
                cause: Cause) -> None:
    detective.meters["searched"] += 1
    world.say(
        f"{detective.id} and {helper.id} {method.action_text}."
    )
    world.say(
        f"{method.discover_text} {cause.trace_text}"
    )


def reveal(world: World, detective: Entity, keeper: Entity, thing: MissingThing,
           cause: Cause) -> None:
    thing_ent = world.get("missing")
    thing_ent.meters["missing"] = 0.0
    thing_ent.meters["found"] += 1
    world.facts["truth_found"] = 1
    propagate(world, narrate=False)
    world.say(
        f"There it was: {cause.location_text}, with {thing.label} safe at last. {cause.reveal_text}"
    )


def apology(world: World, detective: Entity, suspect: Entity) -> None:
    detective.memes["guilt"] += 1
    detective.memes["fairness"] += 1
    suspect.memes["hurt"] = 0.0
    suspect.memes["forgiven"] += 1
    world.say(
        f'{detective.id} turned to {suspect.id} at once. "I am sorry I blamed you before I knew the truth," '
        f'{detective.pronoun()} said. "That was not decent detective work."'
    )
    world.say(
        f"{suspect.id} gave a slow nod. The hard look in {suspect.pronoun('possessive')} eyes softened "
        f"because the apology came quickly and honestly."
    )


def lesson(world: World, detective: Entity, helper: Entity, keeper: Entity,
           cause: Cause, suspect: Entity, thing: MissingThing) -> None:
    detective.memes["lesson"] += 1
    keeper.memes["approval"] += 1
    world.say(
        f'{keeper.label_word.capitalize()} smiled at the little team. "Mysteries do need brave eyes," '
        f'{keeper.pronoun()} said, "but they also need fair hearts."'
    )
    world.say(
        f"In {detective.pronoun('possessive')} head, the lesson clicked into place: "
        f'"A decent detective follows facts, not just first feelings."'
    )
    world.say(
        cause.happy_end
    )


def tell(setting: Setting, thing: MissingThing, clue: Clue, cause: Cause, method: CheckMethod,
         detective_name: str = "Nora", detective_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         suspect_name: str = "Ivy", suspect_gender: str = "girl",
         trait: str = "careful", helper_support: int = 2) -> World:
    world = World(setting)
    world.facts["truth_found"] = 0
    world.facts["predicted_hurt"] = 0

    detective = world.add(Entity(
        id=detective_name,
        kind="character",
        type=detective_gender,
        role="detective",
        traits=[trait],
        attrs={"helper_support": helper_support},
        tags={"detective"},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        traits=["steady"],
        attrs={"support": helper_support},
        tags={"helper"},
    ))
    suspect = world.add(Entity(
        id=suspect_name,
        kind="character",
        type=suspect_gender,
        role=clue.points_to_role,
        traits=["helpful"],
        tags={clue.points_to_role},
    ))
    keeper = world.add(Entity(
        id="Keeper",
        kind="character",
        type=setting.keeper_type,
        role="keeper",
        label=setting.keeper_label,
        tags={"adult"},
    ))
    missing = world.add(Entity(
        id="missing",
        kind="thing",
        type="object",
        label=thing.label,
        attrs={"special": thing.special},
        tags=set(thing.tags),
    ))

    detective.memes["care"] = float(careful_threshold(trait))
    helper.memes["support"] = float(helper_support)
    suspect.memes["hurt"] = 0.0
    missing.meters["missing"] = 0.0
    world.facts["detective"] = detective
    world.facts["helper"] = helper
    world.facts["suspect"] = suspect
    world.facts["keeper"] = keeper
    world.facts["thing_cfg"] = thing
    world.facts["clue_cfg"] = clue
    world.facts["cause_cfg"] = cause
    world.facts["method_cfg"] = method
    world.facts["setting_cfg"] = setting

    introduce(world, detective, helper, keeper, thing)
    world.para()
    vanish(world, detective, helper, keeper, thing)
    find_clue(world, detective, clue)
    helper_warning(world, detective, helper, suspect)

    rash = would_accuse(trait, helper_support)
    world.facts["rash"] = int(rash)

    world.para()
    if rash:
        accuse(world, detective, suspect, clue)
    else:
        pause_instead(world, detective, helper)

    investigate(world, detective, helper, method, cause)

    world.para()
    reveal(world, detective, keeper, thing, cause)
    if rash:
        apology(world, detective, suspect)
    lesson(world, detective, helper, keeper, cause, suspect, thing)

    world.facts["outcome"] = "apology" if rash else "averted"
    return world


SETTINGS = {
    "classroom": Setting(
        id="classroom",
        place="the sunny classroom",
        nook="the reading rug",
        keeper_type="teacher",
        keeper_label="the teacher",
        surface="cubby shelf",
        ambience="Sunlight made bright squares on the floor, and the room smelled faintly of crayons.",
        tags={"classroom"},
    ),
    "clubhouse": Setting(
        id="clubhouse",
        place="the little backyard clubhouse",
        nook="the corner bench",
        keeper_type="mother",
        keeper_label="the mom",
        surface="crate table",
        ambience="The wooden walls held warm afternoon light, and the floor creaked with every tiny step.",
        tags={"clubhouse"},
    ),
    "library": Setting(
        id="library",
        place="the quiet library corner",
        nook="the beanbag nook",
        keeper_type="teacher",
        keeper_label="the librarian",
        surface="low return cart",
        ambience="Everything sounded hushed there, even the turning of one paper page.",
        tags={"library"},
    ),
}

MISSING_THINGS = {
    "sticker_book": MissingThing(
        id="sticker_book",
        label="the sticker book",
        phrase="a sticker book with silver stars on the cover",
        special="every solved puzzle earned one more star inside",
        tags={"stickers"},
    ),
    "marble_pouch": MissingThing(
        id="marble_pouch",
        label="the marble pouch",
        phrase="a velvet marble pouch with a gold drawstring",
        special="the marbles clicked together like secret clues",
        tags={"marbles"},
    ),
    "stamp_card": MissingThing(
        id="stamp_card",
        label="the stamp card",
        phrase="a card of bright animal stamps tucked in a clear sleeve",
        special="each stamp came from a different nice day out",
        tags={"stamps"},
    ),
}

CLUES = {
    "glitter": Clue(
        id="glitter",
        label="glitter on the floor",
        found_text="a bright pinch of glitter on the floor",
        points_to_role="craft_child",
        suspect_line="That was the sort of sparkle Ivy always had on her sleeves after art time.",
        thought_line="Glitter means craft table, and craft table means Ivy. This case may already be solved.",
        tags={"glitter", "clue"},
    ),
    "leaf": Clue(
        id="leaf",
        label="a green leaf by the shelf",
        found_text="a fresh green leaf by the shelf",
        points_to_role="garden_child",
        suspect_line="Leo loved pockets full of leaves, so the clue pointed straight at him.",
        thought_line="A leaf belongs to the garden trail, and Leo was there this morning.",
        tags={"leaf", "clue"},
    ),
    "crumbs": Clue(
        id="crumbs",
        label="cookie crumbs near the desk",
        found_text="cookie crumbs near the desk",
        points_to_role="snack_child",
        suspect_line="Maya had been carrying snack napkins just before clean-up time.",
        thought_line="Crumbs mean snack, and snack means Maya. It feels neat and simple.",
        tags={"crumbs", "clue"},
    ),
}

CAUSES = {
    "spill": Cause(
        id="spill",
        label="slipped into the paper bin",
        reveal_text="A tipped stack of drawing paper had hidden it from sight instead of stealing it away.",
        location_text="half under the paper bin",
        trace_text="A trail of bent papers showed where a quick elbow had nudged it off the shelf.",
        true_role="accident",
        needs_method="track",
        happy_end="Soon the case notes ended with a much better line: the object was found, no friend was blamed, and the little detective office felt wiser than before.",
        tags={"accident"},
    ),
    "squirrel": Cause(
        id="squirrel",
        label="carried by a squirrel",
        reveal_text="A cheeky squirrel had tugged the ribboned corner through the open window and dropped it nearby when it was too awkward to carry.",
        location_text="behind a flowerpot outside the window",
        trace_text="Tiny scratch marks on the sill led right to the open window.",
        true_role="animal",
        needs_method="window",
        happy_end="When they closed the window and laughed in relief, the mystery felt exciting without feeling mean, and that was a much better kind of detective ending.",
        tags={"animal"},
    ),
    "tidy": Cause(
        id="tidy",
        label="put away by the grown-up",
        reveal_text="The grown-up had tucked it somewhere safe during clean-up, not knowing a whole mystery had started around it.",
        location_text="inside the lost-and-found basket",
        trace_text="A neat note in the grown-up's handwriting sat beside the basket.",
        true_role="adult",
        needs_method="ask",
        happy_end="The case ended with everyone smiling at the small mix-up, and the detective notebook gained a new rule written in careful letters.",
        tags={"adult_action"},
    ),
}

METHODS = {
    "track": CheckMethod(
        id="track",
        label="follow the trail on the floor",
        action_text="crouched low and followed the little trail on the floor instead of the first guess in their heads",
        discover_text="Under the next stack, the signs lined up properly.",
        power_roles={"accident"},
        tags={"tracking"},
    ),
    "window": CheckMethod(
        id="window",
        label="check the window ledge",
        action_text="walked to the window and examined the ledge, the latch, and the dust there",
        discover_text="On the sill they found the second clue they really needed.",
        power_roles={"animal"},
        tags={"window"},
    ),
    "ask": CheckMethod(
        id="ask",
        label="ask the grown-up who tidied",
        action_text="went straight to the grown-up and asked what had been moved during clean-up",
        discover_text="The answer came with a surprised smile and a pointed finger toward the basket.",
        power_roles={"adult"},
        tags={"asking"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Ava", "Ella", "Ivy", "Maya", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Theo", "Finn", "Jack", "Noah", "Eli", "Owen"]
TRAITS = ["careful", "patient", "fair", "thoughtful", "decent", "hasty", "proud", "eager"]


@dataclass
class StoryParams:
    setting: str
    missing_thing: str
    clue: str
    cause: str
    method: str
    detective_name: str
    detective_gender: str
    helper_name: str
    helper_gender: str
    suspect_name: str
    suspect_gender: str
    trait: str
    helper_support: int = 2
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
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and asks careful questions to learn what really happened. A good detective does not decide too quickly."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you understand something. One clue can help, but you usually need more than one before you are sure."
        )
    ],
    "glitter": [
        (
            "Why can glitter be a tricky clue?",
            "Glitter can stick to many things and travel from place to place. That means it may show where someone has been, but not always what they did."
        )
    ],
    "leaf": [
        (
            "How can a leaf get indoors?",
            "A leaf can blow in through a door or window, or it can hitch a ride on a shoe or sleeve. That is why a leaf is only one clue, not the whole answer."
        )
    ],
    "crumbs": [
        (
            "Why are crumbs not perfect proof?",
            "Crumbs show that food was nearby, but they do not tell the whole story by themselves. Someone could have walked past with a snack and not taken anything."
        )
    ],
    "apology": [
        (
            "Why is it important to apologize after blaming someone unfairly?",
            "An apology helps repair hurt feelings and shows that you know your mistake mattered. Saying sorry quickly and honestly is part of being fair."
        )
    ],
    "animal": [
        (
            "Why do animals sometimes carry things away?",
            "Some animals grab bright or interesting objects because they are curious. They do not understand that the thing belongs to someone."
        )
    ],
    "adult_action": [
        (
            "Why do grown-ups sometimes put things in a safe place?",
            "Grown-ups often tidy up to keep objects from getting lost or damaged. Sometimes that can look mysterious until someone asks where the object was moved."
        )
    ],
}
KNOWLEDGE_ORDER = ["detective", "clue", "glitter", "leaf", "crumbs", "animal", "adult_action", "apology"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    clue = f["clue_cfg"]
    thing = f["thing_cfg"]
    cause = f["cause_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a short detective story for a 3-to-5-year-old about a missing object, a misleading clue, '
        f'and a child who learns to be a decent detective. Include the word "decent".'
    )
    if outcome == "apology":
        return [
            base,
            f"Tell a cautionary mystery where {detective.id} finds {clue.label} and almost solves the case too fast, "
            f"then apologizes after learning what really happened to {thing.label}.",
            f"Write a gentle inner-monologue detective story where the first clue points the wrong way and the child learns not to accuse before checking facts.",
        ]
    return [
        base,
        f"Tell a detective story where {detective.id} feels ready to blame someone because of {clue.label}, "
        f"but pauses, investigates, and finds the true answer about {thing.label}.",
        f"Write a child-friendly mystery with inner thoughts, a caution against jumping to conclusions, and a calm ending that proves fairness matters.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    suspect = f["suspect"]
    keeper = f["keeper"]
    thing = f["thing_cfg"]
    clue = f["clue_cfg"]
    cause = f["cause_cfg"]
    method = f["method_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a child detective, with {helper.id} helping on the case. They were trying to find {thing.label} after it disappeared."
        ),
        (
            f"What was the first clue?",
            f"The first clue was {clue.label}. It seemed to point toward {suspect.id}, which made the mystery feel simpler than it really was."
        ),
        (
            f"Why did {helper.id} tell {detective.id} to be careful?",
            f"{helper.id} knew one clue was not enough to prove anything. {helper.pronoun().capitalize()} wanted {detective.id} to think about hurt feelings before blaming {suspect.id}."
        ),
    ]
    if outcome == "apology":
        qa.append(
            (
                f"Why did {detective.id} need to apologize?",
                f"{detective.id} accused {suspect.id} before the truth was known, and that hurt {suspect.pronoun('possessive')} feelings. After the real cause was found, {detective.pronoun()} understood that the clue had been misleading."
            )
        )
    else:
        qa.append(
            (
                f"How did {detective.id} stop the mistake before it happened?",
                f"{detective.id} paused instead of blaming {suspect.id} right away. That extra moment made room for a better check, and the better check led to the truth."
            )
        )
    qa.append(
        (
            f"How did they solve the mystery?",
            f"They used {method.label} and found the signs that matched the real cause. Then they discovered that {cause.reveal_text[0].lower() + cause.reveal_text[1:]}"
        )
    )
    qa.append(
        (
            "What did the detective learn at the end?",
            f"{detective.id} learned that a decent detective follows facts instead of first feelings. The ending proves it because the case is solved fairly and no wrong blame is left hanging in the air."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"detective", "clue"}
    tags |= set(f["clue_cfg"].tags)
    tags |= set(f["cause_cfg"].tags)
    if f["outcome"] == "apology":
        tags.add("apology")
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v != ""}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} predicted_hurt={world.facts.get('predicted_hurt')}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="classroom",
        missing_thing="sticker_book",
        clue="glitter",
        cause="spill",
        method="track",
        detective_name="Nora",
        detective_gender="girl",
        helper_name="Ben",
        helper_gender="boy",
        suspect_name="Ivy",
        suspect_gender="girl",
        trait="hasty",
        helper_support=1,
    ),
    StoryParams(
        setting="clubhouse",
        missing_thing="marble_pouch",
        clue="leaf",
        cause="squirrel",
        method="window",
        detective_name="Theo",
        detective_gender="boy",
        helper_name="Mia",
        helper_gender="girl",
        suspect_name="Leo",
        suspect_gender="boy",
        trait="careful",
        helper_support=2,
    ),
    StoryParams(
        setting="library",
        missing_thing="stamp_card",
        clue="crumbs",
        cause="tidy",
        method="ask",
        detective_name="Ava",
        detective_gender="girl",
        helper_name="Finn",
        helper_gender="boy",
        suspect_name="Maya",
        suspect_gender="girl",
        trait="decent",
        helper_support=3,
    ),
    StoryParams(
        setting="classroom",
        missing_thing="marble_pouch",
        clue="leaf",
        cause="spill",
        method="track",
        detective_name="Max",
        detective_gender="boy",
        helper_name="Ruby",
        helper_gender="girl",
        suspect_name="Leo",
        suspect_gender="boy",
        trait="eager",
        helper_support=1,
    ),
    StoryParams(
        setting="library",
        missing_thing="sticker_book",
        clue="glitter",
        cause="squirrel",
        method="window",
        detective_name="Ella",
        detective_gender="girl",
        helper_name="Noah",
        helper_gender="boy",
        suspect_name="Ivy",
        suspect_gender="girl",
        trait="fair",
        helper_support=2,
    ),
]


def explain_combo_rejection(clue: Clue, cause: Cause, method: Optional[CheckMethod] = None) -> str:
    if clue.points_to_role == cause.true_role:
        return (
            f"(No story: {clue.label} points straight to the real cause instead of misleading the detective. "
            f"This world needs a tempting wrong clue so the cautionary lesson matters.)"
        )
    if method is not None and not method_finds_cause(method, cause):
        return (
            f"(No story: {method.label} would not honestly reveal the truth about this case. "
            f"Choose a method that can really uncover the cause.)"
        )
    return "(No story: that mystery setup does not fit this world.)"


def outcome_of(params: StoryParams) -> str:
    return "apology" if would_accuse(params.trait, params.helper_support) else "averted"


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid_clue_cause(C, U) :- clue(C), cause(U), points_to(C, R1), true_role(U, R2), R1 != R2.
method_works(M, U) :- method(M), cause(U), needs_method(U, M), true_role(U, R), power_role(M, R).
valid(S, T, C, U, M) :- setting(S), thing(T), valid_clue_cause(C, U), method_works(M, U).

% --- outcome model ---------------------------------------------------------
careful_score(T, 3) :- trait(T), careful_trait(T).
careful_score(T, 1) :- trait(T), not careful_trait(T).
accuse :- chosen_trait(T), helper_support(H), careful_score(T, C), C + H < 4.

outcome(apology) :- accuse.
outcome(averted) :- not accuse.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in MISSING_THINGS:
        lines.append(asp.fact("thing", tid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("points_to", cid, clue.points_to_role))
    for uid, cause in CAUSES.items():
        lines.append(asp.fact("cause", uid))
        lines.append(asp.fact("true_role", uid, cause.true_role))
        lines.append(asp.fact("needs_method", uid, cause.needs_method))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        for role in sorted(method.power_roles):
            lines.append(asp.fact("power_role", mid, role))
    for trait in TRAITS:
        lines.append(asp.fact("trait", trait))
    for trait in sorted(CAREFUL_TRAITS):
        lines.append(asp.fact("careful_trait", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_trait", params.trait),
        asp.fact("helper_support", params.helper_support),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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
    parser = build_parser()
    for s in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcome differences.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        emit(sample, trace=False, qa=False)
        print("OK: smoke test generation/emit succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective, a misleading clue, and a caution about blaming too fast."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--missing-thing", choices=MISSING_THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--helper-support", type=int, choices=[1, 2, 3])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.cause:
        clue = CLUES[args.clue]
        cause = CAUSES[args.cause]
        if not clue_matches_cause(clue, cause):
            raise StoryError(explain_combo_rejection(clue, cause))
    if args.cause and args.method:
        cause = CAUSES[args.cause]
        method = METHODS[args.method]
        if not method_finds_cause(method, cause):
            clue = CLUES[args.clue] if args.clue else next(iter(CLUES.values()))
            raise StoryError(explain_combo_rejection(clue, cause, method))

    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.missing_thing is None or c[1] == args.missing_thing)
        and (args.clue is None or c[2] == args.clue)
        and (args.cause is None or c[3] == args.cause)
        and (args.method is None or c[4] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting, thing, clue, cause, method = rng.choice(sorted(combos))
    trait = args.trait or rng.choice(TRAITS)
    helper_support = args.helper_support if args.helper_support is not None else rng.choice([1, 2, 3])

    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    suspect_gender = rng.choice(["girl", "boy"])
    detective_name = _pick_name(rng, detective_gender)
    helper_name = _pick_name(rng, helper_gender, avoid=detective_name)
    suspect_name = _pick_name(rng, suspect_gender, avoid=detective_name if suspect_gender == detective_gender else "")

    return StoryParams(
        setting=setting,
        missing_thing=thing,
        clue=clue,
        cause=cause,
        method=method,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        helper_gender=helper_gender,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
        trait=trait,
        helper_support=helper_support,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.missing_thing not in MISSING_THINGS:
        raise StoryError(f"(Unknown missing thing: {params.missing_thing})")
    if params.clue not in CLUES:
        raise StoryError(f"(Unknown clue: {params.clue})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.method not in METHODS:
        raise StoryError(f"(Unknown method: {params.method})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")

    clue = CLUES[params.clue]
    cause = CAUSES[params.cause]
    method = METHODS[params.method]
    if not clue_matches_cause(clue, cause):
        raise StoryError(explain_combo_rejection(clue, cause))
    if not method_finds_cause(method, cause):
        raise StoryError(explain_combo_rejection(clue, cause, method))

    world = tell(
        setting=SETTINGS[params.setting],
        thing=MISSING_THINGS[params.missing_thing],
        clue=clue,
        cause=cause,
        method=method,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        helper_name=params.helper_name,
        helper_gender=params.helper_gender,
        suspect_name=params.suspect_name,
        suspect_gender=params.suspect_gender,
        trait=params.trait,
        helper_support=params.helper_support,
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
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, thing, clue, cause, method) combos:\n")
        for setting, thing, clue, cause, method in combos:
            print(f"  {setting:10} {thing:12} {clue:8} {cause:8} {method}")
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
                f"### {p.detective_name}: {p.clue} -> {p.cause} "
                f"({p.setting}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
