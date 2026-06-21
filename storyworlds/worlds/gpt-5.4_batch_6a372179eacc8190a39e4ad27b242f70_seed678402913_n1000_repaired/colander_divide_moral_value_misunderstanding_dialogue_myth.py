#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py
=========================================================================================

A standalone storyworld for a tiny mythic domain:

A child is told to take a colander to a sacred spring, wash an offering, and
divide it fairly between two bowls. Because the instruction is half-heard or
misunderstood, the child briefly thinks the *water* should be divided with the
colander instead. Dialogue and honesty restore the task, and the ending image
shows fairness made visible.

The world model tracks small physical meters (water carried, water lost, offering
split, bowls filled) and emotional memes (confusion, shame, trust, relief,
reverence). The story text is rendered from that simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --offering star_beans
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --misunderstanding divide_water
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --all
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --qa --json
    python storyworlds/worlds/gpt-5.4/colander_divide_moral_value_misunderstanding_dialogue_myth.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or this nested model directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
        female = {"girl", "mother", "woman", "goddess"}
        male = {"boy", "father", "man", "god"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.label or self.type)


@dataclass
class ShrineSetting:
    id: str
    place: str
    people: str
    image: str
    pair_name: str
    left_bowl: str
    right_bowl: str
    final_sign: str


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    washed_in_colander: bool = True
    divisible: bool = True
    count_word: str = "handfuls"
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    label: str
    object_word: str
    mistake_text: str
    severity: int
    needs_water_task: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    label: str
    asks_before_acting: bool
    confesses_after_acting: bool
    dialogue_with: str
    tags: set[str] = field(default_factory=set)


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


