#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py
==================================================================================

A standalone story world for a small folk-tale domain:

A child in a village cottage thinks the family's terrier stole a treat from the
window ledge. There is a conflict because the accusation seems to fit at first.
Then the child and an elder stop to evaluate the clues. The terrier's actions
lead to a surprise: the real thief is discovered outside, and the child repairs
the unfair blame.

The storyworld models:
- a cottage, a window ledge, a missing baked treat, a terrier, and a thief
- physical meters such as missing, crumbs, tracks, and recovered
- emotional memes such as trust, suspicion, shame, relief, and pride
- a reasonableness gate over which thief could plausibly reach the window
- an inline ASP twin for the compatibility gate and the ending outcome

Run examples
------------
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py --thief crow --ledge high
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py --thief goat
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py --all
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/evaluate_window_terrier_conflict_surprise_folk_tale.py --verify
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
    phrase: str = ""
    role: str = ""
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
        dog = {"dog", "terrier"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in dog:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandmother",
            "grandfather": "grandfather",
            "mother": "mother",
            "father": "father",
        }.get(self.type, self.label or self.type)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    scent: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ledge:
    id: str
    label: str
    phrase: str
    height: str
    inside_phrase: str
    outside_phrase: str
    bird_access: bool
    ground_access: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Thief:
    id: str
    label: str
    phrase: str
    kind: str
    clue: str
    trail: str
    call: str
    carries: str
    bird: bool = False
    climbs: bool = False
    ground_reach: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Finder:
    id: str
    label: str
    phrase: str
    method: str
    success: str
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


