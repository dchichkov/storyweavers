#!/usr/bin/env python3
"""
A standalone storyworld about a macaw whose celebration item goes missing.
The mystery is solved through world-state clues, and the ending turns on
reconciliation rather than blame.

Run it:
    python storyworlds/worlds/gpt-5.4/macaw_positive_mystery_to_solve_reconciliation_animal.py
    python storyworlds/worlds/gpt-5.4/macaw_positive_mystery_to_solve_reconciliation_animal.py --all
    python storyworlds/worlds/gpt-5.4/macaw_positive_mystery_to_solve_reconciliation_animal.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/macaw_positive_mystery_to_solve_reconciliation_animal.py --qa --json
    python storyworlds/worlds/gpt-5.4/macaw_positive_mystery_to_solve_reconciliation_animal.py --verify
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
TRUST_MIN = 4


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    movable: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Celebration:
    id: str
    place: str
    opening: str
    ending: str
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
    use_text: str
    clue_mark: str
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
class HelperAnimal:
    id: str
    label: str
    phrase: str
    move_verb: str
    step_mark: str
    home: str
    safe_places: set[str] = field(default_factory=set)
    reasons: set[str] = field(default_factory=set)
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
class HidingPlace:
    id: str
    label: str
    phrase: str
    scene: str
    allows: set[str] = field(default_factory=set)
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
class Motive:
    id: str
    text: str
    clue_text: str
    apology_text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.history: list[str] = []

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
        clone.facts = copy.deepcopy(self.facts)
        clone.history = list(self.history)
        clone.paragraphs = [[]]
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


def _r_missing_worries(world: World) -> list[str]:
    item = world.get("item")
    seeker = world.get("hero")
    if item.attrs.get("missing") and ("missing_worries",) not in world.fired:
        world.fired.add(("missing_worries",))
        seeker.memes["confusion"] += 1
        seeker.memes["worry"] += 1
    return []


def _r_accusation_strains(world: World) -> list[str]:
    seeker = world.get("hero")
    helper = world.get("helper")
    if seeker.memes["accusation"] >= THRESHOLD and helper.attrs.get("innocent_move", False):
        sig = ("accusation_strains",)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["hurt"] += 1
            seeker.memes["guilt_seed"] += 1
            seeker.memes["trust"] -= 1
            helper.memes["trust"] -= 1
            seeker.meters["distance"] += 1
            helper.meters["distance"] += 1
    return []


def _r_clue_builds_hope(world: World) -> list[str]:
    seeker = world.get("hero")
    if world.facts.get("clue_found") and ("clue_builds_hope",) not in world.fired:
        world.fired.add(("clue_builds_hope",))
        seeker.memes["hope"] += 1
        seeker.memes["curiosity"] += 1
    return []


def _r_explanation_repairs(world: World) -> list[str]:
    seeker = world.get("hero")
    helper = world.get("helper")
    if world.facts.get("explained") and world.facts.get("apologized"):
        sig = ("explanation_repairs",)
        if sig not in world.fired:
            world.fired.add(sig)
            seeker.meters["distance"] = 0.0
            helper.meters["distance"] = 0.0
            seeker.memes["trust"] += 2
            helper.memes["trust"] += 2
            seeker.memes["warmth"] += 1
            helper.memes["warmth"] += 1
            seeker.memes["worry"] = 0.0
            helper.memes["hurt"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="missing_worries", tag="emotional", apply=_r_missing_worries),
    Rule(name="accusation_strains", tag="social", apply=_r_accusation_strains),
    Rule(name="clue_builds_hope", tag="mystery", apply=_r_clue_builds_hope),
    Rule(name="explanation_repairs", tag="social", apply=_r_explanation_repairs),
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
        for line in produced:
            world.say(line)
    return produced


def valid_combo(helper: HelperAnimal, place: HidingPlace, motive: Motive) -> bool:
    return place.id in helper.safe_places and motive.id in helper.reasons and helper.id in place.allows


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for celebration_id in CELEBRATIONS:
        for helper_id, helper in HELPERS.items():
            for place_id, place in PLACES.items():
                for motive_id, motive in MOTIVES.items():
                    if valid_combo(helper, place, motive):
                        combos.append((celebration_id, helper_id, place_id, motive_id))
    return combos


def predict_conflict(helper: HelperAnimal, trust: int) -> dict:
    sim = World()
    hero = sim.add(Entity(id="hero", kind="character", type="macaw", role="hero"))
    side = sim.add(Entity(id="helper", kind="character", type="animal", role="helper"))
    item = sim.add(Entity(id="item", type="item"))
    hero.memes["trust"] = float(trust)
    side.memes["trust"] = float(trust)
    item.attrs["missing"] = True
    side.attrs["innocent_move"] = True
    hero.memes["accusation"] = 1.0
    hero.meters["distance"] = 0.0
    side.meters["distance"] = 0.0
    propagate(sim, narrate=False)
    return {
        "hurt": side.memes["hurt"],
        "distance": side.meters["distance"],
    }


def introduce(world: World, celebration: Celebration, hero: Entity, item_cfg: MissingItem) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"In {celebration.place}, a bright macaw named {hero.id} woke with a positive flutter in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f"That evening the animals would share {celebration.opening}, and {hero.id} had made {item_cfg.phrase} to help {item_cfg.use_text}."
    )


def gather_friends(world: World, helper: Entity, celebration: Celebration) -> None:
    helper.memes["care"] += 1
    world.say(
        f"{helper.id} the {helper.label} came early to help, and together they looked around {celebration.place} while the morning breeze brushed the leaves."
    )


def discover_missing(world: World, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.attrs["missing"] = True
    world.history.append("missing")
    propagate(world, narrate=False)
    world.say(
        f"But when {world.get('hero').id} reached for {item_cfg.phrase}, it was gone. Only a small empty patch remained where it had rested."
    )


def worry_and_guess(world: World, helper_cfg: HelperAnimal, motive_cfg: Motive, trust: int) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    pred = predict_conflict(helper_cfg, trust)
    world.facts["predicted_hurt"] = pred["hurt"]
    world.facts["predicted_distance"] = pred["distance"]
    if trust < TRUST_MIN:
        hero.memes["accusation"] += 1
        world.history.append("accused")
        propagate(world, narrate=False)
        world.say(
            f"{hero.id} saw {helper_cfg.step_mark} near the empty patch and blurted, "
            f'"{helper.id}, did you take it?"'
        )
        world.say(
            f"{helper.id}'s ears drooped. {helper.pronoun().capitalize()} had only meant {motive_cfg.text}, and the question landed like a little sting."
        )
    else:
        hero.memes["suspicion"] += 1
        world.say(
            f"{hero.id} noticed {helper_cfg.step_mark} near the empty patch and wondered if {helper.id} knew something, but {hero.pronoun()} took a slow breath instead of blaming."
        )


def search_for_clue(world: World, place_cfg: HidingPlace, item_cfg: MissingItem, helper_cfg: HelperAnimal, motive_cfg: Motive) -> None:
    hero = world.get("hero")
    world.facts["clue_found"] = True
    world.history.append("clue")
    propagate(world, narrate=False)
    clue_line = motive_cfg.clue_text.replace("{place}", place_cfg.label).replace("{home}", helper_cfg.home)
    world.say(
        f"Then {hero.id} spotted {item_cfg.clue_mark} leading away from the empty patch, curving toward {place_cfg.scene}."
    )
    world.say(clue_line)


def find_item(world: World, place_cfg: HidingPlace, item_cfg: MissingItem) -> None:
    item = world.get("item")
    item.attrs["missing"] = False
    item.attrs["found_at"] = place_cfg.id
    item.meters["safe"] += 1
    world.history.append("found")
    world.say(
        f"There, tucked in {place_cfg.phrase}, lay {item_cfg.phrase}, neat and unharmed."
    )


def explain_move(world: World, helper_cfg: HelperAnimal, motive_cfg: Motive, place_cfg: HidingPlace) -> None:
    helper = world.get("helper")
    world.facts["explained"] = True
    world.history.append("explained")
    propagate(world, narrate=False)
    world.say(
        f'"I moved it to {place_cfg.label}," {helper.id} said softly. "{motive_cfg.text.capitalize()}."'
    )


def apologize(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.facts["apologized"] = True
    world.history.append("apology")
    propagate(world, narrate=False)
    if "accused" in world.history:
        world.say(
            f'{hero.id} lowered {hero.pronoun("possessive")} wings. "I am sorry I blamed you before I knew the whole story," {hero.pronoun()} said.'
        )
    else:
        world.say(
            f'{hero.id} nodded. "I am glad I asked and kept looking," {hero.pronoun()} said. "And I am sorry I almost let worry make a mean guess."'
        )


def reconcile(world: World, celebration: Celebration, item_cfg: MissingItem) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{helper.id} smiled again, and the two friends carried {item_cfg.phrase} back together."
    )
    world.say(
        f"When evening came, {celebration.ending} The mystery had become a lesson about asking kindly, and the air between them felt light and warm."
    )


def tell(
    celebration: Celebration,
    item_cfg: MissingItem,
    helper_cfg: HelperAnimal,
    place_cfg: HidingPlace,
    motive_cfg: Motive,
    hero_name: str = "Mira",
    trust: int = 5,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type="macaw",
            label="macaw",
            role="hero",
            attrs={},
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.phrase.split()[0].capitalize(),
            kind="character",
            type=helper_cfg.id,
            label=helper_cfg.label,
            role="helper",
            attrs={"innocent_move": True},
        )
    )
    item = world.add(
        Entity(
            id="item",
            kind="thing",
            type="item",
            label=item_cfg.label,
            attrs={"missing": False, "found_at": ""},
            movable=True,
        )
    )
    hero.memes["trust"] = float(trust)
    helper.memes["trust"] = float(trust)
    hero.meters["distance"] = 0.0
    helper.meters["distance"] = 0.0
    world.facts.update(
        celebration=celebration,
        item_cfg=item_cfg,
        helper_cfg=helper_cfg,
        place_cfg=place_cfg,
        motive_cfg=motive_cfg,
        trust=trust,
        clue_found=False,
        explained=False,
        apologized=False,
    )

    introduce(world, celebration, hero, item_cfg)
    gather_friends(world, helper, celebration)

    world.para()
    discover_missing(world, item_cfg)
    worry_and_guess(world, helper_cfg, motive_cfg, trust)

    world.para()
    search_for_clue(world, place_cfg, item_cfg, helper_cfg, motive_cfg)
    find_item(world, place_cfg, item_cfg)
    explain_move(world, helper_cfg, motive_cfg, place_cfg)

    world.para()
    apologize(world)
    reconcile(world, celebration, item_cfg)

    world.facts.update(
        hero=hero,
        helper=helper,
        item=item,
        accused=("accused" in world.history),
        reconciled=world.facts["explained"] and world.facts["apologized"] and hero.meters["distance"] == 0.0,
        found_place=place_cfg.id,
    )
    return world


CELEBRATIONS = {
    "dawn_song": Celebration(
        id="dawn_song",
        place="the river grove",
        opening="a dawn song under the fig tree",
        ending="the animals sang under the fig tree while the river held the last gold light",
        tags={"song", "friends"},
    ),
    "lantern_walk": Celebration(
        id="lantern_walk",
        place="the fern path",
        opening="a twilight lantern walk beside the reeds",
        ending="the animals walked the fern path in a bright little line, laughing whenever the lanterns bobbed",
        tags={"lantern", "friends"},
    ),
    "moonberry_sup": Celebration(
        id="moonberry_sup",
        place="the berry clearing",
        opening="a moonberry supper beside the smooth stones",
        ending="the animals shared supper beside the smooth stones, and even the crickets sounded pleased",
        tags={"food", "friends"},
    ),
}

ITEMS = {
    "garland": MissingItem(
        id="garland",
        label="seed garland",
        phrase="the seed garland",
        use_text="decorate the gathering place",
        clue_mark="a few sunflower seeds",
        tags={"seeds", "celebration"},
    ),
    "rattle": MissingItem(
        id="rattle",
        label="shell rattle",
        phrase="the shell rattle",
        use_text="lead the first song",
        clue_mark="one tiny silver shell",
        tags={"music", "shell"},
    ),
    "berry_bowl": MissingItem(
        id="berry_bowl",
        label="berry bowl",
        phrase="the painted berry bowl",
        use_text="serve the first sweet berries",
        clue_mark="a purple berry stain",
        tags={"berries", "food"},
    ),
}

HELPERS = {
    "otter": HelperAnimal(
        id="otter",
        label="otter",
        phrase="an otter",
        move_verb="rolled",
        step_mark="small damp pawprints",
        home="the water's edge",
        safe_places={"reed_nest", "stone_nook"},
        reasons={"keep_dry", "keep_cool"},
        tags={"otter", "water"},
    ),
    "squirrel": HelperAnimal(
        id="squirrel",
        label="squirrel",
        phrase="a squirrel",
        move_verb="carried",
        step_mark="quick little claw marks",
        home="the old fig tree",
        safe_places={"tree_hollow", "stone_nook"},
        reasons={"keep_safe", "keep_tidy"},
        tags={"squirrel", "tree"},
    ),
    "tortoise": HelperAnimal(
        id="tortoise",
        label="tortoise",
        phrase="a tortoise",
        move_verb="nudged",
        step_mark="a gentle trail in the dust",
        home="the shady bank",
        safe_places={"leaf_shelter", "stone_nook"},
        reasons={"keep_safe", "keep_dry"},
        tags={"tortoise", "slow"},
    ),
}

PLACES = {
    "reed_nest": HidingPlace(
        id="reed_nest",
        label="the reed nest",
        phrase="a dry cradle of reeds above the splash line",
        scene="the reeds beside the river",
        allows={"otter"},
        tags={"reeds", "river"},
    ),
    "tree_hollow": HidingPlace(
        id="tree_hollow",
        label="the tree hollow",
        phrase="a smooth hollow in the old fig tree",
        scene="the old fig tree",
        allows={"squirrel"},
        tags={"tree", "hollow"},
    ),
    "leaf_shelter": HidingPlace(
        id="leaf_shelter",
        label="the leaf shelter",
        phrase="a neat shelter of broad leaves under a root",
        scene="the shady roots near the bank",
        allows={"tortoise"},
        tags={"leaves", "shade"},
    ),
    "stone_nook": HidingPlace(
        id="stone_nook",
        label="the stone nook",
        phrase="a cool nook between two smooth stones",
        scene="the smooth stones by the path",
        allows={"otter", "squirrel", "tortoise"},
        tags={"stones", "cool"},
    ),
}

MOTIVES = {
    "keep_dry": Motive(
        id="keep_dry",
        text="keep it dry before the mist reached it",
        clue_text="The trail was damp only at the start, as if someone had hurried to a drier place near {place}.",
        apology_text="I was trying to protect it from the wet.",
        needs={"dry"},
        tags={"weather", "care"},
    ),
    "keep_safe": Motive(
        id="keep_safe",
        text="keep it safe from busy feet before everyone arrived",
        clue_text="Nothing looked broken. The trail pointed away from the path, as if someone wanted the object safe and out of the way near {place}.",
        apology_text="I was trying to keep it from getting bumped.",
        needs={"safe"},
        tags={"care", "crowd"},
    ),
    "keep_tidy": Motive(
        id="keep_tidy",
        text="keep the place tidy until the gathering was ready",
        clue_text="The space looked carefully swept, and the tiny marks led toward {place}, as if neat paws had made a secret errand.",
        apology_text="I thought it would look nicer later.",
        needs={"tidy"},
        tags={"tidy", "care"},
    ),
    "keep_cool": Motive(
        id="keep_cool",
        text="keep it cool in the shade so it would be fresh later",
        clue_text="The air was warmer in the clearing, but the little marks curved toward {place}, the coolest patch nearby.",
        apology_text="I wanted it fresh for later.",
        needs={"cool"},
        tags={"cool", "care"},
    ),
}

MACAW_NAMES = ["Mira", "Luma", "Pico", "Rafi", "Tala", "Nico", "Suri", "Kiri"]


@dataclass
class StoryParams:
    celebration: str
    item: str
    helper: str
    place: str
    motive: str
    hero_name: str
    trust: int = 5
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
    "macaw": [
        (
            "What is a macaw?",
            "A macaw is a large parrot with a strong beak and bright feathers. Macaws can be very clever and loud, and they often live in forests."
        )
    ],
    "otter": [
        (
            "What is an otter like?",
            "An otter is an animal that loves water and swims very well. Otters often use their paws to carry or move things."
        )
    ],
    "squirrel": [
        (
            "What does a squirrel do with things it gathers?",
            "A squirrel often carries and tucks things into safe little places. That is why squirrels are known for stashing food and other treasures."
        )
    ],
    "tortoise": [
        (
            "Why does a tortoise move slowly?",
            "A tortoise has a heavy shell and short sturdy legs, so it moves slowly and carefully. Slow steps can still be very helpful."
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with an answer you do not know yet. You solve it by noticing clues and thinking carefully."
        )
    ],
    "reconciliation": [
        (
            "What does reconciliation mean?",
            "Reconciliation means becoming friendly again after hurt or anger. It often begins with truth, apology, and kindness."
        )
    ],
    "apology": [
        (
            "Why can an apology help friends?",
            "An apology shows that you understand you caused hurt. It helps the other friend feel seen, and it can open the door to trust again."
        )
    ],
    "clue": [
        (
            "What is a clue?",
            "A clue is a small sign that helps you figure something out. A clue does not tell the whole answer, but it points you in the right direction."
        )
    ],
}
KNOWLEDGE_ORDER = ["macaw", "mystery", "clue", "reconciliation", "apology", "otter", "squirrel", "tortoise"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    celebration = f["celebration"]
    return [
        f'Write a positive animal story for ages 3 to 5 about a macaw who must solve a small mystery when {item_cfg.phrase} goes missing before {celebration.opening}.',
        f"Tell a gentle mystery-to-solve story where {hero.id} the macaw worries about {item_cfg.phrase}, follows clues, and reconciles with {helper.id} after learning the truth.",
        f'Write a child-facing animal story that uses the word "positive" and ends with reconciliation after a mistaken suspicion is cleared up.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    item_cfg = f["item_cfg"]
    place_cfg = f["place_cfg"]
    motive_cfg = f["motive_cfg"]
    celebration = f["celebration"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a macaw, and {helper.id} the {helper.label}. They were getting ready for {celebration.opening} together."
        ),
        (
            f"What was missing?",
            f"{item_cfg.phrase.capitalize()} was missing. {hero.id} had planned to use it to help {item_cfg.use_text}."
        ),
        (
            "How did the macaw try to solve the mystery?",
            f"{hero.id} looked for small clues near the empty patch and followed them toward {place_cfg.label}. The clues helped {hero.pronoun()} stop guessing and start noticing what had really happened."
        ),
        (
            f"Why had {helper.id} moved the item?",
            f"{helper.id} moved it to {place_cfg.label} to {motive_cfg.text}. The choice was meant to protect the item, not to spoil the celebration."
        ),
    ]
    if f.get("accused"):
        qa.append(
            (
                f"Why were {hero.id} and {helper.id} upset with each other for a while?",
                f"{hero.id} spoke too quickly and blamed {helper.id} before knowing the truth, so {helper.id} felt hurt. The distance between them grew because worry turned into an accusation before the clue was understood."
            )
        )
    qa.append(
        (
            "How did they reconcile?",
            f"{hero.id} apologized, and {helper.id} explained the kind reason for moving the item. Once the truth was shared, they carried it back together and felt close again."
        )
    )
    qa.append(
        (
            "How did the story end?",
            f"It ended happily and positively, with the friends using {item_cfg.phrase} after all. The final picture shows them joining the gathering together, which proves the friendship was repaired."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"macaw", "mystery", "clue", "reconciliation", "apology", world.facts["helper_cfg"].id}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        attrs = {k: v for k, v in e.attrs.items() if v or isinstance(v, bool)}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if attrs:
            bits.append(f"attrs={attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  history: {world.history}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        celebration="dawn_song",
        item="garland",
        helper="squirrel",
        place="tree_hollow",
        motive="keep_safe",
        hero_name="Mira",
        trust=2,
    ),
    StoryParams(
        celebration="lantern_walk",
        item="rattle",
        helper="otter",
        place="reed_nest",
        motive="keep_dry",
        hero_name="Luma",
        trust=5,
    ),
    StoryParams(
        celebration="moonberry_sup",
        item="berry_bowl",
        helper="tortoise",
        place="leaf_shelter",
        motive="keep_safe",
        hero_name="Pico",
        trust=3,
    ),
    StoryParams(
        celebration="dawn_song",
        item="berry_bowl",
        helper="otter",
        place="stone_nook",
        motive="keep_cool",
        hero_name="Tala",
        trust=6,
    ),
    StoryParams(
        celebration="lantern_walk",
        item="garland",
        helper="squirrel",
        place="stone_nook",
        motive="keep_tidy",
        hero_name="Rafi",
        trust=4,
    ),
]


def explain_rejection(helper: HelperAnimal, place: HidingPlace, motive: Motive) -> str:
    if place.id not in helper.safe_places:
        good = ", ".join(sorted(helper.safe_places))
        return (
            f"(No story: {helper.label} would not reasonably move the missing thing to {place.label}. "
            f"Try a place this helper can truly reach and use, such as: {good}.)"
        )
    if motive.id not in helper.reasons:
        good = ", ".join(sorted(helper.reasons))
        return (
            f"(No story: {helper.label} does not fit the motive '{motive.id}' in this world. "
            f"Try one of: {good}.)"
        )
    if helper.id not in place.allows:
        good = ", ".join(sorted(place.allows))
        return (
            f"(No story: {place.label} is not a plausible hiding place for {helper.label}. "
            f"That place is reserved for: {good}.)"
        )
    return "(No story: that helper, place, and motive do not make a reasonable mystery.)"


def outcome_of(params: StoryParams) -> str:
    return "strained_then_reconciled" if params.trust < TRUST_MIN else "gentle_reconciliation"


ASP_RULES = r"""
valid(C, H, P, M) :- celebration(C), helper(H), place(P), motive(M),
                     safe_place(H, P), reason(H, M), allows(P, H).

