#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sheaf_suspense_sharing_myth.py
==============================================================

A small mythic storyworld about a village that stores grain in a sacred sheaf,
a child feels suspense before the harvest is shared, and the ending proves that
the gift was divided wisely.

The world is built around:
- a sheaf of grain
- suspense: the sheaf may be lost, stolen, or ruined before the rite
- sharing: the harvest is divided among people and a hungry helper
- myth style: a quiet, folkloric voice with a small wonder at the end
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
FEAR_SPIKE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "queen"}
        male = {"boy", "father", "man", "brother", "king"}
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

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Harvest:
    id: str
    grain: str
    sheaf_name: str
    place: str
    scent: str
    risk: int = 0
    shareable: bool = True
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
class Keeper:
    id: str
    label: str
    title: str
    watchword: str
    calmness: int
    share_power: int
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
class Hazard:
    id: str
    label: str
    scent: str
    threat: int
    can_hide: bool = True
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
class ShareWay:
    id: str
    name: str
    method: str
    effect: str
    strength: int
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


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    if "sheaf" not in world.entities:
        return out
    sheaf = world.get("sheaf")
    if sheaf.meters["at_risk"] < THRESHOLD:
        return out
    sig = ("suspense",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"child", "keeper"}:
            ent.memes["fear"] += 1
    world.get("crowd").meters["quiet"] += 1
    out.append("__suspense__")
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    sheaf = world.get("sheaf")
    if sheaf.meters["shared"] < THRESHOLD:
        return out
    sig = ("release",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("crowd").meters["hope"] += 1
    out.append("__release__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    sheaf = world.get("sheaf")
    if sheaf.meters["opened"] < THRESHOLD:
        return out
    sig = ("share",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for ent in list(world.entities.values()):
        if ent.role in {"child", "keeper", "hungry_one"}:
            ent.memes["relief"] += 1
    out.append("__share__")
    return out


CAUSAL_RULES = [
    Rule("suspense", "social", _r_suspense),
    Rule("release", "social", _r_release),
    Rule("share", "social", _r_share),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sent = rule.apply(world)
            if sent:
                changed = True
                out.extend(s for s in sent if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def danger_level(hazard: Hazard, harvest: Harvest, delay: int) -> int:
    return hazard.threat + harvest.risk + delay


def can_share(way: ShareWay, harvest: Harvest, keeper: Keeper) -> bool:
    return way.strength + keeper.share_power >= harvest.risk + 1


def honest_hazard(hazard: Hazard, harvest: Harvest) -> bool:
    return hazard.can_hide and harvest.shareable


def predict_fate(world: World, hazard_id: str, delay: int) -> dict:
    sim = world.copy()
    _apply_hazard(sim, sim.get(hazard_id), narrate=False)
    return {
        "risk": sim.get("sheaf").meters["at_risk"] >= THRESHOLD,
        "quiet": sim.get("crowd").meters["quiet"],
        "opened": sim.get("sheaf").meters["opened"] >= THRESHOLD,
        "shared": sim.get("sheaf").meters["shared"] >= THRESHOLD,
        "delay": delay,
    }


def _apply_hazard(world: World, hazard_ent: Entity, narrate: bool = True) -> None:
    hazard_ent.meters["at_risk"] += 1
    world.get("sheaf").meters["at_risk"] += 1
    propagate(world, narrate=narrate)


def _open_sheaf(world: World, keeper: Keeper, sheaf: Entity, way: ShareWay) -> None:
    sheaf.meters["opened"] += 1
    sheaf.meters["shared"] += 1
    world.get("crowd").meters["shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{keeper.label.capitalize()} lifted the twine with {way.method}, and the sheaf opened like a goldbird's wing."
    )


def _scare(world: World, child: Entity, hazard: Hazard, keeper: Keeper) -> None:
    world.say(
        f"{child.id} saw the {hazard.label} hiding near the threshing floor and held {child.pronoun('possessive')} breath."
    )
    world.say(
        f'"What if the sheaf is lost?" {child.id} whispered. {keeper.label.capitalize()} heard the hush and came closer.'
    )


def _warn(world: World, keeper: Keeper, child: Entity, hazard: Hazard) -> None:
    child.memes["alert"] += 1
    pred = predict_fate(world, hazard.id, 0)
    world.facts["predicted_quiet"] = pred["quiet"]
    world.say(
        f'"{keeper.watchword}," {keeper.label} said. "Stay near the lantern. The {hazard.label} can scatter the grain if we rush."'
    )


def _choose_delay(world: World, delay: int) -> None:
    if delay > 0:
        world.say("The moon hung still, and the people waited one tense breath before touching the sheaf.")


def _share_all(world: World, keeper: Keeper, child: Entity, hungry: Entity, way: ShareWay) -> None:
    child.memes["joy"] += 1
    hungry.memes["joy"] += 1
    keeper.memes["joy"] += 1
    world.say(
        f"{keeper.label.capitalize()} nodded to the child and the hungry wanderer."
    )
    world.say(
        f'"We do not keep a blessing in our hands forever," {keeper.label} said. "We share it."'
    )
    _open_sheaf(world, keeper, world.get("sheaf"), way)
    world.say(
        f"They divided the grain into three warm piles, and even the air seemed sweeter for it."
    )


def tell(harvest: Harvest, keeper: Keeper, hazard: Hazard, way: ShareWay, delay: int,
         child_name: str = "Nia", child_gender: str = "girl",
         hungry_name: str = "Maro", hungry_gender: str = "boy") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=keeper.id, kind="character", type="keeper", label=keeper.label, role="keeper"))
    hungry = world.add(Entity(id=hungry_name, kind="character", type=hungry_gender, role="hungry_one"))
    crowd = world.add(Entity(id="crowd", kind="thing", type="crowd", label="the waiting crowd"))
    sheaf = world.add(Entity(id="sheaf", kind="thing", type="sheaf", label=harvest.sheaf_name))
    danger = world.add(Entity(id=hazard.id, kind="thing", type="hazard", label=hazard.label))

    world.facts.update(harvest=harvest, keeper=keeper, hazard=hazard, way=way, delay=delay)

    world.say(
        f"In the old village, {child.id} watched over {harvest.sheaf_name}, the first sheaf from the barley fields."
    )
    world.say(
        f"It was said that when the grain smelled of sun and rain, a blessing slept inside it."
    )
    world.para()
    _scare(world, child, hazard, elder)
    _warn(world, elder, child, hazard)
    _choose_delay(world, delay)

    if honest_hazard(hazard, harvest):
        _apply_hazard(world, danger)
    world.para()

    if can_share(way, harvest, keeper):
        _share_all(world, elder, child, hungry, way)
        outcome = "shared"
    else:
        world.say(
            f"{elder.label.capitalize()} found the knot too tight for {way.name}, and the village had to wait until dawn."
        )
        world.say(
            f"At sunrise, they used a stronger cord and opened the sheaf without tearing the grain."
        )
        _open_sheaf(world, elder, world.get("sheaf"), way)
        world.say(
            f"Then everyone received a handful, and the hungry wanderer left with a fuller heart."
        )
        outcome = "delayed_shared"

    world.facts["outcome"] = outcome
    world.facts["child"] = child
    world.facts["hungry"] = hungry
    world.facts["crowd"] = crowd
    world.facts["sheaf_entity"] = sheaf
    return world


@dataclass
class StoryParams:
    harvest: str
    keeper: str
    hazard: str
    share_way: str
    delay: int = 0
    child_name: str = "Nia"
    child_gender: str = "girl"
    hungry_name: str = "Maro"
    hungry_gender: str = "boy"
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


HARVESTS = {
    "barley": Harvest(id="barley", grain="barley", sheaf_name="the barley sheaf", place="threshing floor", scent="sun-warm grain", risk=1, tags={"grain", "sheaf"}),
    "wheat": Harvest(id="wheat", grain="wheat", sheaf_name="the wheat sheaf", place="barn", scent="sweet straw", risk=1, tags={"grain", "sheaf"}),
    "oats": Harvest(id="oats", grain="oats", sheaf_name="the oat sheaf", place="granary", scent="dusty sweetness", risk=1, tags={"grain", "sheaf"}),
}

KEEPERS = {
    "grandmother": Keeper(id="grandmother", label="Grandmother Iri", title="grandmother", watchword="steady now", calmness=3, share_power=2, tags={"elder", "myth"}),
    "priest": Keeper(id="priest", label="Priest Orin", title="priest", watchword="soft hands", calmness=4, share_power=3, tags={"elder", "myth"}),
    "weaver": Keeper(id="weaver", label="Weaver Sela", title="weaver", watchword="gentle now", calmness=3, share_power=2, tags={"elder", "myth"}),
}

HAZARDS = {
    "wind": Hazard(id="wind", label="wind", scent="cold dust", threat=1, can_hide=True, tags={"suspense"}),
    "fox": Hazard(id="fox", label="fox-shadow", scent="wild fur", threat=2, can_hide=True, tags={"suspense"}),
    "thief": Hazard(id="thief", label="thief's step", scent="mud and iron", threat=3, can_hide=True, tags={"suspense"}),
}

SHAREWAYS = {
    "cut": ShareWay(id="cut", name="cut twine", method="a small knife", effect="cleanly split the bundles", strength=2, tags={"sharing"}),
    "untie": ShareWay(id="untie", name="untie twine", method="patient fingers", effect="loosened the knot", strength=1, tags={"sharing"}),
    "braid": ShareWay(id="braid", name="braid a cord", method="a braided reed cord", effect="held the grain in kindly loops", strength=3, tags={"sharing"}),
}

GIRL_NAMES = ["Nia", "Liora", "Sera", "Mina", "Iva"]
BOY_NAMES = ["Maro", "Tavi", "Eren", "Bela", "Jorin"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for h in HARVESTS:
        for k in KEEPERS:
            for hz in HAZARDS:
                for sw in SHAREWAYS:
                    if honest_hazard(HAZARDS[hz], HARVESTS[h]):
                        combos.append((h, k, hz, sw))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld about a sheaf, suspense, and sharing.")
    ap.add_argument("--harvest", choices=HARVESTS)
    ap.add_argument("--keeper", choices=KEEPERS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--share-way", choices=SHAREWAYS)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=0)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--hungry-name")
    ap.add_argument("--hungry-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.share_way and args.harvest and args.keeper:
        if not can_share(SHAREWAYS[args.share_way], HARVESTS[args.harvest], KEEPERS[args.keeper]):
            raise StoryError("That sharing method is too weak to open the sheaf kindly.")
    if args.hazard and args.harvest:
        if not honest_hazard(HAZARDS[args.hazard], HARVESTS[args.harvest]):
            raise StoryError("That hazard does not create a real suspenseful risk for this sheaf.")
    combos = [c for c in valid_combos()
              if (args.harvest is None or c[0] == args.harvest)
              and (args.keeper is None or c[1] == args.keeper)
              and (args.hazard is None or c[2] == args.hazard)
              and (args.share_way is None or c[3] == args.share_way)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    harvest, keeper, hazard, share_way = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    hungry_gender = args.hungry_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    hungry_name = args.hungry_name or rng.choice(GIRL_NAMES + BOY_NAMES)
    return StoryParams(
        harvest=harvest,
        keeper=keeper,
        hazard=hazard,
        share_way=share_way,
        delay=args.delay,
        child_name=child_name,
        child_gender=child_gender,
        hungry_name=hungry_name,
        hungry_gender=hungry_gender,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child that includes the word "sheaf" and ends with sharing grain.',
        f"Tell a suspenseful village tale where {f['child'].id} worries over {f['harvest'].sheaf_name} and the people decide how to share it.",
        f"Write a gentle myth about an old harvest, a hidden danger, and a sharing that makes the village safer and kinder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    harvest: Harvest = f["harvest"]
    keeper: Keeper = f["keeper"]
    hazard: Hazard = f["hazard"]
    way: ShareWay = f["way"]
    child: Entity = f["child"]
    hungry: Entity = f["hungry"]
    qa = [
        QAItem(
            question="What was the story's important thing?",
            answer=f"The important thing was {harvest.sheaf_name}. In the myth, everyone watched over it because it held the village's first grain."
        ),
        QAItem(
            question="Why was the story suspenseful?",
            answer=f"There was suspense because {hazard.label} might trouble the sheaf before the sharing rite. The child had to wait in the hush and listen for what would happen next."
        ),
        QAItem(
            question="How did they solve the problem?",
            answer=f"{keeper.label} used {way.method} to open the sheaf and share the grain. That careful sharing kept the blessing from being lost."
        ),
    ]
    if f.get("outcome") == "shared":
        qa.append(QAItem(
            question=f"What did {child.id} and {hungry.id} receive at the end?",
            answer=f"They each received a share of grain, and the hungry wanderer left with a fuller heart. The ending showed that the sheaf was not kept away from others."
        ))
    else:
        qa.append(QAItem(
            question="What changed by the ending?",
            answer="The knot was opened at last, and the grain was divided among the people. The village moved from waiting to sharing."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(
            question="What is a sheaf?",
            answer="A sheaf is a bundle of cut grain tied together with straw or twine. Farmers make sheaves so the harvest can be carried and stored."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means giving parts of something to other people instead of keeping all of it. It is a kind way to make sure everyone gets some."
        ),
    ]
    if f["hazard"].id == "thief":
        out.append(QAItem(
            question="Why are people careful when they think someone might steal?",
            answer="Because a thief can take something away before it is safely stored or shared. Being careful helps protect what the people need."
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
hazard(H) :- hazard(H).
shareway(W) :- way(W).
honest(H, S) :- hazard(H), harvest(S), can_hide(H), shareable(S).
valid(H, K, Z, W) :- honest(H, S), keeper(K), hazard(Z), shareway(W).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for hid, h in HARVESTS.items():
        lines.append(asp.fact("harvest", hid))
        if h.shareable:
            lines.append(asp.fact("shareable", hid))
    for kid in KEEPERS:
        lines.append(asp.fact("keeper", kid))
    for zid, z in HAZARDS.items():
        lines.append(asp.fact("hazard", zid))
        if z.can_hide:
            lines.append(asp.fact("can_hide", zid))
    for wid in SHAREWAYS:
        lines.append(asp.fact("way", wid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between clingo and Python valid_combos().")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test crashed: {exc}")
        rc = 1
    return rc


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_name(args: argparse.Namespace, rng: random.Random, gender: str, provided: Optional[str]) -> str:
    return provided or _pick_name(rng, gender)


def generate(params: StoryParams) -> StorySample:
    for key, reg in [("harvest", HARVESTS), ("keeper", KEEPERS), ("hazard", HAZARDS), ("share_way", SHAREWAYS)]:
        if getattr(params, key) not in reg:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(
        HARVESTS[params.harvest],
        KEEPERS[params.keeper],
        HAZARDS[params.hazard],
        SHAREWAYS[params.share_way],
        params.delay,
        child_name=params.child_name,
        child_gender=params.child_gender,
        hungry_name=params.hungry_name,
        hungry_gender=params.hungry_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
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


def tell(harvest: Harvest, keeper: Keeper, hazard: Hazard, way: ShareWay, delay: int,
         child_name: str, child_gender: str, hungry_name: str, hungry_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    elder = world.add(Entity(id=keeper.id, kind="character", type="queen" if "Grandmother" in keeper.label else "woman", label=keeper.label, role="keeper"))
    hungry = world.add(Entity(id=hungry_name, kind="character", type=hungry_gender, role="hungry_one"))
    crowd = world.add(Entity(id="crowd", kind="thing", label="the crowd"))
    sheaf = world.add(Entity(id="sheaf", kind="thing", label=harvest.sheaf_name))
    threat = world.add(Entity(id=hazard.id, kind="thing", label=hazard.label))

    world.say(f"Long ago, in a village of dust and moonlight, {child.id} guarded {harvest.sheaf_name}.")
    world.say("The people said the first sheaf carried the promise of bread for the winter.")
    world.para()
    child.memes["wonder"] += 1
    elder.memes["calm"] += 1
    world.say(f"{child.id} felt a hush in the chest when {hazard.label} moved near the threshing floor.")
    world.say(f'{keeper.label} raised a hand. "Steady now," {keeper.label_word if False else elder.id} said, and the lantern flame stayed small.')
    if delay > 0:
        world.say("For one long beat, no one touched the twine.")
    _apply_hazard(world, threat)
    world.para()
    if can_share(way, harvest, keeper):
        world.say(f"{elder.label.capitalize()} smiled at {child.id} and the hungry wanderer.")
        world.say(f'"No blessing is whole until it is shared," {elder.label} said.')
        _open_sheaf(world, keeper, sheaf, way)
        world.say(f"{child.id} and {hungry.id} received grain warm as morning sun.")
        world.say("The village ate, and the sheaf's worry became a feast.")
        outcome = "shared"
    else:
        raise StoryError("Unreachable: no valid share way.")
    world.facts.update(harvest=harvest, keeper=keeper, hazard=hazard, way=way, child=child, hungry=hungry, outcome=outcome)
    return world


CURATED = [
    StoryParams(harvest="barley", keeper="grandmother", hazard="fox", share_way="cut", delay=0, child_name="Nia", child_gender="girl", hungry_name="Maro", hungry_gender="boy"),
    StoryParams(harvest="wheat", keeper="priest", hazard="thief", share_way="braid", delay=1, child_name="Liora", child_gender="girl", hungry_name="Tavi", hungry_gender="boy"),
    StoryParams(harvest="oats", keeper="weaver", hazard="wind", share_way="untie", delay=0, child_name="Sera", child_gender="girl", hungry_name="Eren", hungry_gender="boy"),
]


def explain_rejection(harvest: Harvest, hazard: Hazard) -> str:
    return f"(No story: the {hazard.label} does not create enough suspense for {harvest.sheaf_name}.)"


def explain_shareway(way: ShareWay, keeper: Keeper) -> str:
    return f"(No story: {keeper.label} cannot safely use {way.name} to share the sheaf.)"


def build_choice_lists(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.harvest is None or c[0] == args.harvest)
              and (args.keeper is None or c[1] == args.keeper)
              and (args.hazard is None or c[2] == args.hazard)
              and (args.share_way is None or c[3] == args.share_way)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    harvest, keeper, hazard, way = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    hungry_gender = args.hungry_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        harvest=harvest,
        keeper=keeper,
        hazard=hazard,
        share_way=way,
        delay=args.delay,
        child_name=args.child_name or _pick_name(rng, child_gender),
        child_gender=child_gender,
        hungry_name=args.hungry_name or _pick_name(rng, hungry_gender),
        hungry_gender=hungry_gender,
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
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
                params = build_choice_lists(args, random.Random(seed))
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
            header = f"### {p.child_name}: {p.harvest}, {p.hazard}, {p.share_way}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
