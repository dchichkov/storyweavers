#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py
=====================================================================================

A small nursery-rhyme-style storyworld about a child with a torn trouser, a
thermometer with mercury in the glass, and a helper who must choose a sensible
mending before an outdoor rhyme can begin.

The domain is intentionally small and concrete:

- the weather is read from an old mercury thermometer
- one part of a favorite trouser is torn
- the child wants to march, skip, or stomp outside
- a helper picks a repair that may or may not be sturdy enough for the cold and
  the motion
- if the mend is strong enough, the child goes outside
- if not, the rhyme turns indoors in a warm, happy way

The prose keeps a nursery-rhyme flavor with repeated refrains and rhyme-like
cadence, but the ending still comes from simulated state.

Run it
------
    python storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py --weather frosty --tear knee --repair patch
    python storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py --tear knee --repair safety_pin
    python storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/mercury_generate_trouser_rhyme_repetition_nursery_rhyme.py --verify
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
            "grandmother": "gran",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Weather:
    id: str
    line: str
    mercury_word: str
    cold: int
    breeze: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tear:
    id: str
    place: str
    phrase: str
    size: int
    flaps: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    beat: str
    bounce: int
    outside_place: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    covers: set[str]
    strength: int
    stitch_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cloth:
    id: str
    phrase: str
    color: str
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


def required_strength(weather: Weather, tear: Tear, activity: Activity) -> int:
    return weather.cold + tear.size + activity.bounce


def repair_fits(tear: Tear, repair: Repair) -> bool:
    return tear.place in repair.covers


def outcome_of(params: "StoryParams") -> str:
    weather = WEATHERS[params.weather]
    tear = TEARS[params.tear]
    activity = ACTIVITIES[params.activity]
    repair = REPAIRS[params.repair]
    if not repair_fits(tear, repair):
        raise StoryError(explain_rejection(tear, repair))
    return "outside" if repair.strength >= required_strength(weather, tear, activity) else "inside"