def _r_leak(world: World) -> list[str]:
    child = world.entities.get("child")
    colander = world.entities.get("colander")
    if child is None or colander is None:
        return []
    if colander.meters["filled_with_water"] < THRESHOLD:
        return []
    sig = ("leak",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    lost = max(1.0, colander.meters["filled_with_water"])
    colander.meters["held_water"] = 0.0
    colander.meters["water_lost"] += lost
    child.memes["alarm"] += 1
    world.get("spring").meters["spilled_threads"] += 1
    return ["__water_leaked__"]


def _r_fair_split(world: World) -> list[str]:
    left = world.entities.get("left_bowl")
    right = world.entities.get("right_bowl")
    child = world.entities.get("child")
    if left is None or right is None or child is None:
        return []
    if left.meters["portion"] < THRESHOLD or right.meters["portion"] < THRESHOLD:
        return []
    if abs(left.meters["portion"] - right.meters["portion"]) > 0.01:
        return []
    sig = ("fair_split",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.get("shrines").meters["harmony"] += 1
    child.memes["reverence"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="leak", tag="physical", apply=_r_leak),
    Rule(name="fair_split", tag="moral", apply=_r_fair_split),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


SETTINGS = {
    "twin_shrines": ShrineSetting(
        id="twin_shrines",
        place="the stone steps between the twin shrines of Dawn and Rain",
        people="the hill village",
        image="above the terraces where mist slept in the fields",
        pair_name="Dawn and Rain",
        left_bowl="the sun bowl",
        right_bowl="the rain bowl",
        final_sign="both shrine lamps rose with one steady flame",
    ),
    "river_gate": ShrineSetting(
        id="river_gate",
        place="the archway of the river gate, where two altar bowls faced the east",
        people="the reed village",
        image="beside the shining reeds and the first cranes",
        pair_name="River and Reed",
        left_bowl="the river bowl",
        right_bowl="the reed bowl",
        final_sign="the bells over the gate rang together in the same small wind",
    ),
    "orchard_peak": ShrineSetting(
        id="orchard_peak",
        place="the orchard peak, where two old offering stones watched the valley",
        people="the orchard folk",
        image="under the last stars and the first peach-colored cloud",
        pair_name="Sun and Seed",
        left_bowl="the sun stone",
        right_bowl="the seed stone",
        final_sign="two white doves settled side by side on the warm rock",
    ),
}

OFFERINGS = {
    "star_beans": Offering(
        id="star_beans",
        label="star beans",
        phrase="a basket of pale star beans",
        washed_in_colander=True,
        divisible=True,
        count_word="small handfuls",
        tags={"beans", "food", "sharing"},
    ),
    "moon_berries": Offering(
        id="moon_berries",
        label="moon berries",
        phrase="a basket of silver-blue moon berries",
        washed_in_colander=True,
        divisible=True,
        count_word="clusters",
        tags={"berries", "food", "sharing"},
    ),
    "rice_pearls": Offering(
        id="rice_pearls",
        label="rice pearls",
        phrase="a bowl of rice pearls",
        washed_in_colander=True,
        divisible=True,
        count_word="pinches",
        tags={"rice", "food", "sharing"},
    ),
}

MISUNDERSTANDINGS = {
    "divide_water": Misunderstanding(
        id="divide_water",
        label="divide the spring water",
        object_word="water",
        mistake_text="thought the elder meant the spring water should be divided with the colander",
        severity=2,
        needs_water_task=True,
        tags={"misunderstanding", "water", "colander"},
    ),
    "divide_before_washing": Misunderstanding(
        id="divide_before_washing",
        label="divide the offering before washing it",
        object_word="offering",
        mistake_text="thought the offering should be divided first and washed later",
        severity=1,
        needs_water_task=True,
        tags={"misunderstanding", "offering", "order"},
    ),
}

RESOLUTIONS = {
    "ask_friend": Resolution(
        id="ask_friend",
        label="ask the companion before acting",
        asks_before_acting=True,
        confesses_after_acting=False,
        dialogue_with="companion",
        tags={"dialogue", "friendship", "care"},
    ),
    "ask_elder": Resolution(
        id="ask_elder",
        label="ask the elder before acting",
        asks_before_acting=True,
        confesses_after_acting=False,
        dialogue_with="elder",
        tags={"dialogue", "wisdom", "care"},
    ),
    "confess_after": Resolution(
        id="confess_after",
        label="make the mistake, then confess it",
        asks_before_acting=False,
        confesses_after_acting=True,
        dialogue_with="elder",
        tags={"dialogue", "honesty", "repair"},
    ),
}

GIRL_NAMES = ["Nara", "Lina", "Sora", "Mira", "Tali", "Asha", "Ira", "Nila"]
BOY_NAMES = ["Tarin", "Kavi", "Oren", "Milo", "Sami", "Ilan", "Ravi", "Beren"]
TRAITS = ["careful", "eager", "quiet", "kind", "thoughtful", "quick-footed"]


@dataclass
class StoryParams:
    setting: str
    offering: str
    misunderstanding: str
    resolution: str
    child_name: str
    child_gender: str
    companion_name: str
    companion_gender: str
    elder_type: str
    child_trait: str
    companion_trait: str
    seed: Optional[int] = None


def misunderstanding_fits(offering: Offering, misunderstanding: Misunderstanding) -> bool:
    if misunderstanding.needs_water_task and not offering.washed_in_colander:
        return False
    if not offering.divisible and misunderstanding.id == "divide_before_washing":
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for setting_id in SETTINGS:
        for offering_id, offering in OFFERINGS.items():
            for mis_id, mis in MISUNDERSTANDINGS.items():
                if not misunderstanding_fits(offering, mis):
                    continue
                for resolution_id in RESOLUTIONS:
                    combos.append((setting_id, offering_id, mis_id, resolution_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    resolution = RESOLUTIONS[params.resolution]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    if resolution.asks_before_acting:
        return "clarified"
    if misunderstanding.severity >= 2:
        return "mended_after_loss"
    return "mended_quickly"


def explain_rejection(offering: Offering, misunderstanding: Misunderstanding) -> str:
    return (
        f"(No story: {offering.label} would not make sense with the misunderstanding "
        f"'{misunderstanding.label}'. The task must be something a child could honestly "
        f"mishear around washing in a colander and dividing fairly.)"
    )


def introduce(world: World, child: Entity, companion: Entity, elder: Entity, setting: ShrineSetting) -> None:
    world.say(
        f"In the age when springs were said to listen, {setting.people} climbed at dawn to "
        f"{setting.place}, {setting.image}."
    )
    world.say(
        f"That morning, {child.id}, a {child.traits[0]} {child.type}, walked beside "
        f"{companion.id}, while the village {elder.label_word} carried the old brass colander."
    )


def assign_task(world: World, child: Entity, companion: Entity, elder: Entity,
                setting: ShrineSetting, offering: Offering) -> None:
    child.memes["duty"] += 1
    companion.memes["duty"] += 1
    world.say(
        f'The {elder.label_word} set down {offering.phrase} and said, '
        f'"Take this to the spring. Wash the {offering.label} in the colander, '
        f'then divide them equally between {setting.left_bowl} and {setting.right_bowl}. '
        f'When the gifts are shared fairly, {setting.pair_name} bless the fields."'
    )
    world.facts["instruction"] = "wash offering in colander, then divide equally between two bowls"


def stir_confusion(world: World, child: Entity, misunderstanding: Misunderstanding) -> None:
    child.memes["confusion"] += 1
    world.say(
        f"{child.id} heard the holy task, but in the bright sound of the spring {child.pronoun()} "
        f"{misunderstanding.mistake_text}."
    )


def companion_glance(world: World, child: Entity, companion: Entity) -> None:
    companion.memes["care"] += 1
    world.say(
        f"{companion.id} watched {child.id}'s face and saw that {child.pronoun()} was thinking hard."
    )


def ask_before(world: World, child: Entity, companion: Entity, elder: Entity,
               misunderstanding: Misunderstanding, resolution: Resolution) -> None:
    child.memes["honesty"] += 1
    if resolution.id == "ask_friend":
        world.say(
            f'"{companion.id}," {child.id} whispered, "when the {elder.label_word} said '
            f'\'divide them,\' did {child.pronoun()} mean the {misunderstanding.object_word}?"'
        )
        world.say(
            f'"No," said {companion.id}. "The colander lets water pass away. It is for washing, '
            f'not for carrying water. Let us ask again before our hands become foolish."'
        )
        world.say(
            f'Together they turned back. The {elder.label_word} smiled and said, '
            f'"A question asked in time is brighter than a mistake hidden in silence."'
        )
    else:
        world.say(
            f'{child.id} bowed and said, "Village {elder.label_word}, I fear I do not understand. '
            f'Do I divide the {misunderstanding.object_word}, or the {list(OFFERINGS.values())[0].label if False else "offering"}?"'
        )
        world.say(
            f'The {elder.label_word} touched the rim of the colander. '
            f'"You divide the offering," {elder.pronoun()} said. "Water belongs to the spring. '
            f'The holes in this bowl teach us that some things are for cleansing, not for keeping."'
        )
    child.memes["relief"] += 1
    companion.memes["relief"] += 1


def do_mistake(world: World, child: Entity, companion: Entity, elder: Entity,
               misunderstanding: Misunderstanding) -> None:
    child.memes["confusion"] += 1
    if misunderstanding.id == "divide_water":
        colander = world.get("colander")
        colander.meters["filled_with_water"] += 1
        colander.meters["held_water"] += 1
        world.say(
            f"Wanting to obey quickly, {child.id} dipped the colander into the spring and tried to carry "
            f"the shining water toward the bowls so it could be divide'd in two."
        )
        propagate(world, narrate=False)
        world.say(
            f"But the water slipped through the bright little holes in silver threads and fell back to the stones."
        )
        world.say(
            f'"{companion.id}!" cried {child.id}. "The spring is escaping my hands."'
        )
    else:
        world.say(
            f"Wanting to obey quickly, {child.id} set the dry {world.facts['offering'].label} into two uneven piles "
            f"before going to the spring at all."
        )
        world.get("left_bowl").meters["portion"] += 2
        world.get("right_bowl").meters["portion"] += 1
        world.say(
            f"{companion.id} looked from one pile to the other and saw that the gifts already leaned to one side."
        )
    child.memes["shame"] += 1
    companion.memes["alarm"] += 1


def confess_and_repair(world: World, child: Entity, companion: Entity, elder: Entity,
                       misunderstanding: Misunderstanding, setting: ShrineSetting,
                       offering: Offering) -> None:
    child.memes["honesty"] += 1
    world.say(
        f"{child.id}'s cheeks grew warm. Still, {child.pronoun()} did not hide the trouble."
    )
    if misunderstanding.id == "divide_water":
        world.say(
            f'"Village {elder.label_word}," {child.id} said, "I thought I must divide the water, '
            f'but the colander would not hold it. I was ashamed, so I nearly kept quiet."'
        )
        world.say(
            f'The {elder.label_word} answered, "Then you have already chosen the better road, because you spoke. '
            f'The spring lost no honor, and neither have you."'
        )
    else:
        world.say(
            f'"Village {elder.label_word}," {child.id} said, "I divided the {offering.label} before washing them, '
            f'and I made the shares uneven."'
        )
        world.say(
            f'"Then we will begin again," said the {elder.label_word}. "A true tongue can mend a crooked start."'
        )
    child.memes["relief"] += 1
    companion.memes["trust"] += 1
    world.say(
        f"{companion.id} knelt beside {child.id} at the spring, ready to help set the task right."
    )


def wash_and_divide(world: World, child: Entity, companion: Entity,
                    setting: ShrineSetting, offering: Offering) -> None:
    offering_ent = world.get("offering")
    offering_ent.meters["washed"] += 1
    offering_ent.meters["divided"] += 1
    world.get("left_bowl").meters["portion"] = 1.0
    world.get("right_bowl").meters["portion"] = 1.0
    world.get("spring").meters["blessing_taken"] += 1
    child.memes["fairness"] += 1
    companion.memes["fairness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They rinsed the {offering.label} in the colander until the water ran clear."
    )
    world.say(
        f"Then {child.id} and {companion.id} counted by {offering.count_word}, one for "
        f"{setting.left_bowl}, one for {setting.right_bowl}, until each gift matched the other."
    )


def elder_lesson(world: World, child: Entity, elder: Entity, resolution: Resolution) -> None:
    child.memes["lesson"] += 1
    if resolution.asks_before_acting:
        world.say(
            f'The {elder.label_word} raised a hand over the bowls and said, '
            f'"Fair hands begin with clear words. When you do not understand, ask."'
        )
    else:
        world.say(
            f'The {elder.label_word} raised a hand over the bowls and said, '
            f'"Fair hands also need a truthful mouth. When you err, speak, and the path can be made straight again."'
        )


def close_story(world: World, child: Entity, companion: Entity,
                setting: ShrineSetting, outcome: str) -> None:
    world.say(
        f"When the gifts were laid down, {setting.final_sign}."
    )
    if outcome == "clarified":
        world.say(
            f"{child.id} remembered that morning all {child.pronoun('possessive')} life: wisdom does not shrink when it asks a question."
        )
    elif outcome == "mended_after_loss":
        world.say(
            f"{child.id} remembered that morning all {child.pronoun('possessive')} life: an honest word can gather even a leaking moment back into grace."
        )
    else:
        world.say(
            f"{child.id} remembered that morning all {child.pronoun('possessive')} life: a crooked beginning need not rule the ending when truth is spoken."
        )


def tell(setting: ShrineSetting, offering: Offering, misunderstanding: Misunderstanding,
         resolution: Resolution, child_name: str, child_gender: str, companion_name: str,
         companion_gender: str, elder_type: str, child_trait: str, companion_trait: str) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[child_trait],
    ))
    companion = world.add(Entity(
        id=companion_name,
        kind="character",
        type=companion_gender,
        label=companion_name,
        role="companion",
        traits=[companion_trait],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="elder",
        role="elder",
    ))
    world.add(Entity(id="spring", type="spring", label="spring"))
    world.add(Entity(id="shrines", type="shrines", label="shrines"))
    world.add(Entity(id="colander", type="colander", label="colander", phrase="the old brass colander"))
    world.add(Entity(id="offering", type="offering", label=offering.label, phrase=offering.phrase, tags=set(offering.tags)))
    world.add(Entity(id="left_bowl", type="bowl", label=setting.left_bowl))
    world.add(Entity(id="right_bowl", type="bowl", label=setting.right_bowl))

    introduce(world, child, companion, elder, setting)
    assign_task(world, child, companion, elder, setting, offering)

    world.para()
    stir_confusion(world, child, misunderstanding)
    companion_glance(world, child, companion)

    if resolution.asks_before_acting:
        ask_before(world, child, companion, elder, misunderstanding, resolution)
        world.para()
        wash_and_divide(world, child, companion, setting, offering)
    else:
        do_mistake(world, child, companion, elder, misunderstanding)
        world.para()
        confess_and_repair(world, child, companion, elder, misunderstanding, setting, offering)
        wash_and_divide(world, child, companion, setting, offering)

    world.para()
    elder_lesson(world, child, elder, resolution)
    close_story(world, child, companion, setting, outcome_of(StoryParams(
        setting=setting.id,
        offering=offering.id,
        misunderstanding=misunderstanding.id,
        resolution=resolution.id,
        child_name=child_name,
        child_gender=child_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        companion_trait=companion_trait,
        seed=None,
    )))

    world.facts.update(
        setting=setting,
        offering_cfg=offering,
        misunderstanding=misunderstanding,
        resolution=resolution,
        child=child,
        companion=companion,
        elder=elder,
        outcome=outcome_of(StoryParams(
            setting=setting.id,
            offering=offering.id,
            misunderstanding=misunderstanding.id,
            resolution=resolution.id,
            child_name=child_name,
            child_gender=child_gender,
            companion_name=companion_name,
            companion_gender=companion_gender,
            elder_type=elder_type,
            child_trait=child_trait,
            companion_trait=companion_trait,
            seed=None,
        )),
        water_lost=world.get("colander").meters["water_lost"],
        harmony=world.get("shrines").meters["harmony"],
        fair_split=world.get("shrines").meters["harmony"] >= THRESHOLD,
        instruction=world.facts.get("instruction", ""),
        asked_first=resolution.asks_before_acting,
        confessed=resolution.confesses_after_acting,
    )
    return world


CURATED = [
    StoryParams(
        setting="twin_shrines",
        offering="star_beans",
        misunderstanding="divide_water",
        resolution="ask_friend",
        child_name="Nara",
        child_gender="girl",
        companion_name="Kavi",
        companion_gender="boy",
        elder_type="mother",
        child_trait="eager",
        companion_trait="thoughtful",
    ),
    StoryParams(
        setting="river_gate",
        offering="moon_berries",
        misunderstanding="divide_before_washing",
        resolution="ask_elder",
        child_name="Oren",
        child_gender="boy",
        companion_name="Mira",
        companion_gender="girl",
        elder_type="father",
        child_trait="quiet",
        companion_trait="kind",
    ),
    StoryParams(
        setting="orchard_peak",
        offering="rice_pearls",
        misunderstanding="divide_water",
        resolution="confess_after",
        child_name="Lina",
        child_gender="girl",
        companion_name="Tarin",
        companion_gender="boy",
        elder_type="mother",
        child_trait="careful",
        companion_trait="quick-footed",
    ),
]


KNOWLEDGE = {
    "colander": [
        (
            "What is a colander?",
            "A colander is a bowl with many holes in it. Water can run out through the holes, so people use it to wash and drain food."
        )
    ],
    "divide": [
        (
            "What does divide mean?",
            "To divide means to split something into parts. When people divide fairly, each side gets an equal share."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone hears or understands something the wrong way. Talking clearly can fix it."
        )
    ],
    "dialogue": [
        (
            "Why can dialogue help solve a problem?",
            "Dialogue means people talk and listen to each other. It helps them compare ideas, clear confusion, and choose a wiser action."
        )
    ],
    "honesty": [
        (
            "Why is it good to admit a mistake?",
            "Admitting a mistake helps other people understand what went wrong. Then the problem can be repaired instead of hidden."
        )
    ],
    "fairness": [
        (
            "Why is sharing fairly important?",
            "Sharing fairly helps everyone feel respected. Equal sharing can keep peace in a family, a village, or a game."
        )
    ],
}

KNOWLEDGE_ORDER = ["colander", "divide", "misunderstanding", "dialogue", "honesty", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    setting = f["setting"]
    offering = f["offering_cfg"]
    misunderstanding = f["misunderstanding"]
    outcome = f["outcome"]
    if outcome == "clarified":
        return [
            'Write a myth-like story for a 3-to-5-year-old that includes the words "colander" and "divide".',
            f"Tell a gentle myth in which {child.id} is given a sacred job at {setting.place}, misunderstands it, and asks a question before making a mistake.",
            f'Write a short moral tale about fairness and dialogue where a child thinks the wrong thing should be divide\'d, but clear words save the day.',
        ]
    return [
        'Write a myth-like story for a 3-to-5-year-old that includes the words "colander" and "divide".',
        f"Tell a moral myth in which {child.id} misunderstands how to use a colander while preparing {offering.label}, then speaks honestly and helps repair the task.",
        f"Write a short story with dialogue, a misunderstanding, and a lesson that honesty and fairness can mend a mistake.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    companion = f["companion"]
    elder = f["elder"]
    setting = f["setting"]
    offering = f["offering_cfg"]
    misunderstanding = f["misunderstanding"]
    outcome = f["outcome"]
    elder_word = elder.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {companion.id}, and the village {elder_word}. They are carrying an offering to {setting.place}."
        ),
        (
            "What job did the elder give the children?",
            f"The elder told them to wash the {offering.label} in a colander and divide them equally between two bowls. The fairness of the gift mattered as much as the gift itself."
        ),
        (
            f"What did {child.id} misunderstand?",
            f"{child.id} misunderstood the instruction and {misunderstanding.mistake_text}. The trouble came from hearing the task only partly instead of checking the meaning."
        ),
    ]

    if outcome == "clarified":
        qa.append(
            (
                f"How was the misunderstanding solved?",
                f"It was solved through dialogue before any harm was done. {child.id} asked for help, and the answer made the use of the colander clear."
            )
        )
    elif outcome == "mended_after_loss":
        qa.append(
            (
                f"What happened when {child.id} tried the wrong idea?",
                f"{child.id} tried to carry water in the colander, and it leaked out through the holes. Then {child.pronoun().capitalize()} admitted the mistake instead of hiding it, so the elder and {companion.id} could help set the task right."
            )
        )
    else:
        qa.append(
            (
                f"How did {child.id} repair the mistake?",
                f"{child.id} confessed the confusion and began the task again in the right order. Speaking truthfully turned an uneven beginning into a fair ending."
            )
        )

    qa.append(
        (
            "What is the lesson of the story?",
            f"The lesson is that fairness needs clear words, and honesty can mend confusion. Asking or admitting the truth helped the children share the offering rightly."
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"colander", "divide", "misunderstanding", "dialogue", "fairness"}
    if world.facts.get("confessed") or world.facts.get("outcome") != "clarified":
        tags.add("honesty")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
fits(O, M) :- offering(O), misunderstanding(M), washed_in_colander(O), needs_water_task(M).
valid(S, O, M, R) :- setting(S), offering(O), misunderstanding(M), resolution(R), fits(O, M).

outcome(clarified) :- chosen_resolution(R), asks_before(R).
outcome(mended_after_loss) :- chosen_resolution(R), not asks_before(R),
                              chosen_misunderstanding(M), severity(M, V), V >= 2.
outcome(mended_quickly) :- chosen_resolution(R), not asks_before(R),
                           chosen_misunderstanding(M), severity(M, V), V < 2.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for offering_id, offering in OFFERINGS.items():
        lines.append(asp.fact("offering", offering_id))
        if offering.washed_in_colander:
            lines.append(asp.fact("washed_in_colander", offering_id))
        if offering.divisible:
            lines.append(asp.fact("divisible", offering_id))
    for mis_id, mis in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mis_id))
        lines.append(asp.fact("severity", mis_id, mis.severity))
        if mis.needs_water_task:
            lines.append(asp.fact("needs_water_task", mis_id))
    for res_id, res in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", res_id))
        if res.asks_before_acting:
            lines.append(asp.fact("asks_before", res_id))
        if res.confesses_after_acting:
            lines.append(asp.fact("confesses_after", res_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_resolution", params.resolution),
        asp.fact("chosen_misunderstanding", params.misunderstanding),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
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
        print("MISMATCH in valid combos:")
        if asp_set - py_set:
            print("  only in clingo:", sorted(asp_set - py_set))
        if py_set - asp_set:
            print("  only in python:", sorted(py_set - asp_set))

    cases = list(CURATED)
    for seed in range(20):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"ERROR: resolve_params failed during verify for seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError("missing QA or prompts")
        print("OK: smoke test generated a normal story sample.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: a colander, a divided offering, a misunderstanding, and a moral lesson."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--offering", choices=OFFERINGS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--resolution", choices=RESOLUTIONS)
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.offering and args.misunderstanding:
        offering = OFFERINGS[args.offering]
        misunderstanding = MISUNDERSTANDINGS[args.misunderstanding]
        if not misunderstanding_fits(offering, misunderstanding):
            raise StoryError(explain_rejection(offering, misunderstanding))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.offering is None or combo[1] == args.offering)
        and (args.misunderstanding is None or combo[2] == args.misunderstanding)
        and (args.resolution is None or combo[3] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, offering_id, misunderstanding_id, resolution_id = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    companion_gender = rng.choice(["girl", "boy"])
    child_name = _pick_name(rng, child_gender)
    companion_name = _pick_name(rng, companion_gender, avoid=child_name)
    elder_type = args.elder or rng.choice(["mother", "father"])
    child_trait = rng.choice(TRAITS)
    companion_trait = rng.choice([t for t in TRAITS if t != child_trait] or TRAITS)

    return StoryParams(
        setting=setting_id,
        offering=offering_id,
        misunderstanding=misunderstanding_id,
        resolution=resolution_id,
        child_name=child_name,
        child_gender=child_gender,
        companion_name=companion_name,
        companion_gender=companion_gender,
        elder_type=elder_type,
        child_trait=child_trait,
        companion_trait=companion_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.offering not in OFFERINGS:
        raise StoryError(f"(Unknown offering: {params.offering})")
    if params.misunderstanding not in MISUNDERSTANDINGS:
        raise StoryError(f"(Unknown misunderstanding: {params.misunderstanding})")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"(Unknown resolution: {params.resolution})")

    offering = OFFERINGS[params.offering]
    misunderstanding = MISUNDERSTANDINGS[params.misunderstanding]
    if not misunderstanding_fits(offering, misunderstanding):
        raise StoryError(explain_rejection(offering, misunderstanding))

    world = tell(
        setting=SETTINGS[params.setting],
        offering=offering,
        misunderstanding=misunderstanding,
        resolution=RESOLUTIONS[params.resolution],
        child_name=params.child_name,
        child_gender=params.child_gender,
        companion_name=params.companion_name,
        companion_gender=params.companion_gender,
        elder_type=params.elder_type,
        child_trait=params.child_trait,
        companion_trait=params.companion_trait,
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
        print(f"{len(combos)} compatible (setting, offering, misunderstanding, resolution) combos:\n")
        for setting_id, offering_id, misunderstanding_id, resolution_id in combos:
            print(f"  {setting_id:12} {offering_id:12} {misunderstanding_id:22} {resolution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### {p.child_name} and {p.companion_name}: "
                f"{p.offering}, {p.misunderstanding}, {p.resolution}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
