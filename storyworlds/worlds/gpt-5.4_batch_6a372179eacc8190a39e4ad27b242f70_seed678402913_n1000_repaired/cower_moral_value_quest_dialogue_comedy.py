#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py
=====================================================================

A standalone storyworld about a child on a funny little quest to return an item,
tell the truth, and get past a silly obstacle without pretending to be fearless.

The core moral is small but sturdy: bravery is not the same as never feeling
scared. In this world, the child may cower for a moment, but the story turns
when the child tells the truth and asks for help.

Run it
------
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py --all --qa
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py --trace
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py --json
    python storyworlds/worlds/gpt-5.4/cower_moral_value_quest_dialogue_comedy.py --verify
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
# from the nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 2.0


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
        female = {"girl", "mother", "woman", "lady"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    festival: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    owner_role: str
    owner_place: str
    found_at: str
    reason: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Obstacle:
    id: str
    label: str
    phrase: str
    scene: str
    noise: str
    accepts: set[str] = field(default_factory=set)
    severity: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    phrase: str
    provides: set[str] = field(default_factory=set)
    sense: int = 2
    power: int = 1
    method: str = ""
    stumble: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_cower(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    obstacle = world.entities.get("obstacle")
    if hero is None or obstacle is None:
        return out
    if hero.memes["fear"] < THRESHOLD:
        return out
    sig = ("cower", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["humility"] += 1
    out.append("__cower__")
    return out


def _r_ask_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    helper = world.entities.get("helper")
    if hero is None or helper is None:
        return out
    if hero.memes["honesty"] < THRESHOLD or hero.memes["humility"] < THRESHOLD:
        return out
    sig = ("ask_help", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["kindness"] += 1
    hero.memes["relief"] += 1
    out.append("__help__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="cower", tag="emotion", apply=_r_cower),
    Rule(name="ask_help", tag="social", apply=_r_ask_help),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
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


def obstacle_can_be_helped(obstacle: Obstacle, helper: Helper) -> bool:
    return bool(obstacle.accepts & helper.provides)


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for item_id in QUEST_ITEMS:
            for obstacle_id, obstacle in OBSTACLES.items():
                if obstacle_id not in place.affords:
                    continue
                for helper_id, helper in HELPERS.items():
                    if helper.sense < SENSE_MIN:
                        continue
                    if obstacle_can_be_helped(obstacle, helper):
                        combos.append((place_id, item_id, obstacle_id, helper_id))
    return combos


def outcome_of(params: "StoryParams") -> str:
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    return "smooth" if helper.power >= obstacle.severity else "rumpled"


def explain_helper(helper_id: str) -> str:
    helper = HELPERS[helper_id]
    better = ", ".join(sorted(h.id for h in sensible_helpers()))
    return (
        f"(Refusing helper '{helper_id}': it scores too low on common sense "
        f"(sense={helper.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_rejection(place: Place, obstacle: Obstacle, helper: Helper) -> str:
    if obstacle.id not in place.affords:
        return (
            f"(No story: {obstacle.label} does not belong on the route through "
            f"{place.label}, so the quest has no grounded middle obstacle there.)"
        )
    return (
        f"(No story: {helper.label} does not have a sensible way to handle "
        f"{obstacle.label}. Pick a helper whose method actually fits the obstacle.)"
    )


def predict_scare(world: World, obstacle: Obstacle) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["fear"] += float(obstacle.severity)
    propagate(sim, narrate=False)
    return {
        "fear": hero.memes["fear"],
        "will_cower": ("cower", hero.id) in sim.fired,
    }


def introduce(world: World, hero: Entity, item: QuestItem) -> None:
    world.say(
        f"{hero.id} was the kind of child who could trip over a loaf of bread and "
        f"still wave at it politely. On the morning of {world.place.festival}, "
        f"{hero.pronoun()} found {item.phrase} {item.found_at}."
    )
    world.say(
        f'When {hero.pronoun()} remembered that it belonged to the {item.owner_role} '
        f'{item.owner_place}, {hero.pronoun()} pressed it to {hero.pronoun("possessive")} chest and said, '
        f'"Oh! I have to take this back before {item.reason}."'
    )


def promise_quest(world: World, hero: Entity, owner: Entity, item: QuestItem) -> None:
    hero.memes["duty"] += 1
    hero.memes["honesty"] += 1
    world.say(
        f'That turned the errand into a quest in {hero.pronoun("possessive")} mind. '
        f'"I will return {item.label}," {hero.id} declared, "and I will not pretend '
        f'it grew legs and walked away by itself."'
    )
    world.say(
        f'From across the lane, the {owner.label} called, "If anyone sees my {item.label}, '
        f'please tell me before the parade starts!"'
    )


def set_out(world: World, hero: Entity, obstacle: Obstacle) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"So off {hero.pronoun()} went through {world.place.label}, taking the shortcut "
        f"where {obstacle.scene}."
    )


def face_obstacle(world: World, hero: Entity, obstacle: Obstacle) -> None:
    pred = predict_scare(world, obstacle)
    world.facts["predicted_fear"] = pred["fear"]
    hero.memes["fear"] += float(obstacle.severity)
    propagate(world, narrate=False)
    world.say(
        f"But halfway there, {obstacle.phrase} blocked the path. It made {obstacle.noise}, "
        f"which was much too dramatic for such an ordinary morning."
    )
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f'{hero.id} tried to stand tall, then had to cower behind a flower barrel. '
            f'"I am being very brave," {hero.pronoun()} whispered, "from over here."'
        )


def tell_truth(world: World, hero: Entity, helper: Entity, item: QuestItem) -> None:
    hero.memes["honesty"] += 1
    hero.memes["humility"] += 1
    propagate(world, narrate=False)
    world.say(
        f'Just then, {helper.phrase} came by. "{hero.id}," {helper.pronoun()} said, '
        f'"why are you hiding behind the flowers?"'
    )
    world.say(
        f'"Because I am scared," {hero.id} admitted, peeking out, "and because '
        f'I really do need to return this {item.label}. It belongs to someone else, '
        f'so I should tell the truth and take it back."'
    )


def help_smooth(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, item: QuestItem) -> None:
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["cleared"] = 1
    world.say(
        f'"Good," said {helper.id}. "Brave children ask for help before the trouble grows taller than they are." '
        f"Then {helper.pronoun()} {HELPERS[helper.attrs['config']].method}."
    )
    world.say(
        f"The obstacle melted into silliness at once, and the path opened. "
        f"{hero.id} hurried on with the {item.label}, walking a little straighter now that "
        f"{hero.pronoun()} was no longer pretending to be fearless."
    )


def help_rumpled(world: World, hero: Entity, helper: Entity, obstacle: Obstacle, item: QuestItem) -> None:
    hero.memes["relief"] += 1
    hero.memes["bravery"] += 1
    hero.meters["rumpled"] += 1
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["cleared"] = 1
    world.say(
        f'"Let us try anyway," said {helper.id}. Then {helper.pronoun()} {HELPERS[helper.attrs["config"]].stumble}.'
    )
    world.say(
        f"It almost worked. Then the whole scene turned funny at once: hats tilted, feet skipped, "
        f"and {hero.id} had to grab the {item.label} with both hands so it would not fly away."
    )
    world.say(
        f"Still, the path finally opened. {hero.id} arrived a bit rumpled and out of breath, "
        f"but still honest, still carrying the {item.label}, and still going the right way."
    )


def return_item(world: World, hero: Entity, owner: Entity, item: QuestItem) -> None:
    owner.memes["gratitude"] += 1
    hero.memes["pride"] += 1
    world.say(
        f'At last {hero.pronoun()} reached the {owner.label}. "{item.label.capitalize()} delivery!" '
        f'{hero.id} announced. Then {hero.pronoun()} added, quieter, "I found it, and I should have '
        f'brought it back sooner."'
    )
    world.say(
        f'The {owner.label} smiled instead of scolding. "Thank you for returning it and for telling the truth," '
        f'{owner.pronoun()} said. "That is what real bravery looks like."'
    )


def ending(world: World, hero: Entity, owner: Entity, item: QuestItem, outcome: str) -> None:
    hero.memes["joy"] += 1
    if outcome == "smooth":
        world.say(
            f'Soon the whole place felt merry again. {item.ending_image}, and {hero.id} laughed so hard '
            f'{hero.pronoun()} nearly bowed to a cabbage by mistake.'
        )
    else:
        world.say(
            f'Everyone could tell there had been an adventure, because one shoelace was untied and a leaf sat on '
            f'{hero.pronoun("possessive")} hair like a tiny green hat. {item.ending_image}, and even {hero.id} had '
            f'to laugh at the way the quest had wrinkled into comedy.'
        )


def tell(
    place: Place,
    item_cfg: QuestItem,
    obstacle_cfg: Obstacle,
    helper_cfg: Helper,
    *,
    hero_name: str = "Mia",
    hero_gender: str = "girl",
    parent_type: str = "mother",
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        role="hero",
        traits=["earnest", "funny"],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        phrase=helper_cfg.phrase,
        role="helper",
        attrs={"config": helper_cfg.id},
    ))
    owner = world.add(Entity(
        id="owner",
        kind="character",
        type="person",
        label=item_cfg.owner_role,
        role="owner",
    ))
    obstacle = world.add(Entity(
        id="obstacle",
        kind="thing",
        type="obstacle",
        label=obstacle_cfg.label,
        role="obstacle",
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    item = world.add(Entity(
        id="item",
        kind="thing",
        type="item",
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        role="item",
    ))

    hero.memes["bravery"] = BRAVERY_INIT
    world.facts["hero_name"] = hero_name

    introduce(world, hero, item_cfg)
    promise_quest(world, hero, owner, item_cfg)

    world.para()
    set_out(world, hero, obstacle_cfg)
    face_obstacle(world, hero, obstacle_cfg)
    tell_truth(world, hero, helper, item_cfg)

    world.para()
    outcome = "smooth" if helper_cfg.power >= obstacle_cfg.severity else "rumpled"
    if outcome == "smooth":
        help_smooth(world, hero, helper, obstacle_cfg, item_cfg)
    else:
        help_rumpled(world, hero, helper, obstacle_cfg, item_cfg)

    world.para()
    return_item(world, hero, owner, item_cfg)
    ending(world, hero, owner, item_cfg, outcome)

    world.facts.update(
        hero=hero,
        helper=helper,
        owner=owner,
        parent=parent,
        item_cfg=item_cfg,
        item=item,
        obstacle_cfg=obstacle_cfg,
        obstacle=obstacle,
        place=place,
        helper_cfg=helper_cfg,
        outcome=outcome,
        cowered=("cower", hero.id) in world.fired or hero.memes["fear"] >= THRESHOLD,
        honest=hero.memes["honesty"] >= THRESHOLD,
        asked_help=helper.memes["kindness"] >= THRESHOLD,
    )
    return world


PLACES = {
    "market": Place(
        id="market",
        label="the market lane",
        festival="the Noon Noodle Parade",
        affords={"goose", "gate"},
        tags={"market"},
    ),
    "courtyard": Place(
        id="courtyard",
        label="the stone courtyard",
        festival="the Bell-and-Bunting Fair",
        affords={"gate", "cabbages"},
        tags={"courtyard"},
    ),
    "green": Place(
        id="green",
        label="the village green",
        festival="the Lemon Ribbon Picnic",
        affords={"goose", "cabbages"},
        tags={"green"},
    ),
}

QUEST_ITEMS = {
    "bell": QuestItem(
        id="bell",
        label="bell",
        phrase="a little brass bell",
        owner_role="cake judge",
        owner_place="by the ribbon table",
        found_at="under a bench",
        reason="the judging cannot begin without it",
        ending_image="the bell rang bright and silly over the cheering crowd",
        tags={"honesty", "returning"},
    ),
    "ladle": QuestItem(
        id="ladle",
        label="ladle",
        phrase="a long wooden ladle",
        owner_role="soup cook",
        owner_place="beside the steaming pots",
        found_at="beside a crate of turnips",
        reason="the giant soup must be stirred",
        ending_image="the soup pot gave a happy glug while everyone lined up with bowls",
        tags={"honesty", "kindness"},
    ),
    "banner": QuestItem(
        id="banner",
        label="banner",
        phrase="a rolled-up parade banner",
        owner_role="band leader",
        owner_place="near the drum stand",
        found_at="leaning against a lamppost",
        reason="the parade looks bare without it",
        ending_image="the banner fluttered high enough to tickle the drummer's hat",
        tags={"responsibility", "returning"},
    ),
}

OBSTACLES = {
    "goose": Obstacle(
        id="goose",
        label="a goose",
        phrase="a very important-looking goose",
        scene="a goose stood in the middle of the lane like a guard captain",
        noise="one trumpet-like HONK after another",
        accepts={"snack", "shield"},
        severity=3,
        tags={"goose"},
    ),
    "gate": Obstacle(
        id="gate",
        label="a squeaky gate",
        phrase="a tall squeaky gate",
        scene="a squeaky gate leaned across the shortcut",
        noise="a rusty screee and a wobbling clank",
        accepts={"oil"},
        severity=2,
        tags={"gate"},
    ),
    "cabbages": Obstacle(
        id="cabbages",
        label="runaway cabbages",
        phrase="three runaway cabbages",
        scene="three cabbages had rolled loose from a cart and were bumping about like green bowling balls",
        noise="soft thumps and one surprisingly bossy rustle",
        accepts={"basket"},
        severity=1,
        tags={"cabbages"},
    ),
}

HELPERS = {
    "baker": Helper(
        id="baker",
        label="baker",
        type="woman",
        phrase="the baker with flour on her elbows",
        provides={"snack"},
        sense=3,
        power=3,
        method="crumbled a bun, tossed it aside, and marched the goose after the crumbs like a tiny feathery parade",
        stumble="crumbled a bun and lured the goose away so neatly that even the goose seemed pleased with itself",
        qa_text="used bun crumbs to lead the goose away",
        tags={"help", "goose"},
    ),
    "caretaker": Helper(
        id="caretaker",
        label="caretaker",
        type="man",
        phrase="the caretaker with a jangly ring of keys",
        provides={"oil"},
        sense=3,
        power=2,
        method="dabbed the hinges with oil until the gate sighed and swung open without another complaint",
        stumble="splashed a little oil on the hinges, and after one last offended squeal the gate swung wide",
        qa_text="oiled the squeaky gate so it would open",
        tags={"help", "gate"},
    ),
    "grocer": Helper(
        id="grocer",
        label="grocer",
        type="man",
        phrase="the grocer carrying an empty basket",
        provides={"basket"},
        sense=3,
        power=1,
        method="scooped the runaway cabbages into the basket as if this happened every single Tuesday",
        stumble="chased the runaway cabbages with an empty basket until the last one rolled politely inside",
        qa_text="collected the runaway cabbages in a basket",
        tags={"help", "cabbages"},
    ),
    "umbrella_aunt": Helper(
        id="umbrella_aunt",
        label="aunt",
        type="woman",
        phrase="Aunt Poppy with a striped umbrella",
        provides={"shield"},
        sense=2,
        power=2,
        method="opened the umbrella with a pop and steered the goose backward one dignified step at a time",
        stumble="opened the umbrella with a pop, which startled the goose, startled her, and startled two pigeons for no reason at all",
        qa_text="used an umbrella to back the goose away",
        tags={"help", "goose"},
    ),
    "juggler": Helper(
        id="juggler",
        label="juggler",
        type="man",
        phrase="the juggler with six oranges and too much confidence",
        provides={"noise"},
        sense=1,
        power=1,
        method="juggled in front of the problem",
        stumble="juggled in front of the problem, which made everything busier and nothing better",
        qa_text="tried juggling at the obstacle",
        tags={"comedy"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella", "Lucy", "Maya"]
BOY_NAMES = ["Ben", "Theo", "Sam", "Leo", "Max", "Finn", "Eli", "Noah"]


@dataclass
class StoryParams:
    place: str
    item: str
    obstacle: str
    helper: str
    hero_name: str
    hero_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="market",
        item="bell",
        obstacle="goose",
        helper="baker",
        hero_name="Mia",
        hero_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="courtyard",
        item="ladle",
        obstacle="gate",
        helper="caretaker",
        hero_name="Theo",
        hero_gender="boy",
        parent="father",
    ),
    StoryParams(
        place="green",
        item="banner",
        obstacle="goose",
        helper="umbrella_aunt",
        hero_name="Lily",
        hero_gender="girl",
        parent="mother",
    ),
    StoryParams(
        place="courtyard",
        item="bell",
        obstacle="cabbages",
        helper="grocer",
        hero_name="Ben",
        hero_gender="boy",
        parent="father",
    ),
]


KNOWLEDGE = {
    "honesty": [
        (
            "What does honesty mean?",
            "Honesty means telling what is true, even when it feels awkward or scary. It helps other people trust you.",
        )
    ],
    "help": [
        (
            "Why is asking for help brave?",
            "Asking for help is brave because you tell the truth about what you can and cannot do alone. It helps stop a small problem from growing bigger.",
        )
    ],
    "goose": [
        (
            "Why can a goose be scary?",
            "A goose can flap, honk, and rush at people very suddenly. The noise and surprise can make someone jump back even if the goose is not very big.",
        )
    ],
    "gate": [
        (
            "Why do rusty gates squeak?",
            "Rusty gates squeak because their metal parts rub together and do not move smoothly. A little oil can help them swing more quietly.",
        )
    ],
    "cabbages": [
        (
            "Why do round vegetables roll away?",
            "Round vegetables roll because their shape lets them spin when the ground slopes or someone bumps them. That can make a funny mess very quickly.",
        )
    ],
    "returning": [
        (
            "Why should you return something that belongs to someone else?",
            "You should return it because it is the fair and kind thing to do. The owner may need it, and giving it back shows respect.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    obstacle = f["obstacle_cfg"]
    outcome = f["outcome"]
    helper = f["helper_cfg"]
    prompts = [
        f'Write a funny quest story for a 3-to-5-year-old that includes the word "cower" and ends with a child returning a lost {item.label}.',
        f"Tell a comedy where a {hero.type} named {world.facts['hero_name']} tries to bring back a {item.label}, faces {obstacle.phrase}, and learns that honesty and asking for help are part of bravery.",
        f'Write a dialogue-rich moral story where a child says what is true, gets help, and finishes a small quest before {world.place.festival}.',
    ]
    if outcome == "rumpled":
        prompts.append(
            f"Make the help a little messy and comic: {helper.label}'s plan should work only after a funny scramble, but the child should still do the right thing."
        )
    return prompts


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    item = f["item_cfg"]
    obstacle = f["obstacle_cfg"]
    helper = f["helper_cfg"]
    owner = f["owner"]
    out = [
        (
            "Who is the story about?",
            f"It is about {world.facts['hero_name']}, a child on a quest to return a {item.label}, and the {owner.label} who needed it back. The story also includes {helper.phrase} helping at a silly moment.",
        ),
        (
            f"Why did {world.facts['hero_name']} start the quest?",
            f"{world.facts['hero_name']} found {item.phrase} and remembered it belonged to the {owner.label}. Returning it was the honest thing to do, and the owner needed it before {world.place.festival}.",
        ),
        (
            f"What made {world.facts['hero_name']} cower?",
            f"{obstacle.phrase.capitalize()} blocked the shortcut and made {obstacle.noise}. The surprise and noise were enough to make {world.facts['hero_name']} cower behind the flower barrel for a moment.",
        ),
        (
            f"How did {world.facts['hero_name']} solve the problem?",
            f"{world.facts['hero_name']} admitted being scared instead of pretending to be fearless. Then {helper.phrase} helped and {helper.qa_text}, which opened the way again.",
        ),
    ]
    if f["outcome"] == "smooth":
        out.append(
            (
                "What is the moral of the story?",
                "The story teaches that real bravery can include being scared, telling the truth, and asking for help. Doing the right thing mattered more than looking bold.",
            )
        )
    else:
        out.append(
            (
                "How did the story end?",
                f"It ended happily but a little rumpled. {world.facts['hero_name']} reached the {owner.label} out of breath and messy-looking, yet still returned the {item.label} and told the truth.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item_cfg"].tags) | set(world.facts["helper_cfg"].tags) | set(world.facts["obstacle_cfg"].tags)
    ordered = ["honesty", "returning", "help", "goose", "gate", "cabbages"]
    out: list[tuple[str, str]] = []
    for tag in ordered:
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(P, I, O, H) :- place(P), item(I), obstacle(O), helper(H),
                     affords(P, O), sensible(H), can_help(O, H).

sensible(H) :- helper(H), sense(H, S), sense_min(M), S >= M.
can_help(O, H) :- accepts(O, T), provides(H, T).

% --- outcome ---------------------------------------------------------------
outcome(smooth)  :- chosen_obstacle(O), chosen_helper(H), power(H, P), severity(O, S), P >= S.
outcome(rumpled) :- chosen_obstacle(O), chosen_helper(H), power(H, P), severity(O, S), P < S.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for obstacle_id in sorted(place.affords):
            lines.append(asp.fact("affords", pid, obstacle_id))
    for iid in QUEST_ITEMS:
        lines.append(asp.fact("item", iid))
    for oid, obstacle in OBSTACLES.items():
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("severity", oid, obstacle.severity))
        for tag in sorted(obstacle.accepts):
            lines.append(asp.fact("accepts", oid, tag))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, helper.sense))
        lines.append(asp.fact("power", hid, helper.power))
        for tag in sorted(helper.provides):
            lines.append(asp.fact("provides", hid, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_obstacle", params.obstacle),
            asp.fact("chosen_helper", params.helper),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    outs = asp.atoms(model, "outcome")
    return outs[0][0] if outs else "?"


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

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(30):
        try:
            args = parser.parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during random param resolution at seed {seed}.")
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
            raise StoryError("smoke test produced empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: a funny little quest about honesty, asking for help, and not pretending fear away."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=QUEST_ITEMS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.helper and HELPERS[args.helper].sense < SENSE_MIN:
        raise StoryError(explain_helper(args.helper))
    if args.place and args.obstacle and args.helper:
        place = PLACES[args.place]
        obstacle = OBSTACLES[args.obstacle]
        helper = HELPERS[args.helper]
        if obstacle.id not in place.affords or not obstacle_can_be_helped(obstacle, helper):
            raise StoryError(explain_rejection(place, obstacle, helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.item is None or combo[1] == args.item)
        and (args.obstacle is None or combo[2] == args.obstacle)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, item_id, obstacle_id, helper_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        item=item_id,
        obstacle=obstacle_id,
        helper=helper_id,
        hero_name=name,
        hero_gender=gender,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place '{params.place}'.)")
    if params.item not in QUEST_ITEMS:
        raise StoryError(f"(Unknown item '{params.item}'.)")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle '{params.obstacle}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper '{params.helper}'.)")
    place = PLACES[params.place]
    obstacle = OBSTACLES[params.obstacle]
    helper = HELPERS[params.helper]
    if helper.sense < SENSE_MIN:
        raise StoryError(explain_helper(params.helper))
    if obstacle.id not in place.affords or not obstacle_can_be_helped(obstacle, helper):
        raise StoryError(explain_rejection(place, obstacle, helper))

    world = tell(
        place=place,
        item_cfg=QUEST_ITEMS[params.item],
        obstacle_cfg=obstacle,
        helper_cfg=helper,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        parent_type=params.parent,
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
        print(f"{len(combos)} compatible (place, item, obstacle, helper) combos:\n")
        for place, item, obstacle, helper in combos:
            print(f"  {place:10} {item:7} {obstacle:9} {helper}")
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
            header = f"### {p.hero_name}: {p.item} via {p.obstacle} with {p.helper} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
