#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/counter_shaft_lesson_learned_kindness_folk_tale.py
==============================================================================

A standalone folk-tale storyworld about a child at a village workhouse who keeps
food on a counter, meets someone in need, and learns that kindness comes back
when trouble finds the wooden shaft that keeps the day's work moving.

The world model is small but stateful:
- a child, elder, visitor, and workhouse share one simulation space
- physical meters track hunger, a stuck shaft, halted work, and repair
- emotional memes track stinginess, kindness, gratitude, shame, and relief
- prose is rendered from changing state, not from one frozen template

Constraint idea
---------------
Not every visitor can plausibly fix every kind of shaft trouble. This world only
generates combinations where:
- the chosen setting has a specific shaft problem
- the chosen repair fits that problem
- the chosen visitor credibly knows that repair

So the Python gate and the inline ASP twin both reject mismatched stories.

Run it
------
python storyworlds/worlds/gpt-5.4/counter_shaft_lesson_learned_kindness_folk_tale.py
python storyworlds/worlds/gpt-5.4/counter_shaft_lesson_learned_kindness_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/counter_shaft_lesson_learned_kindness_folk_tale.py --setting mill --visitor traveler --repair oil_rag
python storyworlds/worlds/gpt-5.4/counter_shaft_lesson_learned_kindness_folk_tale.py --verify
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
        female = {"girl", "woman", "grandmother", "widow"}
        male = {"boy", "man", "grandfather", "traveler", "shepherd"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
        }.get(self.type, self.type)
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
class Setting:
    id: str
    place: str
    work_name: str
    counter_text: str
    shaft_name: str
    fault: str
    fault_text: str
    stop_text: str
    repair_need: str
    ending_image: str
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
class Gift:
    id: str
    label: str
    phrase: str
    share_text: str
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
class VisitorCfg:
    id: str
    label: str
    type: str
    request_text: str
    knows: set[str] = field(default_factory=set)
    kindness_return: str = ""
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
class Repair:
    id: str
    sense: int
    fixes: str
    action_text: str
    qa_text: str
    fail_text: str
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


def _r_halt_work(world: World) -> list[str]:
    out: list[str] = []
    machine = world.get("machine")
    child = world.get("child")
    if machine.meters["stuck"] >= THRESHOLD:
        sig = ("halt_work", "machine")
        if sig not in world.fired:
            world.fired.add(sig)
            machine.meters["halted"] += 1
            child.memes["worry"] += 1
            out.append("__halt__")
    return out


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    visitor = world.get("visitor")
    if child.meters["gift_shared"] >= THRESHOLD:
        sig = ("gratitude", "visitor")
        if sig not in world.fired:
            world.fired.add(sig)
            visitor.meters["hunger"] = 0.0
            visitor.memes["gratitude"] += 1
            child.memes["kindness"] += 1
            out.append("__gratitude__")
    return out


def _r_willing_help(world: World) -> list[str]:
    out: list[str] = []
    visitor = world.get("visitor")
    machine = world.get("machine")
    if machine.meters["stuck"] < THRESHOLD:
        return out
    if visitor.memes["gratitude"] >= THRESHOLD or visitor.memes["forgiven"] >= THRESHOLD:
        sig = ("willing_help", "visitor")
        if sig not in world.fired:
            world.fired.add(sig)
            visitor.memes["willing_help"] += 1
            out.append("__help__")
    return out


CAUSAL_RULES = [
    Rule(name="halt_work", tag="physical", apply=_r_halt_work),
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="willing_help", tag="social", apply=_r_willing_help),
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


def repair_matches(setting: Setting, repair: Repair) -> bool:
    return setting.repair_need == repair.fixes


def visitor_can_help(visitor: VisitorCfg, repair: Repair) -> bool:
    return repair.id in visitor.knows


