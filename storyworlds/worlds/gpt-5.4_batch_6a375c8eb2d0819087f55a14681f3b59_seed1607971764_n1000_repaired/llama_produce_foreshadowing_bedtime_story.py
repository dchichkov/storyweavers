#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py
=======================================================================

A standalone storyworld for a soft bedtime tale with **foreshadowing**:
a child and a gentle llama bring evening produce in from the garden, notice
a small warning sign, face a spill when they hurry anyway, and then solve the
problem in a calm, sensible way before bed.

The world model tracks physical meters (wobble, spill, bruise, darkness) and
emotional memes (calm, worry, hurry, relief). The middle turn is driven by a
predicted hazard: a creak, wobble, or slipping load foreshadows that the trip
is not safe as-is. The resolution depends on whether the chosen fix is actually
compatible with the cause of the trouble.

Run it
------
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py --produce pumpkins --carrier basket
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py --fix sing
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/llama_produce_foreshadowing_bedtime_story.py --verify
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
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
    sky: str
    sound: str
    path_detail: str
    bedtime_image: str
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
class Produce:
    id: str
    label: str
    phrase: str
    plural: bool
    weight: int
    roll: int
    bruise: int
    hush_end: str
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
class Carrier:
    id: str
    label: str
    phrase: str
    capacity: int
    stable: int
    issue: str
    foreshadow: str
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
class PathType:
    id: str
    label: str
    bumpiness: int
    line: str
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
class Fix:
    id: str
    label: str
    sense: int
    helps: set[str]
    risk_drop: int
    text: str
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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


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


