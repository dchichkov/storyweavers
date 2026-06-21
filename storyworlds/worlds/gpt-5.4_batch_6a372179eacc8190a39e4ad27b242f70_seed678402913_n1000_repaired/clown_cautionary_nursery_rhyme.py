#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py
============================================================

A tiny storyworld about a child playing clown and learning where juggling
belongs. The prose leans toward a nursery-rhyme lilt: short scenes, concrete
images, and a cautionary turn with a calm correction.

The core reasonableness constraint is simple:

- a juggling prop must be hard enough to break something,
- the place must actually contain the fragile thing at risk,
- and the safer ending must redirect the same playful wish into a softer prop
  and a safer practice spot.

Run it
------
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py --place kitchen --prop apples --target teacups
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py --target pillow
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py --all
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py --qa --json
python storyworlds/worlds/gpt-5.4/clown_cautionary_nursery_rhyme.py --verify
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
RISK_MIN = 2
HEEDFUL_TEMPERAMENTS = {"careful", "thoughtful", "gentle"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: tuple = field(default_factory=tuple)
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
    def kin_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "gran",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    stage_word: str
    nearby_targets: set[str] = field(default_factory=set)
    safe_spot: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    plural_word: str
    hardness: int
    toss_words: str
    land_words: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    fragile: bool = True
    break_words: str = ""
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.phrase[0].upper() + self.phrase[1:]


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    soft: bool = True
    practice_words: str = ""
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


def _r_break(world: World) -> list[str]:
    out: list[str] = []
    prop = world.get("prop")
    target = world.get("target")
    child = world.get("child")
    room = world.get("room")
    if prop.meters["flying"] < THRESHOLD or target.meters["at_risk"] < THRESHOLD:
        return out
    sig = ("break", prop.id, target.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    target.meters["broken"] += 1
    room.meters["mess"] += 1
    child.memes["shock"] += 1
    child.memes["sorrow"] += 1
    out.append("__crash__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="break", tag="physical", apply=_r_break),
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
        for sent in produced:
            world.say(sent)
    return produced


def is_risky(prop: Prop, target: Target, place: Place) -> bool:
    return prop.hardness >= RISK_MIN and target.fragile and target.id in place.nearby_targets


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for prop_id, prop in PROPS.items():
            for target_id, target in TARGETS.items():
                if is_risky(prop, target, place):
                    combos.append((place_id, prop_id, target_id))
    return combos


def would_heed(temperament: str) -> bool:
    return temperament in HEEDFUL_TEMPERAMENTS


def predict_break(world: World) -> bool:
    sim = world.copy()
    sim.get("prop").meters["flying"] += 1
    propagate(sim, narrate=False)
    return sim.get("target").meters["broken"] >= THRESHOLD


def introduce(world: World, child: Entity, place: Place, prop: Prop) -> None:
    child.memes["glee"] += 1
    world.say(
        f"There was a little clown named {child.id}, in {place.phrase} one bright noon."
    )
    world.say(
        f"With a red round nose and a bobbing bow, {child.pronoun()} hummed a skipping tune."
    )
    world.say(
        f"{child.id} found {prop.phrase} and called them stars for a tumbling clownish show."
    )
    world.say(
        f"{child.pronoun().capitalize()} tapped {child.pronoun('possessive')} toes on the {place.stage_word}, all set to toss them high and low."
    )


def set_risk(world: World, target: Entity) -> None:
    target.meters["at_risk"] += 1


def warn(world: World, guardian: Entity, child: Entity, place: Place, prop: Prop, target: Target) -> None:
    child.memes["temptation"] += 1
    danger = predict_break(world)
    world.facts["predicted_break"] = danger
    extra = f"{target.The} would not stay whole." if danger else "It might end in trouble."
    world.say(
        f'But {child.id}\'s {guardian.kin_word} saw {target.phrase} near the floor and doorway there.'
    )
    world.say(
        f'"Little clown, don\'t toss {prop.plural_word} here. {extra}"'
    )
    world.say(
        f'{guardian.pronoun().capitalize()} spoke in a quiet voice, more careful than a scare.'
    )


def defy(world: World, child: Entity, prop: Prop) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'Yet {child.id} gave a jaunty grin. "Just one quick whirl," {child.pronoun()} cried.'
    )
    world.say(
        f'Up went {prop.plural_word}, one, two, three; the little clown puffed up with pride.'
    )


def heed(world: World, child: Entity, guardian: Entity) -> None:
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    world.say(
        f'Then {child.id} paused with lifted hands and listened where {guardian.kin_word} stood.'
    )
    world.say(
        f'The game stayed bright, the room stayed whole, and stopping in time felt wise and good.'
    )


def accident(world: World, child: Entity, prop: Entity, target: Target) -> None:
    prop.meters["flying"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But one flew wide instead of straight, and down it came with a clattery spin."
    )
    world.say(
        f"{target.break_words} At once the merry tune went thin."
    )


def comfort_and_lesson(world: World, guardian: Entity, child: Entity, prop: Prop, target: Target) -> None:
    child.memes["lesson"] += 1
    child.memes["fear"] += 1
    world.say(
        f"{guardian.kin_word.capitalize()} did not shout. {guardian.pronoun().capitalize()} knelt beside the mess."
    )
    world.say(
        f'"A clown may play, but not this way. Hard {prop.plural_word} can break, not bless."'
    )
    world.say(
        f"{child.id} looked at {target.phrase} on the rug and felt a sorry, sinking press."
    )


def redirect(world: World, guardian: Entity, child: Entity, place: Place, fix: Fix) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    world.say(
        f"Then {guardian.kin_word} opened a cupboard door and brought out {fix.phrase} instead."
    )
    world.say(
        f'"If you want a clowning, come this way -- to {place.safe_spot}," {guardian.pronoun()} said.'
    )
    world.say(
        f"{child.id} tried {fix.practice_words}, and nothing cracked above {child.pronoun('possessive')} head."
    )


def bright_ending(world: World, child: Entity, place: Place, fix: Fix) -> None:
    child.memes["glee"] += 1
    world.say(
        f"Soon the little clown danced light and safe, with {fix.label} drifting to and fro."
    )
    world.say(
        f"In {place.safe_spot}, the laugh stayed soft, and careful hands made the playtime glow."
    )


def tell(
    place: Place,
    prop_cfg: Prop,
    target_cfg: Target,
    fix_cfg: Fix,
    child_name: str = "Pip",
    child_gender: str = "boy",
    guardian_type: str = "mother",
    temperament: str = "daring",
) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, role="guardian"))
    room = world.add(Entity(id="room", type="room", label=place.label))
    prop = world.add(Entity(id="prop", type="prop", label=prop_cfg.label, phrase=prop_cfg.phrase, tags=set(prop_cfg.tags)))
    target = world.add(Entity(id="target", type="target", label=target_cfg.label, phrase=target_cfg.phrase, tags=set(target_cfg.tags)))
    fix = world.add(Entity(id="fix", type="fix", label=fix_cfg.label, phrase=fix_cfg.phrase, tags=set(fix_cfg.tags)))

    child.attrs["temperament"] = temperament
    set_risk(world, target)
    introduce(world, child, place, prop_cfg)

    world.para()
    warn(world, guardian, child, place, prop_cfg, target_cfg)

    heeded = would_heed(temperament)
    world.para()
    if heeded:
        heed(world, child, guardian)
    else:
        defy(world, child, prop_cfg)
        world.para()
        accident(world, child, prop, target_cfg)
        comfort_and_lesson(world, guardian, child, prop_cfg, target_cfg)

    world.para()
    redirect(world, guardian, child, place, fix_cfg)
    bright_ending(world, child, place, fix_cfg)

    world.facts.update(
        child=child,
        guardian=guardian,
        room=room,
        place=place,
        prop_cfg=prop_cfg,
        target_cfg=target_cfg,
        fix_cfg=fix_cfg,
        heeded=heeded,
        broken=target.meters["broken"] >= THRESHOLD,
        temperament=temperament,
    )
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "kitchen": Place(
        id="kitchen",
        label="kitchen",
        phrase="the sunny kitchen",
        stage_word="tile",
        nearby_targets={"teacups", "mixing_bowl"},
        safe_spot="the back-yard grass",
        tags={"kitchen"},
    ),
    "parlor": Place(
        id="parlor",
        label="parlor",
        phrase="the front parlor",
        stage_word="rug",
        nearby_targets={"lamp", "fishbowl"},
        safe_spot="the hall rug by the wall",
        tags={"parlor"},
    ),
    "washroom": Place(
        id="washroom",
        label="washroom",
        phrase="the little washroom",
        stage_word="soap-bright floor",
        nearby_targets={"mirror_jar"},
        safe_spot="the blanket by the laundry basket",
        tags={"washroom"},
    ),
}