def sensible_repairs() -> list[Repair]:
    return [r for r in REPAIRS.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for visitor_id, visitor in VISITORS.items():
            for gift_id in GIFTS:
                for repair_id, repair in REPAIRS.items():
                    if repair_matches(setting, repair) and visitor_can_help(visitor, repair) and repair.sense >= SENSE_MIN:
                        combos.append((setting_id, visitor_id, gift_id, repair_id))
    return combos


def explain_rejection(setting: Setting, visitor: VisitorCfg, repair: Repair) -> str:
    if not repair_matches(setting, repair):
        return (
            f"(No story: {setting.place} needs a repair for a {setting.repair_need.replace('_', ' ')}, "
            f"but '{repair.id}' fixes {repair.fixes.replace('_', ' ')} trouble instead.)"
        )
    if not visitor_can_help(visitor, repair):
        return (
            f"(No story: the {visitor.label} does not credibly know the '{repair.id}' repair, "
            f"so the kindness-and-help turn would not make sense.)"
        )
    if repair.sense < SENSE_MIN:
        return (
            f"(Refusing repair '{repair.id}': it scores too low on common sense "
            f"(sense={repair.sense} < {SENSE_MIN}).)"
        )
    return "(No story: this combination is not reasonable.)"


def outcome_of(params: "StoryParams") -> str:
    return "early_kindness" if params.trait == "openhanded" else "learned_kindness"


def predict_help(world: World) -> dict:
    sim = world.copy()
    sim.get("machine").meters["stuck"] += 1
    propagate(sim, narrate=False)
    willing = sim.get("visitor").memes["willing_help"] >= THRESHOLD
    return {
        "work_halted": sim.get("machine").meters["halted"] >= THRESHOLD,
        "help_ready": willing,
    }


def folk_opening(setting: Setting) -> str:
    return (
        f"In the old days, when work songs rose earlier than the sun, there stood "
        f"{setting.place}, where every hinge and beam had its own little memory."
    )


def introduce(world: World, child: Entity, elder: Entity, setting: Setting, gift: Gift) -> None:
    world.say(folk_opening(setting))
    world.say(
        f"There lived {child.id}, a {child.type} who helped {child.pronoun('possessive')} "
        f"{elder.title_word} from dawn onward. {setting.counter_text} On it sat {gift.phrase}, "
        f"set out neatly upon the counter."
    )


def first_request(world: World, visitor: Entity, visitor_cfg: VisitorCfg, child: Entity, gift: Gift) -> None:
    visitor.meters["hunger"] = 1.0
    child.memes["guarding"] += 1
    world.say(
        f"Near midday a {visitor_cfg.label} came slowly up the path. {visitor_cfg.request_text} "
        f'"I ask only for {gift.share_text}," {visitor.pronoun()} said.'
    )


def share_now(world: World, child: Entity, visitor: Entity, gift: Gift) -> None:
    child.meters["gift_shared"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} looked at the counter, then at the weary face before {child.pronoun('object')}, "
        f"and set {gift.share_text} into {visitor.pronoun('possessive')} hands. "
        f"It was a small gift, yet it warmed the place like a lamp."
    )


def refuse_now(world: World, child: Entity, elder: Entity, gift: Gift) -> None:
    child.memes["stinginess"] += 1
    world.say(
        f"But {child.id} drew {child.pronoun('possessive')} hand back and said, "
        f'"These must stay upon the counter. If I share them, there may not be enough."'
    )
    world.say(
        f"{elder.title_word.capitalize()} said nothing at first, only watched with the quiet eyes of age."
    )


def shaft_trouble(world: World, setting: Setting, machine: Entity) -> None:
    machine.meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Then the day's turn came. {setting.fault_text} {setting.stop_text}"
    )


def grateful_offer(world: World, visitor: Entity, visitor_cfg: VisitorCfg) -> None:
    world.say(
        f'The {visitor_cfg.label} rose at once. "{visitor_cfg.kindness_return}," {visitor.pronoun()} said.'
    )


def elder_lesson_before_change(world: World, child: Entity, elder: Entity) -> None:
    world.say(
        f'Then {elder.title_word} laid a hand on {child.id}\'s shoulder and said, '
        f'"A closed hand keeps its bread for one hour, but an open hand may keep a whole day from breaking."'
    )


def share_after_shame(world: World, child: Entity, visitor: Entity, gift: Gift) -> None:
    child.memes["shame"] += 1
    child.meters["gift_shared"] += 1
    visitor.memes["forgiven"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} felt the words sink deep. {child.pronoun().capitalize()} took {gift.share_text} from the counter, "
        f"ran to the visitor, and said, "
        f'"I should have shared sooner. Please take this now, and forgive my hard little heart."'
    )


def repair_scene(world: World, setting: Setting, visitor: Entity, repair: Repair) -> None:
    machine = world.get("machine")
    machine.meters["stuck"] = 0.0
    machine.meters["repaired"] += 1
    machine.meters["halted"] = 0.0
    child = world.get("child")
    child.memes["relief"] += 1
    world.say(
        f"The {visitor.type} went straight to the {setting.shaft_name} and {repair.action_text}. "
        f"Soon the wood answered softly instead of groaning, and the work began to move again."
    )