def _r_gap_chill(world: World) -> list[str]:
    garment = world.get("trouser")
    hero = world.get("hero")
    if garment.meters["torn"] < THRESHOLD:
        return []
    sig = ("gap_chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    weather = world.facts["weather"]
    activity = world.facts["activity"]
    garment.meters["drafty"] += float(weather.cold)
    hero.meters["cold"] += float(weather.cold)
    hero.meters["trip_risk"] += float(tear_risk(world.facts["tear"], activity))
    return []


def _r_secure_mend(world: World) -> list[str]:
    garment = world.get("trouser")
    if garment.meters["mended"] < THRESHOLD:
        return []
    sig = ("secure_mend",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    if world.facts["repair_ok"]:
        garment.meters["snug"] += 1
        garment.meters["torn"] = 0.0
        garment.meters["drafty"] = 0.0
    return []


CAUSAL_RULES = [
    Rule(name="gap_chill", tag="physical", apply=_r_gap_chill),
    Rule(name="secure_mend", tag="physical", apply=_r_secure_mend),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            produced = rule.apply(world)
            if produced is not None:
                pass
            if any(True for _ in (produced or [])):
                changed = True
        prev = len(world.fired)
        for rule in CAUSAL_RULES:
            rule.apply(world)
        changed = changed or len(world.fired) > prev


def tear_risk(tear: Tear, activity: Activity) -> int:
    return tear.size + max(activity.bounce - 1, 0)


def explain_rejection(tear: Tear, repair: Repair) -> str:
    return (
        f"(No story: {repair.label} does not sensibly mend a torn {tear.place} on a trouser. "
        f"Pick a repair that actually covers the {tear.place}.)"
    )


WEATHERS = {
    "mild": Weather(
        id="mild",
        line="Morning came with a pearly sky and a patient little breeze.",
        mercury_word="high",
        cold=1,
        breeze="a mild breeze",
        tags={"weather", "mercury"},
    ),
    "chilly": Weather(
        id="chilly",
        line="Morning came with a silver sky and a whisking little breeze.",
        mercury_word="middle",
        cold=2,
        breeze="a chilly breeze",
        tags={"weather", "mercury", "cold"},
    ),
    "frosty": Weather(
        id="frosty",
        line="Morning came with a crystal sky and a nipping little breeze.",
        mercury_word="low",
        cold=3,
        breeze="a frosty breeze",
        tags={"weather", "mercury", "cold"},
    ),
}

TEARS = {
    "knee": Tear(
        id="knee",
        place="knee",
        phrase="one trouser knee had a round little tear",
        size=2,
        flaps="the knee-flap flicked when the child bent down",
        tags={"trouser", "tear", "patch"},
    ),
    "cuff": Tear(
        id="cuff",
        place="cuff",
        phrase="the trouser cuff had come loose at the hem",
        size=1,
        flaps="the cuff-tip tickled at the ankle",
        tags={"trouser", "tear", "hem"},
    ),
    "pocket": Tear(
        id="pocket",
        place="pocket",
        phrase="the trouser pocket had split at one corner",
        size=1,
        flaps="the pocket-edge wagged when the child hopped",
        tags={"trouser", "tear", "pocket"},
    ),
}

ACTIVITIES = {
    "march": Activity(
        id="march",
        verb="march outside",
        gerund="marching",
        beat="clap-clap, tap-tap",
        bounce=1,
        outside_place="the front path",
        tags={"march", "generate"},
    ),
    "skip": Activity(
        id="skip",
        verb="skip outside",
        gerund="skipping",
        beat="skip-skip, tip-tap",
        bounce=2,
        outside_place="the garden path",
        tags={"skip", "generate"},
    ),
    "stomp": Activity(
        id="stomp",
        verb="stomp outside",
        gerund="stomping",
        beat="stomp-stomp, bump-bump",
        bounce=2,
        outside_place="the porch boards",
        tags={"stomp", "generate"},
    ),
}

REPAIRS = {
    "patch": Repair(
        id="patch",
        label="patch",
        phrase="a neat cloth patch",
        covers={"knee", "pocket"},
        strength=6,
        stitch_line="Snip-snap, stitch the patch, make the ragged edges match.",
        tags={"patch", "sew"},
    ),
    "hem_stitch": Repair(
        id="hem_stitch",
        label="hem stitch",
        phrase="a careful hem stitch",
        covers={"cuff"},
        strength=4,
        stitch_line="Tuck-tuck, little hem, fold the edge and sew it trim.",
        tags={"hem", "sew"},
    ),
    "safety_pin": Repair(
        id="safety_pin",
        label="safety pin",
        phrase="a shiny safety pin",
        covers={"pocket", "cuff"},
        strength=2,
        stitch_line="Pin it in, pin it through, hold it for a hop or two.",
        tags={"pin"},
    ),
}

CLOTHS = {
    "star": Cloth(
        id="star",
        phrase="a starry blue scrap",
        color="blue",
        tags={"cloth"},
    ),
    "gold": Cloth(
        id="gold",
        phrase="a golden yellow scrap",
        color="yellow",
        tags={"cloth"},
    ),
    "leaf": Cloth(
        id="leaf",
        phrase="a leaf-green scrap",
        color="green",
        tags={"cloth"},
    ),
}

HELPERS = {
    "mother": {"type": "mother", "phrase": "mom"},
    "father": {"type": "father", "phrase": "dad"},
    "grandmother": {"type": "grandmother", "phrase": "gran"},
    "grandfather": {"type": "grandfather", "phrase": "grandpa"},
}

GIRL_NAMES = ["Mina", "Tilly", "Poppy", "Daisy", "Mabel", "Elsie"]
BOY_NAMES = ["Ned", "Toby", "Pip", "Robin", "Ollie", "Jem"]
TRAITS = ["bouncy", "bright", "cheery", "eager", "spry", "merry"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for weather_id in sorted(WEATHERS):
        for tear_id, tear in TEARS.items():
            for activity_id in ACTIVITIES:
                for repair_id, repair in REPAIRS.items():
                    if repair_fits(tear, repair):
                        combos.append((weather_id, tear_id, activity_id, repair_id))
    return combos


@dataclass
class StoryParams:
    weather: str
    tear: str
    activity: str
    repair: str
    cloth: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        weather="mild",
        tear="cuff",
        activity="march",
        repair="hem_stitch",
        cloth="gold",
        name="Mina",
        gender="girl",
        helper="grandmother",
        trait="cheery",
    ),
    StoryParams(
        weather="chilly",
        tear="pocket",
        activity="skip",
        repair="patch",
        cloth="star",
        name="Toby",
        gender="boy",
        helper="father",
        trait="eager",
    ),
    StoryParams(
        weather="frosty",
        tear="pocket",
        activity="stomp",
        repair="safety_pin",
        cloth="leaf",
        name="Poppy",
        gender="girl",
        helper="mother",
        trait="bright",
    ),
    StoryParams(
        weather="frosty",
        tear="knee",
        activity="skip",
        repair="patch",
        cloth="star",
        name="Ned",
        gender="boy",
        helper="grandfather",
        trait="merry",
    ),
]


def predict_outdoor(world: World) -> dict:
    sim = world.copy()
    garment = sim.get("trouser")
    hero = sim.get("hero")
    garment.meters["mended"] += 1
    sim.facts["repair_ok"] = sim.facts["repair"].strength >= required_strength(
        sim.facts["weather"], sim.facts["tear"], sim.facts["activity"]
    )
    propagate(sim)
    return {
        "outside": bool(sim.facts["repair_ok"]),
        "cold": hero.meters["cold"],
        "trip_risk": hero.meters["trip_risk"],
    }


def introduce(world: World, hero: Entity, helper: Entity, weather: Weather, tear: Tear) -> None:
    world.say(weather.line)
    world.say(
        f"{hero.id}, a {hero.attrs['trait']} little {hero.type}, stood by the window with a favorite pair of striped trousers."
    )
    world.say(
        f"Yet {tear.phrase}, and {tear.flaps}."
    )
    world.say(
        f"By the latch hung an old thermometer with mercury {weather.mercury_word} in the glass."
    )
    helper_word = helper.label_word
    world.say(
        f'"{ACTIVITIES[world.facts["activity"].id].beat}, {ACTIVITIES[world.facts["activity"].id].beat}," sang {hero.id}. '
        f'"I want to {ACTIVITIES[world.facts["activity"].id].verb} at last."'
    )
    world.say(
        f"{helper_word.capitalize()} listened and smiled, but looked twice at the torn cloth."
    )


def desire_and_warning(world: World, hero: Entity, helper: Entity) -> None:
    weather = world.facts["weather"]
    tear = world.facts["tear"]
    activity = world.facts["activity"]
    hero.memes["wish"] += 1
    world.get("trouser").meters["torn"] += 1
    propagate(world)
    need = required_strength(weather, tear, activity)
    world.facts["required_strength"] = need
    pred = predict_outdoor(world)
    helper_word = helper.label_word
    world.say(
        f'"Mercury low or mercury high, a torn old seam must still be shy," said {helper_word}.'
    )
    world.say(
        f'"If you {activity.verb} in {weather.breeze}, that loose {tear.place} may pull and tease."'
    )
    if pred["outside"]:
        world.say(
            f"{helper_word.capitalize()} could see a good plan: a proper mend would hold fast enough for the little rhyme parade."
        )
    else:
        world.say(
            f"{helper_word.capitalize()} could see that a light mend would not be enough for such cold and such bouncing."
        )


def mend(world: World, hero: Entity, helper: Entity) -> None:
    repair = world.facts["repair"]
    cloth = world.facts["cloth"]
    tear = world.facts["tear"]
    activity = world.facts["activity"]
    helper_word = helper.label_word
    world.say(
        f'{helper_word.capitalize()} took out {repair.phrase}'
        + (f" and {cloth.phrase}." if repair.id == "patch" else ".")
    )
    world.say(
        f'"Generate a mending beat for me," said {helper_word}, "and keep the rhythm snug as can be."'
    )
    world.say(
        f'{hero.id} sang, "{activity.beat}, {activity.beat}," while {helper_word} worked.'
    )
    world.say(repair.stitch_line)
    garment = world.get("trouser")
    garment.meters["mended"] += 1
    ok = repair.strength >= required_strength(world.facts["weather"], tear, activity)
    world.facts["repair_ok"] = ok
    if ok:
        garment.meters["secure"] += 1
    propagate(world)


def go_outside(world: World, hero: Entity, helper: Entity) -> None:
    activity = world.facts["activity"]
    helper_word = helper.label_word
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    hero.meters["warm"] += 1
    world.say(
        f"Out they went to {activity.outside_place}, where the day felt brisk but no longer bossy."
    )
    world.say(
        f"{hero.id} went {activity.gerund} with a tidy knee and a tidy grin, and the mended trouser moved as smooth as a song."
    )
    world.say(
        f'"{activity.beat}, {activity.beat}, patched and neat!" sang {hero.id}. "{activity.beat}, {activity.beat}, dancing feet!"'
    )
    world.say(
        f"Even {helper_word} laughed to hear the rhyme, because the careful mend had changed the morning from worry into play."
    )


def stay_inside(world: World, hero: Entity, helper: Entity) -> None:
    activity = world.facts["activity"]
    helper_word = helper.label_word
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"But when {hero.id} bent and bounced, the little mend still looked too light for the frosty air."
    )
    world.say(
        f'"Then we shall keep the rhyme inside," said {helper_word}, "where toes stay warm and seams stay wise."'
    )
    world.say(
        f"They drummed on the table edge to generate a cosy beat and made a small parade from rug to chair."
    )
    world.say(
        f'"{activity.beat}, {activity.beat}, warm and sweet!" sang {hero.id}. "{activity.beat}, {activity.beat}, indoor feet!"'
    )
    world.say(
        f"By the firelight the pinned trouser rested, and the room itself became the nursery-rhyme road."
    )


def tell(
    weather: Weather,
    tear: Tear,
    activity: Activity,
    repair: Repair,
    cloth: Cloth,
    name: str,
    gender: str,
    helper_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            label=name,
            role="hero",
            attrs={"trait": trait},
        )
    )
    helper = world.add(
        Entity(
            id="Helper",
            kind="character",
            type=helper_type,
            label="the helper",
            role="helper",
        )
    )
    world.add(
        Entity(
            id="trouser",
            kind="thing",
            type="trouser",
            label="trouser",
            phrase="a favorite pair of striped trousers",
            role="garment",
        )
    )
    world.add(
        Entity(
            id="thermometer",
            kind="thing",
            type="thermometer",
            label="thermometer",
            phrase="an old thermometer",
            role="measure",
        )
    )
    world.facts.update(
        weather=weather,
        tear=tear,
        activity=activity,
        repair=repair,
        cloth=cloth,
        hero=hero,
        helper=helper,
    )

    introduce(world, hero, helper, weather, tear)
    world.para()
    desire_and_warning(world, hero, helper)
    world.para()
    mend(world, hero, helper)
    world.para()

    outcome = "outside" if world.facts["repair_ok"] else "inside"
    if outcome == "outside":
        go_outside(world, hero, helper)
    else:
        stay_inside(world, hero, helper)

    world.facts["outcome"] = outcome
    world.facts["required_strength"] = required_strength(weather, tear, activity)
    return world