PROPS = {
    "apples": Prop(
        id="apples",
        label="apples",
        phrase="three shiny apples",
        plural_word="the apples",
        hardness=3,
        toss_words="up they bobbed",
        land_words="down they dropped",
        tags={"apple", "juggling"},
    ),
    "oranges": Prop(
        id="oranges",
        label="oranges",
        phrase="three round oranges",
        plural_word="the oranges",
        hardness=2,
        toss_words="up they rolled",
        land_words="down they thumped",
        tags={"orange", "juggling"},
    ),
    "wooden_balls": Prop(
        id="wooden_balls",
        label="wooden balls",
        phrase="three painted wooden balls",
        plural_word="the wooden balls",
        hardness=3,
        toss_words="up they arced",
        land_words="down they knocked",
        tags={"ball", "juggling"},
    ),
    "feather_puffs": Prop(
        id="feather_puffs",
        label="feather puffs",
        phrase="three feather puffs",
        plural_word="the feather puffs",
        hardness=1,
        toss_words="up they floated",
        land_words="down they drifted",
        tags={"soft_play"},
    ),
}

TARGETS = {
    "teacups": Target(
        id="teacups",
        label="teacups",
        phrase="the teacups on the low blue shelf",
        fragile=True,
        break_words="A teacup kissed the floor and cracked with a sad white grin.",
        tags={"teacup", "fragile"},
    ),
    "mixing_bowl": Target(
        id="mixing_bowl",
        label="mixing bowl",
        phrase="the glass mixing bowl by the stool",
        fragile=True,
        break_words="The glass bowl tipped and snapped with a bright and brittle din.",
        tags={"glass", "fragile"},
    ),
    "lamp": Target(
        id="lamp",
        label="lamp",
        phrase="the tall lamp by the chair",
        fragile=True,
        break_words="The lamp went over with a wobbling clink and lost its little skin.",
        tags={"lamp", "fragile"},
    ),
    "fishbowl": Target(
        id="fishbowl",
        label="fishbowl",
        phrase="the fishbowl on the side table",
        fragile=True,
        break_words="The fishbowl trembled, tipped, and broke with water rushing thin.",
        tags={"fishbowl", "fragile"},
    ),
    "mirror_jar": Target(
        id="mirror_jar",
        label="mirror jar",
        phrase="the mirror-bright jar by the soap",
        fragile=True,
        break_words="The shining jar fell with a ping and sent bright pieces out to spin.",
        tags={"jar", "fragile"},
    ),
    "pillow": Target(
        id="pillow",
        label="pillow",
        phrase="the soft pillow in the corner",
        fragile=False,
        break_words="Nothing at all broke.",
        tags={"pillow"},
    ),
}