def elder_closing(world: World, child: Entity, elder: Entity, setting: Setting, outcome: str) -> None:
    child.memes["lesson"] += 1
    child.memes["peace"] += 1
    if outcome == "early_kindness":
        world.say(
            f'{elder.title_word.capitalize()} smiled and said, "Kindness is never counted wrong, even when given from a full counter."'
        )
    else:
        world.say(
            f'{elder.title_word.capitalize()} smiled and said, "Now you know it: kindness given late still mends much, but kindness given early mends more."'
        )
    world.say(
        f"From that day on, {child.id} always kept a small share ready for tired strangers, "
        f"and {setting.ending_image}"
    )


def tell(
    setting: Setting,
    gift: Gift,
    visitor_cfg: VisitorCfg,
    repair: Repair,
    child_name: str = "Mira",
    child_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "openhanded",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    elder = world.add(Entity(id="elder", kind="character", type=elder_type, label=elder_type, role="elder"))
    visitor = world.add(Entity(id="visitor", kind="character", type=visitor_cfg.type, label=visitor_cfg.label, role="visitor"))
    machine = world.add(Entity(id="machine", kind="thing", type="machine", label=setting.work_name, role="machine"))

    child.attrs["name"] = child_name
    elder.attrs["title"] = elder_type
    visitor.attrs["kind"] = visitor_cfg.label
    machine.attrs["shaft_name"] = setting.shaft_name
    child.memes["generosity"] = 1.0 if trait == "openhanded" else 0.0
    visitor.meters["hunger"] = 0.0
    visitor.memes["gratitude"] = 0.0
    visitor.memes["forgiven"] = 0.0
    visitor.memes["willing_help"] = 0.0
    machine.meters["stuck"] = 0.0
    machine.meters["halted"] = 0.0
    machine.meters["repaired"] = 0.0
    child.meters["gift_shared"] = 0.0

    world.facts.update(
        setting=setting,
        gift=gift,
        visitor_cfg=visitor_cfg,
        repair=repair,
        child_name=child_name,
        elder_type=elder_type,
        trait=trait,
    )

    introduce(world, child, elder, setting, gift)
    first_request(world, visitor, visitor_cfg, child, gift)

    world.para()
    if trait == "openhanded":
        share_now(world, child, visitor, gift)
        pred = predict_help(world)
        world.facts["predicted_help"] = pred["help_ready"]
        world.facts["predicted_halt"] = pred["work_halted"]
        shaft_trouble(world, setting, machine)
        grateful_offer(world, visitor, visitor_cfg)
        repair_scene(world, setting, visitor, repair)
        outcome = "early_kindness"
    else:
        refuse_now(world, child, elder, gift)
        pred = predict_help(world)
        world.facts["predicted_help"] = pred["help_ready"]
        world.facts["predicted_halt"] = pred["work_halted"]
        world.para()
        shaft_trouble(world, setting, machine)
        elder_lesson_before_change(world, child, elder)
        share_after_shame(world, child, visitor, gift)
        repair_scene(world, setting, visitor, repair)
        outcome = "learned_kindness"

    world.para()
    elder_closing(world, child, elder, setting, outcome)

    world.facts.update(
        child=child,
        elder=elder,
        visitor=visitor,
        machine=machine,
        outcome=outcome,
        help_given=child.meters["gift_shared"] >= THRESHOLD,
        repaired=machine.meters["repaired"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "mill": Setting(
        id="mill",
        place="the village mill",
        work_name="mill",
        counter_text="Behind the flour bins stood a worn pine counter where measures were counted and tied with string",
        shaft_name="mill shaft",
        fault="dry_shaft",
        fault_text="the great wheel shuddered, and the mill shaft began to cry like a thirsty branch",
        stop_text="The stones slowed, the sacks waited, and the whole mill nearly stood still.",
        repair_need="oil_rag",
        ending_image="the mill shaft turned smooth as a river reed, and no hungry caller was sent away unheard again",
        tags={"mill", "shaft", "counter"},
    ),
    "wellhouse": Setting(
        id="wellhouse",
        place="the village wellhouse",
        work_name="well",
        counter_text="Beside the jars stood a narrow oak counter where cups, ladles, and little cakes were kept for the day",
        shaft_name="pump shaft",
        fault="loose_peg",
        fault_text="the handle jolted, and the pump shaft slipped in its place with a clacking complaint",
        stop_text="No bucket rose cleanly, and the waiting line at the well grew long and worried.",
        repair_need="wooden_peg",
        ending_image="the pump shaft held firm, the water sang into the buckets again, and a kind word lived there with the cups upon the counter",
        tags={"well", "shaft", "counter", "water"},
    ),
    "press": Setting(
        id="press",
        place="the cider press by the orchard",
        work_name="press",
        counter_text="Near the baskets stood a scrubbed chestnut counter where buns and apple slices waited for workers",
        shaft_name="press shaft",
        fault="stone_block",
        fault_text="the screw groaned, and the press shaft caught against a little wedge of stone hidden below",
        stop_text="The apples sat ready, but no sweet cider ran.",
        repair_need="sweep_stones",
        ending_image="the press shaft turned free, and the smell of fresh cider mixed forever after with the custom of sharing from the counter",
        tags={"press", "shaft", "counter", "orchard"},
    ),
}

GIFTS = {
    "bun": Gift(
        id="bun",
        label="bun",
        phrase="a round honey bun and a clean cup of water",
        share_text="the honey bun and the cup",
        tags={"food"},
    ),
    "apple": Gift(
        id="apple",
        label="apple",
        phrase="a red apple and a heel of brown bread",
        share_text="the apple and the bread",
        tags={"food", "apple"},
    ),
    "porridge": Gift(
        id="porridge",
        label="porridge",
        phrase="a warm bowl of oat porridge and a wooden spoon",
        share_text="the warm bowl",
        tags={"food", "porridge"},
    ),
}

VISITORS = {
    "traveler": VisitorCfg(
        id="traveler",
        label="traveler",
        type="traveler",
        request_text="Dust lay on his boots, and hunger showed plain as weather on his face",
        knows={"oil_rag"},
        kindness_return="You fed me before the wheel complained, and I know how to quiet dry wood",
        tags={"traveler", "kindness"},
    ),
    "widow": VisitorCfg(
        id="widow",
        label="widow",
        type="widow",
        request_text="She leaned on a cane and spoke in a voice gentle enough for birds to trust",
        knows={"wooden_peg"},
        kindness_return="A loose shaft needs only a true peg and patient fingers, and I have mended worse",
        tags={"widow", "kindness"},
    ),
    "shepherd": VisitorCfg(
        id="shepherd",
        label="young shepherd",
        type="shepherd",
        request_text="He carried a crook over one shoulder and looked as though the road had eaten his breakfast",
        knows={"sweep_stones"},
        kindness_return="Stones hide where wheels and screws do not want them, and I have cleared many a stubborn place",
        tags={"shepherd", "kindness"},
    ),
}

REPAIRS = {
    "oil_rag": Repair(
        id="oil_rag",
        sense=3,
        fixes="oil_rag",
        action_text="wrapped the wood in an oiled rag, turned it carefully, and let the dry ache drink its fill",
        qa_text="used an oiled rag to soothe the dry shaft and turn it gently free",
        fail_text="rubbed at the wrong place while the dry wood still cried",
        tags={"repair", "oil"},
    ),
    "wooden_peg": Repair(
        id="wooden_peg",
        sense=3,
        fixes="wooden_peg",
        action_text="trimmed a snug wooden peg with a pocket knife and tapped it neatly into the loosened place",
        qa_text="cut and fitted a new wooden peg so the shaft would hold steady again",
        fail_text="tapped in a poor peg that slipped right back out",
        tags={"repair", "peg"},
    ),
    "sweep_stones": Repair(
        id="sweep_stones",
        sense=2,
        fixes="sweep_stones",
        action_text="knelt with a stiff brush and swept the trapped stones away from the turning base",
        qa_text="brushed the blocking stones away so the shaft could turn again",
        fail_text="brushed too lightly and left the stones wedged beneath the turn",
        tags={"repair", "stones"},
    ),
    "kick_it": Repair(
        id="kick_it",
        sense=1,
        fixes="kick_it",
        action_text="kicked the wood in hope and made the whole frame shiver",
        qa_text="kicked at the shaft",
        fail_text="kicked at the shaft and only made matters worse",
        tags={"repair"},
    ),
}

GIRL_NAMES = ["Mira", "Nela", "Tala", "Rosa", "Anya", "Lina", "Pia", "Sela"]
BOY_NAMES = ["Ivo", "Marek", "Tobin", "Nico", "Pavel", "Darin", "Yori", "Luka"]
TRAITS = ["openhanded", "closefisted"]

ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    setting: str
    visitor: str
    gift: str
    repair: str
    child_name: str
    child_type: str
    elder_type: str
    trait: str
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
    "counter": [
        (
            "What is a counter?",
            "A counter is a flat surface where people set down food, tools, or things they are counting. In a shop or workhouse, it helps keep small things in order."
        )
    ],
    "shaft": [
        (
            "What is a shaft in a machine?",
            "A shaft is a long piece inside a tool or machine that turns and helps other parts move. If it sticks or slips, the whole machine can slow down or stop."
        )
    ],
    "oil": [
        (
            "Why does oil help dry wood turn?",
            "Oil makes rubbing parts slide more smoothly instead of scraping. That helps a dry shaft stop groaning and begin to turn again."
        )
    ],
    "peg": [
        (
            "What does a wooden peg do?",
            "A wooden peg can hold two pieces steady by filling an empty or loose place. A good peg keeps a handle or shaft from wobbling."
        )
    ],
    "stones": [
        (
            "Why can small stones stop a machine?",
            "Even little stones can wedge themselves where turning parts need space. When that happens, a strong machine can still get stuck."
        )
    ],
    "kindness": [
        (
            "What is kindness?",
            "Kindness is choosing to help, share, or speak gently when someone needs care. Small kind acts can change what happens next."
        )
    ],
}
KNOWLEDGE_ORDER = ["counter", "shaft", "oil", "peg", "stones", "kindness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    visitor = f["visitor_cfg"]
    gift = f["gift"]
    child = f["child"]
    outcome = f["outcome"]
    if outcome == "early_kindness":
        return [
            f'Write a folk tale for a young child that includes the words "counter" and "shaft" and teaches kindness.',
            f"Tell a village tale where {child.attrs['name']} shares {gift.label} with a {visitor.label}, and that kindness helps save work at {setting.place}.",
            f"Write a simple old-fashioned story where a child gives from a counter before trouble comes, and the lesson is that kindness returns when needed.",
        ]
    return [
        f'Write a folk tale for a young child that includes the words "counter" and "shaft" and ends with a lesson learned about kindness.',
        f"Tell a village story where {child.attrs['name']} first refuses to share from the counter, but learns kindness when the {setting.shaft_name} stops.",
        f"Write an old-style moral tale in which a child mends a hard heart before a helper mends a shaft.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    visitor = f["visitor"]
    visitor_cfg = f["visitor_cfg"]
    setting = f["setting"]
    gift = f["gift"]
    repair = f["repair"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.attrs['name']}, a child helping at {setting.place}, and a {visitor_cfg.label} who came asking for a little food. {elder.title_word.capitalize()} is there too, quietly guiding the lesson."
        ),
        (
            "What was sitting on the counter?",
            f"There was {gift.phrase} waiting on the counter. That small food became important because it was the thing {child.attrs['name']} could choose to share."
        ),
        (
            f"What trouble came to the {setting.work_name}?",
            f"The {setting.shaft_name} went wrong and the day's work nearly stopped. Because the shaft stuck or slipped, the place could not keep doing what the village needed."
        ),
    ]
    if outcome == "early_kindness":
        qa.append(
            (
                f"How did kindness help when the {setting.shaft_name} failed?",
                f"{child.attrs['name']} had already shared food with the {visitor_cfg.label}, so the visitor felt grateful and stayed to help. Then the {visitor_cfg.label} {repair.qa_text}, and the work started moving again."
            )
        )
        qa.append(
            (
                "What lesson did the child learn?",
                f"The child learned that kindness is not wasted, even when it seems small. Sharing from the counter made a friend before trouble came, and that changed the whole day."
            )
        )
    else:
        qa.append(
            (
                "Why did the child feel ashamed?",
                f"At first {child.attrs['name']} refused to share, but the shaft trouble came right after and showed how quickly a day can turn. When {elder.title_word} spoke, the child understood that a closed hand had made the heart smaller, and that is why the shame felt sharp."
            )
        )
        qa.append(
            (
                "How was the problem finally solved?",
                f"After hearing the lesson, {child.attrs['name']} ran back with the gift and asked forgiveness. The {visitor_cfg.label} answered with kindness, {repair.qa_text}, and the work began again."
            )
        )
        qa.append(
            (
                "What lesson was learned at the end?",
                f"The child learned that kindness should be given early, not saved until after trouble begins. Still, the tale also shows that a humble apology and a changed heart can mend much."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"counter", "shaft", "kindness"} | set(f["repair"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="mill",
        visitor="traveler",
        gift="bun",
        repair="oil_rag",
        child_name="Mira",
        child_type="girl",
        elder_type="grandmother",
        trait="openhanded",
        seed=101,
    ),
    StoryParams(
        setting="wellhouse",
        visitor="widow",
        gift="porridge",
        repair="wooden_peg",
        child_name="Ivo",
        child_type="boy",
        elder_type="grandfather",
        trait="closefisted",
        seed=102,
    ),
    StoryParams(
        setting="press",
        visitor="shepherd",
        gift="apple",
        repair="sweep_stones",
        child_name="Rosa",
        child_type="girl",
        elder_type="grandmother",
        trait="openhanded",
        seed=103,
    ),
    StoryParams(
        setting="mill",
        visitor="traveler",
        gift="apple",
        repair="oil_rag",
        child_name="Luka",
        child_type="boy",
        elder_type="grandfather",
        trait="closefisted",
        seed=104,
    ),
]


ASP_RULES = r"""
valid(S,V,G,R) :- setting(S), visitor(V), gift(G), repair(R),
                  need(S,N), fixes(R,N), knows(V,R), sensible(R).

sensible(R) :- repair(R), sense(R,S), sense_min(M), S >= M.

outcome(early_kindness) :- trait(openhanded).
outcome(learned_kindness) :- trait(closefisted).

#show valid/4.
#show sensible/1.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("need", sid, setting.repair_need))
    for vid, visitor in VISITORS.items():
        lines.append(asp.fact("visitor", vid))
        for rid in sorted(visitor.knows):
            lines.append(asp.fact("knows", vid, rid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("sense", rid, repair.sense))
        lines.append(asp.fact("fixes", rid, repair.fixes))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = asp.fact("trait", params.trait)
    model = asp.one_model(asp_program(extra))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Folk-tale storyworld: a counter, a shaft, and a lesson in kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--visitor", choices=VISITORS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.visitor and args.repair:
        setting = SETTINGS[args.setting]
        visitor = VISITORS[args.visitor]
        repair = REPAIRS[args.repair]
        if not (repair_matches(setting, repair) and visitor_can_help(visitor, repair) and repair.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(setting, visitor, repair))
    if args.repair and REPAIRS[args.repair].sense < SENSE_MIN:
        raise StoryError(
            f"(Refusing repair '{args.repair}': it scores too low on common sense "
            f"(sense={REPAIRS[args.repair].sense} < {SENSE_MIN}).)"
        )

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.visitor is None or combo[1] == args.visitor)
        and (args.gift is None or combo[2] == args.gift)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, visitor_id, gift_id, repair_id = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if child_type == "girl" else BOY_NAMES
    child_name = args.child_name or rng.choice(pool)
    elder_type = args.elder_type or rng.choice(ELDERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        visitor=visitor_id,
        gift=gift_id,
        repair=repair_id,
        child_name=child_name,
        child_type=child_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        visitor = VISITORS[params.visitor]
        gift = GIFTS[params.gift]
        repair = REPAIRS[params.repair]
    except KeyError as err:
        raise StoryError(f"(Unknown story parameter: {err.args[0]})") from None

    if not (repair_matches(setting, repair) and visitor_can_help(visitor, repair) and repair.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(setting, visitor, repair))

    world = tell(
        setting=setting,
        gift=gift,
        visitor_cfg=visitor,
        repair=repair,
        child_name=params.child_name,
        child_type=params.child_type,
        elder_type=params.elder_type,
        trait=params.trait,
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

    python_valid = set(valid_combos())
    clingo_valid = set(asp_valid_combos())
    if python_valid == clingo_valid:
        print(f"OK: valid_combos parity holds ({len(python_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos():")
        if python_valid - clingo_valid:
            print("  only in python:", sorted(python_valid - clingo_valid))
        if clingo_valid - python_valid:
            print("  only in clingo:", sorted(clingo_valid - python_valid))

    python_sensible = {r.id for r in sensible_repairs()}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible repairs match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible repairs: python={sorted(python_sensible)} clingo={sorted(clingo_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(25):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected resolve failure at seed {seed}.")
            break

    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible repairs: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, visitor, gift, repair) combos:\n")
        for setting, visitor, gift, repair in combos:
            print(f"  {setting:10} {visitor:10} {gift:8} {repair}")
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
            header = (
                f"### {p.child_name}: {p.setting} / {p.visitor} / {p.gift} / "
                f"{p.repair} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