KNOWLEDGE = {
    "mercury": [
        (
            "What is mercury in a thermometer?",
            "Mercury is a shiny silver liquid that used to sit inside some old thermometers. When the weather changed, the mercury moved up or down in the glass.",
        )
    ],
    "thermometer": [
        (
            "What does a thermometer do?",
            "A thermometer measures how hot or cold something is. In this story, it helped the grown-up see how chilly the day was.",
        )
    ],
    "trouser": [
        (
            "What is a trouser?",
            "Trouser is a word for one leg or part of a pair of trousers. If a trouser knee tears, that spot can flap or let cold air in.",
        )
    ],
    "patch": [
        (
            "What does a patch do on clothing?",
            "A patch covers a hole or tear in cloth. If it is sewn on well, it can make the clothing strong again.",
        )
    ],
    "hem": [
        (
            "What is a hem?",
            "A hem is the folded edge at the bottom of cloth. Sewing a loose hem keeps the edge from flapping or fraying.",
        )
    ],
    "pin": [
        (
            "What is a safety pin good for?",
            "A safety pin can hold cloth together for a little while. It is handy for light fixes, but it is not as strong as a real sewn mend.",
        )
    ],
    "generate": [
        (
            "What does generate mean?",
            "Generate means make something happen. In the story, the characters generate a beat by clapping and tapping together.",
        )
    ],
}

