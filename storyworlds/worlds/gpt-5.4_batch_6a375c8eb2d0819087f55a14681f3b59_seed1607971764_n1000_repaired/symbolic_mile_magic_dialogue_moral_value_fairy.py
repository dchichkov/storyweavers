#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py
==============================================================================

A standalone story world for a small fairy-tale domain: a child walks a symbolic
mile with a single magic charm, meets a creature in need, and discovers that a
gift given away can come back as help when the road grows hard.

The world is built as a simulation rather than a frozen paragraph template:
typed entities carry physical meters and emotional memes, a few causal rules
propagate consequences, and the prose reads back the resulting state. The core
moral shape is simple and child-facing: kindness makes room for help.

Run it
------
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py --choice keep
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py --gift star_spark --helper moth --hazard shadow_path
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py --all
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/symbolic_mile_magic_dialogue_moral_value_fairy.py --verify
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "grandmother", "godmother", "fairy"}
        male = {"boy", "man", "grandfather", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
class Quest:
    id: str
    item: str
    item_phrase: str
    destination: str
    elder_line: str
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
    rescue_kind: str
    glow: str
    lesson: str
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
class Helper:
    id: str
    label: str
    phrase: str
    need: str
    trouble: str
    thanks: str
    aid_kind: str
    return_line: str
    ending_pose: str
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
class Hazard:
    id: str
    label: str
    block_text: str
    solved_by: str
    clear_text: str
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


def _r_gratitude(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    if helper.meters["rescued"] >= THRESHOLD:
        sig = ("gratitude", helper.id)
        if sig not in world.fired:
            world.fired.add(sig)
            helper.memes["gratitude"] += 1
            out.append("__gratitude__")
    return out


def _r_hazard_fear(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    hazard = world.get("hazard")
    if hazard.meters["blocking"] >= THRESHOLD:
        sig = ("hazard_fear", hazard.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] += 1
            out.append("__worry__")
    return out


def _r_repay(world: World) -> list[str]:
    out: list[str] = []
    helper = world.get("helper")
    hazard = world.get("hazard")
    if helper.memes["gratitude"] >= THRESHOLD and hazard.meters["blocking"] >= THRESHOLD:
        if helper.attrs.get("aid_kind") == hazard.attrs.get("solved_by"):
            sig = ("repay", helper.id, hazard.id)
            if sig not in world.fired:
                world.fired.add(sig)
                helper.meters["helping"] += 1
                hazard.meters["cleared"] += 1
                hazard.meters["blocking"] = 0.0
                out.append("__repay__")
    return out


def _r_arrive(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    quest_item = world.get("quest_item")
    hazard = world.get("hazard")
    if quest_item.meters["carried"] >= THRESHOLD and hazard.meters["blocking"] < THRESHOLD:
        sig = ("arrive", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["arrived"] += 1
            out.append("__arrive__")
    return out


CAUSAL_RULES = [
    Rule(name="gratitude", tag="social", apply=_r_gratitude),
    Rule(name="hazard_fear", tag="emotion", apply=_r_hazard_fear),
    Rule(name="repay", tag="social", apply=_r_repay),
    Rule(name="arrive", tag="physical", apply=_r_arrive),
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


def rescue_matches(gift: Gift, helper: Helper) -> bool:
    return gift.rescue_kind == helper.need


def aid_matches(helper: Helper, hazard: Hazard) -> bool:
    return helper.aid_kind == hazard.solved_by


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for quest_id in QUESTS:
        for gift_id, gift in GIFTS.items():
            for helper_id, helper in HELPERS.items():
                for hazard_id, hazard in HAZARDS.items():
                    if rescue_matches(gift, helper) and aid_matches(helper, hazard):
                        combos.append((quest_id, gift_id, helper_id, hazard_id))
    return combos


def explain_rejection(gift: Gift, helper: Helper, hazard: Hazard) -> str:
    if not rescue_matches(gift, helper):
        return (
            f"(No story: {gift.label} cannot help {helper.phrase}. "
            f"{helper.label.capitalize()} needs {helper.need}, but the charm gives "
            f"{gift.rescue_kind}. Pick a charm that can truly help first.)"
        )
    if not aid_matches(helper, hazard):
        return (
            f"(No story: even if {helper.phrase} is helped, {helper.pronoun('subject') if isinstance(helper, Entity) else helper.label} "
            f"would not know how to solve {hazard.label}. The road's turn should be fixed by the creature the child helped.)"
        )
    return "(No story: this combination does not form a coherent fairy-tale chain.)"


def outcome_of(params: "StoryParams") -> str:
    return "delivered" if params.choice == "share" else "turned_back"


def predict_kindness(world: World) -> dict:
    sim = world.copy()
    helper = sim.get("helper")
    helper.meters["rescued"] += 1
    propagate(sim, narrate=False)
    sim.get("hazard").meters["blocking"] += 1
    propagate(sim, narrate=False)
    return {
        "helper_returns": helper.meters["helping"] >= THRESHOLD,
        "arrives": sim.get("hero").meters["arrived"] >= THRESHOLD,
    }


def quest_start(world: World, elder: Entity, hero: Entity, quest: Quest, gift: Gift) -> None:
    hero.memes["duty"] += 1
    hero.memes["wonder"] += 1
    world.say(
        f"Once, when the dawn was still pearly on the cottage roof, {hero.id} was given "
        f"{quest.item_phrase} and a single charm: {gift.phrase}."
    )
    world.say(
        f'"Walk one symbolic mile to {quest.destination}," said {elder.id}. '
        f'"{quest.elder_line}"'
    )


def set_out(world: World, hero: Entity, quest: Quest) -> None:
    item = world.get("quest_item")
    item.meters["carried"] += 1
    world.say(
        f"{hero.id} tucked {quest.item} close and stepped onto the mossy path. "
        f"The mile was not long in boots and stones, but it felt large in the heart."
    )


def meet_helper(world: World, hero: Entity, helper: Entity, helper_cfg: Helper, gift: Gift) -> None:
    helper.meters["troubled"] += 1
    hero.memes["pity"] += 1
    world.say(
        f"Before halfway, {hero.id} heard a small voice. There was {helper_cfg.phrase}, "
        f"and {helper_cfg.trouble}."
    )
    world.say(
        f'"Please," said the {helper_cfg.label}, "I only need a little {helper_cfg.need}. '
        f'Will you spare it?"'
    )
    world.say(
        f"{hero.id} looked at {gift.phrase}. It was the only magic on the path."
    )


def share_gift(world: World, hero: Entity, helper: Entity, helper_cfg: Helper, gift: Gift) -> None:
    gift_ent = world.get("gift")
    gift_ent.meters["shared"] += 1
    gift_ent.meters["charge"] = 0.0
    helper.meters["rescued"] += 1
    hero.memes["kindness"] += 1
    hero.memes["trust"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"Then take it," said {hero.id}. {hero.pronoun("subject").capitalize()} held out '
        f"{gift.phrase}, and at once {gift.glow}."
    )
    world.say(helper_cfg.thanks)
    if helper.memes["gratitude"] >= THRESHOLD:
        world.say(
            f"The little creature bowed so low that its nose nearly brushed the path. "
            f'"I will remember," it said.'
        )


def keep_gift(world: World, hero: Entity, helper_cfg: Helper, gift: Gift) -> None:
    hero.memes["guilt"] += 1
    hero.memes["worry"] += 1
    world.say(
        f'{hero.id} closed {hero.pronoun("possessive")} fingers around {gift.phrase}. '
        f'"I am sorry," {hero.pronoun("subject")} whispered, "but I may need it more."'
    )
    world.say(
        f"The {helper_cfg.label} made no angry sound. That was almost sadder. "
        f"It only drew back and watched {hero.id} go on alone."
    )


def road_turn(world: World, hero: Entity, helper_cfg: Helper, hazard_cfg: Hazard) -> None:
    hazard = world.get("hazard")
    hazard.meters["blocking"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the far end of the wood, the road changed. {hazard_cfg.block_text}"
    )
    if hero.memes["worry"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s courage gave a little shake. The last of the path no longer looked easy."
        )


def repay_help(world: World, helper_cfg: Helper, hazard_cfg: Hazard) -> None:
    helper = world.get("helper")
    if helper.meters["helping"] < THRESHOLD:
        return
    world.say(helper_cfg.return_line)
    world.say(hazard_cfg.clear_text)


def fail_turn(world: World, hero: Entity, hazard_cfg: Hazard) -> None:
    hero.meters["turned_back"] += 1
    hero.memes["lesson"] += 1
    world.say(hazard_cfg.fail_text)
    world.say(
        f"{hero.id} stood very still. At last {hero.pronoun('subject')} turned around, "
        f"carrying the undelivered gift back through the trees."
    )


def arrive_and_finish(world: World, hero: Entity, quest: Quest, elder: Entity, helper_cfg: Helper) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"Beyond the last bend lay {quest.destination}. {hero.id} laid down {quest.item}, "
        f"and {quest.ending_image}"
    )
    world.say(
        f'When {hero.pronoun("subject")} came home, {elder.id} smiled and said, '
        f'"Now you know the oldest magic of all."'
    )
    world.say(
        f'{hero.id} nodded. "A hand that opens on the road does not stay empty for long," '
        f'{hero.pronoun("subject")} said.'
    )
    world.say(
        f"High on a branch nearby, the {helper_cfg.label} kept {helper_cfg.ending_pose}."
    )


def return_and_learn(world: World, hero: Entity, elder: Entity, helper_cfg: Helper, gift: Gift) -> None:
    hero.memes["sadness"] += 1
    world.say(
        f"Back at the cottage, {elder.id} listened without scolding. "
        f'"What did the mile teach you?" {elder.pronoun("subject")} asked.'
    )
    world.say(
        f'{hero.id} looked down at the quiet charm. "That {gift.lesson}," '
        f'{hero.pronoun("subject")} answered. "Next time I will be braver with my kindness."'
    )
    world.say(
        f"Outside, a small shape still waited near the hedge. The {helper_cfg.label} was there, "
        f"and {hero.id} understood whom {hero.pronoun('subject')} had forgotten to see."
    )


def tell(
    quest: Quest,
    gift: Gift,
    helper_cfg: Helper,
    hazard_cfg: Hazard,
    *,
    hero_name: str = "Mira",
    hero_gender: str = "girl",
    elder_type: str = "grandmother",
    choice: str = "share",
) -> World:
    world = World()

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero"))
    elder = world.add(
        Entity(
            id="Grandmother" if elder_type == "grandmother" else "Godmother",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
        )
    )
    helper = world.add(
        Entity(
            id=helper_cfg.label.capitalize(),
            kind="character",
            type="creature",
            role="helper",
            label=helper_cfg.label,
            attrs={"aid_kind": helper_cfg.aid_kind, "need": helper_cfg.need},
        )
    )
    world.add(
        Entity(
            id="gift",
            type="charm",
            label=gift.label,
            attrs={"rescue_kind": gift.rescue_kind},
        )
    )
    world.add(
        Entity(
            id="quest_item",
            type="quest_item",
            label=quest.item,
        )
    )
    world.add(
        Entity(
            id="hazard",
            type="hazard",
            label=hazard_cfg.label,
            attrs={"solved_by": hazard_cfg.solved_by},
        )
    )

    world.facts.update(
        quest=quest,
        gift_cfg=gift,
        helper_cfg=helper_cfg,
        hazard_cfg=hazard_cfg,
        choice=choice,
    )

    world.get("gift").meters["charge"] = 1.0
    world.get("hazard").meters["blocking"] = 0.0
    helper.meters["rescued"] = 0.0
    helper.meters["helping"] = 0.0
    helper.meters["troubled"] = 0.0
    world.get("quest_item").meters["carried"] = 0.0
    hero.meters["arrived"] = 0.0
    hero.meters["turned_back"] = 0.0

    quest_start(world, elder, hero, quest, gift)
    set_out(world, hero, quest)

    world.para()
    meet_helper(world, hero, helper, helper_cfg, gift)

    predicted = predict_kindness(world)
    world.facts["predicted_if_shared"] = predicted

    if choice == "share":
        share_gift(world, hero, helper, helper_cfg, gift)
    else:
        keep_gift(world, hero, helper_cfg, gift)

    world.para()
    road_turn(world, hero, helper_cfg, hazard_cfg)

    if choice == "share":
        repay_help(world, helper_cfg, hazard_cfg)
        propagate(world, narrate=False)
        world.para()
        arrive_and_finish(world, hero, quest, elder, helper_cfg)
        outcome = "delivered"
    else:
        fail_turn(world, hero, hazard_cfg)
        world.para()
        return_and_learn(world, hero, elder, helper_cfg, gift)
        outcome = "turned_back"

    world.facts.update(
        hero=hero,
        elder=elder,
        helper=helper,
        gift=world.get("gift"),
        quest_item=world.get("quest_item"),
        hazard=world.get("hazard"),
        rescued=helper.meters["rescued"] >= THRESHOLD,
        repaid=helper.meters["helping"] >= THRESHOLD,
        arrived=hero.meters["arrived"] >= THRESHOLD,
        turned_back=hero.meters["turned_back"] >= THRESHOLD,
        outcome=outcome,
    )
    return world


QUESTS = {
    "moonwell": Quest(
        id="moonwell",
        item="a silver cup of spring water",
        item_phrase="a silver cup of spring water",
        destination="the Moonwell",
        elder_line="Pour the water there before the noon bell, and the lilies will open for the village",
        ending_image="the pale pool shivered, and white lilies lifted their faces like little moons",
        tags={"moonwell", "water"},
    ),
    "elder_tree": Quest(
        id="elder_tree",
        item="a ribbon of waking gold",
        item_phrase="a ribbon of waking gold",
        destination="the oldest elder tree",
        elder_line="Tie this to the elder's lowest bough, and the sleeping birds will find their song again",
        ending_image="the bark warmed, and leaves came whispering out like green secrets",
        tags={"tree", "birds"},
    ),
    "hill_lantern": Quest(
        id="hill_lantern",
        item="a bell of clear glass",
        item_phrase="a bell of clear glass",
        destination="the lantern tower on the hill",
        elder_line="Hang the bell there, and the lost travelers will see a gentle light by dusk",
        ending_image="the tower window kindled, and gold light streamed across the valley grass",
        tags={"tower", "light"},
    ),
}

GIFTS = {
    "star_spark": Gift(
        id="star_spark",
        label="star-spark",
        phrase="a star-spark in a crystal acorn",
        rescue_kind="light",
        glow="a warm pin of starlight spilled through the dim leaves",
        lesson="magic kept too tightly in the hand can become smaller than kindness",
        tags={"light", "magic"},
    ),
    "healing_hum": Gift(
        id="healing_hum",
        label="healing hum",
        phrase="a healing hum folded inside a blue thimble",
        rescue_kind="healing",
        glow="a soft humming ring floated out and stitched hurt into comfort",
        lesson="a guarded gift cannot mend a lonely heart or a hard road",
        tags={"healing", "magic"},
    ),
    "reed_charm": Gift(
        id="reed_charm",
        label="reed charm",
        phrase="a reed charm tied with river thread",
        rescue_kind="wood",
        glow="the river thread flashed, and little sticks hurried together as if they had heard their names",
        lesson="when help is withheld, the path keeps its thorns and water keeps its width",
        tags={"wood", "magic"},
    ),
}

HELPERS = {
    "moth": Helper(
        id="moth",
        label="moth",
        phrase="a pearl moth shivering in a dark hollow",
        need="light",
        trouble="its powdery wings could not find the opening back to the sky",
        thanks='"You have given me a little dawn," said the moth.',
        aid_kind="guide",
        return_line='Then a flutter of pale wings circled back. "This way," cried the moth.',
        ending_pose="its lantern-pale wings folded like a blessing",
        tags={"moth", "light"},
    ),
    "robin": Helper(
        id="robin",
        label="robin",
        phrase="a red-breasted robin huddled under a fern",
        need="healing",
        trouble="one wing drooped, and every hop looked sore",
        thanks='"My song can breathe again," said the robin.',
        aid_kind="find_gap",
        return_line='There came a bright chirp from above. "Not through the thorns," sang the robin. "Over here."',
        ending_pose="a red feather shining among the leaves",
        tags={"robin", "healing"},
    ),
    "beaver": Helper(
        id="beaver",
        label="beaver",
        phrase="a young beaver beside a spill of broken sticks",
        need="wood",
        trouble="its little dam had come apart, and the stream kept stealing each branch away",
        thanks='"You have put my world back together," said the beaver.',
        aid_kind="bridge",
        return_line='From the reeds came a splash and a slap of a tail. "Wait," called the beaver. "I know this kind of water."',
        ending_pose="its whiskers bright with river drops",
        tags={"beaver", "water", "wood"},
    ),
}

HAZARDS = {
    "shadow_path": Hazard(
        id="shadow_path",
        label="the shadow path",
        block_text="A lane of blue-black shadow lay across the ground, and the true path had gone thin as thread inside it.",
        solved_by="guide",
        clear_text="The moth flew ahead, making a tiny moving star, and the hidden path stepped out from the dark as plainly as ribbon on a table.",
        fail_text="The shadows kept folding over one another until the wood seemed full of false turnings.",
        tags={"dark", "path"},
    ),
    "thorn_gate": Hazard(
        id="thorn_gate",
        label="the thorn gate",
        block_text="A wall of briars had knitted itself over the road, with only one narrow and secret opening somewhere inside.",
        solved_by="find_gap",
        clear_text="The robin darted to a low green arch that no one on the ground would have noticed, and soon the child was through without one scratch.",
        fail_text="The briars hooked at sleeves and hems, and every opening led to more green needles.",
        tags={"thorns", "path"},
    ),
    "brook_crossing": Hazard(
        id="brook_crossing",
        label="the brook crossing",
        block_text="The stepping stones were gone under a quick silver brook, and the water talked too loudly to trust.",
        solved_by="bridge",
        clear_text="The beaver nosed branches into place, patted them tight with clever paws, and made a bridge that held as steady as an old promise.",
        fail_text="The brook ran broad and laughing, and there was no safe way to step across with the precious burden dry.",
        tags={"brook", "water"},
    ),
}

GIRL_NAMES = ["Mira", "Elsie", "Nora", "Wren", "Lina", "Ada", "Ivy", "Tessa"]
BOY_NAMES = ["Rowan", "Theo", "Finn", "Eli", "Hugo", "Milo", "Alden", "Pip"]


@dataclass
class StoryParams:
    quest: str
    gift: str
    helper: str
    hazard: str
    choice: str
    hero_name: str
    hero_gender: str
    elder_type: str
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
    "magic": [
        (
            "What is magic in a fairy tale?",
            "In a fairy tale, magic is a special power that can change what happens in the world. It often works best when it is used wisely and kindly."
        )
    ],
    "symbolic": [
        (
            "What does symbolic mean?",
            "Symbolic means something stands for a bigger idea. A symbolic mile can be a short walk that also shows a big lesson in the heart."
        )
    ],
    "moral": [
        (
            "What is a moral in a story?",
            "A moral is the lesson a story teaches. Many fairy tales use wonder and trouble to show what kind choices matter."
        )
    ],
    "moth": [
        (
            "How can a moth help in the dark?",
            "A moth can find its way by light and flutter ahead where others cannot see well. In a fairy tale, that makes it a gentle guide."
        )
    ],
    "robin": [
        (
            "Why is a robin a good fairy-tale helper?",
            "A robin can sing from high branches and spot things from above. That makes it a good little scout for hidden paths."
        )
    ],
    "beaver": [
        (
            "Why is a beaver linked with bridges?",
            "Beavers are good at moving sticks and shaping water. So in a story, a beaver can believably help at a stream."
        )
    ],
    "kindness": [
        (
            "Why can kindness change a story?",
            "Kindness can make another person or creature feel safe enough to help back. In stories and in life, care often travels in a circle."
        )
    ],
    "shadow": [
        (
            "Why are shadows often scary in fairy tales?",
            "Shadows hide the shape of the road and make small things feel uncertain. Fairy tales use them to show fear before courage."
        )
    ],
    "thorn": [
        (
            "Why do fairy tales use thorns?",
            "Thorns can stand for a hard problem that cannot be rushed through. They make the hero slow down and find a wiser way."
        )
    ],
    "brook": [
        (
            "What is a brook?",
            "A brook is a small stream of moving water. It can still be hard to cross when it runs fast."
        )
    ],
}

KNOWLEDGE_ORDER = ["magic", "symbolic", "moral", "moth", "robin", "beaver", "kindness", "shadow", "thorn", "brook"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    quest = f["quest"]
    gift = f["gift_cfg"]
    helper = f["helper_cfg"]
    hazard = f["hazard_cfg"]
    hero = f["hero"]
    if f["outcome"] == "delivered":
        return [
            f'Write a short fairy tale that includes the words "symbolic" and "mile", with magic, dialogue, and a clear moral value.',
            f"Tell a fairy-tale story where {hero.id} walks a symbolic mile to {quest.destination}, gives away {gift.phrase}, and later receives help from a {helper.label} at {hazard.label}.",
            f"Write a gentle moral tale where kindness given on the road becomes the very magic that helps a child finish a quest.",
        ]
    return [
        f'Write a short fairy tale that includes the words "symbolic" and "mile", with magic, dialogue, and a clear moral value.',
        f"Tell a cautionary fairy-tale story where {hero.id} keeps {gift.phrase}, reaches {hazard.label} alone, and learns that kindness would have opened the road.",
        f"Write a moral tale in which a child chooses fear over generosity on a magical journey and comes home wiser.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    quest = f["quest"]
    gift = f["gift_cfg"]
    helper = f["helper_cfg"]
    hazard = f["hazard_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child sent on a fairy-tale errand by {elder.id}. The journey is small in distance but big in meaning, which is why the mile feels symbolic."
        ),
        (
            f"What was {hero.id} asked to do?",
            f"{hero.pronoun('subject').capitalize()} was asked to carry {quest.item_phrase} to {quest.destination}. The task mattered because {quest.elder_line.lower()}."
        ),
        (
            f"Whom did {hero.id} meet on the road?",
            f"{hero.pronoun('subject').capitalize()} met {helper.phrase}. The little creature asked for {helper.need}, which tested whether the child would hold tight or share."
        ),
    ]
    if f["choice"] == "share":
        qa.append(
            (
                f"Why did the {helper.label} help {hero.id} later?",
                f"The {helper.label} helped because {hero.id} had shared the only charm instead of keeping it. That rescue created gratitude, and the grateful creature returned when the road became dangerous."
            )
        )
        qa.append(
            (
                f"How did {hero.id} get past {hazard.label}?",
                f"{helper.return_line.replace(chr(34), '')} {hazard.clear_text} The solution came from the very creature {hero.id} had helped earlier."
            )
        )
        qa.append(
            (
                "What is the moral of this story?",
                f"The moral is that kindness can be a stronger magic than keeping things for yourself. {hero.id}'s open hand led to safety, success, and a brighter ending."
            )
        )
    else:
        qa.append(
            (
                f"Why could {hero.id} not get past {hazard.label}?",
                f"{hero.pronoun('subject').capitalize()} reached the hard part of the road alone because {hero.pronoun('subject')} had not helped the {helper.label}. The story shows cause and effect: the missing act of kindness meant no one came back to guide or rescue {hero.pronoun('object')}."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hero.id} turning back and bringing the lesson home instead of finishing the errand. That sadder ending still resolves the story because the child understands what should be done next time."
            )
        )
        qa.append(
            (
                "What is the moral of this story?",
                f"The moral is that fear can make a hand close, but a closed hand often leaves a person lonelier. The child learns that kindness shared on the road might have opened the way."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"magic", "symbolic", "moral", "kindness"}
    tags |= set(world.facts["helper_cfg"].tags)
    tags |= set(world.facts["hazard_cfg"].tags)
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
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:12} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        quest="moonwell",
        gift="star_spark",
        helper="moth",
        hazard="shadow_path",
        choice="share",
        hero_name="Mira",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="elder_tree",
        gift="healing_hum",
        helper="robin",
        hazard="thorn_gate",
        choice="share",
        hero_name="Rowan",
        hero_gender="boy",
        elder_type="godmother",
    ),
    StoryParams(
        quest="hill_lantern",
        gift="reed_charm",
        helper="beaver",
        hazard="brook_crossing",
        choice="share",
        hero_name="Nora",
        hero_gender="girl",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="moonwell",
        gift="star_spark",
        helper="moth",
        hazard="shadow_path",
        choice="keep",
        hero_name="Theo",
        hero_gender="boy",
        elder_type="grandmother",
    ),
    StoryParams(
        quest="elder_tree",
        gift="healing_hum",
        helper="robin",
        hazard="thorn_gate",
        choice="keep",
        hero_name="Ivy",
        hero_gender="girl",
        elder_type="godmother",
    ),
]


ASP_RULES = r"""
usable(G,H) :- gift(G), helper(H), rescues(G,K), needs(H,K).
repays(H,Z) :- helper(H), hazard(Z), aids(H,A), solved_by(Z,A).
valid(Q,G,H,Z) :- quest(Q), usable(G,H), repays(H,Z).

outcome(delivered) :- choice(share).
outcome(turned_back) :- choice(keep).

#show valid/4.
#show outcome/1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("rescues", gid, gift.rescue_kind))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("needs", hid, helper.need))
        lines.append(asp.fact("aids", hid, helper.aid_kind))
    for zid, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", zid))
        lines.append(asp.fact("solved_by", zid, hazard.solved_by))
    return "\n".join(lines)


def asp_program(extra: str = "") -> str:
    return f"{asp_facts()}\n{extra}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    model = asp.one_model(asp_program(asp.fact("choice", params.choice)))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale story world: a symbolic mile, a small magic charm, a choice between fear and kindness."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--choice", choices=["share", "keep"])
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "godmother"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.gift and args.helper and not rescue_matches(GIFTS[args.gift], HELPERS[args.helper]):
        raise StoryError(explain_rejection(GIFTS[args.gift], HELPERS[args.helper], HAZARDS[args.hazard] if args.hazard else next(iter(HAZARDS.values()))))
    if args.helper and args.hazard and not aid_matches(HELPERS[args.helper], HAZARDS[args.hazard]):
        gift = GIFTS[args.gift] if args.gift else next(iter(GIFTS.values()))
        raise StoryError(explain_rejection(gift, HELPERS[args.helper], HAZARDS[args.hazard]))

    combos = [
        combo for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.gift is None or combo[1] == args.gift)
        and (args.helper is None or combo[2] == args.helper)
        and (args.hazard is None or combo[3] == args.hazard)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    quest, gift, helper, hazard = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "godmother"])
    choice = args.choice or rng.choice(["share", "keep"])
    return StoryParams(
        quest=quest,
        gift=gift,
        helper=helper,
        hazard=hazard,
        choice=choice,
        hero_name=hero_name,
        hero_gender=hero_gender,
        elder_type=elder_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Invalid quest: {params.quest})")
    if params.gift not in GIFTS:
        raise StoryError(f"(Invalid gift: {params.gift})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Invalid hazard: {params.hazard})")
    if params.choice not in {"share", "keep"}:
        raise StoryError(f"(Invalid choice: {params.choice})")
    if (params.quest, params.gift, params.helper, params.hazard) not in set(valid_combos()):
        raise StoryError(explain_rejection(GIFTS[params.gift], HELPERS[params.helper], HAZARDS[params.hazard]))

    world = tell(
        QUESTS[params.quest],
        GIFTS[params.gift],
        HELPERS[params.helper],
        HAZARDS[params.hazard],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        elder_type=params.elder_type,
        choice=params.choice,
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
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid-combo gate matches ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    cases = list(CURATED)
    default_args = build_parser().parse_args([])
    for s in range(20):
        try:
            p = resolve_params(default_args, random.Random(s))
            p.seed = s
            cases.append(p)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed on seed {s}.")
            break

    bad = 0
    for params in cases:
        ao = asp_outcome(params)
        po = outcome_of(params)
        if ao != po:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(cases[0])
        if not smoke.story.strip():
            raise StoryError("(Smoke test generated an empty story.)")
        emit(smoke, trace=False, qa=False, header="--- smoke test ---")
        print("OK: smoke test story generated and emitted.")
    except Exception as err:
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
        print(f"{len(combos)} compatible (quest, gift, helper, hazard) combos:\n")
        for quest, gift, helper, hazard in combos:
            print(f"  {quest:12} {gift:12} {helper:8} {hazard}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
            header = f"### {p.hero_name}: {p.choice} / {p.gift} / {p.helper} / {p.hazard}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
