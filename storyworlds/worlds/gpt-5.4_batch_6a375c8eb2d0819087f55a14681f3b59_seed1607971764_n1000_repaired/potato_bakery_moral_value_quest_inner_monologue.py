#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py
==============================================================================

A standalone story world for a fairy-tale bakery quest built around a warm
potato pastry, a hungry errand, an inner monologue, and a moral choice.

Premise
-------
In a little bakery, a young helper is trusted with a quest: carry the last warm
potato loaf to someone who truly needs it. The road offers both an outer problem
(rain, wind, or birds) and an inner one (the smell of the loaf and the wish to
keep a bite). The story turns on a moral choice: patience and kindness, or a
mistake followed by honesty. Either way, the world model drives what happens.

Run it
------
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py --recipient watchman --obstacle rain --gear waxed_cloth
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py --gear bell_ribbon --obstacle rain
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py --all
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/potato_bakery_moral_value_quest_inner_monologue.py --verify
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
RESIST_THRESHOLD = 8


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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man", "watchman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Recipient:
    id: str
    label: str
    phrase: str
    type: str
    place: str
    need_text: str
    thanks_text: str
    route: set[str] = field(default_factory=set)
    need_score: int = 4
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
class Obstacle:
    id: str
    label: str
    danger_text: str
    image_text: str
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
class Gear:
    id: str
    label: str
    phrase: str
    use_text: str
    guards: set[str] = field(default_factory=set)
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
class Trait:
    id: str
    score: int
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
class World:
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


def _r_obstacle_harms_pastry(world: World) -> list[str]:
    pastry = world.entities.get("pastry")
    road = world.entities.get("road")
    gear = world.entities.get("gear")
    if not pastry or not road or road.meters["hazard"] < THRESHOLD:
        return []
    obstacle_id = world.facts.get("obstacle_id", "")
    protected = bool(gear and obstacle_id in gear.attrs.get("guards", set()))
    sig = ("hazard", obstacle_id, protected)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if protected:
        pastry.meters["safe"] += 1
        return []
    pastry.meters["damaged"] += 1
    if obstacle_id == "rain":
        pastry.meters["wet"] += 1
    elif obstacle_id == "wind":
        pastry.meters["cold"] += 1
    elif obstacle_id == "birds":
        pastry.meters["pecked"] += 1
    hero = world.entities.get("hero")
    if hero:
        hero.memes["worry"] += 1
    return ["__damage__"]