def _r_warning(world: World) -> list[str]:
    carrier = world.get("carrier")
    if carrier.meters["risk"] < THRESHOLD:
        return []
    sig = ("warning", carrier.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    kid = world.get("child")
    llama = world.get("llama")
    kid.memes["worry"] += 1
    llama.memes["worry"] += 1
    return ["__warning__"]


def _r_spill(world: World) -> list[str]:
    carrier = world.get("carrier")
    produce = world.get("produce")
    if carrier.meters["tipped"] < THRESHOLD:
        return []
    sig = ("spill", produce.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    produce.meters["spilled"] += 1
    if world.facts.get("bruise_factor", 0) > 0:
        produce.meters["bruised"] += 1
    for eid in ("child", "llama"):
        world.get(eid).memes["alarm"] += 1
    return ["__spill__"]


CAUSAL_RULES = [
    Rule(name="warning", tag="foreshadow", apply=_r_warning),
    Rule(name="spill", tag="physical", apply=_r_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def hazard_kind(produce: Produce, carrier: Carrier, path: PathType) -> Optional[str]:
    if produce.weight > carrier.capacity:
        return "overload"
    if produce.roll >= 2 and carrier.stable + path.bumpiness <= 2:
        return "rolling"
    if path.bumpiness >= 2 and carrier.stable <= 1:
        return "wobble"
    return None


def base_risk(produce: Produce, carrier: Carrier, path: PathType) -> int:
    cause = hazard_kind(produce, carrier, path)
    if cause == "overload":
        return 3
    if cause == "rolling":
        return 2
    if cause == "wobble":
        return 2
    return 0


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for produce_id, produce in PRODUCE.items():
            for carrier_id, carrier in CARRIERS.items():
                if hazard_kind(produce, carrier, PATHS[setting_id]) is not None:
                    combos.append((setting_id, produce_id, carrier_id))
    return combos


def sensible_fixes() -> list[Fix]:
    return [fix for fix in FIXES.values() if fix.sense >= SENSE_MIN]


def fix_works(fix: Fix, produce: Produce, carrier: Carrier, path: PathType) -> bool:
    cause = hazard_kind(produce, carrier, path)
    if cause is None:
        return False
    return cause in fix.helps and (base_risk(produce, carrier, path) - fix.risk_drop) <= 0


def outcome_of(params: "StoryParams") -> str:
    produce = PRODUCE[params.produce]
    carrier = CARRIERS[params.carrier]
    path = PATHS[params.setting]
    fix = FIXES[params.fix]
    return "saved" if fix_works(fix, produce, carrier, path) else "spilled"


def explain_rejection(produce: Produce, carrier: Carrier, path: PathType) -> str:
    return (
        f"(No story: {carrier.phrase} carrying {produce.phrase} over {path.label} "
        f"does not create enough trouble to foreshadow a spill. Pick a shakier "
        f"carrier, a heavier produce load, or a bumpier path.)"
    )


def explain_fix(fid: str, produce: Produce, carrier: Carrier, path: PathType) -> str:
    fix = FIXES[fid]
    cause = hazard_kind(produce, carrier, path)
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fid}': it is too weak for this world "
            f"(sense={fix.sense} < {SENSE_MIN}). Bedtime stories here prefer calm, "
            f"helpful solutions.)"
        )
    return (
        f"(No story: {fix.label} does not solve the problem. The trouble here is "
        f"{cause}, so the fix must actually steady the load.)"
    )


def predict_spill(world: World) -> dict:
    sim = world.copy()
    carrier = sim.get("carrier")
    carrier.meters["tipped"] += 1
    propagate(sim, narrate=False)
    return {
        "spill": sim.get("produce").meters["spilled"] >= THRESHOLD,
        "bruised": sim.get("produce").meters["bruised"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, llama: Entity, helper: Entity,
              setting: Setting, produce: Produce, carrier: Carrier) -> None:
    child.memes["calm"] += 1
    llama.memes["calm"] += 1
    world.say(
        f"In {setting.place}, when the sky was {setting.sky} and {setting.sound}, "
        f"{child.id} helped a sleepy llama named {llama.id} bring in {produce.phrase}."
    )
    world.say(
        f"{helper.label_word.capitalize()} had set out {carrier.phrase}, and the two "
        f"friends moved slowly so the evening could stay soft."
    )


def bedtime_goal(world: World, child: Entity, llama: Entity, produce: Produce,
                 setting: Setting) -> None:
    world.say(
        f"They wanted to tuck the produce away before bed, while the garden still "
        f"held a little warmth and {setting.path_detail}."
    )
    world.say(
        f"{llama.id} breathed a sleepy hum, and {child.id} stroked {llama.pronoun('possessive')} "
        f"neck as if even chores could whisper good night."
    )


def foreshadow(world: World, child: Entity, llama: Entity, produce: Produce,
               carrier: Carrier, path: PathType) -> None:
    carrier_ent = world.get("carrier")
    carrier_ent.meters["risk"] = float(base_risk(produce, carrier, path))
    world.facts["cause"] = hazard_kind(produce, carrier, path)
    world.facts["predicted"] = predict_spill(world)
    propagate(world, narrate=False)
    extra = ""
    if world.facts["cause"] == "overload":
        extra = " The load sat a little too high."
    elif world.facts["cause"] == "rolling":
        extra = " Round things inside kept nudging one another."
    elif world.facts["cause"] == "wobble":
        extra = " Each small bump made the trip feel less steady."
    world.say(
        f"But before they had gone far, {carrier.foreshadow}.{extra}"
    )
    world.say(
        f"{child.id} paused. \"Did you hear that?\" {child.pronoun()} whispered. "
        f"{llama.id} lifted {llama.pronoun('possessive')} ears toward {path.line.lower()}."
    )


def hurry(world: World, child: Entity, llama: Entity, helper: Entity) -> None:
    child.memes["hurry"] += 1
    world.say(
        f'"It is only a little way," said {child.id}, hoping they could finish '
        f'before it grew any darker.'
    )
    world.say(
        f"{llama.id} took another careful step, but the wish to be done tugged them onward."
    )


def accident(world: World, child: Entity, llama: Entity, produce: Produce,
             carrier: Carrier, path: PathType) -> None:
    carrier_ent = world.get("carrier")
    carrier_ent.meters["tipped"] += 1
    propagate(world, narrate=False)
    line = {
        "overload": f"the heavy load leaned hard to one side of the {carrier.label}",
        "rolling": f"the round {produce.label} rolled together inside the {carrier.label}",
        "wobble": f"the {carrier.label} gave a sharp little wobble on {path.label}",
    }[hazard_kind(produce, carrier, path)]
    world.say(
        f"Then, right where {path.line.lower()}, {line}, and everything slipped."
    )
    if produce.plural:
        bruise = "A few bumped softly into the grass" if produce.bruise else "They scattered in a sleepy little rush"
    else:
        bruise = "It landed with a soft thump"
    world.say(
        f"{bruise}. {child.id} gasped, and {llama.id} stopped so suddenly that the bells on "
        f"{llama.pronoun('possessive')} halter barely chimed."
    )


def helper_arrives(world: World, helper: Entity, child: Entity, llama: Entity) -> None:
    helper.memes["calm"] += 1
    child.memes["relief"] += 1
    llama.memes["relief"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came out with a lantern glow behind {helper.pronoun('object')} "
        f"and knelt beside the path."
    )
    world.say(
        f"\"It is all right,\" {helper.pronoun()} said. \"The warning was trying to tell us something.\""
    )


def repair(world: World, helper: Entity, child: Entity, llama: Entity,
           produce: Produce, carrier: Carrier, path: PathType, fix: Fix) -> None:
    world.get("carrier").meters["risk"] = 0.0
    child.memes["lesson"] += 1
    llama.memes["lesson"] += 1
    child.memes["alarm"] = 0.0
    llama.memes["alarm"] = 0.0
    world.say(
        f"Together they {fix.text}."
    )
    world.say(
        f"After that, the trip felt different: slower, steadier, and kind."
    )


def bedtime_end_safe(world: World, child: Entity, llama: Entity, helper: Entity,
                     produce: Produce, setting: Setting) -> None:
    child.memes["sleepy"] += 1
    llama.memes["sleepy"] += 1
    child.memes["relief"] += 1
    llama.memes["relief"] += 1
    world.say(
        f"They carried the produce the rest of the way without another tumble, and soon "
        f"the kitchen smelled sweet and earthy."
    )
    world.say(
        f"Later, {child.id} tucked a blanket over {llama.id}. {setting.bedtime_image}, "
        f"and {produce.hush_end}."
    )


def bedtime_end_spilled(world: World, child: Entity, llama: Entity, helper: Entity,
                        produce: Produce, carrier: Carrier, fix: Fix,
                        setting: Setting) -> None:
    child.memes["sleepy"] += 1
    llama.memes["sleepy"] += 1
    child.memes["sad"] += 1
    llama.memes["sad"] += 1
    world.say(
        f"They tried to keep going after that, but {fix.text}, and the path stayed messy."
    )
    if world.get("produce").meters["bruised"] >= THRESHOLD:
        world.say(
            f"Some of the {produce.label} had been bruised, so they could not all be tucked away for breakfast."
        )
    else:
        world.say(
            f"Not everything was lost, but the evening chore ended in a tired little muddle."
        )
    world.say(
        f"That night {child.id} lay very still, remembering the first small sound. "
        f"{setting.bedtime_image}, and next time even a tiny warning would matter."
    )


def tell(setting: Setting, produce: Produce, carrier: Carrier, path: PathType,
         fix: Fix, child_name: str = "Nora", child_gender: str = "girl",
         llama_name: str = "Moss", helper_type: str = "grandmother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    llama = world.add(Entity(id=llama_name, kind="character", type="llama", role="llama"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, role="helper"))
    world.add(Entity(id="carrier", kind="thing", type="carrier", label=carrier.label))
    world.add(Entity(id="produce", kind="thing", type="produce", label=produce.label))

    world.facts["bruise_factor"] = produce.bruise
    world.facts["setting"] = setting
    world.facts["produce_cfg"] = produce
    world.facts["carrier_cfg"] = carrier
    world.facts["path_cfg"] = path
    world.facts["fix_cfg"] = fix
    world.facts["child"] = child
    world.facts["llama"] = llama
    world.facts["helper"] = helper

    introduce(world, child, llama, helper, setting, produce, carrier)
    bedtime_goal(world, child, llama, produce, setting)

    world.para()
    foreshadow(world, child, llama, produce, carrier, path)
    hurry(world, child, llama, helper)

    world.para()
    accident(world, child, llama, produce, carrier, path)
    helper_arrives(world, helper, child, llama)

    world.para()
    if fix_works(fix, produce, carrier, path):
        repair(world, helper, child, llama, produce, carrier, path, fix)
        bedtime_end_safe(world, child, llama, helper, produce, setting)
        outcome = "saved"
    else:
        bedtime_end_spilled(world, child, llama, helper, produce, carrier, fix, setting)
        outcome = "spilled"

    world.facts.update(
        outcome=outcome,
        cause=hazard_kind(produce, carrier, path),
        predicted_spill=world.facts.get("predicted", {}).get("spill", False),
        bruised=world.get("produce").meters["bruised"] >= THRESHOLD,
        fix_worked=(outcome == "saved"),
    )
    return world


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="a little garden behind the house",
        sky="turning lavender",
        sound="the crickets had begun their thin night song",
        path_detail="dew was gathering on the bean leaves",
        bedtime_image="Outside, the moon rested over the fence like a pale round button",
    ),
    "orchard": Setting(
        id="orchard",
        place="the orchard at the edge of the yard",
        sky="soft blue with one early star",
        sound="leaves whispered over the grass",
        path_detail="the pear trees smelled cool and sleepy",
        bedtime_image="By the window, the star had climbed higher and the room felt hushed",
    ),
    "patch": Setting(
        id="patch",
        place="the vegetable patch near the barn",
        sky="dim and golden at the edges",
        sound="the barn swallows were settling down",
        path_detail="the last warm light lay in stripes across the dirt",
        bedtime_image="In the loft, the barn beams held the night as gently as hands",
    ),
}

PATHS = {
    "garden": PathType(
        id="stone",
        label="the stone path",
        bumpiness=2,
        line="the stone path bent past the mint bed",
        tags={"path", "stone"},
    ),
    "orchard": PathType(
        id="roots",
        label="the root-crossed path",
        bumpiness=2,
        line="the root-crossed path dipped under the trees",
        tags={"path", "roots"},
    ),
    "patch": PathType(
        id="grass",
        label="the grassy walk",
        bumpiness=1,
        line="the grassy walk curved beside the barn",
        tags={"path", "grass"},
    ),
}

PRODUCE = {
    "pumpkins": Produce(
        id="pumpkins",
        label="pumpkins",
        phrase="three round pumpkins",
        plural=True,
        weight=3,
        roll=2,
        bruise=1,
        hush_end="the sleepy llama gave one last happy snuffle into the straw",
        tags={"pumpkins", "produce"},
    ),
    "apples": Produce(
        id="apples",
        label="apples",
        phrase="a basket of red apples",
        plural=True,
        weight=2,
        roll=2,
        bruise=1,
        hush_end="the apples sat in a bowl, rosy and still in the moonlight",
        tags={"apples", "produce"},
    ),
    "carrots": Produce(
        id="carrots",
        label="carrots",
        phrase="a bundle of carrots with feathery tops",
        plural=True,
        weight=2,
        roll=0,
        bruise=0,
        hush_end="the carrots waited on the table with their green tops drooping softly",
        tags={"carrots", "produce"},
    ),
    "tomatoes": Produce(
        id="tomatoes",
        label="tomatoes",
        phrase="a shallow tray of tomatoes",
        plural=True,
        weight=1,
        roll=1,
        bruise=1,
        hush_end="the tomatoes glowed like small red lamps in the pantry basket",
        tags={"tomatoes", "produce"},
    ),
}

CARRIERS = {
    "basket": Carrier(
        id="basket",
        label="basket",
        phrase="a woven basket",
        capacity=2,
        stable=1,
        issue="one handle was stretched and tired",
        foreshadow="the basket handle gave a dry little creak",
        tags={"basket"},
    ),
    "wagon": Carrier(
        id="wagon",
        label="wagon",
        phrase="a small wooden wagon",
        capacity=3,
        stable=1,
        issue="one wheel liked to wobble on bumps",
        foreshadow="one wagon wheel made a tiny side-to-side shimmy",
        tags={"wagon"},
    ),
    "tray": Carrier(
        id="tray",
        label="tray",
        phrase="a shallow garden tray",
        capacity=1,
        stable=0,
        issue="its smooth bottom let round things slide",
        foreshadow="something inside the tray slipped with a soft skitter",
        tags={"tray"},
    ),
}

FIXES = {
    "two_trips": Fix(
        id="two_trips",
        label="make two small trips",
        sense=3,
        helps={"overload"},
        risk_drop=3,
        text="split the load and made two small trips instead of one big one",
        qa_text="They solved the problem by splitting the load and carrying it in two smaller trips",
        tags={"two_trips", "careful"},
    ),
    "tie_handle": Fix(
        id="tie_handle",
        label="tie the loose handle with twine",
        sense=3,
        helps={"overload"},
        risk_drop=1,
        text="tied the basket handle snugly with twine and carried less at a time",
        qa_text="They tied the loose handle with twine and carried less at a time",
        tags={"twine", "repair"},
    ),
    "blanket_ring": Fix(
        id="blanket_ring",
        label="nestle the round produce in a blanket ring",
        sense=3,
        helps={"rolling"},
        risk_drop=2,
        text="lined the carrier with a folded blanket so the round produce could not roll together",
        qa_text="They lined the carrier with a folded blanket so the produce would not roll",
        tags={"blanket", "steady"},
    ),
    "tighten_wheel": Fix(
        id="tighten_wheel",
        label="tighten the wagon wheel",
        sense=3,
        helps={"wobble"},
        risk_drop=2,
        text="tightened the little wagon wheel and tested it before moving again",
        qa_text="They tightened the wagon wheel before setting off again",
        tags={"wheel", "repair"},
    ),
    "sing": Fix(
        id="sing",
        label="sing a soft walking song",
        sense=1,
        helps=set(),
        risk_drop=0,
        text="sang a soft walking song to feel brave",
        qa_text="They only tried singing, which did not steady the load",
        tags={"song"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Ava", "Ella", "Ruby", "June", "Cora"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Eli", "Theo", "Finn", "Otis"]
LLAMA_NAMES = ["Moss", "Clover", "Pip", "Thimble", "Pebble", "Fern"]
HELPERS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
class StoryParams:
    setting: str
    produce: str
    carrier: str
    fix: str
    child_name: str
    child_gender: str
    llama_name: str
    helper: str
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
    "produce": [
        (
            "What does produce mean?",
            "Produce means fruits and vegetables that are grown and picked. People bring produce in from gardens, farms, and orchards.",
        )
    ],
    "llama": [
        (
            "What is a llama?",
            "A llama is a gentle animal with long legs, a long neck, and a soft woolly coat. People sometimes keep llamas on farms.",
        )
    ],
    "pumpkins": [
        (
            "Why do pumpkins roll so easily?",
            "Pumpkins are round and heavy, so when they are on a bumpy path they can start rolling. That makes them hard to carry in a shaky container.",
        )
    ],
    "apples": [
        (
            "Why can apples spill out of a carrier?",
            "Apples are round and smooth, so they can roll into one another. If a basket tilts, they can slip right out.",
        )
    ],
    "carrots": [
        (
            "Why are carrots easier to carry than pumpkins?",
            "Carrots are not round, so they do not roll the way pumpkins do. They can still be heavy in a big bundle, though.",
        )
    ],
    "basket": [
        (
            "What is a basket good for?",
            "A basket is good for carrying light things together. If it gets too full or a handle gets weak, it can tip or strain.",
        )
    ],
    "wagon": [
        (
            "Why should a wagon wheel be checked?",
            "A wagon needs steady wheels to roll safely. If a wheel wobbles, the wagon can tip when it hits bumps.",
        )
    ],
    "twine": [
        (
            "What is twine used for?",
            "Twine is a strong thin string used for tying things together. It can help hold a loose handle or bundle steady.",
        )
    ],
    "blanket": [
        (
            "How can a blanket keep round things from rolling?",
            "A folded blanket makes a soft nest around the things inside. That helps stop them from sliding and bumping together.",
        )
    ],
    "wheel": [
        (
            "Why is tightening a wheel helpful?",
            "A loose wheel wiggles when it should stay straight. Tightening it helps the wagon roll smoothly and safely.",
        )
    ],
    "careful": [
        (
            "Why can two small trips be safer than one big trip?",
            "A smaller load is easier to balance and easier to carry. Going more slowly can stop an accident before it starts.",
        )
    ],
    "foreshadow": [
        (
            "What is foreshadowing in a story?",
            "Foreshadowing is a small clue that hints something may happen later. A creak or wobble can warn readers before the real trouble begins.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "llama",
    "produce",
    "pumpkins",
    "apples",
    "carrots",
    "basket",
    "wagon",
    "twine",
    "blanket",
    "wheel",
    "careful",
    "foreshadow",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    llama = f["llama"]
    produce = f["produce_cfg"]
    carrier = f["carrier_cfg"]
    fix = f["fix_cfg"]
    cause = f["cause"]
    if f["outcome"] == "saved":
        return [
            f'Write a bedtime story that includes the words "llama" and "produce" and uses foreshadowing.',
            f"Tell a gentle bedtime story where {child.id} and a llama named {llama.id} carry {produce.phrase}, notice a warning sign in the {carrier.label}, and solve the problem calmly before sleep.",
            f"Write a soft story in which a small clue hints that the load may spill, but a grown-up helps fix the {cause} by the end.",
        ]
    return [
        f'Write a bedtime story that includes the words "llama" and "produce" and uses foreshadowing.',
        f"Tell a quiet cautionary bedtime story where {child.id} and {llama.id} notice a warning sign while carrying {produce.phrase}, but do not truly fix it in time.",
        f"Write a story where a tiny clue early on hints that the load may tumble later, and the child learns to listen to small warnings.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    llama = f["llama"]
    helper = f["helper"]
    produce = f["produce_cfg"]
    carrier = f["carrier_cfg"]
    path = f["path_cfg"]
    fix = f["fix_cfg"]
    cause = f["cause"]
    helper_word = helper.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a gentle llama named {llama.id}, and {child.pronoun('possessive')} {helper_word} bringing produce in at the end of the day.",
        ),
        (
            "What were they carrying?",
            f"They were carrying {produce.phrase} in {carrier.phrase}. The evening chore was to bring the produce in before bedtime.",
        ),
        (
            "What was the warning sign?",
            f"The warning sign was that {carrier.foreshadow}. That small clue foreshadowed that the load was not steady.",
        ),
    ]
    if cause == "overload":
        why = "The load was too heavy for the carrier, so it leaned and strained."
    elif cause == "rolling":
        why = "The produce was round, and the carrier was not steady enough to stop it from rolling together."
    else:
        why = "The path was bumpy and the carrier was wobbly, so each step made it less steady."
    qa.append(
        (
            "Why did the produce spill?",
            f"It spilled because {why} When they kept going, the warning turned into a real tumble.",
        )
    )
    if f["outcome"] == "saved":
        qa.append(
            (
                f"How did {helper_word} fix the problem?",
                f"{helper_word.capitalize()} helped them because {fix.qa_text}. That fix matched the real cause of the trouble, so the rest of the trip felt steady.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully with the produce safely indoors and {llama.id} tucked in for the night. The calm ending shows that listening to small warnings can lead to a kinder bedtime.",
            )
        )
    else:
        qa.append(
            (
                "Why didn't the first solution work?",
                f"It did not work because {fix.label} did not truly steady the load. The story shows that a comforting idea is not always the same as a useful fix.",
            )
        )
        qa.append(
            (
                "What did the child learn?",
                f"{child.id} learned to pay attention to little clues like creaks and wobbles. Those small signs can matter because they warn you before a bigger problem arrives.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"llama", "produce", "foreshadow"}
    produce = world.facts["produce_cfg"]
    carrier = world.facts["carrier_cfg"]
    fix = world.facts["fix_cfg"]
    tags |= set(produce.tags) | set(carrier.tags) | set(fix.tags)
    if "two_trips" in tags:
        tags.add("careful")
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
        parts = []
        if e.role:
            parts.append(f"role={e.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(parts)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} cause={world.facts.get('cause')}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        produce="pumpkins",
        carrier="basket",
        fix="two_trips",
        child_name="Nora",
        child_gender="girl",
        llama_name="Moss",
        helper="grandmother",
    ),
    StoryParams(
        setting="orchard",
        produce="apples",
        carrier="tray",
        fix="blanket_ring",
        child_name="Ben",
        child_gender="boy",
        llama_name="Clover",
        helper="father",
    ),
    StoryParams(
        setting="garden",
        produce="carrots",
        carrier="wagon",
        fix="tighten_wheel",
        child_name="Mia",
        child_gender="girl",
        llama_name="Pebble",
        helper="mother",
    ),
    StoryParams(
        setting="patch",
        produce="pumpkins",
        carrier="basket",
        fix="sing",
        child_name="Leo",
        child_gender="boy",
        llama_name="Fern",
        helper="grandfather",
    ),
    StoryParams(
        setting="orchard",
        produce="tomatoes",
        carrier="tray",
        fix="sing",
        child_name="Ella",
        child_gender="girl",
        llama_name="Pip",
        helper="grandmother",
    ),
]


ASP_RULES = r"""
hazard(overload,P,C,S) :- produce(P), carrier(C), setting(S), weight(P,W), capacity(C,K), W > K.
hazard(rolling,P,C,S)  :- produce(P), carrier(C), setting(S), roll(P,R), stable(C,St), bump(S,B), R >= 2, St + B <= 2.
hazard(wobble,P,C,S)   :- produce(P), carrier(C), setting(S), bump(S,B), stable(C,St), B >= 2, St <= 1, not hazard(overload,P,C,S), not hazard(rolling,P,C,S).

valid(S,P,C) :- setting(S), produce(P), carrier(C), hazard(_,P,C,S).

sensible(F) :- fix(F), sense(F,S), sense_min(M), S >= M.

works(F,P,C,S) :- fix(F), hazard(H,P,C,S), helps(F,H), risk_drop(F,D), base_risk(P,C,S,R), R - D <= 0.
works(F,P,C,S) :- fix(F), hazard(overload,P,C,S), has_fix_text(F), helps(F,overload), risk_drop(F,D), base_risk(P,C,S,R), R - D <= 0.

base_risk(P,C,S,3) :- hazard(overload,P,C,S).
base_risk(P,C,S,2) :- hazard(rolling,P,C,S).
base_risk(P,C,S,2) :- hazard(wobble,P,C,S).

outcome(saved)   :- chosen_setting(S), chosen_produce(P), chosen_carrier(C), chosen_fix(F), works(F,P,C,S).
outcome(spilled) :- chosen_setting(S), chosen_produce(P), chosen_carrier(C), chosen_fix(F), not works(F,P,C,S).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("bump", sid, PATHS[sid].bumpiness))
    for pid, p in PRODUCE.items():
        lines.append(asp.fact("produce", pid))
        lines.append(asp.fact("weight", pid, p.weight))
        lines.append(asp.fact("roll", pid, p.roll))
    for cid, c in CARRIERS.items():
        lines.append(asp.fact("carrier", cid))
        lines.append(asp.fact("capacity", cid, c.capacity))
        lines.append(asp.fact("stable", cid, c.stable))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, fix.sense))
        lines.append(asp.fact("risk_drop", fid, fix.risk_drop))
        lines.append(asp.fact("has_fix_text", fid))
        for h in sorted(fix.helps):
            lines.append(asp.fact("helps", fid, h))
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
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_produce", params.produce),
            asp.fact("chosen_carrier", params.carrier),
            asp.fact("chosen_fix", params.fix),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    items = asp.atoms(model, "outcome")
    return items[0][0] if items else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sense = {fix.id for fix in sensible_fixes()}
    asp_sense = set(asp_sensible())
    if py_sense == asp_sense:
        print(f"OK: sensible fixes match ({sorted(py_sense)}).")
    else:
        rc = 1
        print("MISMATCH in sensible fixes:")
        print("  clingo:", sorted(asp_sense))
        print("  python:", sorted(py_sense))

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("smoke test generated an empty story")
        emit(smoke, trace=False, qa=False, header="")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Bedtime storyworld: a child and a llama bring produce in, "
        "a warning sign foreshadows trouble, and a calm fix may save the night."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--produce", choices=PRODUCE)
    ap.add_argument("--carrier", choices=CARRIERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--llama-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.produce and args.carrier:
        produce = PRODUCE[args.produce]
        carrier = CARRIERS[args.carrier]
        path = PATHS[args.setting]
        if hazard_kind(produce, carrier, path) is None:
            raise StoryError(explain_rejection(produce, carrier, path))
        if args.fix:
            fix = FIXES[args.fix]
            if fix.sense < SENSE_MIN:
                raise StoryError(explain_fix(args.fix, produce, carrier, path))
            if not fix_works(fix, produce, carrier, path):
                raise StoryError(explain_fix(args.fix, produce, carrier, path))
    elif args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing fix '{args.fix}': it is too weak for this world "
            f"(sense={FIXES[args.fix].sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.produce is None or combo[1] == args.produce)
        and (args.carrier is None or combo[2] == args.carrier)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, produce_id, carrier_id = rng.choice(sorted(combos))
    produce = PRODUCE[produce_id]
    carrier = CARRIERS[carrier_id]
    path = PATHS[setting_id]

    fix_choices = [
        fid
        for fid, fix in FIXES.items()
        if (args.fix is None or fid == args.fix)
        and fix.sense >= SENSE_MIN
        and fix_works(fix, produce, carrier, path)
    ]
    if not fix_choices:
        raise StoryError("(No valid fix matches the given options for this story.)")

    fix_id = rng.choice(sorted(fix_choices))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    llama_name = args.llama_name or rng.choice(LLAMA_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(
        setting=setting_id,
        produce=produce_id,
        carrier=carrier_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        llama_name=llama_name,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.produce not in PRODUCE:
        raise StoryError(f"(Unknown produce: {params.produce})")
    if params.carrier not in CARRIERS:
        raise StoryError(f"(Unknown carrier: {params.carrier})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    setting = SETTINGS[params.setting]
    produce = PRODUCE[params.produce]
    carrier = CARRIERS[params.carrier]
    path = PATHS[params.setting]
    fix = FIXES[params.fix]

    if hazard_kind(produce, carrier, path) is None:
        raise StoryError(explain_rejection(produce, carrier, path))
    if fix.sense < SENSE_MIN or not fix_works(fix, produce, carrier, path):
        raise StoryError(explain_fix(params.fix, produce, carrier, path))

    world = tell(
        setting=setting,
        produce=produce,
        carrier=carrier,
        path=path,
        fix=fix,
        child_name=params.child_name,
        child_gender=params.child_gender,
        llama_name=params.llama_name,
        helper_type=params.helper,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        for setting_id, produce_id, carrier_id in asp_valid_combos():
            fixes = [
                fid for fid, fix in FIXES.items()
                if fix.sense >= SENSE_MIN
                and fix_works(fix, PRODUCE[produce_id], CARRIERS[carrier_id], PATHS[setting_id])
            ]
            print(f"  {setting_id:8} {produce_id:10} {carrier_id:8} -> {', '.join(sorted(fixes))}")
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
            header = f"### {p.child_name} & {p.llama_name}: {p.produce} in {p.carrier} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
