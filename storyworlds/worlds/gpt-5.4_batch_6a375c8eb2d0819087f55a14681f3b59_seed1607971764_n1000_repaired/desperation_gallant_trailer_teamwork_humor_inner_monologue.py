#!/usr/bin/env python3
"""
A standalone story world about two children hauling supplies in a little trailer
to a neighborhood gathering. The turn comes from a wobble risk on the route, the
fix comes from teamwork, and the ending proves what changed.

Run it
------
python storyworlds/worlds/gpt-5.4/desperation_gallant_trailer_teamwork_humor_inner_monologue.py
python storyworlds/worlds/gpt-5.4/desperation_gallant_trailer_teamwork_humor_inner_monologue.py --route grassy_shortcut --cargo cupcakes
python storyworlds/worlds/gpt-5.4/desperation_gallant_trailer_teamwork_humor_inner_monologue.py --fix joke_only
python storyworlds/worlds/gpt-5.4/desperation_gallant_trailer_teamwork_humor_inner_monologue.py --all --qa
python storyworlds/worlds/gpt-5.4/desperation_gallant_trailer_teamwork_humor_inner_monologue.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Route:
    id: str
    label: str
    place_line: str
    bumpiness: int
    slope: int
    comic: str
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
class Cargo:
    id: str
    label: str
    phrase: str
    plural: bool
    tippy: int
    messy: bool
    destination: str
    end_image: str
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
class TrailerCfg:
    id: str
    label: str
    phrase: str
    side_support: int
    sturdy: bool
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
class Fix:
    id: str
    sense: int
    power: int
    teamwork: bool
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


@dataclass
class Mood:
    id: str
    opening: str
    joke: str
    thought: str
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
        return [e for e in self.entities.values() if e.role in {"hero", "helper"}]

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


def base_risk(route: Route, cargo: Cargo, trailer: TrailerCfg, hurry: int) -> int:
    return max(0, route.bumpiness + route.slope + cargo.tippy + hurry - trailer.side_support)


def hazard_present(route: Route, cargo: Cargo, trailer: TrailerCfg, hurry: int) -> bool:
    return base_risk(route, cargo, trailer, hurry) > 0


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def best_fix() -> Fix:
    return max(FIXES.values(), key=lambda f: (f.sense, f.power))


def outcome_for(route: Route, cargo: Cargo, trailer: TrailerCfg, fix: Fix, hurry: int) -> str:
    return "saved" if fix.power >= base_risk(route, cargo, trailer, hurry) else "spill"


def _r_worry(world: World) -> list[str]:
    trailer = world.get("trailer")
    cargo = world.get("cargo")
    if trailer.meters["wobble"] < THRESHOLD:
        return []
    sig = ("worry",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["danger"] += 1
    for kid in world.kids():
        kid.memes["alarm"] += 1
    return []


def _r_spill(world: World) -> list[str]:
    trailer = world.get("trailer")
    cargo = world.get("cargo")
    if trailer.meters["wobble"] < THRESHOLD or trailer.meters["stabilized"] >= THRESHOLD:
        return []
    need = float(world.facts["risk"])
    if trailer.meters["wobble"] < need:
        return []
    sig = ("spill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    cargo.meters["spilled"] += 1
    if cargo.attrs.get("messy"):
        cargo.meters["mess"] += 1
    for kid in world.kids():
        kid.memes["oops"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="worry", tag="emotional", apply=_r_worry),
    Rule(name="spill", tag="physical", apply=_r_spill),
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
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_route(route: Route, cargo: Cargo, trailer: TrailerCfg, hurry: int) -> dict:
    sim = World()
    sim.add(Entity(id="trailer", type="trailer", label=trailer.label))
    sim.add(Entity(id="cargo", type="cargo", label=cargo.label, attrs={"messy": cargo.messy}))
    sim.facts["risk"] = base_risk(route, cargo, trailer, hurry)
    sim.get("trailer").meters["wobble"] = float(sim.facts["risk"])
    propagate(sim, narrate=False)
    return {
        "risk": sim.facts["risk"],
        "danger": sim.get("cargo").meters["danger"],
        "will_spill": sim.get("cargo").meters["spilled"] >= THRESHOLD,
    }


def introduce(world: World, hero: Entity, helper: Entity, parent: Entity,
              cargo: Cargo, trailer: TrailerCfg, route: Route, mood: Mood) -> None:
    for kid in (hero, helper):
        kid.memes["helpful"] += 1
        kid.memes["pride"] += 1
    world.say(
        f"On the evening of the neighborhood share night, {hero.id} and {helper.id} had one small job: "
        f"pull {cargo.phrase} in {trailer.phrase} to {cargo.destination}."
    )
    world.say(
        f"{route.place_line} {mood.opening}"
    )
    world.say(
        f'"We look very official," {helper.id} said, giving the trailer handle a tiny gallant bow. '
        f'"Official and a little squeaky."'
    )
    world.say(
        f'The trailer answered with a ridiculous eeek, and both children laughed.'
    )
    world.facts["goal"] = cargo.destination
    world.facts["comic"] = route.comic


def set_off(world: World, hero: Entity, helper: Entity, cargo: Cargo, route: Route, mood: Mood) -> None:
    hero.memes["determination"] += 1
    world.say(
        f"They started down {route.label}, one child at the front and one at the side, trying to keep the little trailer straight."
    )
    world.say(
        f'{hero.id} thought, "{mood.thought}"'
    )
    if cargo.id == "cupcakes":
        world.say(f"The frosting swayed so politely that it somehow looked even more nervous than {hero.id}.")
    elif cargo.id == "lemonade":
        world.say(f"The lemonade gave a soft slosh that sounded like it was clearing its throat.")
    elif cargo.id == "seedlings":
        world.say(f"Every tiny leaf trembled as if the plants were whispering, Easy now.")
    else:
        world.say(f"The folded chairs clacked together like they had their own opinion about being moved.")


def warn(world: World, hero: Entity, helper: Entity, route: Route, cargo: Cargo,
         trailer: TrailerCfg, hurry: int) -> None:
    pred = predict_route(route, cargo, trailer, hurry)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_risk"] = pred["risk"]
    world.say(
        f"At the roughest part, the wheels gave a jump. {hero.id} felt a quick splash of desperation in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f'{hero.id} thought, "If this keeps wobbling, {cargo.it()} will never make it to {cargo.destination}."'
    )
    if pred["risk"] >= 3:
        world.say(
            f'"Slow feet!" {helper.id} said. "{route.comic}"'
        )
    else:
        world.say(
            f'"Tiny steps," {helper.id} said. "{route.comic}"'
        )


def wobble(world: World, hero: Entity, helper: Entity, route: Route, cargo: Cargo,
           trailer: TrailerCfg, hurry: int) -> None:
    risk = base_risk(route, cargo, trailer, hurry)
    world.facts["risk"] = risk
    trailer_ent = world.get("trailer")
    cargo_ent = world.get("cargo")
    trailer_ent.meters["rolling"] += 1
    trailer_ent.meters["wobble"] += float(risk)
    cargo_ent.attrs["messy"] = cargo.messy
    propagate(world, narrate=False)
    if risk >= 3:
        world.say(
            f"The trailer tipped from one wheel to the other, and {cargo.it()} leaned so far that both children made the same startled face."
        )
    else:
        world.say(
            f"The trailer gave one hard shimmy, enough to make both children suck in a breath."
        )


def teamwork_fix(world: World, hero: Entity, helper: Entity, fix: Fix, cargo: Cargo) -> None:
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    if fix.teamwork:
        hero.memes["trust"] += 1
        helper.memes["trust"] += 1
    world.say(fix.text.replace("{hero}", hero.id).replace("{helper}", helper.id).replace("{cargo}", cargo.label))


def saved_ending(world: World, hero: Entity, helper: Entity, parent: Entity,
                 cargo: Cargo, fix: Fix, mood: Mood) -> None:
    trailer_ent = world.get("trailer")
    cargo_ent = world.get("cargo")
    trailer_ent.meters["stabilized"] += 1
    trailer_ent.meters["wobble"] = 0.0
    cargo_ent.meters["danger"] = 0.0
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    hero.memes["humor"] += 1
    helper.memes["humor"] += 1
    world.say(
        f"Soon the wheels were behaving again, and the little trailer rolled the way it should have from the start."
    )
    world.say(
        f'When they reached {cargo.destination}, {parent.label_word.capitalize()} looked up and smiled. '
        f'"You two made that look easy."'
    )
    if cargo.id == "cupcakes":
        world.say(
            f"{helper.id} grinned at the frosting and said it had survived with more dignity than most grown-ups at a bake sale."
        )
    elif cargo.id == "lemonade":
        world.say(
            f"{hero.id} held up the jug and laughed because not even the lemons had escaped."
        )
    elif cargo.id == "seedlings":
        world.say(
            f"The seedlings arrived standing tall, and the children set them down as carefully as if they were tiny green guests."
        )
    else:
        world.say(
            f"The chairs unfolded around the screen a few minutes later, and the children sat in them with the pleased look of people who had helped make the evening happen."
        )
    world.say(
        f"{cargo.end_image}"
    )
    world.facts["used_fix_text"] = fix.qa_text


def spill_ending(world: World, hero: Entity, helper: Entity, parent: Entity,
                 cargo: Cargo, fix: Fix) -> None:
    cargo_ent = world.get("cargo")
    cargo_ent.meters["spilled"] += 1
    if cargo.messy:
        cargo_ent.meters["mess"] += 1
    hero.memes["embarrassment"] += 1
    helper.memes["embarrassment"] += 1
    hero.memes["humor"] += 1
    helper.memes["humor"] += 1
    world.say(
        fix.fail.replace("{hero}", hero.id).replace("{helper}", helper.id).replace("{cargo}", cargo.label)
    )
    if cargo.id == "cupcakes":
        world.say(
            f"Only two cupcakes slumped sideways, wearing their frosting like crooked hats."
        )
    elif cargo.id == "lemonade":
        world.say(
            f"A bright little wave of lemonade escaped over the rim and dotted their shoes."
        )
    elif cargo.id == "seedlings":
        world.say(
            f"One seedling tipped into the blanket, scattering a little puff of soil."
        )
    else:
        world.say(
            f"One folded chair clattered out and made such a dramatic noise that all three children stared at it."
        )
    world.say(
        f'{parent.label_word.capitalize()} came over with a towel and a kind face. '
        f'"Well," {parent.pronoun()} said, "now the trailer has a story too."'
    )
    world.say(
        f"The children cleaned up together, then finished the trip more slowly. By the time they arrived, the desperate feeling had turned into giggles and a careful new habit of walking side by side."
    )
    world.facts["used_fix_text"] = fix.qa_text


def tell(route: Route, cargo: Cargo, trailer: TrailerCfg, fix: Fix, mood: Mood,
         hero_name: str = "Maya", hero_gender: str = "girl",
         helper_name: str = "Ben", helper_gender: str = "boy",
         parent_type: str = "mother", hurry: int = 1) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, role="helper"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    trailer_ent = world.add(Entity(id="trailer", type="trailer", label=trailer.label, attrs={"sturdy": trailer.sturdy}))
    cargo_ent = world.add(Entity(id="cargo", type="cargo", label=cargo.label, attrs={"messy": cargo.messy}))

    world.facts["risk"] = base_risk(route, cargo, trailer, hurry)
    world.facts["route"] = route
    world.facts["cargo_cfg"] = cargo
    world.facts["trailer_cfg"] = trailer
    world.facts["fix_cfg"] = fix
    world.facts["mood"] = mood
    world.facts["hurry"] = hurry

    introduce(world, hero, helper, parent, cargo, trailer, route, mood)
    world.para()
    set_off(world, hero, helper, cargo, route, mood)
    warn(world, hero, helper, route, cargo, trailer, hurry)
    wobble(world, hero, helper, route, cargo, trailer, hurry)

    world.para()
    teamwork_fix(world, hero, helper, fix, cargo)
    if outcome_for(route, cargo, trailer, fix, hurry) == "saved":
        saved_ending(world, hero, helper, parent, cargo, fix, mood)
        outcome = "saved"
    else:
        spill_ending(world, hero, helper, parent, cargo, fix)
        outcome = "spill"

    world.facts.update(
        hero=hero,
        helper=helper,
        parent=parent,
        cargo=cargo_ent,
        trailer=trailer_ent,
        outcome=outcome,
        used_teamwork=fix.teamwork,
        predicted_spill=world.facts["predicted_risk"] > 0,
    )
    return world


ROUTES = {
    "sidewalk_crack": Route(
        id="sidewalk_crack",
        label="the old sidewalk by the maple tree",
        place_line="The sun was low, and the block smelled like cut grass and warm toast from somebody's kitchen.",
        bumpiness=1,
        slope=0,
        comic="That crack always acts like it wants applause.",
        tags={"sidewalk", "wheels"},
    ),
    "alley_ramp": Route(
        id="alley_ramp",
        label="the alley ramp behind the garages",
        place_line="The air held that busy evening sound when everyone seemed to be carrying one more thing outside.",
        bumpiness=1,
        slope=1,
        comic="This ramp thinks it is a mountain.",
        tags={"ramp", "wheels"},
    ),
    "grassy_shortcut": Route(
        id="grassy_shortcut",
        label="the grassy shortcut beside the fence",
        place_line="A sprinkler had stopped only minutes before, leaving the grass shiny and full of tiny dimples.",
        bumpiness=2,
        slope=1,
        comic="The grass is pretending to be the moon.",
        tags={"grass", "wheels"},
    ),
}

CARGOES = {
    "cupcakes": Cargo(
        id="cupcakes",
        label="cupcakes",
        phrase="a tray of frosted cupcakes",
        plural=True,
        tippy=2,
        messy=True,
        destination="the folding table near the movie screen",
        end_image="A little later, while the first cartoon flickered onto the sheet, they each ate a cupcake that was still perfectly upright.",
        tags={"cupcakes", "food"},
    ),
    "lemonade": Cargo(
        id="lemonade",
        label="lemonade jug",
        phrase="a big glass jug of lemonade",
        plural=False,
        tippy=2,
        messy=True,
        destination="the snack table by the curb",
        end_image="When the cups were poured, the lemonade tasted bright and cold, and the children felt absurdly proud of every drop.",
        tags={"lemonade", "food"},
    ),
    "seedlings": Cargo(
        id="seedlings",
        label="seedling tray",
        phrase="a tray of tomato seedlings",
        plural=False,
        tippy=1,
        messy=True,
        destination="the community garden gate",
        end_image="At the gate, they lined the seedlings in a row, and the leaves caught the evening light like small green hands.",
        tags={"plants", "garden"},
    ),
    "chairs": Cargo(
        id="chairs",
        label="folded chairs",
        phrase="three folded lawn chairs",
        plural=True,
        tippy=1,
        messy=False,
        destination="the white sheet where the movie would start",
        end_image="Soon families were settling into the chairs, and the children kept glancing at the trailer as if it had become part of the crew.",
        tags={"chairs", "gathering"},
    ),
}

TRAILERS = {
    "red_wagon_trailer": TrailerCfg(
        id="red_wagon_trailer",
        label="red wagon trailer",
        phrase="a little red trailer hitched to an old wagon handle",
        side_support=1,
        sturdy=False,
        tags={"wagon", "trailer"},
    ),
    "garden_trailer": TrailerCfg(
        id="garden_trailer",
        label="garden trailer",
        phrase="a small garden trailer with deeper sides",
        side_support=2,
        sturdy=True,
        tags={"garden_trailer", "trailer"},
    ),
    "bike_trailer": TrailerCfg(
        id="bike_trailer",
        label="bike trailer",
        phrase="a bright bike trailer with a canvas flap tied open",
        side_support=2,
        sturdy=True,
        tags={"bike_trailer", "trailer"},
    ),
}

FIXES = {
    "two_side_hold": Fix(
        id="two_side_hold",
        sense=3,
        power=3,
        teamwork=True,
        text="{hero} grabbed one side, {helper} grabbed the other, and together they kept the trailer level with slow, matching steps.",
        fail="{hero} and {helper} both grabbed the sides, but the wobble had already turned bossy and one corner still dipped too far.",
        qa_text="They each held one side of the trailer and walked in matching steps.",
        tags={"teamwork", "carry"},
    ),
    "repack_flat": Fix(
        id="repack_flat",
        sense=3,
        power=4,
        teamwork=True,
        text="{helper} knelt at once while {hero} handed things down, and together they repacked the {cargo} lower and flatter before trying again.",
        fail="{helper} and {hero} repacked the load, but they were still moving too quickly and the trailer lurched again.",
        qa_text="They stopped to repack the load lower and flatter together.",
        tags={"teamwork", "packing"},
    ),
    "strap_and_pull": Fix(
        id="strap_and_pull",
        sense=2,
        power=2,
        teamwork=True,
        text="{helper} found the bungee cord under the seat, and the two of them strapped the load tight before pulling together.",
        fail="{helper} and {hero} strapped the load tight, but the route was rougher than the little trailer could forgive.",
        qa_text="They strapped the load down and pulled together.",
        tags={"teamwork", "strap"},
    ),
    "joke_only": Fix(
        id="joke_only",
        sense=1,
        power=0,
        teamwork=False,
        text='{helper} tried to cheer everyone up by saluting the trailer and saying, "Be brave, tiny cart."',
        fail='{helper} saluted the trailer and joked, "Be brave, tiny cart," but jokes alone did not stop the wobble.',
        qa_text="They tried to laugh it off instead of changing how they moved the trailer.",
        tags={"humor"},
    ),
}

MOODS = {
    "steady": Mood(
        id="steady",
        opening="Somebody was testing speakers at the far end of the block, and every few moments a drumbeat bounced softly across the pavement.",
        joke="I am not panicking. I am just being extra alert.",
        thought="We only have to get there in one piece. That is not a lot to ask from two kids and one squeaky trailer.",
    ),
    "chatty": Mood(
        id="chatty",
        opening="Neighbors called to one another over fences, and the whole street had the feel of a room with its walls taken away.",
        joke="If the trailer behaves, maybe it can get its own snack ticket.",
        thought="Be calm, feet. Be sensible, wheels. Please do not embarrass me in front of the cupcakes.",
    ),
    "hopeful": Mood(
        id="hopeful",
        opening="Paper lanterns were already beginning to glow on porches, making the whole block look as if it had dressed up for company.",
        joke="I can do this. Probably. Very probably.",
        thought="This should be simple. Walk, breathe, and do not let the trailer invent a new kind of disaster.",
    ),
}

GIRL_NAMES = ["Maya", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Mina"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Max", "Eli", "Finn", "Noah"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_fixes():
        return combos
    for route_id, route in ROUTES.items():
        for cargo_id, cargo in CARGOES.items():
            for trailer_id, trailer in TRAILERS.items():
                risk = base_risk(route, cargo, trailer, hurry=1)
                if risk <= 0:
                    continue
                if any(f.power >= risk for f in sensible_fixes()):
                    combos.append((route_id, cargo_id, trailer_id))
    return combos


@dataclass
class StoryParams:
    route: str
    cargo: str
    trailer: str
    fix: str
    mood: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    parent: str
    hurry: int = 1
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
    "trailer": [
        (
            "What is a trailer?",
            "A trailer is a small thing with wheels that carries other things behind or beside you. It helps move a load so your arms do not have to hold all the weight at once.",
        )
    ],
    "wheels": [
        (
            "Why do wheels wobble on bumpy ground?",
            "Wheels wobble when the ground pushes them unevenly from side to side. If the load is high or tippy, that uneven push can make everything lean.",
        )
    ],
    "ramp": [
        (
            "Why is it harder to pull something up a ramp?",
            "A ramp makes you work against gravity, so the load feels heavier. You usually have to go slower and keep it balanced.",
        )
    ],
    "grass": [
        (
            "Why can grass be tricky for small wheels?",
            "Small wheels sink and bump over soft grass more than they do on smooth pavement. That makes a cart or trailer harder to steer.",
        )
    ],
    "food": [
        (
            "Why do drinks and frosted treats spill easily?",
            "Liquids slosh and tall frosting tips when something jerks suddenly. A gentle ride helps them stay in place.",
        )
    ],
    "garden": [
        (
            "Why do seedlings need careful carrying?",
            "Seedlings are young plants with soft stems and small roots. If they tip over too hard, the soil spills and the stems can bend.",
        )
    ],
    "teamwork": [
        (
            "Why can teamwork make a hard job easier?",
            "Teamwork lets two people share the weight and watch the problem from different sides. One person can steady while the other pulls or adjusts.",
        )
    ],
    "packing": [
        (
            "Why does packing things lower help?",
            "A lower load is less tippy because its weight stays closer to the ground. That makes it easier for wheels to stay balanced.",
        )
    ],
    "strap": [
        (
            "What does a strap or bungee cord do?",
            "A strap holds a load in place so it cannot slide as much. It does not fix every problem, but it helps keep things from shifting.",
        )
    ],
    "carry": [
        (
            "Why do matching steps help when two people carry or steady something?",
            "Matching steps keep the load from jerking in two directions at once. Smooth, even movement helps it stay level.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "trailer",
    "wheels",
    "ramp",
    "grass",
    "food",
    "garden",
    "teamwork",
    "packing",
    "strap",
    "carry",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    cargo = f["cargo_cfg"]
    route = f["route"]
    outcome = f["outcome"]
    trailer = f["trailer_cfg"]
    base = (
        f'Write a slice-of-life story for a 3-to-5-year-old about two children using a little trailer to carry {cargo.label} across {route.label}. '
        f'Include the words "desperation", "gallant", and "trailer".'
    )
    if outcome == "saved":
        return [
            base,
            f"Tell a neighborhood teamwork story where {hero.id} feels a flash of desperation when the load wobbles, {helper.id} makes a gallant little joke, and together they save the trip.",
            f"Write a gentle story with inner monologue, humor, and teamwork: {hero.id} worries about a squeaky {trailer.label}, but the children solve the problem and arrive proud.",
        ]
    return [
        base,
        f"Tell a gentle mishap story where {hero.id} and {helper.id} try to get {cargo.label} there, the trailer wobbles, and a small spill teaches them to slow down and work together.",
        f"Write a child-friendly story with inner monologue and humor where a joke is not enough to fix a wobbling trailer, but the children recover kindly together.",
    ]


def pair_noun(a: Entity, b: Entity) -> str:
    if a.type == "girl" and b.type == "girl":
        return "two friends"
    if a.type == "boy" and b.type == "boy":
        return "two friends"
    return "two children"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    parent = f["parent"]
    cargo_cfg = f["cargo_cfg"]
    route = f["route"]
    trailer_cfg = f["trailer_cfg"]
    outcome = f["outcome"]
    pair = pair_noun(hero, helper)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {hero.id} and {helper.id}, who were taking {cargo_cfg.label} in a little trailer. They were trying to help at {cargo_cfg.destination}.",
        ),
        (
            "What problem happened on the way?",
            f"The trailer started to wobble on {route.label}. That made the load lean and gave {hero.id} a quick feeling of desperation because {cargo_cfg.it()} might spill.",
        ),
        (
            f"Why did {hero.id} feel worried?",
            f"{hero.id} could feel the wheels jump under the trailer and saw the load tip. {hero.pronoun('subject').capitalize()} worried because they might not get {cargo_cfg.label} safely to {cargo_cfg.destination}.",
        ),
    ]
    if outcome == "saved":
        qa.append(
            (
                "How did they solve the problem?",
                f"They worked together instead of rushing. {f['used_fix_text']} That changed the motion of the trailer and kept the load from spilling.",
            )
        )
        qa.append(
            (
                f"What was funny in the story?",
                f"The trailer squeaked so much that it seemed to answer back, and {helper.id} treated it like a very dramatic helper. The joke eased the tense moment, but the real fix was their teamwork.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"They arrived with {cargo_cfg.label} safe and useful for the gathering. The ending shows that the children learned to slow down, steady the trailer, and help each other.",
            )
        )
    else:
        qa.append(
            (
                "Did the joke fix the problem by itself?",
                f"No. The joke made the moment a little less scary, but it did not steady the trailer. They still had to clean up and finish the trip more carefully.",
            )
        )
        qa.append(
            (
                "How did the children act after the spill?",
                f"They cleaned up together and kept going more slowly. The small mishap turned their desperation into a better plan, which is why the ending still feels warm instead of harsh.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with a small mess but no big disaster. The children learned that a wobbling trailer needs action, not only jokes, and they finished the job side by side.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    route = f["route"]
    cargo = f["cargo_cfg"]
    fix = f["fix_cfg"]
    tags: set[str] = {"trailer", "teamwork"} | set(route.tags) | set(cargo.tags) | set(fix.tags)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  facts: risk={world.facts.get('risk')} outcome={world.facts.get('outcome')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        route="sidewalk_crack",
        cargo="cupcakes",
        trailer="red_wagon_trailer",
        fix="repack_flat",
        mood="chatty",
        hero="Maya",
        hero_gender="girl",
        helper="Ben",
        helper_gender="boy",
        parent="mother",
        hurry=1,
    ),
    StoryParams(
        route="alley_ramp",
        cargo="lemonade",
        trailer="garden_trailer",
        fix="two_side_hold",
        mood="steady",
        hero="Noah",
        hero_gender="boy",
        helper="Ruby",
        helper_gender="girl",
        parent="father",
        hurry=1,
    ),
    StoryParams(
        route="grassy_shortcut",
        cargo="seedlings",
        trailer="red_wagon_trailer",
        fix="strap_and_pull",
        mood="hopeful",
        hero="Ella",
        hero_gender="girl",
        helper="Finn",
        helper_gender="boy",
        parent="mother",
        hurry=1,
    ),
    StoryParams(
        route="grassy_shortcut",
        cargo="cupcakes",
        trailer="red_wagon_trailer",
        fix="joke_only",
        mood="chatty",
        hero="Zoe",
        hero_gender="girl",
        helper="Theo",
        helper_gender="boy",
        parent="father",
        hurry=2,
    ),
    StoryParams(
        route="alley_ramp",
        cargo="chairs",
        trailer="bike_trailer",
        fix="strap_and_pull",
        mood="steady",
        hero="Leo",
        hero_gender="boy",
        helper="Mina",
        helper_gender="girl",
        parent="mother",
        hurry=1,
    ),
]


def explain_rejection(route: Route, cargo: Cargo, trailer: TrailerCfg) -> str:
    risk = base_risk(route, cargo, trailer, hurry=1)
    if risk <= 0:
        return (
            f"(No story: {cargo.label} in the {trailer.label} along {route.label} is too stable. "
            f"This world needs a real wobble problem so teamwork matters.)"
        )
    if not any(f.power >= risk for f in sensible_fixes()):
        return (
            f"(No story: the wobble on {route.label} is too much for any sensible fix in this world. "
            f"Pick a steadier trailer or a less tippy load.)"
        )
    return "(No story: this combination does not fit the world model.)"


def explain_fix(fix_id: str) -> str:
    fix = FIXES[fix_id]
    better = ", ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fix_id}': it scores too low on common sense for this world "
        f"(sense={fix.sense} < {SENSE_MIN}). Try one of the teamwork fixes: {better}.)"
    )


ASP_RULES = r"""
hazard(R,C,T) :- route(R), cargo(C), trailer(T), bump(R,B), slope(R,S), tippy(C,Ti),
                 side_support(T,Su), hurry(1), B + S + Ti - Su > 0.

sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.

solvable(R,C,T) :- hazard(R,C,T), sensible(F), power(F,P),
                   bump(R,B), slope(R,S), tippy(C,Ti), side_support(T,Su), hurry(1),
                   P >= B + S + Ti - Su.

valid(R,C,T) :- route(R), cargo(C), trailer(T), solvable(R,C,T).

risk(B + S + Ti + H - Su) :- chosen_route(R), chosen_cargo(C), chosen_trailer(T),
                             bump(R,B), slope(R,S), tippy(C,Ti), hurry(H),
                             side_support(T,Su), B + S + Ti + H - Su > 0.
risk(0) :- chosen_route(R), chosen_cargo(C), chosen_trailer(T),
           bump(R,B), slope(R,S), tippy(C,Ti), hurry(H),
           side_support(T,Su), B + S + Ti + H - Su <= 0.

saved :- chosen_fix(F), power(F,P), risk(Rk), P >= Rk.
spill :- chosen_fix(F), power(F,P), risk(Rk), P < Rk.

outcome(saved) :- saved.
outcome(spill) :- spill.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for route_id, route in ROUTES.items():
        lines.append(asp.fact("route", route_id))
        lines.append(asp.fact("bump", route_id, route.bumpiness))
        lines.append(asp.fact("slope", route_id, route.slope))
    for cargo_id, cargo in CARGOES.items():
        lines.append(asp.fact("cargo", cargo_id))
        lines.append(asp.fact("tippy", cargo_id, cargo.tippy))
    for trailer_id, trailer in TRAILERS.items():
        lines.append(asp.fact("trailer", trailer_id))
        lines.append(asp.fact("side_support", trailer_id, trailer.side_support))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        lines.append(asp.fact("power", fix_id, fix.power))
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
    return sorted(f for (f,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_route", params.route),
            asp.fact("chosen_cargo", params.cargo),
            asp.fact("chosen_trailer", params.trailer),
            asp.fact("chosen_fix", params.fix),
            asp.fact("hurry", params.hurry),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def _smoke_test_generation() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "trailer" not in sample.story.lower():
        raise StoryError("Smoke test failed: story generation produced no usable story.")
    buf = io.StringIO()
    with redirect_stdout(buf):
        emit(sample, trace=False, qa=True, header="### smoke")
    if "### smoke" not in buf.getvalue():
        raise StoryError("Smoke test failed: emit() did not render output.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    clingo_sensible = set(asp_sensible())
    python_sensible = {f.id for f in sensible_fixes()}
    if clingo_sensible == python_sensible:
        print(f"OK: sensible fixes match ({sorted(clingo_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(clingo_sensible)} python={sorted(python_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(50):
        try:
            p = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(p)
    bad = 0
    for params in cases:
        python_outcome = outcome_for(
            ROUTES[params.route],
            CARGOES[params.cargo],
            TRAILERS[params.trailer],
            FIXES[params.fix],
            params.hurry,
        )
        if asp_outcome(params) != python_outcome:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        _smoke_test_generation()
        print("OK: generation/emit smoke test passed.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a little trailer, a wobble problem, and a teamwork fix."
    )
    ap.add_argument("--route", choices=ROUTES)
    ap.add_argument("--cargo", choices=CARGOES)
    ap.add_argument("--trailer", choices=TRAILERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--hurry", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible route/cargo/trailer combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.route and args.cargo and args.trailer:
        route = ROUTES[args.route]
        cargo = CARGOES[args.cargo]
        trailer = TRAILERS[args.trailer]
        if (args.hurry if args.hurry is not None else 1) <= 2:
            risk = base_risk(route, cargo, trailer, args.hurry if args.hurry is not None else 1)
            if risk <= 0 or not any(f.power >= risk for f in sensible_fixes()):
                raise StoryError(explain_rejection(route, cargo, trailer))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        # Allowed as an explicit choice only when the user wants a gentle spill story.
        pass

    default_hurry = args.hurry if args.hurry is not None else 1
    combos = [
        combo
        for combo in valid_combos()
        if (args.route is None or combo[0] == args.route)
        and (args.cargo is None or combo[1] == args.cargo)
        and (args.trailer is None or combo[2] == args.trailer)
    ]
    if not combos:
        if args.route and args.cargo and args.trailer:
            raise StoryError(explain_rejection(ROUTES[args.route], CARGOES[args.cargo], TRAILERS[args.trailer]))
        raise StoryError("(No valid combination matches the given options.)")

    route_id, cargo_id, trailer_id = rng.choice(sorted(combos))
    route = ROUTES[route_id]
    cargo = CARGOES[cargo_id]
    trailer = TRAILERS[trailer_id]

    hurry = default_hurry
    if args.hurry is None:
        hurry = rng.choice([0, 1, 1, 2])
        while base_risk(route, cargo, trailer, hurry) <= 0:
            hurry = rng.choice([0, 1, 1, 2])

    risk = base_risk(route, cargo, trailer, hurry)
    if args.fix:
        fix_id = args.fix
    else:
        good = [f.id for f in sensible_fixes() if FIXES[f.id].power >= risk]
        if not good:
            raise StoryError(explain_rejection(route, cargo, trailer))
        fix_id = rng.choice(sorted(good))

    mood_id = args.mood or rng.choice(sorted(MOODS))
    hero, hero_gender = _pick_kid(rng)
    helper, helper_gender = _pick_kid(rng, avoid=hero)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        route=route_id,
        cargo=cargo_id,
        trailer=trailer_id,
        fix=fix_id,
        mood=mood_id,
        hero=hero,
        hero_gender=hero_gender,
        helper=helper,
        helper_gender=helper_gender,
        parent=parent,
        hurry=hurry,
    )


def generate(params: StoryParams) -> StorySample:
    if params.route not in ROUTES:
        raise StoryError(f"(Unknown route '{params.route}').")
    if params.cargo not in CARGOES:
        raise StoryError(f"(Unknown cargo '{params.cargo}').")
    if params.trailer not in TRAILERS:
        raise StoryError(f"(Unknown trailer '{params.trailer}').")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix '{params.fix}').")
    if params.mood not in MOODS:
        raise StoryError(f"(Unknown mood '{params.mood}').")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type '{params.parent}').")

    route = ROUTES[params.route]
    cargo = CARGOES[params.cargo]
    trailer = TRAILERS[params.trailer]
    fix = FIXES[params.fix]
    mood = MOODS[params.mood]

    if params.hurry not in {0, 1, 2}:
        raise StoryError("(Hurry must be 0, 1, or 2.)")
    if not hazard_present(route, cargo, trailer, params.hurry):
        raise StoryError(explain_rejection(route, cargo, trailer))

    world = tell(
        route=route,
        cargo=cargo,
        trailer=trailer,
        fix=fix,
        mood=mood,
        hero_name=params.hero,
        hero_gender=params.hero_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        parent_type=params.parent,
        hurry=params.hurry,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (route, cargo, trailer) combos:\n")
        for route, cargo, trailer in combos:
            print(f"  {route:16} {cargo:10} {trailer}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
            route = ROUTES[p.route].label
            header = f"### {p.hero} & {p.helper}: {p.cargo} on {route} ({p.trailer}, {p.fix})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