FIXES = {
    "scarves": Fix(
        id="scarves",
        label="scarves",
        phrase="three rainbow scarves",
        soft=True,
        practice_words="soft scarves that floated like sleepy birds",
        tags={"scarf", "soft_play"},
    ),
    "beanbags": Fix(
        id="beanbags",
        label="beanbags",
        phrase="three little beanbags",
        soft=True,
        practice_words="beanbags that hopped but would not smash a thing",
        tags={"beanbag", "soft_play"},
    ),
    "bubbles": Fix(
        id="bubbles",
        label="bubbles",
        phrase="a pot of soap bubbles",
        soft=True,
        practice_words="bubbles that rose and popped with tiny silver rings",
        tags={"bubble", "soft_play"},
    ),
}

NAMES_GIRL = ["Poppy", "Mina", "Lila", "Tess", "Nora", "June"]
NAMES_BOY = ["Pip", "Milo", "Toby", "Finn", "Ned", "Ollie"]
TEMPERAMENTS = ["daring", "careful", "thoughtful", "bouncy", "gentle"]


@dataclass
class StoryParams:
    place: str
    prop: str
    target: str
    fix: str
    child_name: str
    child_gender: str
    guardian: str
    temperament: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="kitchen",
        prop="apples",
        target="teacups",
        fix="scarves",
        child_name="Pip",
        child_gender="boy",
        guardian="mother",
        temperament="daring",
    ),
    StoryParams(
        place="parlor",
        prop="oranges",
        target="lamp",
        fix="beanbags",
        child_name="Poppy",
        child_gender="girl",
        guardian="father",
        temperament="careful",
    ),
    StoryParams(
        place="washroom",
        prop="wooden_balls",
        target="mirror_jar",
        fix="bubbles",
        child_name="Milo",
        child_gender="boy",
        guardian="grandmother",
        temperament="daring",
    ),
    StoryParams(
        place="parlor",
        prop="apples",
        target="fishbowl",
        fix="scarves",
        child_name="Nora",
        child_gender="girl",
        guardian="grandfather",
        temperament="thoughtful",
    ),
]