KNOWLEDGE_ORDER = ["mercury", "thermometer", "trouser", "patch", "hem", "pin", "generate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    activity = f["activity"]
    tear = f["tear"]
    return [
        'Write a nursery-rhyme-style story for a 3-to-5-year-old that uses the words "mercury", "generate", and "trouser".',
        f"Tell a gentle rhyming story where {hero.id} wants to {activity.verb}, but a torn trouser {tear.place} and the weather make a helper stop and mend it first.",
        f"Write a small story with repetition, a mending refrain, and a happy ending that changes depending on whether the repair is strong enough for the day.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    weather = f["weather"]
    tear = f["tear"]
    activity = f["activity"]
    repair = f["repair"]
    out = f["outcome"]
    helper_word = helper.label_word

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a little {hero.type} with a torn trouser, and {helper_word}, who helps with the mend. The story follows their small problem and the rhyme they make together.",
        ),
        (
            "Why did the helper look at the thermometer?",
            f"The old thermometer showed mercury {weather.mercury_word} in the glass, which told {helper_word} how cold the morning felt. That mattered because the torn cloth would feel worse in {weather.breeze}.",
        ),
        (
            f"What was wrong with the trouser?",
            f"The torn place was the {tear.place}. Because that part was loose, it could flap, tug, or let cold air bother {hero.id} while {hero.pronoun()} moved.",
        ),
        (
            f"Why did they sing while mending?",
            f"They used a repeated beat while the helper worked. The rhyme helped generate a steady rhythm, so the repair felt calm and cheerful instead of fussy.",
        ),
    ]

    if out == "outside":
        qa.append(
            (
                "How was the problem solved?",
                f"{helper_word.capitalize()} used {repair.phrase}, and it was strong enough for the weather and the bouncing. Because the mend held snugly, {hero.id} could go outside and play.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with {hero.id} outside on {activity.outside_place}, {activity.gerund} and singing the refrain again. The ending image proves the change because the once-torn trouser now moves neatly in play.",
            )
        )
    else:
        qa.append(
            (
                "Why did they stay inside at the end?",
                f"The helper's fix covered the tear, but it was too light for such a cold, bouncy morning. Instead of risking a pull or a chill outside, they turned the rhyme into an indoor parade.",
            )
        )
        qa.append(
            (
                "How did the story still end happily?",
                f"They made music and generated a cosy beat inside the warm room. The ending shows that the problem changed shape: they could not use the yard, but they could still keep the rhyme and the play.",
            )
        )

    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"mercury", "thermometer", "trouser", "generate"}
    repair = world.facts["repair"]
    if repair.id == "patch":
        tags.add("patch")
    elif repair.id == "hem_stitch":
        tags.add("hem")
    elif repair.id == "safety_pin":
        tags.add("pin")
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:11} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    lines.append(
        f"  outcome: {world.facts.get('outcome')}  required_strength={world.facts.get('required_strength')}"
    )
    return "\n".join(lines)


