#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py
================================================================================================

A standalone story world for a small detective-style tale about a young sleuth
who follows a strange clue, discovers that a grieving grown-up is struggling
with a hand spasm while preparing a condolence gift, and goes on a short quest
to fetch the right aid. The mystery turns into kindness; the case is solved not
by catching a villain, but by understanding what hurt was hiding behind the odd
noise.

This world models:
- a child detective noticing a concrete mystery in a small town setting
- a maker trying to prepare a condolence gift
- physical instability caused by a hand spasm
- a reasonableness gate: only aids that truly support the gift are valid
- a short quest to fetch that aid
- an outcome model: in-time success vs too-late failure
- a transformation from suspicion to empathy

Run it
------
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py --gift bouquet --aid basket
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py --gift soup --aid clamp_board
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py --all
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/condolence_spasm_problem_solving_quest_transformation_detective.py --verify
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "florist", "baker", "lantern_maker"}
        male = {"boy", "man", "father", "clockmaker"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        mapping = {
            "florist": "florist",
            "baker": "baker",
            "lantern_maker": "lantern-maker",
            "clockmaker": "clockmaker",
            "mother": "mom",
            "father": "dad",
        }
        return mapping.get(self.type, self.type)
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Setting:
    id: str
    label: str
    scene: str
    clue_spot: str
    affords: set[str] = field(default_factory=set)
    stocks: set[str] = field(default_factory=set)
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
class Gift:
    id: str
    label: str
    phrase: str
    need: str
    urgency: int
    noise: str
    wobble_line: str
    finish_line: str
    fail_line: str
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
class Aid:
    id: str
    label: str
    phrase: str
    supports: set[str]
    power: int
    fetch_line: str
    use_line: str
    qa_text: str
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
        self.facts: dict = {
            "predicted_wobble": False,
            "predicted_late": False,
            "outcome": "",
            "solved": False,
            "late": False,
        }

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


def _r_spasm(world: World) -> list[str]:
    maker = world.get("maker")
    gift = world.get("gift")
    if maker.meters["grief"] < THRESHOLD or maker.meters["strain"] < THRESHOLD:
        return []
    sig = ("spasm", maker.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    maker.meters["spasm"] += 1
    maker.memes["worry"] += 1
    gift.meters["risk"] += 1
    return ["__spasm__"]


def _r_wobble(world: World) -> list[str]:
    maker = world.get("maker")
    gift = world.get("gift")
    aid = world.get("aid")
    if maker.meters["spasm"] < THRESHOLD or gift.meters["in_hand"] < THRESHOLD:
        return []
    if aid.attrs.get("active"):
        return []
    sig = ("wobble", gift.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["wobble"] += 1
    maker.memes["frustration"] += 1
    world.get("room").meters["mystery"] += 1
    world.get("detective").memes["curiosity"] += 1
    return ["__wobble__"]


def _r_steady(world: World) -> list[str]:
    maker = world.get("maker")
    gift = world.get("gift")
    aid = world.get("aid")
    if maker.meters["spasm"] < THRESHOLD or not aid.attrs.get("active"):
        return []
    sig = ("steady", gift.id, aid.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    gift.meters["steady"] += 1
    gift.meters["wobble"] = 0.0
    maker.memes["relief"] += 1
    world.get("detective").memes["purpose"] += 1
    return ["__steady__"]


CAUSAL_RULES = [
    Rule(name="spasm", tag="physical", apply=_r_spasm),
    Rule(name="wobble", tag="physical", apply=_r_wobble),
    Rule(name="steady", tag="physical", apply=_r_steady),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def supports_gift(aid: Aid, gift: Gift) -> bool:
    return gift.need in aid.supports


def aid_available(setting: Setting, aid_id: str) -> bool:
    return aid_id in setting.stocks


def valid_combo(setting: Setting, gift: Gift, aid: Aid) -> bool:
    return gift.id in setting.affords and aid_available(setting, aid.id) and supports_gift(aid, gift)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for gid in sorted(setting.affords):
            gift = GIFTS[gid]
            for aid_id in sorted(setting.stocks):
                aid = AIDS[aid_id]
                if valid_combo(setting, gift, aid):
                    combos.append((sid, gid, aid_id))
    return combos


def finish_pressure(gift: Gift, delay: int) -> int:
    return gift.urgency + delay


def finishes_in_time(gift: Gift, aid: Aid, delay: int) -> bool:
    return aid.power >= finish_pressure(gift, delay)


def predict_trouble(world: World) -> dict:
    sim = world.copy()
    sim.get("gift").meters["in_hand"] = 1.0
    propagate(sim, narrate=False)
    return {
        "wobble": sim.get("gift").meters["wobble"] >= THRESHOLD,
        "mystery": sim.get("room").meters["mystery"] >= THRESHOLD,
    }


def introduce_case(world: World, detective: Entity, setting: Setting, gift: Gift) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"On a gray afternoon in {setting.label}, {detective.id} walked with a small notebook in one pocket "
        f"and a blunt pencil in the other. {setting.scene}"
    )
    world.say(
        f"Then a queer clue came from {setting.clue_spot}: {gift.noise}. "
        f'"A real detective listens twice," {detective.id} whispered.'
    )


def inspect_clue(world: World, detective: Entity, maker: Entity, setting: Setting) -> None:
    world.say(
        f"{detective.id} followed the sound past stacked boxes and polished handles until "
        f"{detective.pronoun()} found {maker.id}, the {maker.label_word}, alone in the back."
    )
    world.say(
        f"{maker.id} was trying very hard to work quietly, but sadness sat on {maker.pronoun('possessive')} face "
        f"like a shadow."
    )


def reveal_problem(world: World, detective: Entity, maker: Entity, gift: Gift) -> None:
    pred = predict_trouble(world)
    world.facts["predicted_wobble"] = pred["wobble"]
    maker.meters["grief"] = 1.0
    maker.meters["strain"] = 1.0
    world.get("gift").meters["in_hand"] = 1.0
    propagate(world, narrate=False)
    if pred["wobble"]:
        world.say(
            f'"I am making {gift.phrase}," {maker.id} said softly. "It is a condolence gift for my old neighbor, '
            f'but my hand keeps having a little spasm."'
        )
        world.say(
            gift.wobble_line
        )
    else:
        world.say(
            f'"I am making {gift.phrase}," {maker.id} said softly. "It is a condolence gift for my old neighbor."'
        )


def suspect_to_sympathy(world: World, detective: Entity, maker: Entity) -> None:
    detective.memes["empathy"] += 1
    maker.memes["trust"] += 1
    world.say(
        f"At first {detective.id} had expected a sneaky trick, but this was not a villain's case at all. "
        f"It was a hurt person's hard moment."
    )
    world.say(
        f'"Then the case is not who made the noise," {detective.id} said. "The case is how to help you finish."'
    )


def quest_for_aid(world: World, detective: Entity, aid: Aid, setting: Setting) -> None:
    detective.memes["purpose"] += 1
    world.say(
        f"That gave the mystery a new shape. {detective.id} spun on one heel and hurried through {setting.label} "
        f"on a short quest for {aid.phrase}."
    )
    world.say(aid.fetch_line.format(name=detective.id))


def use_aid(world: World, detective: Entity, maker: Entity, aid: Aid, gift: Gift) -> None:
    tool = world.get("aid")
    tool.attrs["active"] = True
    propagate(world, narrate=False)
    world.say(
        f"When {detective.id} came back, {maker.id} set the work down once more and used {aid.phrase}. "
        f"{aid.use_line}"
    )
    world.say(
        gift.finish_line
    )


def too_late(world: World, detective: Entity, maker: Entity, aid: Aid, gift: Gift) -> None:
    detective.memes["sadness"] += 1
    maker.memes["sadness"] += 1
    world.say(
        f"{detective.id} did bring {aid.phrase}, and it helped, but the delay had already stretched too long. "
        f"{gift.fail_line}"
    )
    world.say(
        f"For a second the room felt heavier than before, and even {detective.id}'s notebook seemed quiet."
    )


def kinder_backup(world: World, detective: Entity, maker: Entity) -> None:
    detective.memes["care"] += 1
    maker.memes["relief"] += 1
    world.say(
        f"Then {detective.id} opened the notebook to a blank page. Together they wrote a simple condolence note in "
        f"careful letters, and that smaller gift was honest and ready."
    )
    world.say(
        f"{maker.id} pressed the folded note to {maker.pronoun('possessive')} heart and thanked {detective.id} for "
        f"staying instead of giving up."
    )


def delivery_success(world: World, detective: Entity, maker: Entity, gift: Gift) -> None:
    detective.memes["pride"] += 1
    maker.memes["hope"] += 1
    world.say(
        f"Soon the two of them carried {gift.phrase} out into the lane together. The case ended not with a shout, "
        f"but with a gentle knock and a gift made ready at last."
    )
    world.say(
        f"On the walk home, {detective.id} wrote one last line in the notebook: "
        f'"Best clue of all: sometimes a mystery turns into a kindness."'
    )


def delivery_backup(world: World, detective: Entity, maker: Entity) -> None:
    detective.memes["pride"] += 1
    maker.memes["hope"] += 1
    world.say(
        f"They carried the note out together anyway. It was smaller than the first plan, but it reached the neighbor "
        f"while the evening lamps were still coming on."
    )
    world.say(
        f"On the way back, {detective.id} understood something new: solving a case can mean changing the ending, "
        f"even when it cannot restore the first version of things."
    )


def tell(
    setting: Setting,
    gift_cfg: Gift,
    aid_cfg: Aid,
    detective_name: str = "Mina",
    detective_gender: str = "girl",
    maker_name: str = "Mrs. Vale",
    maker_type: str = "florist",
    delay: int = 0,
) -> World:
    world = World(setting)
    detective = world.add(Entity(id=detective_name, kind="character", type=detective_gender, role="detective"))
    maker = world.add(Entity(
        id=maker_name,
        kind="character",
        type=maker_type,
        role="maker",
        attrs={"gift_id": gift_cfg.id},
        tags=set(gift_cfg.tags),
    ))
    gift = world.add(Entity(
        id="gift",
        type="gift",
        label=gift_cfg.label,
        attrs={"need": gift_cfg.need, "completed": False},
        tags=set(gift_cfg.tags),
    ))
    aid = world.add(Entity(
        id="aid",
        type="aid",
        label=aid_cfg.label,
        attrs={"active": False},
        tags=set(aid_cfg.tags),
    ))
    room = world.add(Entity(id="room", type="room", label=setting.label))

    detective.memes["curiosity"] = 0.0
    detective.memes["empathy"] = 0.0
    detective.memes["purpose"] = 0.0
    detective.memes["care"] = 0.0
    detective.meters["steps"] = 0.0

    maker.meters["grief"] = 1.0
    maker.meters["strain"] = 1.0
    maker.meters["spasm"] = 0.0
    maker.memes["worry"] = 0.0
    maker.memes["trust"] = 0.0
    maker.memes["relief"] = 0.0
    maker.memes["hope"] = 0.0
    maker.memes["sadness"] = 0.0

    gift.meters["risk"] = 0.0
    gift.meters["in_hand"] = 0.0
    gift.meters["wobble"] = 0.0
    gift.meters["steady"] = 0.0
    room.meters["mystery"] = 0.0

    introduce_case(world, detective, setting, gift_cfg)
    world.para()
    inspect_clue(world, detective, maker, setting)
    reveal_problem(world, detective, maker, gift_cfg)
    suspect_to_sympathy(world, detective, maker)

    world.para()
    quest_for_aid(world, detective, aid_cfg, setting)
    detective.meters["steps"] += 1 + delay

    success = finishes_in_time(gift_cfg, aid_cfg, delay)
    world.facts["predicted_late"] = not success

    if success:
        use_aid(world, detective, maker, aid_cfg, gift_cfg)
        world.para()
        delivery_success(world, detective, maker, gift_cfg)
        world.facts["outcome"] = "solved"
        world.facts["solved"] = True
        world.facts["late"] = False
        gift.attrs["completed"] = True
    else:
        too_late(world, detective, maker, aid_cfg, gift_cfg)
        kinder_backup(world, detective, maker)
        world.para()
        delivery_backup(world, detective, maker)
        world.facts["outcome"] = "late"
        world.facts["solved"] = False
        world.facts["late"] = True
        gift.attrs["completed"] = False

    world.facts.update(
        detective=detective,
        maker=maker,
        gift_cfg=gift_cfg,
        gift=gift,
        aid_cfg=aid_cfg,
        aid=aid,
        setting=setting,
        delay=delay,
        pressure=finish_pressure(gift_cfg, delay),
    )
    return world


SETTINGS = {
    "market_lane": Setting(
        id="market_lane",
        label="Market Lane",
        scene="Rain-dark cobbles shone like little mirrors, and every shop front looked as if it might be hiding a clue.",
        clue_spot="the flower stall beside the baker's window",
        affords={"bouquet", "soup"},
        stocks={"basket", "cart", "tray"},
    ),
    "lantern_row": Setting(
        id="lantern_row",
        label="Lantern Row",
        scene="Strings of paper stars hung under the eaves, and the narrow street seemed stitched together with soft light.",
        clue_spot="the lantern-maker's half-open workroom door",
        affords={"lantern", "bouquet"},
        stocks={"tray", "clamp_board", "basket"},
    ),
    "clock_arcade": Setting(
        id="clock_arcade",
        label="Clock Arcade",
        scene="Tiny brass gears winked in the windows, and each tick in the passage sounded like a secret counting to itself.",
        clue_spot="the back passage near the old service counter",
        affords={"lantern", "soup"},
        stocks={"cart", "tray", "clamp_board"},
    ),
}

GIFTS = {
    "bouquet": Gift(
        id="bouquet",
        label="bouquet",
        phrase="a condolence bouquet of white flowers",
        need="upright",
        urgency=1,
        noise="a bucket gave a soft clink-clink against the floorboards",
        wobble_line="Every time the stems were gathered, the flowers tipped sideways and the pail knocked the floor with a tiny, nervous sound.",
        finish_line="With the flowers held upright and still, the stems slipped into a neat ribboned bunch at last.",
        fail_line="Some petals had already bent and bruised, so the bouquet could not be made as fresh and proud as they had hoped.",
        tags={"bouquet", "flowers", "condolence"},
    ),
    "soup": Gift(
        id="soup",
        label="soup jar",
        phrase="a warm jar of condolence soup",
        need="steady",
        urgency=2,
        noise="a lid made a sharp little tap every few breaths",
        wobble_line="Whenever the jar was lifted, the hand spasm made it jerk, and the spoon beside it rattled like a tiny alarm.",
        finish_line="With the jar kept steady, the lid was tightened, the cloth was tied, and the warm soup was ready to travel.",
        fail_line="The soup was still kind, but it had gone lukewarm and sloshed onto the wrapping cloth before they could finish it neatly.",
        tags={"soup", "condolence", "help"},
    ),
    "lantern": Gift(
        id="lantern",
        label="paper lantern",
        phrase="a starry paper condolence lantern",
        need="flat",
        urgency=2,
        noise="paper gave a whispery flap and a wooden frame clicked against the table",
        wobble_line="Each little spasm made the folded paper jump, and the pasted star points would not stay lined up.",
        finish_line="At last the paper lay flat and calm, and the lantern opened into a clean bright star.",
        fail_line="One side had already creased badly, so the lantern could not open into the fine even star they had planned.",
        tags={"lantern", "paper", "condolence"},
    ),
}

AIDS = {
    "basket": Aid(
        id="basket",
        label="padded basket",
        phrase="a padded basket",
        supports={"upright", "steady"},
        power=2,
        fetch_line="{name} darted to a shelf of delivery things and found a padded basket with high soft sides.",
        use_line="The high sides stopped the shaking from tipping the work askew.",
        qa_text="used a padded basket to hold the gift upright and calm",
        tags={"basket", "help"},
    ),
    "tray": Aid(
        id="tray",
        label="two-hand tray",
        phrase="a two-hand tray",
        supports={"flat", "steady"},
        power=2,
        fetch_line="{name} slipped past a stack of tins and found a broad two-hand tray hanging on a hook.",
        use_line="Resting the work across both handles gave the maker a steadier hold than one trembling hand alone.",
        qa_text="used a two-hand tray so the gift could stay flat and steady",
        tags={"tray", "help"},
    ),
    "cart": Aid(
        id="cart",
        label="little rolling cart",
        phrase="a little rolling cart",
        supports={"upright", "flat", "steady"},
        power=3,
        fetch_line="{name} hurried into the storeroom and tugged out a little rolling cart that moved with a soft rubber squeak.",
        use_line="Once the work rested on the cart, the maker no longer had to fight every shake in the air.",
        qa_text="used a little rolling cart to carry the gift without depending on a shaky hand",
        tags={"cart", "help"},
    ),
    "clamp_board": Aid(
        id="clamp_board",
        label="clamp board",
        phrase="a clamp board",
        supports={"flat"},
        power=1,
        fetch_line="{name} found a clamp board under a workbench, with two small clips ready to hold paper still.",
        use_line="The clips pinned the edges in place while the maker finished the careful folds.",
        qa_text="used a clamp board to keep the paper from slipping",
        tags={"clamp_board", "paper", "help"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tess", "Ivy", "June", "Clara", "Ruby"]
BOY_NAMES = ["Owen", "Theo", "Max", "Eli", "Sam", "Finn", "Miles", "Noah"]

MAKERS = {
    "florist": {"names": ["Mrs. Vale", "Ms. Rowan", "Aunt Bea"], "gift_types": {"bouquet"}},
    "baker": {"names": ["Mr. Pruitt", "Mrs. Hale", "Baker Wren"], "gift_types": {"soup"}},
    "lantern_maker": {"names": ["Ms. Lark", "Mr. Finch", "Mira Reed"], "gift_types": {"lantern"}},
    "clockmaker": {"names": ["Mr. Bell", "Master Orrin", "Ms. Peck"], "gift_types": {"lantern", "soup"}},
}


@dataclass
class StoryParams:
    setting: str
    gift: str
    aid: str
    detective: str
    detective_gender: str
    maker_name: str
    maker_type: str
    delay: int = 0
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
            "A detective looks for clues and asks careful questions. The goal is to understand what really happened."
        )
    ],
    "condolence": [
        (
            "What is a condolence gift?",
            "A condolence gift is something kind you bring when someone is sad because a person has died. It shows care and comfort."
        )
    ],
    "spasm": [
        (
            "What is a spasm?",
            "A spasm is a sudden jump or tightening in part of the body, like a hand or leg. It can make careful work hard for a moment."
        )
    ],
    "flowers": [
        (
            "Why do people bring flowers when someone is sad?",
            "Flowers can be a gentle way to show love and respect. They tell the sad person that others are thinking of them."
        )
    ],
    "soup": [
        (
            "Why is soup a caring thing to bring someone?",
            "Soup is warm and easy to share. Bringing food can help a sad or tired person feel looked after."
        )
    ],
    "paper": [
        (
            "Why can folded paper be hard to handle?",
            "Paper bends and slips easily, especially when it must stay lined up. A small shake can make the fold go crooked."
        )
    ],
    "basket": [
        (
            "What does a padded basket do?",
            "A padded basket holds things softly so they do not tip or bump as much. That makes carrying fragile things easier."
        )
    ],
    "tray": [
        (
            "Why is a two-hand tray steadier than one hand?",
            "Using two hands spreads the weight and helps keep things level. That makes spills and slips less likely."
        )
    ],
    "cart": [
        (
            "Why can a rolling cart help with carrying?",
            "A rolling cart lets the wheels do the carrying work. You do not have to hold all the weight in your hands."
        )
    ],
    "help": [
        (
            "What is good problem solving?",
            "Good problem solving means noticing the real problem and picking a fix that truly fits it. It often starts with listening well."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "detective",
    "condolence",
    "spasm",
    "flowers",
    "soup",
    "paper",
    "basket",
    "tray",
    "cart",
    "help",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    maker = f["maker"]
    gift = f["gift_cfg"]
    aid = f["aid_cfg"]
    setting = f["setting"]
    if f["outcome"] == "solved":
        return [
            f'Write a gentle detective story for a 3-to-5-year-old that includes the words "condolence" and "spasm".',
            f"Tell a mystery set in {setting.label} where {detective.id} follows a strange sound and discovers that {maker.id} needs help finishing {gift.phrase}.",
            f"Write a small quest story where a child detective solves a problem by fetching {aid.phrase}, and the ending transforms fear into kindness.",
        ]
    return [
        f'Write a gentle detective story for a 3-to-5-year-old that includes the words "condolence" and "spasm".',
        f"Tell a mystery set in {setting.label} where {detective.id} follows a clue, learns why {maker.id} cannot finish {gift.phrase}, and helps make a smaller caring gift instead.",
        "Write a story with problem solving, a short quest, and a transformation from suspicion to empathy, even though the first plan cannot be saved in time.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    maker = f["maker"]
    gift_cfg = f["gift_cfg"]
    aid_cfg = f["aid_cfg"]
    setting = f["setting"]
    delay = f["delay"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.id}, a young detective, and {maker.id}, the {maker.label_word}. "
            f"They meet in {setting.label} because of a strange clue."
        ),
        (
            "What was the mystery at the beginning?",
            f"The mystery was the odd sound coming from {setting.clue_spot}. "
            f"{detective.id} followed it because a detective knows small noises can hide an important problem."
        ),
        (
            f"Why was {maker.id} having trouble?",
            f"{maker.id} was trying to make {gift_cfg.phrase}, but grief and strain were bringing on a hand spasm. "
            f"That sudden jump kept the work from staying still."
        ),
    ]
    if f["predicted_wobble"]:
        qa.append(
            (
                f"Why did {detective.id} decide to fetch {aid_cfg.phrase}?",
                f"{detective.id} could see that the gift kept wobbling whenever {maker.id} tried to hold it. "
                f"The aid fit the real problem because it could support the gift in the way {maker.pronoun('possessive')} shaky hand could not."
            )
        )
    if f["outcome"] == "solved":
        qa.append(
            (
                "How was the case solved?",
                f"The case was solved when they used {aid_cfg.phrase} and finished the gift in time. "
                f"That turned the mystery into a successful act of care."
            )
        )
        qa.append(
            (
                "How did the story change by the end?",
                f"It began like a detective case about a suspicious sound, but it ended with kindness and company. "
                f"{detective.id} changed from clue-chaser to helper, and {maker.id} was no longer alone with the problem."
            )
        )
    else:
        qa.append(
            (
                "Did the first plan work in time?",
                f"No. The aid helped, but the delay of {delay} meant the first gift could not be finished the way they hoped. "
                f"So they solved the deeper problem by making a smaller condolence note instead."
            )
        )
        qa.append(
            (
                "How did the story change by the end?",
                f"It began like a mystery, then became a problem-solving quest, and ended as a kinder, humbler act of care. "
                f"The transformation was not into a perfect victory, but into understanding and help."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"detective", "spasm", "condolence", "help"}
    gift_cfg = world.facts["gift_cfg"]
    aid_cfg = world.facts["aid_cfg"]
    if "flowers" in gift_cfg.tags:
        tags.add("flowers")
    if "soup" in gift_cfg.tags:
        tags.add("soup")
    if "paper" in gift_cfg.tags:
        tags.add("paper")
    tags |= set(aid_cfg.tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:12} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="market_lane",
        gift="bouquet",
        aid="basket",
        detective="Mina",
        detective_gender="girl",
        maker_name="Mrs. Vale",
        maker_type="florist",
        delay=0,
    ),
    StoryParams(
        setting="clock_arcade",
        gift="soup",
        aid="tray",
        detective="Owen",
        detective_gender="boy",
        maker_name="Mrs. Hale",
        maker_type="baker",
        delay=1,
    ),
    StoryParams(
        setting="lantern_row",
        gift="lantern",
        aid="clamp_board",
        detective="Ruby",
        detective_gender="girl",
        maker_name="Ms. Lark",
        maker_type="lantern_maker",
        delay=2,
    ),
    StoryParams(
        setting="clock_arcade",
        gift="lantern",
        aid="cart",
        detective="Theo",
        detective_gender="boy",
        maker_name="Mr. Bell",
        maker_type="clockmaker",
        delay=0,
    ),
    StoryParams(
        setting="market_lane",
        gift="soup",
        aid="cart",
        detective="Clara",
        detective_gender="girl",
        maker_name="Baker Wren",
        maker_type="baker",
        delay=0,
    ),
]


def explain_rejection(setting: Setting, gift: Gift, aid: Aid) -> str:
    if gift.id not in setting.affords:
        return (
            f"(No story: {setting.label} does not plausibly host the making of {gift.phrase}. "
            f"Pick a gift that belongs in this setting.)"
        )
    if aid.id not in setting.stocks:
        return (
            f"(No story: {aid.phrase} is not available in {setting.label}, so the detective has no honest way to fetch it there.)"
        )
    if not supports_gift(aid, gift):
        return (
            f"(No story: {aid.phrase} does not truly support {gift.phrase}. "
            f"The fix must fit the real problem, not just appear helpful.)"
        )
    return "(No story: this setting, gift, and aid do not make a reasonable case.)"


def maker_matches_gift(maker_type: str, gift_id: str) -> bool:
    return gift_id in MAKERS[maker_type]["gift_types"]


def explain_maker(maker_type: str, gift_id: str) -> str:
    choices = []
    for mt, info in MAKERS.items():
        if gift_id in info["gift_types"]:
            choices.append(mt)
    return (
        f"(No story: a {maker_type} is not the right craftsperson for {gift_id} here. "
        f"Try one of: {', '.join(sorted(choices))}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "solved" if finishes_in_time(GIFTS[params.gift], AIDS[params.aid], params.delay) else "late"


ASP_RULES = r"""
supports_gift(A,G) :- aid(A), gift(G), needs(G,N), supports(A,N).
valid(S,G,A) :- setting(S), gift(G), aid(A), affords(S,G), stocks(S,A), supports_gift(A,G).

pressure(G, U + D) :- chosen_gift(G), urgency(G,U), delay(D).
aid_power(P) :- chosen_aid(A), power(A,P).

outcome(solved) :- aid_power(P), pressure(GP), P >= GP.
outcome(late) :- aid_power(P), pressure(GP), P < GP.

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for gid in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, gid))
        for aid_id in sorted(setting.stocks):
            lines.append(asp.fact("stocks", sid, aid_id))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("needs", gid, gift.need))
        lines.append(asp.fact("urgency", gid, gift.urgency))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("power", aid_id, aid.power))
        for need in sorted(aid.supports):
            lines.append(asp.fact("supports", aid_id, need))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_gift", params.gift),
            asp.fact("chosen_aid", params.aid),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra=extra, show="#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    params = CURATED[0]
    sample = generate(params)
    if not sample.story or "condolence" not in sample.story or "spasm" not in sample.story:
        raise StoryError("(Smoke test failed: generated story was missing required content.)")
    emit(sample, trace=False, qa=False, header="")


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

    cases = list(CURATED)
    for s in range(80):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child detective follows a clue, solves a problem, and turns a mystery into kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--maker-type", choices=MAKERS)
    ap.add_argument("--maker-name")
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the quest takes before the aid arrives")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.gift and args.aid:
        setting = SETTINGS[args.setting]
        gift = GIFTS[args.gift]
        aid = AIDS[args.aid]
        if not valid_combo(setting, gift, aid):
            raise StoryError(explain_rejection(setting, gift, aid))
    if args.maker_type and args.gift and not maker_matches_gift(args.maker_type, args.gift):
        raise StoryError(explain_maker(args.maker_type, args.gift))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.gift is None or combo[1] == args.gift)
        and (args.aid is None or combo[2] == args.aid)
        and (args.maker_type is None or maker_matches_gift(args.maker_type, combo[1]))
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, gift_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    detective_name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    possible_makers = [
        mt for mt, info in MAKERS.items()
        if gift_id in info["gift_types"] and (args.maker_type is None or mt == args.maker_type)
    ]
    if not possible_makers:
        raise StoryError(explain_maker(args.maker_type or "unknown", gift_id))
    maker_type = rng.choice(sorted(possible_makers))
    maker_name = args.maker_name or rng.choice(MAKERS[maker_type]["names"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        setting=setting_id,
        gift=gift_id,
        aid=aid_id,
        detective=detective_name,
        detective_gender=gender,
        maker_name=maker_name,
        maker_type=maker_type,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Unknown gift: {params.gift})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")
    if params.maker_type not in MAKERS:
        raise StoryError(f"(Unknown maker type: {params.maker_type})")

    setting = SETTINGS[params.setting]
    gift = GIFTS[params.gift]
    aid = AIDS[params.aid]

    if not valid_combo(setting, gift, aid):
        raise StoryError(explain_rejection(setting, gift, aid))
    if not maker_matches_gift(params.maker_type, params.gift):
        raise StoryError(explain_maker(params.maker_type, params.gift))

    world = tell(
        setting=setting,
        gift_cfg=gift,
        aid_cfg=aid,
        detective_name=params.detective,
        detective_gender=params.detective_gender,
        maker_name=params.maker_name,
        maker_type=params.maker_type,
        delay=params.delay,
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
        print(asp_program(show="#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, gift, aid) combos:\n")
        for setting, gift, aid in combos:
            print(f"  {setting:12} {gift:8} {aid}")
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
            header = f"### {p.detective}: {p.gift} in {p.setting} with {p.aid} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