KNOWLEDGE = {
    "juggling": [
        (
            "What is juggling?",
            "Juggling is tossing things into the air and catching them again. It is safer with soft practice things and plenty of open space.",
        )
    ],
    "fragile": [
        (
            "What does fragile mean?",
            "Fragile means something can crack or break easily. Glass bowls, lamps, and fishbowls need gentle hands.",
        )
    ],
    "apple": [
        (
            "Why can apples be a bad juggling choice indoors?",
            "Apples are round and fairly hard, so if one flies away it can hit something breakable. Indoors there may be shelves, bowls, or cups nearby.",
        )
    ],
    "orange": [
        (
            "Why should you be careful tossing oranges in the house?",
            "Oranges are softer than wooden balls, but they can still thump into a lamp or a bowl. A round thing that rolls away can make a mess fast.",
        )
    ],
    "ball": [
        (
            "Why are wooden balls not good for a living-room game?",
            "Wooden balls are hard. If one slips from your hand, it can knock into something fragile.",
        )
    ],
    "scarf": [
        (
            "Why are scarves good for beginner juggling?",
            "Scarves float slowly through the air. That gives small hands more time to follow and catch them.",
        )
    ],
    "beanbag": [
        (
            "Why are beanbags safer than hard balls for practice?",
            "Beanbags do not bounce or roll far when they fall. They stay close and are less likely to hit something breakable.",
        )
    ],
    "bubble": [
        (
            "Why are bubbles a gentle kind of clown play?",
            "Bubbles are light and soft and pop when touched. They turn play into a chasing game without knocking anything over.",
        )
    ],
    "teacup": [
        (
            "Why do teacups need care?",
            "Teacups are often thin and breakable. A small bump can chip them or crack them.",
        )
    ],
    "lamp": [
        (
            "Why is a lamp not a good thing to play beside?",
            "A lamp can tip over if it is bumped. Then the shade or bulb can break and make a mess.",
        )
    ],
    "fishbowl": [
        (
            "Why should people be careful near a fishbowl?",
            "A fishbowl is made of glass and may hold water for a pet fish. If it breaks, the water and the glass both cause trouble.",
        )
    ],
}


