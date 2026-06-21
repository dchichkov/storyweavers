#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py
======================================================

A small story world for a nursery-rhyme-flavored quest tale: a teen is sent on a
kind errand, meets one obstacle on the path, uses the right aid, and comes home
changed. The world refuses mismatched obstacle/aid pairs, because a quest should
turn on a sensible fix instead of a decorative prop.

Run it
------
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --quest moonbell --obstacle brook --aid stepping_stones
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --obstacle brook --aid candle
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --json
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --asp
    python storyworlds/worlds/gpt-5.4/teen_quest_nursery_rhyme.py --verify
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Quest:
    id: str
    place: str
    path_name: str
    prize_label: str
    prize_phrase: str
    purpose: str
    opening: str
    ending: str
    obstacles: set[str] = field(default_factory=set)
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
class Obstacle:
    id: str
    label: str
    phrase: str
    risk: str
    meter_key: str
    solved_by: set[str] = field(default_factory=set)
    crossing_line: str = ""
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
    use_line: str
    fixes: set[str] = field(default_factory=set)
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


def _r_clear_path(world: World) -> list[str]:
    teen = world.get("teen")
    obstacle = world.get("obstacle")
    aid = world.get("aid")
    if teen.meters["using_aid"] < THRESHOLD:
        return []
    if obstacle.attrs.get("needs") != aid.attrs.get("solves"):
        return []
    sig = ("clear_path", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    obstacle.meters["blocked"] = 0.0
    obstacle.meters["cleared"] += 1
    teen.memes["courage"] += 1
    return ["__cleared__"]


def _r_risk(world: World) -> list[str]:
    teen = world.get("teen")
    obstacle = world.get("obstacle")
    if obstacle.meters["blocked"] < THRESHOLD or teen.meters["trying_path"] < THRESHOLD:
        return []
    sig = ("risk", obstacle.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    teen.meters[obstacle.attrs["meter_key"]] += 1
    teen.memes["worry"] += 1
    return ["__risk__"]


def _r_return_joy(world: World) -> list[str]:
    teen = world.get("teen")
    elder = world.get("elder")
    prize = world.get("prize")
    if teen.meters["home"] < THRESHOLD or prize.meters["carried"] < THRESHOLD:
        return []
    sig = ("return_joy", prize.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    elder.memes["relief"] += 1
    elder.memes["joy"] += 1
    teen.memes["pride"] += 1
    return ["__home__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="clear_path", tag="physical", apply=_r_clear_path),
    Rule(name="risk", tag="physical", apply=_r_risk),
    Rule(name="return_joy", tag="social", apply=_r_return_joy),
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
    return produced


def aid_solves(obstacle: Obstacle, aid: Aid) -> bool:
    return aid.id in obstacle.solved_by and obstacle.id in aid.fixes


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for qid, quest in QUESTS.items():
        for oid in sorted(quest.obstacles):
            obstacle = OBSTACLES[oid]
            for aid_id, aid in AIDS.items():
                if aid_solves(obstacle, aid):
                    combos.append((qid, oid, aid_id))
    return sorted(combos)


def explain_rejection(quest: Quest, obstacle: Obstacle, aid: Aid) -> str:
    if obstacle.id not in quest.obstacles:
        return (
            f"(No story: the path to {quest.place} in this world does not use {obstacle.phrase}. "
            f"Pick an obstacle that belongs on the way to {quest.place}.)"
        )
    return (
        f"(No story: {aid.phrase.capitalize()} cannot sensibly solve {obstacle.phrase}. "
        f"For this quest, the turning point must honestly fit the trouble on the path.)"
    )


def predict_without_aid(world: World) -> dict:
    sim = world.copy()
    teen = sim.get("teen")
    teen.meters["trying_path"] += 1
    propagate(sim, narrate=False)
    obstacle = sim.get("obstacle")
    return {
        "risked": obstacle.attrs["meter_key"] if teen.meters[obstacle.attrs["meter_key"]] >= THRESHOLD else "",
        "worry": teen.memes["worry"],
    }


def introduce(world: World, teen: Entity, elder: Entity, quest: Quest) -> None:
    world.say(
        f"Hush-a-bye morning, pale and clean: in the cottage lived {teen.id}, a kind teen with quick feet and a listening face."
    )
    world.say(
        f"{quest.opening} {elder.label_word.capitalize()} said the house needed {quest.prize_phrase} {quest.purpose}."
    )


def send_quest(world: World, teen: Entity, elder: Entity, quest: Quest) -> None:
    teen.memes["duty"] += 1
    world.say(
        f'"Will you go on this little quest?" asked {elder.label_word}. "{quest.place.capitalize()} keeps what we need."'
    )
    world.say(
        f'{teen.id} nodded. "I will go by {quest.path_name} and come back before the kettle sings."'
    )


def set_out(world: World, teen: Entity, quest: Quest) -> None:
    teen.meters["walking"] += 1
    teen.memes["hope"] += 1
    world.say(
        f"So off went {teen.id}, over the lane and under the lark, with a soft bag at {teen.pronoun('possessive')} side and a brave little spark in {teen.pronoun('possessive')} heart."
    )


def meet_obstacle(world: World, teen: Entity, obstacle: Obstacle) -> None:
    obstacle_ent = world.get("obstacle")
    obstacle_ent.meters["blocked"] += 1
    world.say(
        f"But on the path there waited {obstacle.phrase}. It stood between the teen and the quest, promising that {obstacle.risk}."
    )


def warn(world: World, teen: Entity, obstacle: Obstacle) -> None:
    pred = predict_without_aid(world)
    world.facts["predicted_risk"] = pred["risked"]
    world.facts["predicted_worry"] = pred["worry"]
    risk_text = {
        "wet": "boots full of cold water",
        "scratched": "hands full of little scratches",
        "lost": "feet wandering in the wrong direction",
    }.get(pred["risked"], "trouble on the path")
    world.say(
        f"{teen.id} paused and thought, \"If I rush at it now, I may come home with {risk_text} instead of the thing we need.\""
    )


def use_aid(world: World, teen: Entity, obstacle: Obstacle, aid: Aid) -> None:
    teen.meters["using_aid"] += 1
    world.say(aid.use_line)
    produced = propagate(world, narrate=False)
    if "__cleared__" not in produced or world.get("obstacle").meters["cleared"] < THRESHOLD:
        raise StoryError(explain_rejection(world.facts["quest"], obstacle, aid))
    world.say(obstacle.crossing_line)


def claim_prize(world: World, teen: Entity, quest: Quest) -> None:
    prize = world.get("prize")
    prize.meters["found"] += 1
    prize.meters["carried"] += 1
    teen.memes["joy"] += 1
    world.say(
        f"At last {teen.id} reached {quest.place} and found {quest.prize_phrase}. {teen.pronoun().capitalize()} tucked it safely into the bag as if carrying a bright note from a song."
    )


def return_home(world: World, teen: Entity, elder: Entity, quest: Quest) -> None:
    teen.meters["home"] += 1
    propagate(world, narrate=False)
    world.say(
        f"Back came {teen.id} by the same small road, quicker now, because the hard part had been answered."
    )
    world.say(
        f"{elder.label_word.capitalize()} took the prize with smiling hands, and soon {quest.ending}"
    )


def close_story(world: World, teen: Entity, elder: Entity, aid: Aid) -> None:
    teen.memes["calm"] += 1
    world.say(
        f'"A quest is not won by hurrying alone," said {elder.label_word}. "It is won by noticing what helps."'
    )
    world.say(
        f"And after that day, whenever a path looked puzzling, {teen.id} remembered {aid.label} and walked with steadier courage."
    )


def tell(
    quest: Quest,
    obstacle: Obstacle,
    aid: Aid,
    teen_name: str = "Mira",
    teen_type: str = "girl",
    elder_type: str = "grandmother",
    trait: str = "gentle",
) -> World:
    world = World()
    teen = world.add(
        Entity(
            id=teen_name,
            kind="character",
            type=teen_type,
            label=teen_name,
            role="teen",
            traits=["teen", trait],
        )
    )
    elder = world.add(
        Entity(
            id="Elder",
            kind="character",
            type=elder_type,
            label="the elder",
            role="elder",
            traits=["wise"],
        )
    )
    obstacle_ent = world.add(
        Entity(
            id="obstacle",
            kind="thing",
            type="obstacle",
            label=obstacle.label,
            phrase=obstacle.phrase,
            attrs={"needs": obstacle.id, "meter_key": obstacle.meter_key},
        )
    )
    aid_ent = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            phrase=aid.phrase,
            attrs={"solves": next(iter(aid.fixes)) if aid.fixes else ""},
        )
    )
    prize = world.add(
        Entity(
            id="prize",
            kind="thing",
            type="prize",
            label=quest.prize_label,
            phrase=quest.prize_phrase,
        )
    )

    world.facts.update(
        quest=quest,
        obstacle_cfg=obstacle,
        aid_cfg=aid,
        teen=teen,
        elder=elder,
        prize=prize,
    )

    introduce(world, teen, elder, quest)
    send_quest(world, teen, elder, quest)

    world.para()
    set_out(world, teen, quest)
    meet_obstacle(world, teen, obstacle)
    warn(world, teen, obstacle)

    world.para()
    use_aid(world, teen, obstacle, aid)
    claim_prize(world, teen, quest)

    world.para()
    return_home(world, teen, elder, quest)
    close_story(world, teen, elder, aid)

    world.facts.update(
        solved=world.get("obstacle").meters["cleared"] >= THRESHOLD,
        prize_found=prize.meters["found"] >= THRESHOLD,
        returned=teen.meters["home"] >= THRESHOLD,
    )
    return world


QUESTS = {
    "moonbell": Quest(
        id="moonbell",
        place="the silver hill",
        path_name="the sheep path",
        prize_label="moonbell flower",
        prize_phrase="a moonbell flower",
        purpose="for the cradle wreath before evening",
        opening="The sparrows hopped by the sill and the spoon gave a tiny ring.",
        ending="the cradle wore a moonbell wreath, and the room seemed to hum its own sleepy tune.",
        obstacles={"brook", "bramble"},
        tags={"flower", "quest", "hill"},
    ),
    "mill_ribbon": Quest(
        id="mill_ribbon",
        place="the old windmill",
        path_name="the turning lane",
        prize_label="blue ribbon",
        prize_phrase="a blue ribbon",
        purpose="to tie around the May-day loaf",
        opening="The cat curled on the mat and the morning bread grew warm.",
        ending="the loaf was tied with blue, and even the flour dust looked merry in the light.",
        obstacles={"brook", "mist"},
        tags={"ribbon", "quest", "mill"},
    ),
    "orchard_plum": Quest(
        id="orchard_plum",
        place="the far orchard",
        path_name="the hedgerow path",
        prize_label="first plum",
        prize_phrase="the first plum",
        purpose="for the supper pie and its sweet song",
        opening="The kettle whispered, and the little clock tapped twice.",
        ending="the pie smelled sweet on the table, and the whole kitchen glowed as if dusk had turned to honey.",
        obstacles={"bramble", "mist"},
        tags={"plum", "quest", "orchard"},
    ),
}

OBSTACLES = {
    "brook": Obstacle(
        id="brook",
        label="brook",
        phrase="a laughing brook with quick cold water",
        risk="wet boots and a late return",
        meter_key="wet",
        solved_by={"stepping_stones"},
        crossing_line="Stone by stone, step by step, the teen crossed the brook without a splash worth telling.",
        tags={"brook", "water"},
    ),
    "bramble": Obstacle(
        id="bramble",
        label="bramble hedge",
        phrase="a bramble hedge knitted thick with thorns",
        risk="scratched hands and a torn bag",
        meter_key="scratched",
        solved_by={"garden_gloves"},
        crossing_line="Gloved and careful, the teen parted the thorny stems and slipped through with the bag unsnagged.",
        tags={"bramble", "thorn"},
    ),
    "mist": Obstacle(
        id="mist",
        label="mist",
        phrase="a pearly mist that muddled the lane",
        risk="lost feet and a wandering quest",
        meter_key="lost",
        solved_by={"lantern"},
        crossing_line="The lantern made a small gold pool on the road, and the true turning showed itself at once.",
        tags={"mist", "path"},
    ),
}

AIDS = {
    "stepping_stones": Aid(
        id="stepping_stones",
        label="stepping stones",
        phrase="stepping stones",
        use_line="Then the teen noticed a row of stepping stones, round as little moons in the water, and tested them one by one.",
        fixes={"brook"},
        tags={"stones", "water"},
    ),
    "garden_gloves": Aid(
        id="garden_gloves",
        label="garden gloves",
        phrase="garden gloves",
        use_line="So the teen pulled on a pair of garden gloves from the bag, flexed brave fingers, and reached for the safest gap in the hedge.",
        fixes={"bramble"},
        tags={"gloves", "thorn"},
    ),
    "lantern": Aid(
        id="lantern",
        label="lantern",
        phrase="a lantern",
        use_line="So the teen lit a lantern with a click and a glow, holding it low where the lane was trying to hide.",
        fixes={"mist"},
        tags={"lantern", "light"},
    ),
    "candle": Aid(
        id="candle",
        label="candle stub",
        phrase="a candle stub",
        use_line="The teen tried to think of using a candle stub, but it was a poor little thing for a big path.",
        fixes=set(),
        tags={"candle"},
    ),
}

GIRL_NAMES = ["Mira", "Nell", "Ada", "June", "Elsie", "Mae", "Cora", "Wren"]
BOY_NAMES = ["Finn", "Tobin", "Jude", "Milo", "Robin", "Ash", "Ned", "Theo"]
TRAITS = ["gentle", "steady", "bright", "patient", "cheerful", "careful"]


@dataclass
class StoryParams:
    quest: str
    obstacle: str
    aid: str
    teen_name: str
    teen_type: str
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
    "brook": [
        (
            "Why can a brook make a journey hard?",
            "A brook is moving water, so it can soak shoes and slow you down if there is no safe way across. Even a small stream can matter when someone is trying to get somewhere on time.",
        )
    ],
    "bramble": [
        (
            "What is a bramble hedge?",
            "A bramble hedge is a tangle of thorny stems. The thorns can scratch your skin and catch on bags or sleeves.",
        )
    ],
    "mist": [
        (
            "Why is mist confusing on a path?",
            "Mist makes faraway things look blurry, so turns and landmarks are harder to see. That is why a good light can help you keep the right way.",
        )
    ],
    "stones": [
        (
            "What are stepping stones for?",
            "Stepping stones are firm places to put your feet when you cross shallow water. They help you stay dry because you do not have to splash straight through.",
        )
    ],
    "gloves": [
        (
            "Why do garden gloves help with thorns?",
            "Garden gloves cover your hands with a thicker layer than skin alone. That makes it easier to touch prickly stems without getting scratched.",
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern makes a steady light you can carry with you. It helps you see the path, especially when the air is dim or foggy.",
        )
    ],
    "flower": [
        (
            "Why do people pick flowers for special days?",
            "Flowers can make a room or a gift feel bright and loved. People often choose them because they carry beauty into an ordinary moment.",
        )
    ],
    "ribbon": [
        (
            "What does a ribbon do?",
            "A ribbon ties around something to decorate it or hold it neatly. A bright ribbon can make bread, hair, or a gift look festive.",
        )
    ],
    "plum": [
        (
            "What is a plum?",
            "A plum is a soft, sweet fruit that grows on a tree. It can be eaten fresh or baked into pies and other treats.",
        )
    ],
}
KNOWLEDGE_ORDER = ["brook", "bramble", "mist", "stones", "gloves", "lantern", "flower", "ribbon", "plum"]


CURATED = [
    StoryParams(
        quest="moonbell",
        obstacle="brook",
        aid="stepping_stones",
        teen_name="Mira",
        teen_type="girl",
        elder_type="grandmother",
        trait="steady",
    ),
    StoryParams(
        quest="mill_ribbon",
        obstacle="mist",
        aid="lantern",
        teen_name="Finn",
        teen_type="boy",
        elder_type="grandfather",
        trait="bright",
    ),
    StoryParams(
        quest="orchard_plum",
        obstacle="bramble",
        aid="garden_gloves",
        teen_name="June",
        teen_type="girl",
        elder_type="mother",
        trait="careful",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    teen = f["teen"]
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    return [
        f'Write a nursery-rhyme-style quest story that includes the word "teen" and sends a teen to fetch {quest.prize_phrase}.',
        f"Tell a gentle quest where {teen.id}, a {next((t for t in teen.traits if t != 'teen'), 'kind')} teen, must pass {obstacle.phrase} and succeeds by using {aid.label}.",
        f"Write a short story with a lilting, nursery-rhyme feeling: an elder asks for {quest.prize_phrase}, the path goes wrong for a moment, and the ending shows the home made happier.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    teen = f["teen"]
    elder = f["elder"]
    quest = f["quest"]
    obstacle = f["obstacle_cfg"]
    aid = f["aid_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {teen.id}, a teen who went on a small quest for {elder.label_word}. The errand mattered because the house was waiting for {quest.prize_phrase}.",
        ),
        (
            f"Why did {teen.id} set out?",
            f"{teen.id} set out to bring back {quest.prize_phrase} {quest.purpose}. The quest began because {elder.label_word} asked for help, and {teen.id} wanted to do something useful.",
        ),
        (
            f"What problem stood in the way?",
            f"The path was blocked by {obstacle.phrase}. That obstacle threatened {obstacle.risk}, so hurrying straight through would have spoiled the quest.",
        ),
        (
            f"How did {teen.id} get past the trouble?",
            f"{teen.id} used {aid.label} to answer the problem on the path. That worked because {aid.label} fit the obstacle instead of pretending the trouble was something else.",
        ),
        (
            f"What happened after {teen.id} reached {quest.place}?",
            f"{teen.pronoun().capitalize()} found {quest.prize_phrase} and carried it home. When {elder.label_word} received it, the whole house changed from waiting to gladness.",
        ),
        (
            "How did the story end?",
            f"It ended with the quest completed and home made brighter. The final image shows that {teen.id} did not just travel somewhere; {teen.pronoun()} brought back exactly what was needed and grew more confident too.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["quest"].tags) | set(f["obstacle_cfg"].tags) | set(f["aid_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
path_has(Q, O) :- quest(Q), obstacle(O), offered(Q, O).
solves(O, A) :- obstacle(O), aid(A), needs(O, O), fixes(A, O).
valid(Q, O, A) :- path_has(Q, O), solves(O, A).

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for oid in sorted(quest.obstacles):
            lines.append(asp.fact("offered", qid, oid))
    for oid in OBSTACLES:
        lines.append(asp.fact("obstacle", oid))
        lines.append(asp.fact("needs", oid, oid))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        for fix in sorted(aid.fixes):
            lines.append(asp.fact("fixes", aid_id, fix))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def outcome_of(params: StoryParams) -> str:
    quest = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if obstacle.id not in quest.obstacles:
        return "invalid"
    return "solved" if aid_solves(obstacle, aid) else "invalid"


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

    smoke_cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(10):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
            params.seed = seed
            smoke_cases.append(params)
        except StoryError as err:
            rc = 1
            print(f"SMOKE resolve failed for seed {seed}: {err}")
            break

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("empty story")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:
            rc = 1
            print(f"SMOKE generate/emit failed for {params}: {err}")
            break

    if rc == 0:
        print(f"OK: smoke-tested generate/emit on {len(smoke_cases)} scenarios.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme quest world: a teen takes a small quest, meets one obstacle, and uses the right help."
    )
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--obstacle", choices=OBSTACLES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--teen-name")
    ap.add_argument("--teen-type", choices=["girl", "boy"])
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.quest and args.obstacle and args.aid:
        quest = QUESTS[args.quest]
        obstacle = OBSTACLES[args.obstacle]
        aid = AIDS[args.aid]
        if args.obstacle not in quest.obstacles or not aid_solves(obstacle, aid):
            raise StoryError(explain_rejection(quest, obstacle, aid))

    filtered = [
        combo
        for combo in valid_combos()
        if (args.quest is None or combo[0] == args.quest)
        and (args.obstacle is None or combo[1] == args.obstacle)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")

    quest_id, obstacle_id, aid_id = rng.choice(sorted(filtered))
    teen_type = args.teen_type or rng.choice(["girl", "boy"])
    teen_name = args.teen_name or rng.choice(GIRL_NAMES if teen_type == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        quest=quest_id,
        obstacle=obstacle_id,
        aid=aid_id,
        teen_name=teen_name,
        teen_type=teen_type,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.quest not in QUESTS:
        raise StoryError(f"(Unknown quest: {params.quest})")
    if params.obstacle not in OBSTACLES:
        raise StoryError(f"(Unknown obstacle: {params.obstacle})")
    if params.aid not in AIDS:
        raise StoryError(f"(Unknown aid: {params.aid})")

    quest = QUESTS[params.quest]
    obstacle = OBSTACLES[params.obstacle]
    aid = AIDS[params.aid]
    if params.obstacle not in quest.obstacles or not aid_solves(obstacle, aid):
        raise StoryError(explain_rejection(quest, obstacle, aid))

    world = tell(
        quest=quest,
        obstacle=obstacle,
        aid=aid,
        teen_name=params.teen_name,
        teen_type=params.teen_type,
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (quest, obstacle, aid) combos:\n")
        for quest_id, obstacle_id, aid_id in combos:
            print(f"  {quest_id:12} {obstacle_id:9} {aid_id}")
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.teen_name}: {p.quest} by way of {p.obstacle} with {p.aid}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