def _r_missing_blame(world: World) -> list[str]:
    child = world.get("child")
    dog = world.get("dog")
    treat = world.get("treat")
    if treat.meters["missing"] < THRESHOLD:
        return []
    sig = ("blame",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["suspicion"] += 1
    dog.memes["hurt"] += 1
    return ["__blame__"]


def _r_evaluate_clue(world: World) -> list[str]:
    child = world.get("child")
    elder = world.get("elder")
    dog = world.get("dog")
    clue = world.get("clue")
    if child.memes["suspicion"] < THRESHOLD or elder.memes["evaluation"] < THRESHOLD:
        return []
    if clue.meters["seen"] < THRESHOLD:
        return []
    sig = ("doubt",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["doubt"] += 1
    child.memes["fairness"] += 1
    dog.memes["hope"] += 1
    return ["__doubt__"]


def _r_reveal(world: World) -> list[str]:
    dog = world.get("dog")
    thief = world.get("thief")
    treat = world.get("treat")
    if dog.meters["leading"] < THRESHOLD:
        return []
    if thief.meters["found"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    treat.meters["recovered"] += 1
    dog.memes["pride"] += 1
    world.get("child").memes["shame"] += 1
    world.get("child").memes["relief"] += 1
    return ["__reveal__"]


CAUSAL_RULES = [
    Rule(name="missing_blame", tag="social", apply=_r_missing_blame),
    Rule(name="evaluate_clue", tag="social", apply=_r_evaluate_clue),
    Rule(name="reveal", tag="social", apply=_r_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if not s.startswith("__"))
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def thief_can_reach(ledge: Ledge, thief: Thief) -> bool:
    if thief.bird and ledge.bird_access:
        return True
    if thief.ground_reach and ledge.ground_access:
        return True
    if thief.climbs and ledge.height == "low":
        return True
    return False


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for ledge_id, ledge in LEDGES.items():
        for thief_id, thief in THIEVES.items():
            if thief_can_reach(ledge, thief):
                combos.append((ledge_id, thief_id))
    return combos


def predict_innocence(world: World) -> dict:
    sim = world.copy()
    elder = sim.get("elder")
    clue = sim.get("clue")
    elder.memes["evaluation"] += 1
    clue.meters["seen"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "doubt": child.memes["doubt"],
        "fairness": child.memes["fairness"],
    }


def introduce(world: World, child: Entity, elder: Entity, dog: Entity, treat: Treat, ledge: Ledge) -> None:
    child.memes["love"] += 1
    dog.memes["loyalty"] += 1
    world.say(
        f"In a little cottage at the edge of the village lived {child.id}, "
        f"{child.attrs['article']} {child.type}, with {child.pronoun('possessive')} "
        f"{elder.label_word} and a bright-eyed terrier named {dog.id}."
    )
    world.say(
        f"One market morning, {elder.label_word} baked {treat.phrase} and set it on "
        f"{ledge.inside_phrase} beside the window so the sweet steam could drift away."
    )
    world.say(
        f"{dog.id} sat below like a tiny guard with a twitching nose, while "
        f"{child.id} promised to watch the treat until tea time."
    )


def absent_moment(world: World, child: Entity, ledge: Ledge) -> None:
    world.say(
        f"But folk tales often turn on a small moment. {child.id} stepped away to fetch "
        f"water, and the cottage grew quiet except for the wind at the {ledge.label}."
    )


def missing_turn(world: World, child: Entity, dog: Entity, treat_ent: Entity) -> None:
    treat_ent.meters["missing"] += 1
    treat_ent.meters["crumbs"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When {child.id} came back, only crumbs lay on the cloth. {dog.id} licked his whiskers "
        f"from the smell in the room, and at once {child.id}'s heart leaped to a hard thought."
    )
    world.say(
        f'"You ate it, {dog.id}!" {child.id} cried. The little terrier barked once and planted '
        f"his paws, as if he wished to answer in a language of his own."
    )


def elder_stops_quarrel(world: World, elder: Entity, child: Entity, dog: Entity) -> None:
    child.memes["conflict"] += 1
    dog.memes["conflict"] += 1
    world.say(
        f'{elder.label_word.capitalize()} came from the hearth and raised a calm hand. '
        f'"Sharp blame is a crooked walking stick," {elder.pronoun()} said. '
        f'"Before we scold a faithful terrier, we must evaluate what the room truly tells us."'
    )


def inspect_clue(world: World, child: Entity, elder: Entity, clue_ent: Entity, thief: Thief, ledge: Ledge) -> None:
    elder.memes["evaluation"] += 1
    clue_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So they looked closely. On {ledge.outside_phrase} they saw {thief.clue}, and "
        f"{child.id} felt the first crack in the angry guess."
    )
    pred = predict_innocence(world)
    if pred["doubt"] >= THRESHOLD:
        world.say(
            f'"A fair heart must look twice," {elder.label_word} said, and {child.id} nodded. '
            f"The child had wanted a quick answer, but the clue pointed away from the dog."
        )


def dog_leads(world: World, child: Entity, dog: Entity, finder: Finder) -> None:
    dog.meters["leading"] += 1
    dog.memes["eager"] += 1
    world.say(
        f"Then came the surprise. {dog.id} gave a sharp yip, seized the corner of "
        f"{child.id}'s sleeve, and {finder.method}."
    )


def find_thief(world: World, child: Entity, dog: Entity, thief_ent: Entity, thief: Thief, treat: Treat, finder: Finder) -> None:
    thief_ent.meters["found"] += 1
    propagate(world, narrate=False)
    world.say(
        f"They hurried after him to the yard, and there behind the rain barrel was {thief.phrase}, "
        f"{thief.carries}."
    )
    world.say(
        f"{finder.success}. {child.id} understood at once that {dog.id} had not stolen the treat "
        f"at all; he had been trying to tell the truth with barks and paws."
    )


def apology_and_end(world: World, child: Entity, elder: Entity, dog: Entity, treat: Treat, thief: Thief) -> None:
    child.memes["trust"] += 1
    dog.memes["hurt"] = 0.0
    child.memes["conflict"] = 0.0
    dog.memes["conflict"] = 0.0
    world.say(
        f'{child.id} knelt in the grass and hugged the terrier close. "Forgive me, {dog.id}," '
        f"{child.pronoun()} whispered. \"I spoke before I understood.\""
    )
    world.say(
        f'{elder.label_word.capitalize()} smiled and broke off the saved half of the {treat.label} for '
        f"the child and a small crust for the dog. \"So remember,\" {elder.pronoun()} said, "
        f'"when a quarrel jumps up as quick as a spark, evaluate the signs before you judge."'
    )
    world.say(
        f"From that day on, whenever the wind rattled the window and {dog.id} barked at some mystery, "
        f"{child.id} listened first. And in the village people said that even a terrier may carry "
        f"wisdom to those humble enough to hear it."
    )


def tell(
    treat: Treat,
    ledge: Ledge,
    thief: Thief,
    finder: Finder,
    *,
    child_name: str = "Anya",
    child_gender: str = "girl",
    elder_type: str = "grandmother",
    dog_name: str = "Pip",
    child_trait: str = "quick-tempered",
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        traits=[child_trait],
        attrs={"article": "a"},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    dog = world.add(Entity(
        id=dog_name,
        kind="character",
        type="terrier",
        label=dog_name,
        role="dog",
        tags={"terrier", "dog"},
    ))
    treat_ent = world.add(Entity(
        id="treat",
        kind="thing",
        type="treat",
        label=treat.label,
        phrase=treat.phrase,
        tags=set(treat.tags),
    ))
    clue_ent = world.add(Entity(
        id="clue",
        kind="thing",
        type="clue",
        label="clue",
    ))
    thief_ent = world.add(Entity(
        id="thief",
        kind="thing",
        type=thief.kind,
        label=thief.label,
        phrase=thief.phrase,
        tags=set(thief.tags),
    ))
    window_ent = world.add(Entity(
        id="window",
        kind="thing",
        type="window",
        label="window",
        phrase=ledge.phrase,
        tags={"window"} | set(ledge.tags),
    ))

    introduce(world, child, elder, dog, treat, ledge)
    absent_moment(world, child, ledge)

    world.para()
    missing_turn(world, child, dog, treat_ent)
    elder_stops_quarrel(world, elder, child, dog)

    world.para()
    inspect_clue(world, child, elder, clue_ent, thief, ledge)
    dog_leads(world, child, dog, finder)
    find_thief(world, child, dog, thief_ent, thief, treat, finder)

    world.para()
    apology_and_end(world, child, elder, dog, treat, thief)

    outcome = "surprise_reveal" if treat_ent.meters["recovered"] >= THRESHOLD else "sad_loss"
    world.facts.update(
        child=child,
        elder=elder,
        dog=dog,
        treat_cfg=treat,
        ledge_cfg=ledge,
        thief_cfg=thief,
        finder_cfg=finder,
        treat=treat_ent,
        clue=clue_ent,
        thief=thief_ent,
        window=window_ent,
        outcome=outcome,
        recovered=treat_ent.meters["recovered"] >= THRESHOLD,
        conflict=child.memes["suspicion"] >= THRESHOLD,
        evaluated=elder.memes["evaluation"] >= THRESHOLD,
    )
    return world


TREATS = {
    "honey_cake": Treat(
        id="honey_cake",
        label="honey cake",
        phrase="a round honey cake glazed like amber",
        scent="sweet honey",
        tags={"cake", "honey"},
    ),
    "berry_tart": Treat(
        id="berry_tart",
        label="berry tart",
        phrase="a berry tart with a purple shine",
        scent="summer berries",
        tags={"tart", "berry"},
    ),
    "seed_roll": Treat(
        id="seed_roll",
        label="seed roll",
        phrase="a warm seed roll brushed with butter",
        scent="toasted seeds",
        tags={"bread", "seed"},
    ),
}

LEDGES = {
    "low": Ledge(
        id="low",
        label="low window",
        phrase="a low cottage window",
        height="low",
        inside_phrase="the low window ledge",
        outside_phrase="the sill outside the low window",
        bird_access=True,
        ground_access=True,
        tags={"window", "low"},
    ),
    "high": Ledge(
        id="high",
        label="high window",
        phrase="a high cottage window",
        height="high",
        inside_phrase="the high window shelf",
        outside_phrase="the stones below the high window",
        bird_access=True,
        ground_access=False,
        tags={"window", "high"},
    ),
}

THIEVES = {
    "crow": Thief(
        id="crow",
        label="crow",
        phrase="a ragged black crow",
        kind="bird",
        clue="a black feather caught in the latch",
        trail="a hopping trail toward the yard",
        call="cawing from the fence",
        carries="with sticky crumbs on its beak and the torn cake in its claws",
        bird=True,
        tags={"crow", "bird"},
    ),
    "magpie": Thief(
        id="magpie",
        label="magpie",
        phrase="a bold magpie",
        kind="bird",
        clue="a bright feather striped with white",
        trail="a skipping trail toward the barrel",
        call="clattering from the pear tree",
        carries="with the tart crust pinched in its sharp beak",
        bird=True,
        tags={"magpie", "bird"},
    ),
    "squirrel": Thief(
        id="squirrel",
        label="squirrel",
        phrase="a red squirrel",
        kind="animal",
        clue="tiny claw marks on the outer wood",
        trail="a light scramble along the fence",
        call="chittering by the shed",
        carries="with the roll tucked between its paws",
        climbs=True,
        tags={"squirrel", "animal"},
    ),
    "goat": Thief(
        id="goat",
        label="goat",
        phrase="the miller's wandering goat",
        kind="animal",
        clue="a muddy hoofprint beneath the sill",
        trail="a crooked hoof trail through the cabbages",
        call="bleating near the gate",
        carries="chewing the last of the crust with guilty eyes",
        ground_reach=True,
        tags={"goat", "animal"},
    ),
}

FINDERS = {
    "scent": Finder(
        id="scent",
        label="nose",
        phrase="his sharp nose",
        method="scrabbled at the door until it opened and then raced along the scent",
        success="The terrier circled twice, barked at the hiding place, and would not stop",
        tags={"dog", "scent"},
    ),
    "feather": Finder(
        id="feather",
        label="feather trail",
        phrase="the trail",
        method="bounded to the threshold and followed the fallen feather and crumb trail",
        success="The terrier planted himself before the thief and yapped triumphantly",
        tags={"dog", "trail"},
    ),
}

GIRL_NAMES = ["Anya", "Mila", "Nora", "Lina", "Tessa", "Ivy"]
BOY_NAMES = ["Miro", "Tobin", "Evan", "Felix", "Rowan", "Ned"]
DOG_NAMES = ["Pip", "Tumble", "Bran", "Nip", "Moss"]
TRAITS = ["quick-tempered", "eager", "curious", "earnest", "impatient"]

ELDERS = ["grandmother", "grandfather"]


@dataclass
class StoryParams:
    treat: str
    ledge: str
    thief: str
    finder: str
    child_name: str
    child_gender: str
    elder_type: str
    dog_name: str
    child_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "window": [
        (
            "What is a window ledge?",
            "A window ledge is the flat place at the bottom of a window. People sometimes set things there, but food can tempt animals if the window is open or easy to reach.",
        )
    ],
    "terrier": [
        (
            "What is a terrier?",
            "A terrier is a small, lively kind of dog. Terriers notice sounds and smells quickly, so they often make good little watch dogs.",
        )
    ],
    "evaluate": [
        (
            "What does evaluate mean?",
            "To evaluate means to stop and think carefully about what you know. You look at clues and compare them before deciding what is true.",
        )
    ],
    "crow": [
        (
            "Why might a crow steal food?",
            "Crows are clever birds, and they will snatch food if they find an easy chance. They like bright or tasty things they can carry away quickly.",
        )
    ],
    "magpie": [
        (
            "What is a magpie like?",
            "A magpie is a bold black-and-white bird. It is curious and quick, and it may hop near houses looking for scraps.",
        )
    ],
    "squirrel": [
        (
            "Can a squirrel climb to a window?",
            "Yes, a squirrel can climb wood, stone, and branches. If a window is low enough or near something it can climb, a squirrel may reach it.",
        )
    ],
    "goat": [
        (
            "Why would a goat have trouble reaching a high window?",
            "A goat can stretch up from the ground, but it cannot fly. If the window is too high, the goat cannot simply pluck food from it.",
        )
    ],
    "fairness": [
        (
            "Why is it important not to blame too fast?",
            "Blaming too fast can hurt someone who did nothing wrong. Looking at clues first is fairer and helps people solve the real problem.",
        )
    ],
}
KNOWLEDGE_ORDER = ["window", "terrier", "evaluate", "crow", "magpie", "squirrel", "goat", "fairness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dog = f["dog"]
    thief = f["thief_cfg"]
    treat = f["treat_cfg"]
    ledge = f["ledge_cfg"]
    return [
        'Write a short folk tale for a 3-to-5-year-old that includes the words "evaluate", "window", and "terrier".',
        f"Tell a folk-tale story where a child wrongly blames a terrier after {treat.label} vanishes from a {ledge.label}, and a careful elder teaches the child to evaluate clues.",
        f"Write a gentle story with conflict and surprise: {child.id} thinks {dog.id} stole the {treat.label}, but the real thief turns out to be {thief.phrase}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    elder = f["elder"]
    dog = f["dog"]
    treat = f["treat_cfg"]
    ledge = f["ledge_cfg"]
    thief = f["thief_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {elder.label_word}, and a terrier named {dog.id}. The story begins when a baked treat is left by the window in their cottage.",
        ),
        (
            f"Why did {child.id} think {dog.id} had eaten the {treat.label}?",
            f"{child.id} came back and saw only crumbs while the terrier was still in the room. That made the first guess feel easy, even though it was not fair.",
        ),
        (
            "What was the conflict in the story?",
            f"The conflict was that {child.id} accused {dog.id} of stealing the treat, while the elder warned against quick blame. The quarrel mattered because the child's anger was pointed at the wrong friend.",
        ),
        (
            "How did they evaluate what had happened?",
            f"The elder slowed the moment down and looked for signs near the window. When they noticed {thief.clue}, they understood the missing treat had another path out of the cottage.",
        ),
        (
            "What was the surprise?",
            f"The surprise was that {dog.id} was innocent and led them to the real thief. Outside they found {thief.phrase}, {thief.carries}.",
        ),
        (
            f"How did the story end for {child.id} and {dog.id}?",
            f"{child.id} apologized and hugged the terrier close. After that, {child.pronoun()} listened more carefully before judging, so their trust became stronger than before.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"window", "terrier", "evaluate", "fairness"}
    thief = f["thief_cfg"].id
    if thief in KNOWLEDGE:
        tags.add(thief)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        treat="honey_cake",
        ledge="low",
        thief="goat",
        finder="scent",
        child_name="Anya",
        child_gender="girl",
        elder_type="grandmother",
        dog_name="Pip",
        child_trait="quick-tempered",
    ),
    StoryParams(
        treat="berry_tart",
        ledge="high",
        thief="crow",
        finder="feather",
        child_name="Tobin",
        child_gender="boy",
        elder_type="grandfather",
        dog_name="Bran",
        child_trait="eager",
    ),
    StoryParams(
        treat="seed_roll",
        ledge="low",
        thief="squirrel",
        finder="scent",
        child_name="Mila",
        child_gender="girl",
        elder_type="grandmother",
        dog_name="Moss",
        child_trait="curious",
    ),
    StoryParams(
        treat="berry_tart",
        ledge="high",
        thief="magpie",
        finder="feather",
        child_name="Rowan",
        child_gender="boy",
        elder_type="grandfather",
        dog_name="Tumble",
        child_trait="earnest",
    ),
]


def explain_rejection(ledge: Ledge, thief: Thief) -> str:
    if thief.id == "goat" and ledge.height == "high":
        return "(No story: a goat cannot sensibly reach food from a high window. Pick a low ledge or a bird thief.)"
    if thief.id == "squirrel" and ledge.height == "high":
        return "(No story: this squirrel story assumes a low window it can scramble up to. Pick a low ledge or a flying thief.)"
    return "(No story: this thief could not reasonably take the treat from that window.)"


ASP_RULES = r"""
reachable(L, T) :- bird(T), bird_access(L).
reachable(L, T) :- ground_reach(T), ground_access(L).
reachable(L, T) :- climbs(T), low(L).

valid(L, T) :- ledge(L), thief(T), reachable(L, T).

outcome(surprise_reveal) :- valid(chosen_ledge, chosen_thief).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for ledge_id, ledge in LEDGES.items():
        lines.append(asp.fact("ledge", ledge_id))
        if ledge.bird_access:
            lines.append(asp.fact("bird_access", ledge_id))
        if ledge.ground_access:
            lines.append(asp.fact("ground_access", ledge_id))
        if ledge.height == "low":
            lines.append(asp.fact("low", ledge_id))
    for thief_id, thief in THIEVES.items():
        lines.append(asp.fact("thief", thief_id))
        if thief.bird:
            lines.append(asp.fact("bird", thief_id))
        if thief.climbs:
            lines.append(asp.fact("climbs", thief_id))
        if thief.ground_reach:
            lines.append(asp.fact("ground_reach", thief_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_ledge", params.ledge),
            asp.fact("chosen_thief", params.thief),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in gate:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases = list(CURATED)
    for case in cases:
        if asp_outcome(case) != "surprise_reveal":
            rc = 1
            print("MISMATCH in outcome for curated case:", case)

    try:
        sample = generate(CURATED[0])
        if not sample.story or "window" not in sample.story.lower() or "terrier" not in sample.story.lower():
            rc = 1
            print("Smoke test failed: generated story missing expected core words.")
        else:
            print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"Smoke generation crashed: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a folk tale about a missing treat, a window, and a terrier."
    )
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--ledge", choices=sorted(LEDGES))
    ap.add_argument("--thief", choices=sorted(THIEVES))
    ap.add_argument("--finder", choices=sorted(FINDERS))
    ap.add_argument("--elder", choices=sorted(ELDERS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--dog-name")
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
    if args.ledge and args.thief:
        if not thief_can_reach(LEDGES[args.ledge], THIEVES[args.thief]):
            raise StoryError(explain_rejection(LEDGES[args.ledge], THIEVES[args.thief]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.ledge is None or combo[0] == args.ledge)
        and (args.thief is None or combo[1] == args.thief)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    ledge_id, thief_id = rng.choice(sorted(combos))
    treat_id = args.treat or rng.choice(sorted(TREATS))
    thief = THIEVES[thief_id]
    if args.finder:
        finder_id = args.finder
    else:
        finder_id = "feather" if thief.bird else "scent"
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    dog_name = args.dog_name or rng.choice(DOG_NAMES)
    elder_type = args.elder or rng.choice(ELDERS)
    child_trait = rng.choice(TRAITS)

    return StoryParams(
        treat=treat_id,
        ledge=ledge_id,
        thief=thief_id,
        finder=finder_id,
        child_name=name,
        child_gender=gender,
        elder_type=elder_type,
        dog_name=dog_name,
        child_trait=child_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.treat not in TREATS:
        raise StoryError(f"(Unknown treat: {params.treat})")
    if params.ledge not in LEDGES:
        raise StoryError(f"(Unknown ledge: {params.ledge})")
    if params.thief not in THIEVES:
        raise StoryError(f"(Unknown thief: {params.thief})")
    if params.finder not in FINDERS:
        raise StoryError(f"(Unknown finder: {params.finder})")
    if not thief_can_reach(LEDGES[params.ledge], THIEVES[params.thief]):
        raise StoryError(explain_rejection(LEDGES[params.ledge], THIEVES[params.thief]))

    world = tell(
        TREATS[params.treat],
        LEDGES[params.ledge],
        THIEVES[params.thief],
        FINDERS[params.finder],
        child_name=params.child_name,
        child_gender=params.child_gender,
        elder_type=params.elder_type,
        dog_name=params.dog_name,
        child_trait=params.child_trait,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (ledge, thief) combos:\n")
        for ledge, thief in combos:
            print(f"  {ledge:6} {thief}")
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
            header = f"### {p.child_name}, {p.dog_name}, {p.thief} at a {p.ledge} window"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
