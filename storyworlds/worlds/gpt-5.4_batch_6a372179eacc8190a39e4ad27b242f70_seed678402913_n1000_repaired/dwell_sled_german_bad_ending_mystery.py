#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dwell_sled_german_bad_ending_mystery.py
==================================================================

A small mystery storyworld about children following odd snow clues from their
dwelling with a sled toward an old cabin. The clues may truly point to a culprit
or may fade in weather, and the ending can be safe or bad depending on light,
weather, and timing.

Seed requirements carried through the rendered stories:
- the word "dwell" appears in the mystery question about the cabin
- a sled is part of the action
- "German" appears via a German shepherd

Run it
------
python storyworlds/worlds/gpt-5.4/dwell_sled_german_bad_ending_mystery.py
python storyworlds/worlds/gpt-5.4/dwell_sled_german_bad_ending_mystery.py --all
python storyworlds/worlds/gpt-5.4/dwell_sled_german_bad_ending_mystery.py --culprit german_shepherd --time dusk
python storyworlds/worlds/gpt-5.4/dwell_sled_german_bad_ending_mystery.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
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
class Setting:
    id: str
    place: str
    hill: str
    old_dwelling: str
    snow_depth: int
    storm_base: int
    track_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    missing_item: str
    missing_phrase: str
    owner_line: str
    clue_kind: str
    clue_text: str
    opening: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Culprit:
    id: str
    label: str
    phrase: str
    clue_kind: str
    motive: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    light: int
    warmth: int
    sense: int
    success_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


SETTINGS = {
    "pine_hollow": Setting(
        id="pine_hollow",
        place="Pine Hollow",
        hill="the pine hill beyond the fence",
        old_dwelling="an old gray cabin near the trees",
        snow_depth=3,
        storm_base=2,
        track_text="The yard held clear tracks and a pale path of churned snow.",
        tags={"snow", "cabin"},
    ),
    "river_lane": Setting(
        id="river_lane",
        place="River Lane",
        hill="the long lane above the frozen creek",
        old_dwelling="a lonely shed by the willow trees",
        snow_depth=2,
        storm_base=1,
        track_text="Fresh marks crossed the lane and bent toward the creek.",
        tags={"snow", "shed"},
    ),
    "mill_field": Setting(
        id="mill_field",
        place="Mill Field",
        hill="the white field behind the old mill",
        old_dwelling="a boarded hut beside the mill wall",
        snow_depth=3,
        storm_base=3,
        track_text="Wind had brushed the field, but one trail still cut across it.",
        tags={"snow", "hut"},
    ),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing_item="bell",
        missing_phrase="the little brass bell from the front latch",
        owner_line="Without it, the front latch looked strangely bare.",
        clue_kind="paw",
        clue_text="small paw prints",
        opening="That afternoon, someone noticed that the little brass bell from the front latch was gone.",
        tags={"bell", "paw"},
    ),
    "pie": Mystery(
        id="pie",
        missing_item="pie",
        missing_phrase="the round apple pie cooling on the window ledge",
        owner_line="The empty plate made the kitchen feel wrong at once.",
        clue_kind="paw",
        clue_text="paw prints and one sticky crumb",
        opening="Just before supper, the round apple pie cooling on the window ledge vanished.",
        tags={"pie", "paw"},
    ),
    "scarf": Mystery(
        id="scarf",
        missing_item="scarf",
        missing_phrase="the red wool scarf from the porch peg",
        owner_line="Its bright color had been part of the porch all winter.",
        clue_kind="thread",
        clue_text="a line of red wool threads",
        opening="At dusk, the red wool scarf from the porch peg could not be found.",
        tags={"scarf", "thread"},
    ),
}