def _r_damage_causes_guilt(world: World) -> list[str]:
    hero = world.entities.get("hero")
    pastry = world.entities.get("pastry")
    if not hero or not pastry or pastry.meters["damaged"] < THRESHOLD:
        return []
    sig = ("guilt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["guilt"] += 1
    return []


def _r_delivery_comforts(world: World) -> list[str]:
    recipient = world.entities.get("recipient")
    pastry = world.entities.get("pastry")
    if not recipient or not pastry or pastry.meters["delivered"] < THRESHOLD:
        return []
    sig = ("comfort",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    recipient.meters["comfort"] += 1
    hero = world.entities.get("hero")
    baker = world.entities.get("baker")
    if hero:
        hero.memes["relief"] += 1
        hero.memes["joy"] += 1
    if baker:
        baker.memes["pride"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="obstacle_harms_pastry", tag="physical", apply=_r_obstacle_harms_pastry),
    Rule(name="damage_causes_guilt", tag="emotional", apply=_r_damage_causes_guilt),
    Rule(name="delivery_comforts", tag="social", apply=_r_delivery_comforts),
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
        for s in produced:
            world.say(s)
    return produced


RECIPIENTS = {
    "watchman": Recipient(
        id="watchman",
        label="watchman",
        phrase="the old watchman in the clock tower",
        type="watchman",
        place="the clock tower",
        need_text="had stood in the dawn cold since before the ovens were lit",
        thanks_text="The old watchman wrapped both hands around the loaf as if it were a little sun.",
        route={"wind"},
        need_score=5,
        tags={"kindness", "tower", "share"},
    ),
    "seamstress": Recipient(
        id="seamstress",
        label="seamstress",
        phrase="the village seamstress by the river lane",
        type="woman",
        place="the river lane",
        need_text="had worked all night mending coats for children",
        thanks_text="The seamstress smiled over her silver needle and said the bakery had stitched warmth right into the morning.",
        route={"rain"},
        need_score=4,
        tags={"kindness", "river", "share"},
    ),
    "gardener": Recipient(
        id="gardener",
        label="gardener",
        phrase="the sleepy gardener beyond the plum yard",
        type="man",
        place="the plum yard",
        need_text="had spent the early hours turning the earth and had not yet eaten",
        thanks_text="The gardener laughed softly and said even the plum trees seemed happier when kindness arrived with breakfast.",
        route={"birds"},
        need_score=3,
        tags={"kindness", "garden", "share"},
    ),
}

OBSTACLES = {
    "rain": Obstacle(
        id="rain",
        label="rain",
        danger_text="thin rain began to stitch the street with silver threads",
        image_text="The drops pattered on shutters and tried to creep into the basket.",
        tags={"rain"},
    ),
    "wind": Obstacle(
        id="wind",
        label="wind",
        danger_text="a hill wind came swirling down the stones",
        image_text="It tugged at aprons and sniffed greedily at the warm crust.",
        tags={"wind"},
    ),
    "birds": Obstacle(
        id="birds",
        label="birds",
        danger_text="three bold sparrows darted from a signpost",
        image_text="They hopped near the basket and peeped as if asking for a crumb.",
        tags={"birds"},
    ),
}

GEAR = {
    "waxed_cloth": Gear(
        id="waxed_cloth",
        label="waxed cloth",
        phrase="a waxed cloth printed with little wheat stars",
        use_text="wrapped the loaf snugly in the waxed cloth, so the weather could not sip at it",
        guards={"rain"},
        tags={"cover", "rain"},
    ),
    "lidded_basket": Gear(
        id="lidded_basket",
        label="lidded basket",
        phrase="a lidded willow basket",
        use_text="tucked the loaf into the lidded basket, where the wind could only grumble outside",
        guards={"wind"},
        tags={"basket", "wind"},
    ),
    "bell_ribbon": Gear(
        id="bell_ribbon",
        label="bell ribbon",
        phrase="a blue ribbon with one tiny bell",
        use_text="tied on the bell ribbon, and each bright chime sent the sparrows fluttering back to the signpost",
        guards={"birds"},
        tags={"bell", "birds"},
    ),
}

TRAITS = {
    "steadfast": Trait(
        id="steadfast",
        score=4,
        line="Steadfast hearts remember their promise even when the road smells delicious.",
        tags={"patience", "duty"},
    ),
    "tender": Trait(
        id="tender",
        score=3,
        line="Tender hearts think quickly of another person's empty stomach.",
        tags={"kindness"},
    ),
    "dreamy": Trait(
        id="dreamy",
        score=2,
        line="Dreamy hearts can drift close to trouble before they notice.",
        tags={"temptation"},
    ),
    "impulsive": Trait(
        id="impulsive",
        score=1,
        line="Impulsive feet and hungry noses do not always wait for wisdom.",
        tags={"temptation"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Nora", "Ava", "Ella", "Mina", "Rose", "Talia"]
BOY_NAMES = ["Tobin", "Milo", "Finn", "Eli", "Theo", "Ben", "Nico", "Rowan"]

KNOWLEDGE = {
    "potato": [
        (
            "What is a potato?",
            "A potato is a round or lumpy vegetable that grows in the ground. Bakers and cooks can mash it, roast it, or tuck it into warm bread."
        )
    ],
    "bakery": [
        (
            "What is a bakery?",
            "A bakery is a place where people mix dough and bake bread, buns, and pastries in hot ovens. It often smells warm and yeasty."
        )
    ],
    "rain": [
        (
            "Why would rain be a problem for bread?",
            "Rain can make bread wet and soggy. Wet crust stops feeling crisp and warm."
        )
    ],
    "wind": [
        (
            "How can wind bother someone carrying food?",
            "Strong wind can chill food and jostle a basket. It can also make it harder to hold things safely."
        )
    ],
    "birds": [
        (
            "Why might birds come near a loaf of bread?",
            "Birds notice crumbs and smells very quickly. If food is uncovered, curious birds may hop over to peck at it."
        )
    ],
    "honesty": [
        (
            "Why is honesty important after a mistake?",
            "Honesty helps other people know what really happened. Telling the truth is often the first step to fixing the problem."
        )
    ],
    "kindness": [
        (
            "What does kindness mean?",
            "Kindness means noticing what someone else needs and choosing to help. It can be small, warm actions that make another person feel cared for."
        )
    ],
    "patience": [
        (
            "What does patience help you do?",
            "Patience helps you wait instead of grabbing what you want right away. It gives wisdom enough time to catch up."
        )
    ],
    "basket": [
        (
            "Why use a basket with a lid?",
            "A lid helps keep food clean, warm, and protected while you carry it. It is like a little traveling shelter for the loaf."
        )
    ],
    "bell": [
        (
            "Why would a tiny bell scare birds away?",
            "A sudden chime tells birds that someone is moving near them. Many birds flutter back when they hear a bright sound."
        )
    ],
    "cover": [
        (
            "Why wrap bread in cloth?",
            "A cloth can keep bread warm and protect it from damp air or drops of rain. Wrapping also helps hold in the smell and steam."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "potato", "bakery", "rain", "wind", "birds", "honesty",
    "kindness", "patience", "basket", "bell", "cover",
]


def route_has_obstacle(recipient_id: str, obstacle_id: str) -> bool:
    return obstacle_id in RECIPIENTS[recipient_id].route


def gear_protects(gear_id: str, obstacle_id: str) -> bool:
    return obstacle_id in GEAR[gear_id].guards


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for rid in RECIPIENTS:
        for oid in OBSTACLES:
            for gid in GEAR:
                if route_has_obstacle(rid, oid) and gear_protects(gid, oid):
                    combos.append((rid, oid, gid))
    return combos


@dataclass
class StoryParams:
    recipient: str
    obstacle: str
    gear: str
    hero_name: str
    hero_gender: str
    baker_type: str
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


def outcome_of(params: StoryParams) -> str:
    if params.recipient not in RECIPIENTS or params.trait not in TRAITS:
        raise StoryError("(No story: unknown recipient or trait.)")
    total = RECIPIENTS[params.recipient].need_score + TRAITS[params.trait].score
    return "resist" if total >= RESIST_THRESHOLD else "confess"


def explain_combo(recipient_id: str, obstacle_id: str, gear_id: str) -> str:
    if not route_has_obstacle(recipient_id, obstacle_id):
        return (
            f"(No story: the road to {RECIPIENTS[recipient_id].place} does not bring "
            f"the obstacle '{obstacle_id}', so that detail would not honestly belong in the quest.)"
        )
    if not gear_protects(gear_id, obstacle_id):
        return (
            f"(No story: {GEAR[gear_id].label} does not solve the problem of {OBSTACLES[obstacle_id].label}. "
            f"Choose gear that really protects the loaf on that road.)"
        )
    return "(No story: that combination does not fit this world.)"


def setup_bakery(world: World, hero: Entity, baker: Entity, recipient_cfg: Recipient, trait: Trait) -> None:
    hero.memes["hunger"] = 3.0
    hero.memes["duty"] = 3.0
    hero.memes["temptation"] = 2.0
    world.say(
        f"In a flour-dusted bakery at the edge of the village, {hero.id} helped {baker.label} "
        f"wake the ovens before the sun had climbed the church roof."
    )
    world.say(
        f"All around them, sweet steam and warm crust drifted through the room, but one round "
        f"potato loaf waited apart on the wooden peel, shining softly as if the oven had left a little gold inside it."
    )
    world.say(trait.line)


def assign_quest(world: World, hero: Entity, baker: Entity, recipient_cfg: Recipient, gear_cfg: Gear) -> None:
    pastry = world.get("pastry")
    pastry.meters["warm"] = 1.0
    world.say(
        f'{baker.label.capitalize()} lifted the loaf and said, "This one is not for our shelf. '
        f'It is for {recipient_cfg.phrase}, who {recipient_cfg.need_text}. Will you carry it to {recipient_cfg.place}?"'
    )
    world.say(
        f"{hero.id} nodded. The quest felt small enough to fit in two hands and large enough to matter to the whole morning."
    )
    world.say(
        f"Before {hero.pronoun()} left, {baker.label} chose {gear_cfg.phrase} for the road."
    )


def inner_monologue(world: World, hero: Entity, recipient_cfg: Recipient) -> None:
    world.say(
        f'As {hero.id} held the warm loaf, {hero.pronoun()} thought, "It smells so good. '
        f'My own stomach is singing. But this bread is walking toward someone whose need is greater than mine."'
    )
    world.say(
        f'At the bakery door, another thought fluttered in: "No one would notice one tiny bite... would they?"'
    )


def nibble(world: World, hero: Entity) -> None:
    pastry = world.get("pastry")
    pastry.meters["bitten"] += 1
    pastry.meters["damaged"] += 1
    pastry.meters["crumbs"] += 1
    hero.memes["guilt"] += 1
    hero.memes["temptation"] = 0.0
    world.say(
        f"But hunger tugged faster than wisdom. {hero.id} broke off one little corner, and the smell that had been merry a moment ago turned heavy in {hero.pronoun('possessive')} chest."
    )
    world.say(
        f'"Oh dear," {hero.pronoun()} whispered inside {hero.pronoun('possessive')} own heart. "A quest loaf should arrive whole. Warm hands can mend dough, but not a hidden bite."'
    )


def confess_and_repair(world: World, hero: Entity, baker: Entity) -> None:
    pastry = world.get("pastry")
    spare = world.get("spare")
    hero.memes["honesty"] += 1
    world.say(
        f"{hero.id} turned right back to the bakery and set the bitten loaf on the table. "
        f'"I was hungry, and I took a bite," {hero.pronoun()} admitted. "I am sorry."'
    )
    world.say(
        f"{baker.label.capitalize()} did not shout. {baker.pronoun().capitalize()} laid one floury hand on the table and said, "
        f'"A hidden wrong grows heavier in a basket. A spoken wrong can be made lighter."'
    )
    spare.meters["used"] = 1.0
    pastry.meters["replaced"] = 1.0
    pastry.meters["bitten"] = 0.0
    pastry.meters["damaged"] = 0.0
    pastry.meters["crumbs"] = 0.0
    pastry.meters["warm"] = 1.0
    hero.memes["guilt"] = 0.0
    hero.memes["relief"] += 1
    world.say(
        f"From a basket under the bench, {baker.label} brought out another baked potato loaf that had been saved for the shopkeeper's lunch. "
        f'"We will share the nibbled one here," {baker.pronoun()} said, "and the whole loaf will go on the true errand."'
    )


def step_into_road(world: World, hero: Entity, obstacle_cfg: Obstacle, gear_cfg: Gear) -> None:
    road = world.get("road")
    gear = world.get("gear")
    road.meters["hazard"] = 1.0
    world.facts["obstacle_id"] = obstacle_cfg.id
    gear.attrs["guards"] = set(gear_cfg.guards)
    world.say(
        f"Out on the road, {obstacle_cfg.danger_text} {obstacle_cfg.image_text}"
    )
    world.say(
        f"{hero.id} remembered the baker's care and {gear_cfg.use_text}."
    )
    propagate(world, narrate=False)


def resist_line(world: World, hero: Entity) -> None:
    hero.memes["patience"] += 1
    hero.memes["kindness"] += 1
    world.say(
        f'Yet {hero.id} straightened {hero.pronoun("possessive")} shoulders and answered the whisper inside: '
        f'"No. A hungry thought is not the same as a hungry need."'
    )


def arrive_and_deliver(world: World, hero: Entity, recipient_cfg: Recipient) -> None:
    pastry = world.get("pastry")
    recipient = world.get("recipient")
    pastry.meters["delivered"] += 1
    recipient.memes["gratitude"] += 1
    propagate(world, narrate=False)
    whole = pastry.meters["bitten"] < THRESHOLD and pastry.meters["damaged"] < THRESHOLD
    if whole:
        world.say(
            f"When {hero.id} reached {recipient_cfg.place}, {hero.pronoun()} placed the loaf in {recipient.phrase} hands, still warm and whole."
        )
    else:
        world.say(
            f"When {hero.id} reached {recipient_cfg.place}, {hero.pronoun()} placed the loaf in {recipient.phrase} hands as carefully as {hero.pronoun()} could."
        )
    world.say(recipient_cfg.thanks_text)


def ending_resist(world: World, hero: Entity, baker: Entity, recipient_cfg: Recipient) -> None:
    world.say(
        f"On the walk back, the village seemed brighter than before. {hero.id} had carried more than bread; "
        f"{hero.pronoun()} had carried {hero.pronoun('possessive')} promise all the way to {recipient_cfg.place}."
    )
    world.say(
        f"By the time {hero.pronoun()} stepped into the bakery again, the ovens glowed like friendly suns, "
        f"and even the smell of fresh crust felt gentler, because {hero.pronoun()} had learned that patience can keep kindness warm."
    )


def ending_confess(world: World, hero: Entity, baker: Entity, recipient_cfg: Recipient) -> None:
    world.say(
        f"When {hero.id} returned, the bakery windows were bright with noon. The nibbled loaf had become the baker's and helper's simple meal, "
        f"and the whole loaf had found its true home."
    )
    world.say(
        f"{hero.id} never forgot that day: honesty had not erased the mistake, but it had shown the road back to goodness, "
        f"clear as flour on a dark wooden table."
    )


def tell(
    recipient_cfg: Recipient,
    obstacle_cfg: Obstacle,
    gear_cfg: Gear,
    hero_name: str,
    hero_gender: str,
    baker_type: str,
    trait_cfg: Trait,
) -> World:
    world = World()
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait_cfg.id],
    ))
    baker = world.add(Entity(
        id="Baker",
        kind="character",
        type=baker_type,
        label="the baker",
        phrase="the baker",
        role="baker",
    ))
    recipient = world.add(Entity(
        id="recipient",
        kind="character",
        type=recipient_cfg.type,
        label=recipient_cfg.label,
        phrase=recipient_cfg.phrase,
        role="recipient",
    ))
    world.add(Entity(
        id="pastry",
        type="loaf",
        label="potato loaf",
        phrase="the warm potato loaf",
        attrs={"kind": "potato loaf"},
    ))
    world.add(Entity(
        id="gear",
        type="gear",
        label=gear_cfg.label,
        phrase=gear_cfg.phrase,
        attrs={"guards": set()},
    ))
    world.add(Entity(
        id="road",
        type="road",
        label="road",
        phrase="the village road",
    ))
    world.add(Entity(
        id="spare",
        type="spare_loaf",
        label="spare loaf",
        phrase="a second potato loaf",
    ))

    world.facts["recipient_id"] = recipient_cfg.id
    world.facts["obstacle_id"] = obstacle_cfg.id
    world.facts["gear_id"] = gear_cfg.id
    world.facts["trait_id"] = trait_cfg.id

    setup_bakery(world, hero, baker, recipient_cfg, trait_cfg)
    world.para()
    assign_quest(world, hero, baker, recipient_cfg, gear_cfg)
    inner_monologue(world, hero, recipient_cfg)

    outcome = "resist" if (recipient_cfg.need_score + trait_cfg.score) >= RESIST_THRESHOLD else "confess"
    world.facts["outcome"] = outcome

    world.para()
    if outcome == "confess":
        nibble(world, hero)
        confess_and_repair(world, hero, baker)
    else:
        resist_line(world, hero)

    world.para()
    step_into_road(world, hero, obstacle_cfg, gear_cfg)
    arrive_and_deliver(world, hero, recipient_cfg)

    world.para()
    if outcome == "confess":
        ending_confess(world, hero, baker, recipient_cfg)
    else:
        ending_resist(world, hero, baker, recipient_cfg)

    pastry = world.get("pastry")
    world.facts.update(
        hero=hero,
        baker=baker,
        recipient=recipient,
        recipient_cfg=recipient_cfg,
        obstacle_cfg=obstacle_cfg,
        gear_cfg=gear_cfg,
        trait_cfg=trait_cfg,
        confessed=outcome == "confess",
        resisted=outcome == "resist",
        delivered=pastry.meters["delivered"] >= THRESHOLD,
        used_gear=True,
        whole=pastry.meters["bitten"] < THRESHOLD and pastry.meters["damaged"] < THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    recipient_cfg = f["recipient_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    outcome = f["outcome"]
    if outcome == "confess":
        return [
            f'Write a fairy-tale story set in a bakery about a child carrying a potato loaf on a quest to {recipient_cfg.place}. Include inner monologue, a mistake, and a gentle lesson about honesty.',
            f"Tell a child-friendly quest where {hero.id} is tempted by the smell of a warm potato loaf, admits a wrong choice, and still learns how goodness can be repaired.",
            f'Write a moral fairy tale with the word "potato" where a bakery errand meets {obstacle_cfg.label} on the road, and the ending teaches that honesty helps mend mistakes.',
        ]
    return [
        f'Write a fairy-tale story set in a bakery about a child carrying a warm potato loaf on a quest to {recipient_cfg.place}. Include inner monologue and a clear lesson about kindness and patience.',
        f"Tell a gentle quest where {hero.id} wants to taste the loaf but chooses to bring it whole to someone who needs it more.",
        f'Write a moral story with the word "potato" where a bakery errand faces {obstacle_cfg.label}, and the child proves goodness through patient self-control.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    baker = f["baker"]
    recipient_cfg = f["recipient_cfg"]
    obstacle_cfg = f["obstacle_cfg"]
    gear_cfg = f["gear_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young bakery helper, and {baker.label}, who trusted {hero.pronoun('object')} with a warm potato loaf. The quest was to carry it to {recipient_cfg.phrase}."
        ),
        (
            "What was the quest?",
            f"{hero.id}'s quest was to bring the warm potato loaf from the bakery to {recipient_cfg.place}. The loaf mattered because {recipient_cfg.phrase} {recipient_cfg.need_text}."
        ),
        (
            f"Why was {hero.id} tempted?",
            f"{hero.id} was tempted because the loaf smelled warm and delicious, and {hero.pronoun()} was hungry too. The story makes the struggle clear by letting us hear {hero.pronoun('possessive')} thoughts before the choice."
        ),
        (
            f"How did {gear_cfg.label} help on the road?",
            f"It protected the loaf from {obstacle_cfg.label}. That mattered because the road brought a real problem, and the baker chose gear that honestly fit that danger."
        ),
    ]
    if outcome == "resist":
        qa.append((
            f"What choice did {hero.id} make in the middle of the story?",
            f"{hero.id} chose not to nibble the loaf, even though {hero.pronoun()} wanted to. {hero.pronoun().capitalize()} remembered that someone else needed it more, so patience helped kindness win."
        ))
        qa.append((
            "What is the moral of this version of the story?",
            "The moral is that kindness sometimes means giving up a small comfort so someone else can be cared for. Patience kept the promise warm all the way to the end."
        ))
    else:
        qa.append((
            f"What mistake did {hero.id} make, and what happened next?",
            f"{hero.id} took a bite from the loaf because hunger pulled harder than wisdom for a moment. Then {hero.pronoun()} felt guilty, went back, and told the truth so the baker could set the quest right."
        ))
        qa.append((
            "What is the moral of this version of the story?",
            "The moral is that a mistake should not be hidden. Honesty opened the way to repair the problem, so the loaf still reached the person who needed it."
        ))
    qa.append((
        "How did the ending show that something had changed?",
        f"The ending shows change because the loaf reached its true home and the child came back wiser than before. The bakery felt different afterward: not just warm with ovens, but warm with a learned lesson."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    outcome = f["outcome"]
    tags = {"potato", "bakery"} | set(f["obstacle_cfg"].tags) | set(f["gear_cfg"].tags)
    if outcome == "confess":
        tags.add("honesty")
    else:
        tags |= {"kindness", "patience"}
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
            shown = {}
            for k, v in ent.attrs.items():
                if isinstance(v, set):
                    if v:
                        shown[k] = sorted(v)
                elif v:
                    shown[k] = v
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:9} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        recipient="watchman",
        obstacle="wind",
        gear="lidded_basket",
        hero_name="Mira",
        hero_gender="girl",
        baker_type="father",
        trait="steadfast",
    ),
    StoryParams(
        recipient="seamstress",
        obstacle="rain",
        gear="waxed_cloth",
        hero_name="Tobin",
        hero_gender="boy",
        baker_type="mother",
        trait="tender",
    ),
    StoryParams(
        recipient="gardener",
        obstacle="birds",
        gear="bell_ribbon",
        hero_name="Nora",
        hero_gender="girl",
        baker_type="father",
        trait="impulsive",
    ),
    StoryParams(
        recipient="gardener",
        obstacle="birds",
        gear="bell_ribbon",
        hero_name="Finn",
        hero_gender="boy",
        baker_type="mother",
        trait="dreamy",
    ),
]


ASP_RULES = r"""
valid(R,O,G) :- recipient(R), obstacle(O), gear(G), route_has(R,O), guards(G,O).

resist_score(TS + NS) :- chosen_trait(T), trait_score(T,TS),
                         chosen_recipient(R), need_score(R,NS).
resist :- resist_score(S), resist_threshold(M), S >= M.

outcome(resist) :- resist.
outcome(confess) :- not resist.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for rid, r in RECIPIENTS.items():
        lines.append(asp.fact("recipient", rid))
        lines.append(asp.fact("need_score", rid, r.need_score))
        for oid in sorted(r.route):
            lines.append(asp.fact("route_has", rid, oid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for oid in sorted(g.guards):
            lines.append(asp.fact("guards", gid, oid))
    for tid, t in TRAITS.items():
        lines.append(asp.fact("trait", tid))
        lines.append(asp.fact("trait_score", tid, t.score))
    lines.append(asp.fact("resist_threshold", RESIST_THRESHOLD))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_recipient", params.recipient),
        asp.fact("chosen_trait", params.trait),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for p in cases:
        py = outcome_of(p)
        asp_out = asp_outcome(p)
        if py != asp_out:
            bad += 1
            print(f"MISMATCH outcome for {p}: python={py} asp={asp_out}")
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1

    try:
        smoke_params = resolve_params(parser.parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story or not sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale bakery quest: a warm potato loaf, an inner struggle, and a moral lesson."
    )
    ap.add_argument("--recipient", choices=RECIPIENTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--baker", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str) -> str:
    if gender == "girl":
        return rng.choice(GIRL_NAMES)
    return rng.choice(BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.recipient and args.obstacle and args.gear:
        if not (route_has_obstacle(args.recipient, args.obstacle) and gear_protects(args.gear, args.obstacle)):
            raise StoryError(explain_combo(args.recipient, args.obstacle, args.gear))
    if args.recipient and args.obstacle and not route_has_obstacle(args.recipient, args.obstacle):
        any_gear = args.gear or next(iter(GEAR))
        raise StoryError(explain_combo(args.recipient, args.obstacle, any_gear))
    if args.obstacle and args.gear and not gear_protects(args.gear, args.obstacle):
        some_recipient = args.recipient or next(iter(RECIPIENTS))
        raise StoryError(explain_combo(some_recipient, args.obstacle, args.gear))

    combos = [
        c for c in valid_combos()
        if (args.recipient is None or c[0] == args.recipient)
        and (args.obstacle is None or c[1] == args.obstacle)
        and (args.gear is None or c[2] == args.gear)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    recipient_id, obstacle_id, gear_id = rng.choice(sorted(combos))
    trait_id = args.trait or rng.choice(sorted(TRAITS))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or _pick_name(rng, hero_gender)
    baker_type = args.baker or rng.choice(["mother", "father"])
    return StoryParams(
        recipient=recipient_id,
        obstacle=obstacle_id,
        gear=gear_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        baker_type=baker_type,
        trait=trait_id,
    )


def generate(params: StoryParams) -> StorySample:
    if params.recipient not in RECIPIENTS:
        raise StoryError(f"(No story: unknown recipient '{params.recipient}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(No story: unknown obstacle '{params.obstacle}'.)")
    if params.gear not in GEAR:
        raise StoryError(f"(No story: unknown gear '{params.gear}'.)")
    if params.trait not in TRAITS:
        raise StoryError(f"(No story: unknown trait '{params.trait}'.)")
    if params.hero_gender not in {"girl", "boy"}:
        raise StoryError(f"(No story: unknown hero gender '{params.hero_gender}'.)")
    if params.baker_type not in {"mother", "father"}:
        raise StoryError(f"(No story: unknown baker type '{params.baker_type}'.)")
    if not (route_has_obstacle(params.recipient, params.obstacle) and gear_protects(params.gear, params.obstacle)):
        raise StoryError(explain_combo(params.recipient, params.obstacle, params.gear))

    world = tell(
        recipient_cfg=RECIPIENTS[params.recipient],
        obstacle_cfg=OBSTACLES[params.obstacle],
        gear_cfg=GEAR[params.gear],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        baker_type=params.baker_type,
        trait_cfg=TRAITS[params.trait],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (recipient, obstacle, gear) combos:\n")
        for recipient_id, obstacle_id, gear_id in combos:
            print(f"  {recipient_id:10} {obstacle_id:7} {gear_id}")
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
            header = (
                f"### {p.hero_name}: {p.recipient} by way of {p.obstacle} "
                f"with {p.gear} ({outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