strained_then_reconciled :- trust(T), trust_min(M), T < M.
gentle_reconciliation    :- trust(T), trust_min(M), T >= M.

outcome(strained_then_reconciled) :- strained_then_reconciled.
outcome(gentle_reconciliation)    :- gentle_reconciliation.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for cid in CELEBRATIONS:
        lines.append(asp.fact("celebration", cid))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for place in sorted(helper.safe_places):
            lines.append(asp.fact("safe_place", hid, place))
        for motive in sorted(helper.reasons):
            lines.append(asp.fact("reason", hid, motive))
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for helper_id in sorted(place.allows):
            lines.append(asp.fact("allows", pid, helper_id))
    for mid in MOTIVES:
        lines.append(asp.fact("motive", mid))
    lines.append(asp.fact("trust_min", TRUST_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("trust", params.trust)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py_set == asp_set:
        print(f"OK: gate matches valid_combos() ({len(py_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for trust in range(0, 8):
        for combo in valid_combos()[:5]:
            cases.append(
                StoryParams(
                    celebration=combo[0],
                    item="garland",
                    helper=combo[1],
                    place=combo[2],
                    motive=combo[3],
                    hero_name="Mira",
                    trust=trust,
                )
            )
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a positive macaw mystery with clues, apology, and reconciliation."
    )
    ap.add_argument("--celebration", choices=CELEBRATIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--motive", choices=MOTIVES)
    ap.add_argument("--hero-name")
    ap.add_argument("--trust", type=int, choices=list(range(0, 8)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible scenarios derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and args.place and args.motive:
        helper = HELPERS[args.helper]
        place = PLACES[args.place]
        motive = MOTIVES[args.motive]
        if not valid_combo(helper, place, motive):
            raise StoryError(explain_rejection(helper, place, motive))

    combos = [
        combo
        for combo in valid_combos()
        if (args.celebration is None or combo[0] == args.celebration)
        and (args.helper is None or combo[1] == args.helper)
        and (args.place is None or combo[2] == args.place)
        and (args.motive is None or combo[3] == args.motive)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    celebration, helper, place, motive = rng.choice(sorted(combos))
    item = args.item or rng.choice(sorted(ITEMS))
    hero_name = args.hero_name or rng.choice(MACAW_NAMES)
    trust = args.trust if args.trust is not None else rng.randint(0, 7)
    return StoryParams(
        celebration=celebration,
        item=item,
        helper=helper,
        place=place,
        motive=motive,
        hero_name=hero_name,
        trust=trust,
    )


def generate(params: StoryParams) -> StorySample:
    if params.celebration not in CELEBRATIONS:
        raise StoryError(f"(Unknown celebration: {params.celebration})")
    if params.item not in ITEMS:
        raise StoryError(f"(Unknown item: {params.item})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.motive not in MOTIVES:
        raise StoryError(f"(Unknown motive: {params.motive})")
    helper = HELPERS[params.helper]
    place = PLACES[params.place]
    motive = MOTIVES[params.motive]
    if not valid_combo(helper, place, motive):
        raise StoryError(explain_rejection(helper, place, motive))

    world = tell(
        celebration=CELEBRATIONS[params.celebration],
        item_cfg=ITEMS[params.item],
        helper_cfg=helper,
        place_cfg=place,
        motive_cfg=motive,
        hero_name=params.hero_name,
        trust=params.trust,
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
        print(asp_program("", "#show valid/4.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (celebration, helper, place, motive) combos:\n")
        for c, h, p, m in combos:
            print(f"  {c:12} {h:9} {p:12} {m}")
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
                f"### {p.hero_name}: {p.item} missing before {p.celebration} "
                f"({p.helper} -> {p.place}, {p.motive}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