CULPRITS = {
    "german_shepherd": Culprit(
        id="german_shepherd",
        label="German shepherd",
        phrase="a big German shepherd with snow on his back",
        clue_kind="paw",
        motive="He had grabbed the thing because it smelled interesting and carried it to his hiding place.",
        reveal="From inside came a low bark, then a thump of a tail against wood.",
        tags={"dog", "german", "paw"},
    ),
    "raven": Culprit(
        id="raven",
        label="raven",
        phrase="a glossy black raven with a crooked step",
        clue_kind="feather",
        motive="It liked shiny and bright things and had dragged the prize toward its nest.",
        reveal="A wing beat rattled the roof, and a black feather slid down the snow.",
        tags={"bird", "feather"},
    ),
    "goat": Culprit(
        id="goat",
        label="goat",
        phrase="a neighbor's goat with a rope trailing behind it",
        clue_kind="hoof",
        motive="It had nibbled and tugged at whatever smelled tasty or soft.",
        reveal="Something bumped the wall, and two curved shadows crossed the crack under the door.",
        tags={"goat", "hoof"},
    ),
    "wind": Culprit(
        id="wind",
        label="wind",
        phrase="the hard winter wind",
        clue_kind="drift",
        motive="No one had stolen anything at all; the wind had blown it farther downhill.",
        reveal="No creature waited inside. Only wind hissed through the boards.",
        tags={"wind", "drift"},
    ),
}

GEAR = {
    "lantern": Gear(
        id="lantern",
        label="lantern",
        phrase="a warm lantern",
        light=2,
        warmth=1,
        sense=3,
        success_text="The lantern made a yellow pool on the snow, and the clue trail stayed easy to read.",
        fail_text="The lantern glowed, but the wind kept swallowing its light at the edge of the field.",
        tags={"light", "lantern"},
    ),
    "flashlight": Gear(
        id="flashlight",
        label="flashlight",
        phrase="a bright flashlight",
        light=2,
        warmth=0,
        sense=3,
        success_text="The flashlight cut a neat white line over the tracks and the sled runners.",
        fail_text="The flashlight found bits of the trail, but blowing snow kept erasing the rest.",
        tags={"light", "flashlight"},
    ),
    "blanket": Gear(
        id="blanket",
        label="blanket",
        phrase="a thick blanket tucked over their knees",
        light=0,
        warmth=2,
        sense=2,
        success_text="The blanket kept the ride quiet and warm, though it offered no help for reading clues.",
        fail_text="The blanket held some heat, but it could not show them where the trail had gone.",
        tags={"blanket", "warmth"},
    ),
    "mittens": Gear(
        id="mittens",
        label="mittens",
        phrase="only their mittens",
        light=0,
        warmth=1,
        sense=1,
        success_text="The mittens kept stinging fingers from going numb at once.",
        fail_text="Their mittens were not enough against darkness and rising snow.",
        tags={"mittens", "warmth"},
    ),
}


def valid_pair(mystery: Mystery, culprit: Culprit) -> bool:
    return mystery.clue_kind == culprit.clue_kind