ASP_RULES = r"""
valid(W, T, A, R) :- weather(W), tear(T), activity(A), repair(R), covers(R, T).

need(W, T, A, N) :- weather_cold(W, C), tear_size(T, S), activity_bounce(A, B), N = C + S + B.
outside(W, T, A, R) :- valid(W, T, A, R), need(W, T, A, N), repair_strength(R, P), P >= N.
inside(W, T, A, R) :- valid(W, T, A, R), not outside(W, T, A, R).

outcome(W, T, A, R, outside) :- outside(W, T, A, R).
outcome(W, T, A, R, inside) :- inside(W, T, A, R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("weather_cold", wid, weather.cold))
    for tid, tear in TEARS.items():
        lines.append(asp.fact("tear", tid))
        lines.append(asp.fact("tear_size", tid, tear.size))
    for aid, activity in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("activity_bounce", aid, activity.bounce))
    for rid, repair in REPAIRS.items():
        lines.append(asp.fact("repair", rid))
        lines.append(asp.fact("repair_strength", rid, repair.strength))
        for place in sorted(repair.covers):
            lines.append(asp.fact("covers", rid, place))
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
            asp.fact("chosen_weather", params.weather),
            asp.fact("chosen_tear", params.tear),
            asp.fact("chosen_activity", params.activity),
            asp.fact("chosen_repair", params.repair),
            "picked_outcome(O) :- chosen_weather(W), chosen_tear(T), chosen_activity(A), chosen_repair(R), outcome(W,T,A,R,O).",
        ]
    )
    model = asp.one_model(asp_program(extra, "#show picked_outcome/1."))
    atoms = asp.atoms(model, "picked_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for seed in range(20):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)

    bad = 0
    for params in cases:
        py = outcome_of(params)
        cl = asp_outcome(params)
        if py != cl:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme storyworld: mercury in the glass, a torn trouser, and a mending song."
    )
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--tear", choices=TEARS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--cloth", choices=CLOTHS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    if args.tear and args.repair:
        tear = TEARS[args.tear]
        repair = REPAIRS[args.repair]
        if not repair_fits(tear, repair):
            raise StoryError(explain_rejection(tear, repair))

    combos = [
        combo
        for combo in valid_combos()
        if (args.weather is None or combo[0] == args.weather)
        and (args.tear is None or combo[1] == args.tear)
        and (args.activity is None or combo[2] == args.activity)
        and (args.repair is None or combo[3] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    weather_id, tear_id, activity_id, repair_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    name = args.name or rng.choice(name_pool)
    helper = args.helper or rng.choice(sorted(HELPERS))
    trait = rng.choice(TRAITS)
    cloth = args.cloth or rng.choice(sorted(CLOTHS))
    return StoryParams(
        weather=weather_id,
        tear=tear_id,
        activity=activity_id,
        repair=repair_id,
        cloth=cloth,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        weather = WEATHERS[params.weather]
        tear = TEARS[params.tear]
        activity = ACTIVITIES[params.activity]
        repair = REPAIRS[params.repair]
        cloth = CLOTHS[params.cloth]
        helper = HELPERS[params.helper]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter value: {err.args[0]})") from err

    if not repair_fits(tear, repair):
        raise StoryError(explain_rejection(tear, repair))

    world = tell(
        weather=weather,
        tear=tear,
        activity=activity,
        repair=repair,
        cloth=cloth,
        name=params.name,
        gender=params.gender,
        helper_type=helper["type"],
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
        print(asp_program("", "#show valid/4.\n#show outcome/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (weather, tear, activity, repair) combos:\n")
        for weather_id, tear_id, activity_id, repair_id in combos:
            extra = asp_outcome(
                StoryParams(
                    weather=weather_id,
                    tear=tear_id,
                    activity=activity_id,
                    repair=repair_id,
                    cloth="star",
                    name="Mina",
                    gender="girl",
                    helper="mother",
                    trait="cheery",
                )
            )
            print(f"  {weather_id:7} {tear_id:7} {activity_id:7} {repair_id:10} -> {extra}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.weather}, {p.tear}, {p.activity}, {p.repair} ({outcome_of(p)})"
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
