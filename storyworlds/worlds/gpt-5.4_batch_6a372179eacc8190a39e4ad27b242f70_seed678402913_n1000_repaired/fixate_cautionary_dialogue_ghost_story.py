#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py
====================================================================

A standalone story world for gentle, child-facing ghost-story variations built
around one caution: when something in the dark feels spooky, do not fixate on a
scary guess. Speak up, use safe light, and let a grown-up help check.

This world models a night-time scare with typed entities, physical meters, and
emotional memes. A strange sign in a room is paired with an ordinary cause. One
child starts to fixate on the idea of a ghost; a second child or cousin answers
with dialogue, and together they either:
- speak up, use safe light, and discover the harmless cause, or
- stay quiet too long, letting fear swell before a grown-up finally helps.

The stories stay in a ghost-story mood, but the simulation insists on an
ordinary cause and a sensible, safe resolution.

Run it
------
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --sign tapping --cause branch
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --cause moonbeam
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --response shout_adult
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/fixate_cautionary_dialogue_ghost_story.py --verify
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
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
            "aunt": "aunt",
            "uncle": "uncle",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    room: str
    opening: str
    bedtime_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    sense: str
    line: str
    ghost_guess: str
    pairs_with: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    phrase: str
    reveal: str
    motion: str
    matches: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    prompt: str
    action: str
    reveal_style: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"fixater", "steady"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
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