def sensible_gear() -> list[Gear]:
    return [g for g in GEAR.values() if g.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        if setting.snow_depth < 2:
            continue
        for mystery_id, mystery in MYSTERIES.items():
            for culprit_id, culprit in CULPRITS.items():
                if valid_pair(mystery, culprit):
                    combos.append((setting_id, mystery_id, culprit_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    culprit: str
    gear: str
    time: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    caution: str
    delay: int = 0
    seed: Optional[int] = None


TIME_CHOICES = ["afternoon", "dusk"]
CAUTION_TRAITS = ["careful", "steady", "thoughtful", "nervous", "bold"]

CURATED = [
    StoryParams(
        setting="pine_hollow",
        mystery="bell",
        culprit="german_shepherd",
        gear="mittens",
        time="dusk",
        child1="Mila",
        child1_gender="girl",
        child2="Ben",
        child2_gender="boy",
        parent="mother",
        caution="bold",
        delay=1,
    ),
    StoryParams(
        setting="river_lane",
        mystery="pie",
        culprit="german_shepherd",
        gear="lantern",
        time="afternoon",
        child1="Leo",
        child1_gender="boy",
        child2="Nora",
        child2_gender="girl",
        parent="father",
        caution="careful",
        delay=0,
    ),
    StoryParams(
        setting="mill_field",
        mystery="scarf",
        culprit="wind",
        gear="blanket",
        time="dusk",
        child1="Ava",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        parent="mother",
        caution="nervous",
        delay=1,
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Ava", "Ella", "Nora", "Rose", "Mila", "Zoe"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Eli"]


def storm_severity(setting: Setting, time: str, delay: int) -> int:
    return setting.storm_base + (1 if time == "dusk" else 0) + delay


def can_solve(gear: Gear, setting: Setting, time: str, delay: int) -> bool:
    need = storm_severity(setting, time, delay)
    capacity = gear.light + gear.warmth
    if time == "dusk" and gear.light < 1:
        return False
    return capacity >= need


def outcome_of(params: StoryParams) -> str:
    try:
        setting = SETTINGS[params.setting]
        mystery = MYSTERIES[params.mystery]
        culprit = CULPRITS[params.culprit]
        gear = GEAR[params.gear]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]})")
    if not valid_pair(mystery, culprit):
        return "invalid"
    return "solved" if can_solve(gear, setting, params.time, params.delay) else "lost"


def introduce(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["curiosity"] += 1
    world.say(
        f"{mystery.opening} {owner_line(mystery)} In their snowy dwelling at {setting.place}, "
        f"{a.id} and {b.id} stopped playing and stared at the empty place where it should have been."
    )
    world.say(setting.track_text)
    world.say(
        f"Near the steps lay {mystery.clue_text}, leading away from the house."
    )


def owner_line(mystery: Mystery) -> str:
    return mystery.owner_line


def question_the_cabin(world: World, a: Entity, b: Entity, setting: Setting) -> None:
    world.say(
        f'"Who could dwell in {setting.old_dwelling} this time of year?" {b.id} whispered.'
    )
    world.say(
        f"{a.id} looked toward {setting.hill}, where the snow seemed to keep its own secrets."
    )


def warn(world: World, parent: Entity, a: Entity, b: Entity, setting: Setting, gear: Gear, time: str) -> None:
    for kid in (a, b):
        kid.memes["warning"] += 1
    if time == "dusk":
        line = "It is getting dark, and the snow is deep enough to hide the path."
    else:
        line = "The hill is quiet now, but even quiet snow can swallow a trail."
    world.say(
        f'{parent.label_word.capitalize()} saw them eyeing the sled and said, "{line} '
        f'If you go, take {gear.phrase} and come straight back."'
    )


def depart(world: World, a: Entity, b: Entity, gear: Gear) -> None:
    sled = world.get("sled")
    sled.meters["distance"] += 1
    for kid in (a, b):
        kid.memes["resolve"] += 1
    world.say(
        f"They pulled the red sled to the gate, climbed on in turns, and pushed off into the squeaking snow."
    )
    world.say(gear.success_text if gear.light or gear.warmth else "")


def investigate(world: World, a: Entity, b: Entity, setting: Setting, culprit: Culprit, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.memes["fear"] += 1
    world.say(
        f"The trail led up toward {setting.old_dwelling}. Halfway there, the marks bent, crossed the sled runners, and slipped under a drift."
    )
    world.say(
        f"{culprit.reveal} For one breath, the whole mystery seemed ready to open."
    )


def solve_mystery(world: World, a: Entity, b: Entity, culprit: Culprit, mystery: Mystery, gear: Gear) -> None:
    found = world.get("missing")
    found.meters["recovered"] += 1
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["wonder"] += 1
    world.say(
        f"Inside they found {culprit.phrase} beside {mystery.missing_phrase}. {culprit.motive}"
    )
    world.say(
        f"{a.id} laughed first, then {b.id}. What had felt like a thief in the snow was only a muddled creature with a strange hiding place."
    )
    world.say(
        f"They set the lost {mystery.missing_item} on the sled and hurried home before the path changed."
    )
    world.say(
        f"Back at the dwelling, the mystery was solved, the house felt warm again, and the sled left one bright line all the way to the door."
    )


def lose_the_trail(world: World, a: Entity, b: Entity, setting: Setting, gear: Gear, culprit: Culprit, mystery: Mystery) -> None:
    sled = world.get("sled")
    sled.meters["stuck"] += 1
    for kid in (a, b):
        kid.meters["cold"] += 1
        kid.memes["fear"] += 1
        kid.memes["regret"] += 1
    world.say(gear.fail_text)
    world.say(
        f"Then the weather turned mean. Snow hissed sideways across {setting.hill}, and the clue trail broke apart under their boots."
    )
    world.say(
        f"They reached the dark boards at last, but the mystery did not open for them. {culprit.reveal} It was too little and too late."
    )
    world.say(
        f"When they tried to turn the sled back, one runner sank hard in a drift. The lost {mystery.missing_item} was nowhere to be seen."
    )


def bad_ending(world: World, a: Entity, b: Entity, parent: Entity, setting: Setting, mystery: Mystery) -> None:
    for kid in (a, b):
        kid.meters["cold"] += 1
        kid.memes["shame"] += 1
    world.say(
        f"They huddled behind the wall of {setting.old_dwelling} until neighbors found them by lantern light and led them home slowly, one hand on the rope of the sled."
    )
    world.say(
        f'No one scolded at first. {parent.label_word.capitalize()} only wrapped them in blankets and counted their fingers again and again.'
    )
    world.say(
        f"But the mystery stayed unsolved. By morning, the hill had smoothed itself flat, and the red sled stood half-buried by the door, while the missing {mystery.missing_item} was still gone."
    )


def tell(
    setting: Setting,
    mystery: Mystery,
    culprit: Culprit,
    gear: Gear,
    time: str,
    child1: str,
    child1_gender: str,
    child2: str,
    child2_gender: str,
    parent_type: str,
    caution: str,
    delay: int,
) -> World:
    world = World()
    a = world.add(Entity(id=child1, kind="character", type=child1_gender, role="lead"))
    b = world.add(Entity(id=child2, kind="character", type=child2_gender, role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    world.add(Entity(id="sled", type="sled", label="red sled", phrase="the red sled", tags={"sled"}))
    world.add(Entity(id="missing", type="missing", label=mystery.missing_item, phrase=mystery.missing_phrase))
    world.facts["setting_cfg"] = setting
    world.facts["mystery_cfg"] = mystery
    world.facts["culprit_cfg"] = culprit
    world.facts["gear_cfg"] = gear

    introduce(world, a, b, parent, setting, mystery)
    question_the_cabin(world, a, b, setting)

    world.para()
    warn(world, parent, a, b, setting, gear, time)
    depart(world, a, b, gear)
    investigate(world, a, b, setting, culprit, mystery)

    world.para()
    solved = can_solve(gear, setting, time, delay)
    if solved:
        solve_mystery(world, a, b, culprit, mystery, gear)
        outcome = "solved"
    else:
        lose_the_trail(world, a, b, setting, gear, culprit, mystery)
        bad_ending(world, a, b, parent, setting, mystery)
        outcome = "lost"

    world.facts.update(
        child1=a,
        child2=b,
        parent=parent,
        setting=setting,
        mystery=mystery,
        culprit=culprit,
        gear=gear,
        time=time,
        delay=delay,
        outcome=outcome,
        storm=storm_severity(setting, time, delay),
        solved=solved,
    )
    return world


KNOWLEDGE = {
    "sled": [
        (
            "What is a sled?",
            "A sled is something you slide over snow. People can ride on it or pull things with it across winter ground.",
        )
    ],
    "german": [
        (
            "What is a German shepherd?",
            "A German shepherd is a large kind of dog. It is known for being strong, smart, and good at following smells.",
        )
    ],
    "lantern": [
        (
            "Why is a lantern useful in snow?",
            "A lantern makes a warm circle of light, so people can see the path and each other in the dark. That matters even more when snow starts hiding tracks.",
        )
    ],
    "flashlight": [
        (
            "What does a flashlight help you do?",
            "A flashlight helps you see in dark places. It can show you a path, a clue, or a safe way home.",
        )
    ],
    "winter": [
        (
            "Why can snow make it hard to solve a mystery?",
            "Snow can cover tracks and change how places look. A clue that is clear one minute can be gone the next.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a problem with missing answers at first. You solve it by noticing clues and fitting them together carefully.",
        )
    ],
}

KNOWLEDGE_ORDER = ["sled", "german", "lantern", "flashlight", "winter", "mystery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting = f["setting"]
    mystery = f["mystery"]
    culprit = f["culprit"]
    gear = f["gear"]
    outcome = f["outcome"]
    base = (
        f'Write a snowy mystery for a young child that includes the words "dwell", "sled", and "German". '
        f"The story should begin with a missing {mystery.missing_item} at a dwelling and a clue in the snow."
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a mystery where two children ride a sled toward {setting.old_dwelling}, hoping to solve the missing {mystery.missing_item}, but the weather turns and the ending is bad.",
            f"Write a gentle but unhappy mystery in which a clue seems to point to {culprit.label}, yet darkness and weak gear keep the children from solving it before night.",
        ]
    return [
        base,
        f"Tell a winter mystery where two children follow clues by sled, find {culprit.phrase}, and solve the case safely with {gear.label}.",
        f"Write a simple mystery about a missing {mystery.missing_item} that turns out not to be as scary as it first seemed.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    mystery = f["mystery"]
    setting = f["setting"]
    culprit = f["culprit"]
    gear = f["gear"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "What was missing at the start of the story?",
            f"The missing thing was {mystery.missing_phrase}. Its absence made the dwelling feel strange right away.",
        ),
        (
            "What clue did the children find?",
            f"They found {mystery.clue_text} in the snow. That clue made them think someone or something had carried the missing {mystery.missing_item} away.",
        ),
        (
            "Why did the children take the sled?",
            f"They used the sled to go after the trail through the snow and to carry the missing thing back if they found it. The sled turned the search into a real winter journey.",
        ),
        (
            'Why did one child ask who could "dwell" in the old cabin or shed?',
            f"The old place looked lonely and secretive, so {b.id} wondered whether someone lived there and had taken the missing thing. The mystery felt bigger because the trail pointed straight toward that dark building.",
        ),
    ]
    if outcome == "solved":
        qa.append(
            (
                "Who had the missing thing, and why?",
                f"It was {culprit.phrase}. {culprit.motive}",
            )
        )
        qa.append(
            (
                "How was the mystery solved?",
                f"The children could still read the trail because they had enough help from {gear.label} for the weather. They reached the hiding place before the snow changed the path.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the missing {mystery.missing_item} back at home and the winter mystery explained. The final sled track leading to the door showed that the children had made it back in time.",
            )
        )
    else:
        qa.append(
            (
                "Why could the children not solve the mystery?",
                f"They set out when the weather and darkness were stronger than their gear could handle. The snow erased the clue trail, so by the time they reached the old place, the answer was already slipping away.",
            )
        )
        qa.append(
            (
                "What made the ending bad?",
                f"They became cold and lost precious time, and neighbors had to bring them home. The missing {mystery.missing_item} was still gone, so the mystery stayed open instead of ending in relief.",
            )
        )
        qa.append(
            (
                "What image shows that things ended badly?",
                f"The red sled standing half-buried by the door shows it. That picture proves the night won, the search failed, and the children came home shaken rather than proud.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"sled", "winter", "mystery"}
    culprit = world.facts["culprit"]
    gear = world.facts["gear"]
    if culprit.id == "german_shepherd":
        tags.add("german")
    if gear.id == "lantern":
        tags.add("lantern")
    if gear.id == "flashlight":
        tags.add("flashlight")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: outcome={world.facts.get('outcome')} storm={world.facts.get('storm')}")
    return "\n".join(lines)


def explain_pair(mystery: Mystery, culprit: Culprit) -> str:
    return (
        f"(No story: the clue for {mystery.missing_item} is {mystery.clue_kind}, "
        f"but {culprit.label} would leave {culprit.clue_kind}. The mystery's clues must point to a plausible culprit.)"
    )


def explain_gear(gear: Gear) -> str:
    better = ", ".join(sorted(g.id for g in sensible_gear()))
    return (
        f"(Refusing gear '{gear.id}': it scores too low on common sense "
        f"(sense={gear.sense} < {SENSE_MIN}) for a child mystery in snow. Try: {better}.)"
    )


ASP_RULES = r"""
snowworthy(S) :- setting(S), snow_depth(S, D), D >= 2.
valid_pair(M, C) :- mystery(M), culprit(C), clue_of(M, K), clue_of_culprit(C, K).
valid(S, M, C) :- snowworthy(S), valid_pair(M, C).

usable_gear(G) :- gear(G), sense(G, X), sense_min(M), X >= M.

storm(N) :- chosen_setting(S), snow_storm(S, B), chosen_delay(D), chosen_time(afternoon), N = B + D.
storm(N) :- chosen_setting(S), snow_storm(S, B), chosen_delay(D), chosen_time(dusk), N = B + 1 + D.

enough_light :- chosen_gear(G), light(G, L), L >= 1.
capacity(C) :- chosen_gear(G), light(G, L), warmth(G, W), C = L + W.

solved :- chosen_time(afternoon), capacity(C), storm(N), C >= N.
solved :- chosen_time(dusk), enough_light, capacity(C), storm(N), C >= N.

outcome(solved) :- solved.
outcome(lost) :- not solved.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        lines.append(asp.fact("snow_depth", setting_id, setting.snow_depth))
        lines.append(asp.fact("snow_storm", setting_id, setting.storm_base))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        lines.append(asp.fact("clue_of", mystery_id, mystery.clue_kind))
    for culprit_id, culprit in CULPRITS.items():
        lines.append(asp.fact("culprit", culprit_id))
        lines.append(asp.fact("clue_of_culprit", culprit_id, culprit.clue_kind))
    for gear_id, gear in GEAR.items():
        lines.append(asp.fact("gear", gear_id))
        lines.append(asp.fact("light", gear_id, gear.light))
        lines.append(asp.fact("warmth", gear_id, gear.warmth))
        lines.append(asp.fact("sense", gear_id, gear.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_usable_gear() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show usable_gear/1."))
    return sorted(g for (g,) in asp.atoms(model, "usable_gear"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_gear", params.gear),
            asp.fact("chosen_time", params.time),
            asp.fact("chosen_delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Snowy mystery storyworld: a missing thing, a sled, an old dwelling, and clues that may lead to a German shepherd or to trouble."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--time", choices=TIME_CHOICES)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1], help="extra delay before the weather turns")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery triples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mystery and args.culprit:
        mystery = MYSTERIES[args.mystery]
        culprit = CULPRITS[args.culprit]
        if not valid_pair(mystery, culprit):
            raise StoryError(explain_pair(mystery, culprit))
    if args.gear and GEAR[args.gear].sense < SENSE_MIN:
        raise StoryError(explain_gear(GEAR[args.gear]))

    combos = [
        combo
        for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.mystery is None or combo[1] == args.mystery)
        and (args.culprit is None or combo[2] == args.culprit)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, mystery_id, culprit_id = rng.choice(sorted(combos))
    gear_id = args.gear or rng.choice(sorted(g.id for g in sensible_gear()))
    time = args.time or rng.choice(TIME_CHOICES)
    child1, child1_gender = _pick_kid(rng)
    child2, child2_gender = _pick_kid(rng, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])
    caution = rng.choice(CAUTION_TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([0, 1])
    return StoryParams(
        setting=setting_id,
        mystery=mystery_id,
        culprit=culprit_id,
        gear=gear_id,
        time=time,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        parent=parent,
        caution=caution,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Invalid setting: {params.setting})")
    if params.mystery not in MYSTERIES:
        raise StoryError(f"(Invalid mystery: {params.mystery})")
    if params.culprit not in CULPRITS:
        raise StoryError(f"(Invalid culprit: {params.culprit})")
    if params.gear not in GEAR:
        raise StoryError(f"(Invalid gear: {params.gear})")

    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    culprit = CULPRITS[params.culprit]
    gear = GEAR[params.gear]

    if not valid_pair(mystery, culprit):
        raise StoryError(explain_pair(mystery, culprit))
    if gear.sense < SENSE_MIN:
        raise StoryError(explain_gear(gear))

    world = tell(
        setting=setting,
        mystery=mystery,
        culprit=culprit,
        gear=gear,
        time=params.time,
        child1=params.child1,
        child1_gender=params.child1_gender,
        child2=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
        caution=params.caution,
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid mystery combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    py_gear = {g.id for g in sensible_gear()}
    asp_gear = set(asp_usable_gear())
    if py_gear == asp_gear:
        print(f"OK: sensible gear matches ({sorted(py_gear)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible gear: python={sorted(py_gear)} clingo={sorted(asp_gear)}")

    cases = list(CURATED)
    parser = build_parser()
    for s in range(40):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(s))
        except StoryError:
            continue
        params.seed = s
        cases.append(params)

    mismatches = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "sled" not in sample.story.lower():
            raise StoryError("smoke test generated empty or malformed story")
        emit(sample, trace=False, qa=False, header="### smoke test")
        print("OK: smoke test generate/emit succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show usable_gear/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible gear: {', '.join(asp_usable_gear())}\n")
        print(f"{len(combos)} compatible (setting, mystery, culprit) combos:\n")
        for setting_id, mystery_id, culprit_id in combos:
            print(f"  {setting_id:12} {mystery_id:8} {culprit_id}")
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
            header = f"### {p.child1} & {p.child2}: {p.mystery} at {p.setting} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