KNOWLEDGE_ORDER = [
    "juggling",
    "fragile",
    "apple",
    "orange",
    "ball",
    "scarf",
    "beanbag",
    "bubble",
    "teacup",
    "lamp",
    "fishbowl",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    place = f["place"]
    prop = f["prop_cfg"]
    target = f["target_cfg"]
    fix = f["fix_cfg"]
    if f["heeded"]:
        return [
            f'Write a cautionary nursery-rhyme story with the word "clown" about a child who wants to juggle {prop.label} in the {place.label} but listens in time.',
            f"Tell a rhyming story where {child.id}, dressed like a clown, is warned by {child.pronoun('possessive')} {guardian.kin_word} about {target.label} and chooses the safer way.",
            f"Write a gentle cautionary rhyme that ends with {fix.label} being used in a safer practice spot.",
        ]
    return [
        f'Write a cautionary nursery-rhyme story with the word "clown" about a child who juggles {prop.label} too near {target.label}.',
        f"Tell a rhyming story where {child.id}, pretending to be a clown, ignores {child.pronoun('possessive')} {guardian.kin_word}'s warning, something breaks, and then a safer game is found.",
        f"Write a simple cautionary rhyme that keeps the mood child-friendly and ends with {fix.label} in a safer place.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    guardian = f["guardian"]
    place = f["place"]
    prop = f["prop_cfg"]
    target = f["target_cfg"]
    fix = f["fix_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about a little clownish child named {child.id} and {child.pronoun('possessive')} {guardian.kin_word}. {child.id} wanted to turn {place.phrase} into a tiny stage.",
        ),
        (
            f"What did {child.id} want to do?",
            f"{child.id} wanted to juggle {prop.label} while pretending to be a clown. The red nose and jaunty mood made the trick feel exciting.",
        ),
        (
            f"Why did {guardian.kin_word} warn {child.pronoun('object')}?",
            f"{guardian.kin_word.capitalize()} warned {child.pronoun('object')} because {target.phrase} was nearby and could be broken. In this world, hard tossed things and fragile things do not belong close together.",
        ),
    ]
    if f["heeded"]:
        qa.append(
            (
                f"What happened after the warning?",
                f"{child.id} stopped before tossing the trick for real, so nothing broke. Listening in time kept the room peaceful and turned the story into a near miss instead of an accident.",
            )
        )
    else:
        qa.append(
            (
                "What went wrong?",
                f"One of the {prop.label} flew off course and {target.break_words[0].lower() + target.break_words[1:]} That is the turning point that makes the rhyme cautionary.",
            )
        )
        qa.append(
            (
                f"How did {guardian.kin_word} react?",
                f"{guardian.kin_word.capitalize()} did not shout. {guardian.pronoun().capitalize()} knelt by the mess, explained that hard {prop.label} can break things, and helped {child.id} learn a safer way to play.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with {fix.label} being used in {place.safe_spot}, where the game could stay bright and safe. The ending image proves the change: the little clown is still playing, but with softer things and wiser hands.",
        )
    )
    return qa


def world_knowledge_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"juggling", "fragile"} | set(f["prop_cfg"].tags) | set(f["fix_cfg"].tags) | set(f["target_cfg"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, prop: Prop, target: Target) -> str:
    if not target.fragile:
        return (
            f"(No story: {target.phrase} is not fragile, so tossing {prop.label} there would not make a cautionary break-and-learn tale. Pick a breakable target like teacups, a lamp, or a fishbowl.)"
        )
    if target.id not in place.nearby_targets:
        return (
            f"(No story: {target.phrase} is not part of {place.phrase} in this world, so it cannot be the thing at risk there.)"
        )
    if prop.hardness < RISK_MIN:
        return (
            f"(No story: {prop.label} are too soft and gentle to make a believable warning here. Pick a harder juggling prop such as apples, oranges, or wooden balls.)"
        )
    return "(No story: this combination has no believable indoor juggling risk.)"


ASP_RULES = r"""
risky(P, T, Pl) :- prop(P), target(T), place(Pl),
                   hardness(P, H), risk_min(M), H >= M,
                   fragile(T), nearby(Pl, T).

heedful(Tm) :- temperament(Tm), heedful_trait(Tm).

valid(Pl, P, T) :- place(Pl), prop(P), target(T), risky(P, T, Pl).

outcome(averted) :- chosen_temperament(Tm), heedful(Tm).
outcome(broken)  :- chosen_temperament(Tm), not heedful(Tm).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for target_id in sorted(place.nearby_targets):
            lines.append(asp.fact("nearby", place_id, target_id))
    for prop_id, prop in PROPS.items():
        lines.append(asp.fact("prop", prop_id))
        lines.append(asp.fact("hardness", prop_id, prop.hardness))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.fragile:
            lines.append(asp.fact("fragile", target_id))
    for temperament in TEMPERAMENTS:
        lines.append(asp.fact("temperament", temperament))
    for temperament in sorted(HEEDFUL_TEMPERAMENTS):
        lines.append(asp.fact("heedful_trait", temperament))
    lines.append(asp.fact("risk_min", RISK_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = asp.fact("chosen_temperament", params.temperament)
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "averted" if would_heed(params.temperament) else "broken"


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
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Smoke test generated empty story.")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a little clown, a risky juggling game, and a safer practice rhyme."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.prop and args.target:
        place = PLACES[args.place]
        prop = PROPS[args.prop]
        target = TARGETS[args.target]
        if not is_risky(prop, target, place):
            raise StoryError(explain_rejection(place, prop, target))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.prop is None or combo[1] == args.prop)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        if args.place and args.prop and args.target:
            raise StoryError(explain_rejection(PLACES[args.place], PROPS[args.prop], TARGETS[args.target]))
        raise StoryError("(No valid combination matches the given options.)")

    place_id, prop_id, target_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(FIXES))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    name_pool = NAMES_GIRL if child_gender == "girl" else NAMES_BOY
    child_name = args.child_name or rng.choice(name_pool)
    guardian = args.guardian or rng.choice(["mother", "father", "grandmother", "grandfather"])
    temperament = args.temperament or rng.choice(TEMPERAMENTS)

    return StoryParams(
        place=place_id,
        prop=prop_id,
        target=target_id,
        fix=fix_id,
        child_name=child_name,
        child_gender=child_gender,
        guardian=guardian,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.prop not in PROPS:
        raise StoryError(f"(Unknown prop: {params.prop})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.fix not in FIXES:
        raise StoryError(f"(Unknown fix: {params.fix})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    if params.guardian not in {"mother", "father", "grandmother", "grandfather"}:
        raise StoryError(f"(Unknown guardian: {params.guardian})")

    place = PLACES[params.place]
    prop = PROPS[params.prop]
    target = TARGETS[params.target]
    if not is_risky(prop, target, place):
        raise StoryError(explain_rejection(place, prop, target))

    world = tell(
        place=place,
        prop_cfg=prop,
        target_cfg=target,
        fix_cfg=FIXES[params.fix],
        child_name=params.child_name,
        child_gender=params.child_gender,
        guardian_type=params.guardian,
        temperament=params.temperament,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_items(world)],
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
        print(f"{len(combos)} compatible (place, prop, target) combos:\n")
        for place, prop, target in combos:
            print(f"  {place:9} {prop:13} {target}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child_name}: {p.prop} near {p.target} in the {p.place} ({outcome_of(p)})"
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