def _r_fixation_fear(world: World) -> list[str]:
    out: list[str] = []
    for kid in world.kids():
        if kid.memes["fixation"] < THRESHOLD:
            continue
        sig = ("fixation_fear", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        kid.memes["fear"] += 1
        out.append("__fear__")
    return out


def _r_room_dread(world: World) -> list[str]:
    out: list[str] = []
    if "room" not in world.entities:
        return out
    room = world.get("room")
    kids = world.kids()
    if not kids:
        return out
    if sum(k.memes["fear"] for k in kids) < THRESHOLD * 2:
        return out
    sig = ("room_dread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.memes["dread"] += 1
    out.append("__dread__")
    return out


def _r_light_relief(world: World) -> list[str]:
    out: list[str] = []
    if "lamp" not in world.entities:
        return out
    lamp = world.get("lamp")
    if lamp.meters["on"] < THRESHOLD:
        return out
    for kid in world.kids():
        sig = ("light_relief", kid.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if kid.memes["fear"] > 0:
            kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1.0)
        kid.memes["relief"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fixation_fear", tag="emotional", apply=_r_fixation_fear),
    Rule(name="room_dread", tag="emotional", apply=_r_room_dread),
    Rule(name="light_relief", tag="emotional", apply=_r_light_relief),
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


def plausible(sign: Sign, cause: Cause) -> bool:
    return cause.id in sign.pairs_with and sign.id in cause.matches


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def fear_level(delay: int) -> int:
    return 1 + delay


def is_quick_response(response: Response, delay: int) -> bool:
    return response.sense >= fear_level(delay)


def explain_rejection(sign: Sign, cause: Cause) -> str:
    return (
        f"(No story: {cause.phrase} would not make {sign.label}. "
        f"This world only tells ordinary-cause ghost stories where the sign and "
        f"the revealed cause really fit each other.)"
    )


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it scores too low on common sense "
        f"(sense={response.sense} < {SENSE_MIN}). In this world, children should "
        f"speak up or use safe light with help. Try: {better}.)"
    )


def predict_spook(world: World) -> dict:
    sim = world.copy()
    fixater = sim.get("fixater")
    fixater.memes["fixation"] += 1
    propagate(sim, narrate=False)
    return {
        "fear": fixater.memes["fear"],
        "dread": sim.get("room").memes["dread"],
    }


def introduce(world: World, a: Entity, b: Entity, adult: Entity) -> None:
    world.say(
        f"{world.setting.opening} {a.id} and {b.id} were meant to be settling down "
        f"for the night while {adult.label_word} finished the last quiet jobs of bedtime."
    )
    world.say(world.setting.bedtime_line)


def first_sign(world: World, sign: Sign) -> None:
    room = world.get("room")
    room.meters["strange"] += 1
    world.say(
        f"Then the room changed. {sign.line} It was only a small thing, but in the dark it sounded bigger."
    )


def fixate(world: World, a: Entity, sign: Sign) -> None:
    a.memes["fixation"] += 1
    a.memes["fear"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{a.id} sat up fast. "{sign.ghost_guess}" {a.pronoun()} whispered. '
        f'{a.pronoun().capitalize()} began to fixate on that thought until every shadow seemed to lean closer.'
    )


def answer(world: World, b: Entity, a: Entity, sign: Sign) -> None:
    pred = predict_spook(world)
    b.memes["care"] += 1
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_dread"] = pred["dread"]
    extra = ""
    if pred["dread"] >= THRESHOLD:
        extra = " The whole room would feel scarier if they kept feeding the idea."
    world.say(
        f'"Maybe not," {b.id} said softly. "Let\'s not fixate on a ghost guess. '
        f'{sign.sense.capitalize()} can come from something ordinary in the dark."{extra}'
    )


def wait_too_long(world: World, a: Entity, b: Entity, delay: int) -> None:
    for _ in range(delay):
        a.memes["fear"] += 1
        b.memes["fear"] += 1
    if delay > 0:
        room = world.get("room")
        room.memes["dread"] += 1
    if delay == 1:
        world.say(
            "For one long moment, neither child moved. The hush in the room felt thick, and the sound came again."
        )
    elif delay >= 2:
        world.say(
            "They stayed frozen through two long moments. Each time the sound came back, their blankets crept higher and the dark felt deeper."
        )


def ask_for_help(world: World, a: Entity, b: Entity, adult: Entity, response: Response) -> None:
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.say(
        f'{response.prompt} "{adult.label_word.capitalize()}?" {b.id} called. '
        f'"We heard something." {a.id} swallowed and added, "And it sounds spooky."'
    )


def reveal(world: World, adult: Entity, cause: Cause, response: Response, quick: bool) -> None:
    lamp = world.get("lamp")
    lamp.meters["on"] += 1
    propagate(world, narrate=False)
    pace = "right away" if quick else "after hearing the worry in their voices"
    world.say(
        f"{adult.label_word.capitalize()} came {pace} and {response.action}. {response.reveal_style} {cause.reveal}"
    )
    world.say(
        f'"See?" {adult.label_word.capitalize()} said. "It is only {cause.phrase}. '
        f'Night can make ordinary things look and sound strange."'
    )


def settle(world: World, a: Entity, b: Entity, adult: Entity, cause: Cause, quick: bool) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["lesson"] += 1
        kid.memes["fear"] = 0.0
    if quick:
        world.say(
            f'{a.id} let out a shaky laugh. "{cause.label} was the ghost all along," {a.pronoun()} said.'
        )
    else:
        world.say(
            f"{a.id} pressed a hand to {a.pronoun('possessive')} chest and let out a slow breath. "
            f"The scary feeling had grown big, but the answer was small and real."
        )
    world.say(
        f'"Next time," {adult.label_word} said, tucking the blankets smooth, '
        f'"do not feed a spooky guess. If something worries you, speak up and let light in."'
    )
    world.say(
        f"Soon the room looked like a room again, not a haunted place at all, and {a.id} and {b.id} listened to the house settle without fear."
    )


def tell(
    setting: Setting,
    sign: Sign,
    cause: Cause,
    response: Response,
    fixer_name: str = "Nora",
    fixer_gender: str = "girl",
    steady_name: str = "Ben",
    steady_gender: str = "boy",
    adult_type: str = "mother",
    relation: str = "siblings",
    delay: int = 0,
    fixer_trait: str = "imaginative",
    steady_trait: str = "calm",
) -> World:
    world = World(setting)
    a = world.add(Entity(
        id="fixater",
        kind="character",
        type=fixer_gender,
        label=fixer_name,
        role="fixater",
        traits=[fixer_trait],
        attrs={"name": fixer_name, "relation": relation},
    ))
    b = world.add(Entity(
        id="steady",
        kind="character",
        type=steady_gender,
        label=steady_name,
        role="steady",
        traits=[steady_trait],
        attrs={"name": steady_name, "relation": relation},
    ))
    adult = world.add(Entity(
        id="adult",
        kind="character",
        type=adult_type,
        label="the adult",
        role="adult",
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=setting.room,
        phrase=setting.room,
        tags=set(setting.tags),
    ))
    world.add(Entity(
        id="lamp",
        type="lamp",
        label="lamp",
        phrase="the bedside lamp",
    ))
    source = world.add(Entity(
        id="source",
        type="source",
        label=cause.label,
        phrase=cause.phrase,
        tags=set(cause.tags),
    ))
    source.meters["present"] = 1

    introduce(world, a, b, adult)
    world.para()
    first_sign(world, sign)
    fixate(world, a, sign)
    answer(world, b, a, sign)

    if delay > 0:
        wait_too_long(world, a, b, delay)

    world.para()
    ask_for_help(world, a, b, adult, response)
    quick = is_quick_response(response, delay)
    reveal(world, adult, cause, response, quick)

    world.para()
    settle(world, a, b, adult, cause, quick)

    outcome = "quick" if quick else "late"
    world.facts.update(
        setting=setting,
        sign=sign,
        cause_cfg=cause,
        response=response,
        fixater=a,
        steady=b,
        adult=adult,
        source=source,
        delay=delay,
        outcome=outcome,
        relation=relation,
        lesson=True,
    )
    return world


SETTINGS = {
    "bedroom": Setting(
        id="bedroom",
        room="the bedroom",
        opening="The house had gone hushed, and the moon had thinned to a pale stripe outside the curtains.",
        bedtime_line="The blanket cave around their pillows felt warm, but the corners of the room were full of old-night shadows.",
        tags={"bedroom", "night"},
    ),
    "guest_room": Setting(
        id="guest_room",
        room="the guest room",
        opening="In the guest room at Grandma's house, the floorboards gave small sleepy sighs and the window glass held a dim silver glow.",
        bedtime_line="A quilt lay heavy over the bed, and every chair and coat hook looked stranger after dark.",
        tags={"bedroom", "night"},
    ),
    "attic_room": Setting(
        id="attic_room",
        room="the attic room",
        opening="At the top of the house, the attic room seemed tucked under the roof like a secret.",
        bedtime_line="The slanted ceiling and old trunk made the shadows feel long and story-shaped.",
        tags={"attic", "night"},
    ),
}

SIGNS = {
    "tapping": Sign(
        id="tapping",
        label="a tapping at the window",
        sense="a tapping at the window",
        line="From the window came a light tap ... tap-tap ... as if tiny knuckles were trying the glass",
        ghost_guess="Did you hear that? Something is tapping to come in.",
        pairs_with={"branch"},
        tags={"window", "sound"},
    ),
    "fluttering": Sign(
        id="fluttering",
        label="a fluttering shape by the curtain",
        sense="a fluttering shape by the curtain",
        line="Near the curtain, a pale shape gave a soft flap and twist, as if it had drifted loose from nowhere",
        ghost_guess="There is a ghost by the curtain.",
        pairs_with={"sheet"},
        tags={"curtain", "shape"},
    ),
    "glowing": Sign(
        id="glowing",
        label="a small glowing face on the shelf",
        sense="a small glowing face on the shelf",
        line="On the shelf, two round dots and a crooked grin glimmered faintly in the dark",
        ghost_guess="A ghost face is watching us.",
        pairs_with={"clock"},
        tags={"glow", "shape"},
    ),
    "creaking": Sign(
        id="creaking",
        label="a long creak above the bed",
        sense="a long creak above the bed",
        line="Above them, the ceiling gave a slow complaining creak, like careful steps crossing the dark",
        ghost_guess="Something is walking on the roof.",
        pairs_with={"rafters"},
        tags={"sound", "roof"},
    ),
}

CAUSES = {
    "branch": Cause(
        id="branch",
        label="the branch",
        phrase="a windy branch brushing the glass",
        reveal="Outside, a thin branch was bowing in the wind and tapping the pane with its leaves.",
        motion="brushes and taps",
        matches={"tapping"},
        tags={"branch", "wind", "window"},
    ),
    "sheet": Cause(
        id="sheet",
        label="the laundry sheet",
        phrase="a laundry sheet hung too close to the curtain",
        reveal="A white sheet on the drying rack had slipped free at one corner and was fluttering whenever the vent breathed.",
        motion="flutters",
        matches={"fluttering"},
        tags={"sheet", "laundry", "curtain"},
    ),
    "clock": Cause(
        id="clock",
        label="the toy clock",
        phrase="a toy clock with glow-in-the-dark numbers",
        reveal="The little toy clock on the shelf had two glowing buttons and a curved line of numbers that looked like a face from far away.",
        motion="glows",
        matches={"glowing"},
        tags={"clock", "glow"},
    ),
    "rafters": Cause(
        id="rafters",
        label="the rafters",
        phrase="old rafters settling in the cool night air",
        reveal="The roof beams gave another long creak as the night air cooled them, and then they went still again.",
        motion="creaks",
        matches={"creaking"},
        tags={"roof", "wood", "night"},
    ),
    "moonbeam": Cause(
        id="moonbeam",
        label="the moonbeam",
        phrase="a moonbeam on the wall",
        reveal="A bar of moonlight lay across the wall, bright and plain.",
        motion="glows",
        matches=set(),
        tags={"moon", "light"},
    ),
}

RESPONSES = {
    "switch_on": Response(
        id="switch_on",
        sense=3,
        prompt="Together they scooted closer instead of hiding under the blankets.",
        action="clicked on the bedside lamp",
        reveal_style="Warm light spread over the room.",
        qa_text="turned on the lamp and showed them the ordinary cause",
        tags={"lamp", "light"},
    ),
    "shout_adult": Response(
        id="shout_adult",
        sense=2,
        prompt="They did not try to creep through the dark by themselves.",
        action="opened the door and turned on the hall light",
        reveal_style="A clean stripe of light fell across the floorboards.",
        qa_text="turned on the hall light and checked with them",
        tags={"light", "hall"},
    ),
    "hide_under_blanket": Response(
        id="hide_under_blanket",
        sense=1,
        prompt="They pulled the blanket over both heads and waited in a shaky little heap.",
        action="lifted the blanket edge at last",
        reveal_style="The dark still looked dark, and the room had not become any safer for waiting.",
        qa_text="waited under the blanket instead of getting help right away",
        tags={"blanket", "delay"},
    ),
}

GIRL_NAMES = ["Nora", "Lily", "Mia", "Zoe", "Eva", "Clara", "Lucy", "Anna"]
BOY_NAMES = ["Ben", "Leo", "Max", "Sam", "Finn", "Noah", "Eli", "Theo"]
TRAITS_FIXATER = ["imaginative", "dreamy", "sensitive", "curious"]
TRAITS_STEADY = ["calm", "careful", "steady", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for setting_id in SETTINGS:
        for sign_id, sign in SIGNS.items():
            for cause_id, cause in CAUSES.items():
                if plausible(sign, cause):
                    combos.append((setting_id, sign_id, cause_id))
    return combos


@dataclass
class StoryParams:
    setting: str
    sign: str
    cause: str
    response: str
    fixater_name: str
    fixater_gender: str
    steady_name: str
    steady_gender: str
    adult: str
    relation: str
    delay: int = 0
    fixater_trait: str = "imaginative"
    steady_trait: str = "calm"
    seed: Optional[int] = None


KNOWLEDGE = {
    "ghost_guess": [
        (
            "What should you do if your mind jumps to a scary ghost idea at night?",
            "Do not fixate on the scary guess. Take a breath, speak up, and ask a grown-up to help you check what is really there."
        )
    ],
    "window": [
        (
            "Why can a branch make spooky sounds on a window?",
            "When the wind moves a branch, it can tap the glass again and again. In the dark, that small sound can seem much bigger than it really is."
        )
    ],
    "curtain": [
        (
            "Why can a sheet or curtain look spooky at night?",
            "Soft cloth moves in strange shapes when air pushes it. In dim light, your eyes may mistake that motion for something alive."
        )
    ],
    "glow": [
        (
            "Why do glow-in-the-dark things look different at night?",
            "When the room is dark, even a tiny glow stands out strongly. Your brain may turn a few bright spots into a face or a figure."
        )
    ],
    "roof": [
        (
            "Why do old houses creak at night?",
            "Wood can shift a little as the air cools and the house settles. Those creaks can sound mysterious even when nothing is wrong."
        )
    ],
    "light": [
        (
            "Why does turning on a light help when something seems scary?",
            "Light shows shapes, corners, and objects clearly. When you can see better, your brain does not have to guess so much."
        )
    ],
    "call_adult": [
        (
            "Why is it smart to call a grown-up when something feels scary?",
            "A grown-up can help check safely and calmly. Asking for help is a brave way to learn what is really happening."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost_guess", "window", "curtain", "glow", "roof", "light", "call_adult"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two cousins"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["fixater"]
    b = f["steady"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    return [
        'Write a gentle ghost-story scene for a 3-to-5-year-old that includes the word "fixate" and lots of dialogue.',
        f"Tell a cautionary bedtime story where {a.label} hears {sign.label}, starts to imagine a ghost, and {b.label} says not to fixate on the spooky idea.",
        f"Write a story with a ghost-story mood but an ordinary ending: the children ask for help, a light comes on, and {cause.phrase} is revealed."
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["fixater"]
    b = f["steady"]
    adult = f["adult"]
    sign = f["sign"]
    cause = f["cause_cfg"]
    response = f["response"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.label} and {b.label}, and their {adult.label_word}. They are in the dark when something ordinary sounds spooky."
        ),
        (
            f"What scared {a.label} at first?",
            f"{a.label} heard or saw {sign.label} and guessed it might be a ghost. The dark made that small sign feel much bigger and stranger."
        ),
        (
            f"What did {b.label} say when {a.label} got scared?",
            f"{b.label} told {a.label} not to fixate on the ghost guess. {b.pronoun().capitalize()} reminded {a.pronoun('object')} that strange night sounds and shapes can have ordinary causes."
        ),
        (
            "How did they find out the truth?",
            f"They spoke up and got help instead of sneaking around in the dark alone. Their {adult.label_word} {response.qa_text}, and then they could see it was really {cause.phrase}."
        ),
    ]
    if f["outcome"] == "late":
        qa.append(
            (
                "Did waiting quietly help?",
                "No. Waiting made the fear feel bigger before the answer came. The story warns that feeding a spooky guess can make a harmless problem feel much worse."
            )
        )
    else:
        qa.append(
            (
                "What changed at the end?",
                f"The room stopped feeling haunted as soon as the truth was clear. Once the light came on, {a.label} and {b.label} could hear the same house sounds without being afraid."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"ghost_guess", "call_adult"}
    sign = world.facts["sign"]
    cause = world.facts["cause_cfg"]
    response = world.facts["response"]
    for tag in sign.tags | cause.tags | response.tags:
        if tag in {"window", "curtain", "glow", "roof", "light"}:
            tags.add(tag)
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
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="bedroom",
        sign="tapping",
        cause="branch",
        response="switch_on",
        fixater_name="Nora",
        fixater_gender="girl",
        steady_name="Ben",
        steady_gender="boy",
        adult="mother",
        relation="siblings",
        delay=0,
        fixater_trait="imaginative",
        steady_trait="calm",
    ),
    StoryParams(
        setting="guest_room",
        sign="fluttering",
        cause="sheet",
        response="shout_adult",
        fixater_name="Mia",
        fixater_gender="girl",
        steady_name="Lucy",
        steady_gender="girl",
        adult="aunt",
        relation="cousins",
        delay=1,
        fixater_trait="dreamy",
        steady_trait="careful",
    ),
    StoryParams(
        setting="attic_room",
        sign="glowing",
        cause="clock",
        response="switch_on",
        fixater_name="Max",
        fixater_gender="boy",
        steady_name="Theo",
        steady_gender="boy",
        adult="father",
        relation="siblings",
        delay=0,
        fixater_trait="sensitive",
        steady_trait="thoughtful",
    ),
    StoryParams(
        setting="bedroom",
        sign="creaking",
        cause="rafters",
        response="shout_adult",
        fixater_name="Anna",
        fixater_gender="girl",
        steady_name="Leo",
        steady_gender="boy",
        adult="mother",
        relation="siblings",
        delay=2,
        fixater_trait="curious",
        steady_trait="steady",
    ),
]


def outcome_of(params: StoryParams) -> str:
    return "quick" if is_quick_response(RESPONSES[params.response], params.delay) else "late"


ASP_RULES = r"""
% --- compatibility gate ----------------------------------------------------
plausible(S, C) :- sign(S), cause(C), sign_pairs(S, C), cause_matches(C, S).
sensible(R)     :- response(R), sense(R, V), sense_min(M), V >= M.
valid(St, S, C) :- setting(St), plausible(S, C), sensible(_).

% --- outcome model ---------------------------------------------------------
fear_need(1 + D) :- delay(D).
quick            :- chosen_response(R), sense(R, V), fear_need(N), V >= N.
outcome(quick)   :- quick.
outcome(late)    :- not quick.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for sign_id, sign in SIGNS.items():
        lines.append(asp.fact("sign", sign_id))
        for cause_id in sorted(sign.pairs_with):
            lines.append(asp.fact("sign_pairs", sign_id, cause_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        for sign_id in sorted(cause.matches):
            lines.append(asp.fact("cause_matches", cause_id, sign_id))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


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

    c_sens = set(asp_sensible())
    p_sens = {r.id for r in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child starts to fixate on a ghost guess, then safe light and dialogue reveal the truth."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the children wait before calling for help")
    ap.add_argument("--relation", choices=["siblings", "cousins"])
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


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.sign and args.cause:
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        if not plausible(sign, cause):
            raise StoryError(explain_rejection(sign, cause))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.sign is None or combo[1] == args.sign)
        and (args.cause is None or combo[2] == args.cause)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, sign_id, cause_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    fixater_name, fixater_gender = _pick_name(rng)
    steady_name, steady_gender = _pick_name(rng, avoid=fixater_name)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    relation = args.relation or rng.choice(["siblings", "cousins"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(
        setting=setting_id,
        sign=sign_id,
        cause=cause_id,
        response=response_id,
        fixater_name=fixater_name,
        fixater_gender=fixater_gender,
        steady_name=steady_name,
        steady_gender=steady_gender,
        adult=adult,
        relation=relation,
        delay=delay,
        fixater_trait=rng.choice(TRAITS_FIXATER),
        steady_trait=rng.choice(TRAITS_STEADY),
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError(f"(Unknown setting: {params.setting})")
    if params.sign not in SIGNS:
        raise StoryError(f"(Unknown sign: {params.sign})")
    if params.cause not in CAUSES:
        raise StoryError(f"(Unknown cause: {params.cause})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    sign = SIGNS[params.sign]
    cause = CAUSES[params.cause]
    response = RESPONSES[params.response]

    if not plausible(sign, cause):
        raise StoryError(explain_rejection(sign, cause))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        setting=SETTINGS[params.setting],
        sign=sign,
        cause=cause,
        response=response,
        fixer_name=params.fixater_name,
        fixer_gender=params.fixater_gender,
        steady_name=params.steady_name,
        steady_gender=params.steady_gender,
        adult_type=params.adult,
        relation=params.relation,
        delay=params.delay,
        fixer_trait=params.fixater_trait,
        steady_trait=params.steady_trait,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, sign, cause) combos:\n")
        for setting_id, sign_id, cause_id in combos:
            print(f"  {setting_id:10} {sign_id:10} {cause_id}")
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
            header = (
                f"### {p.fixater_name} & {p.steady_name}: {p.sign} in {p.setting} "
                f"({p.cause}, {p.response}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
