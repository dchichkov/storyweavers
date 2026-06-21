#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py
==============================================================

A small storyworld about a child who thinks a house might hold a ghost at noon.
The world model keeps fear and curiosity in tension, then resolves the mystery
through a sensible investigation with an older helper. The stories stay gentle
and child-facing: spooky shadows and whispers are allowed, but the ending always
shows what really changed in the world.

Run it
------
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py --place attic --sign shape
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py --cause kitten
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py --method shake_it   # refused
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/noon_rouse_curiosity_ghost_story.py --verify
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
CURIOUS_TRAITS = {"curious", "wondering", "careful", "brave"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt", "sister"}
        male = {"boy", "man", "father", "grandfather", "uncle", "brother"}
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
            "sister": "sister",
            "brother": "brother",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    detail: str
    image: str
    signs: set[str] = field(default_factory=set)
    causes: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Sign:
    id: str
    label: str
    appear: str
    suspect: str
    sensation: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Cause:
    id: str
    label: str
    category: str
    reveal: str
    proof: str
    comfort: str
    places: set[str] = field(default_factory=set)
    signs: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    category: str
    sense: int
    lead: str
    reveal_line: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    sign: str
    cause: str
    method: str
    child_name: str
    child_gender: str
    helper_type: str
    helper_name: str
    trait: str
    child_age: int = 6
    helper_age: int = 10
    seed: Optional[int] = None


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


def _r_ghost_guess(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["fear"] < THRESHOLD or child.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("ghost_guess",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["wonder"] += 1
    world.facts["guessed_ghost"] = True
    return []


def _r_courage(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if helper.memes["reassure"] < THRESHOLD:
        return []
    sig = ("courage",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = max(0.0, child.memes["fear"] - 1.0)
    child.memes["bravery"] += 1
    world.facts["helped"] = True
    return []


CAUSAL_RULES = [
    Rule(name="ghost_guess", tag="emotional", apply=_r_ghost_guess),
    Rule(name="courage", tag="emotional", apply=_r_courage),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            world.say(bit)
    return produced


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the attic at the top of the stairs",
        detail="Dusty trunks sat under the sloping roof, and one small window poured in a pale square of noon light.",
        image="The rafters made long stripes across the floorboards.",
        signs={"shape", "tapping"},
        causes={"sheet", "kitten"},
        tags={"attic"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the long hallway by the clock",
        detail="Family pictures watched from the walls, and the grandfather clock waited at the end like a tall dark guard.",
        image="The noon light lay in bright bars across the runner rug.",
        signs={"whisper", "shape"},
        causes={"draft", "sheet"},
        tags={"hallway"},
    ),
    "sunroom": Place(
        id="sunroom",
        label="sunroom",
        phrase="the glassy sunroom behind the kitchen",
        detail="Plant leaves trembled in their pots, and white curtains shivered against the windows.",
        image="The bright noon sun made every moving shadow look sharper than usual.",
        signs={"whisper", "tapping"},
        causes={"draft", "magpie"},
        tags={"sunroom"},
    ),
}

SIGNS = {
    "shape": Sign(
        id="shape",
        label="white shape",
        appear="a tall white shape swaying in the bright light",
        suspect="looked exactly like a ghost in a storybook sheet",
        sensation="It did not moan, but it seemed to breathe whenever the air moved.",
        tags={"shape", "ghost"},
    ),
    "whisper": Sign(
        id="whisper",
        label="whisper",
        appear='a hush-hush whisper that seemed to say "come closer"',
        suspect="sounded like secret ghost words sliding along the wall",
        sensation="The sound was soft enough to make the room feel even stiller.",
        tags={"whisper", "ghost"},
    ),
    "tapping": Sign(
        id="tapping",
        label="tapping",
        appear="a tap-tap-tap from above the window",
        suspect="sounded like tiny ghost knuckles asking to be let in",
        sensation="Each little tap made the quiet room jump.",
        tags={"tapping", "ghost"},
    ),
}

CAUSES = {
    "sheet": Cause(
        id="sheet",
        label="laundry sheet",
        category="lift",
        reveal="an old laundry sheet hanging from a trunk latch",
        proof="When the helper lifted it, the cloth turned from a ghost shape into plain white cotton.",
        comfort="It was only laundry caught in the moving air.",
        places={"attic", "hallway"},
        signs={"shape"},
        tags={"sheet", "air"},
    ),
    "draft": Cause(
        id="draft",
        label="loose window",
        category="window",
        reveal="a loose window latch letting a thin draft slip through",
        proof="When the helper pressed the latch shut, the whisper stopped at once and the curtain went still.",
        comfort="It had been the wind making a spooky sound all along.",
        places={"hallway", "sunroom"},
        signs={"whisper"},
        tags={"wind", "window"},
    ),
    "kitten": Cause(
        id="kitten",
        label="kitten",
        category="peek",
        reveal="a sleepy gray kitten tucked behind a trunk",
        proof="The tiny nose poked out first, and then the kitten batted at the dangling cord that had made the tapping.",
        comfort="It was not a ghost at all, only a hidden kitten looking for a nap place.",
        places={"attic"},
        signs={"tapping"},
        tags={"kitten", "pet"},
    ),
    "magpie": Cause(
        id="magpie",
        label="magpie",
        category="peek",
        reveal="a shiny black-and-white magpie hopping on the outside sill",
        proof="Its beak tapped the glass again, and its bright eye flashed in the sun.",
        comfort="It was a bird seeing its reflection, not a ghost trying to get in.",
        places={"sunroom"},
        signs={"tapping"},
        tags={"bird", "window"},
    ),
}

METHODS = {
    "lift_cloth": Method(
        id="lift_cloth",
        label="lift the cloth together",
        category="lift",
        sense=3,
        lead="stood close together and gently reached for the pale cloth",
        reveal_line="The helper pinched one corner and lifted.",
        qa_text="lifted the cloth together to see what it really was",
        tags={"investigate", "cloth"},
    ),
    "close_window": Method(
        id="close_window",
        label="check the window latch",
        category="window",
        sense=3,
        lead="followed the whisper to the window and looked carefully at the latch",
        reveal_line="The helper pushed the latch snug against the frame.",
        qa_text="checked the window latch and closed it",
        tags={"investigate", "window"},
    ),
    "peek_behind": Method(
        id="peek_behind",
        label="peek behind the hiding place",
        category="peek",
        sense=2,
        lead="crept close enough to peer behind the place where the sound came from",
        reveal_line="They bent down and peeped in together.",
        qa_text="peeked behind the hiding place instead of guessing",
        tags={"investigate", "peek"},
    ),
    "shake_it": Method(
        id="shake_it",
        label="shake the scary thing hard",
        category="lift",
        sense=1,
        lead="grabbed at the mystery and shook it hard",
        reveal_line="That was far too rough for a careful ghost mystery.",
        qa_text="shook the mystery hard",
        tags={"rough"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Zoe", "Anna", "Ruby", "Ella"]
BOY_NAMES = ["Owen", "Ben", "Max", "Theo", "Leo", "Sam", "Eli"]
TRAITS = ["curious", "wondering", "careful", "brave", "timid"]
HELPERS = ["grandmother", "grandfather", "sister", "brother"]


def sign_matches(place: Place, sign: Sign) -> bool:
    return sign.id in place.signs


def cause_matches(place: Place, sign: Sign, cause: Cause) -> bool:
    return place.id in cause.places and sign.id in cause.signs


def method_matches(cause: Cause, method: Method) -> bool:
    return cause.category == method.category and method.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for sign_id, sign in SIGNS.items():
            if not sign_matches(place, sign):
                continue
            for cause_id, cause in CAUSES.items():
                if not cause_matches(place, sign, cause):
                    continue
                for method_id, method in METHODS.items():
                    if method_matches(cause, method):
                        combos.append((place_id, sign_id, cause_id, method_id))
    return combos


def curiosity_value(trait: str) -> float:
    return 3.0 if trait in CURIOUS_TRAITS else 1.0


def outcome_of(params: StoryParams) -> str:
    return "investigate_now" if curiosity_value(params.trait) >= 2.0 else "need_reassurance"


def predict_reveal(world: World, cause: Cause, method: Method) -> dict:
    sim = world.copy()
    child = sim.get("child")
    helper = sim.get("helper")
    child.memes["fear"] += 1
    child.memes["curiosity"] += curiosity_value(child.attrs.get("trait", "timid"))
    helper.memes["reassure"] += 1
    propagate(sim, narrate=False)
    return {
        "ghost_guess": bool(sim.facts.get("guessed_ghost")),
        "helped": bool(sim.facts.get("helped")),
        "method_ok": method_matches(cause, method),
    }


def introduce(world: World, child: Entity, helper: Entity, place: Place) -> None:
    world.say(
        f"At noon, {child.id} was visiting {helper.id} and wandering near {place.phrase}. "
        f"{place.detail}"
    )
    world.say(place.image)


def noon_sound(world: World, child: Entity) -> None:
    child.memes["stillness"] += 1
    world.say(
        "Then the clock downstairs gave twelve slow booms, and the last one seemed to rouse every tiny sound in the house."
    )


def notice_sign(world: World, child: Entity, sign: Sign) -> None:
    child.memes["fear"] += 1
    child.memes["curiosity"] += curiosity_value(child.attrs.get("trait", "timid"))
    propagate(world, narrate=False)
    world.say(
        f"In that hush, {child.id} noticed {sign.appear}. It {sign.suspect}. {sign.sensation}"
    )


def wonder_ghost(world: World, child: Entity) -> None:
    if world.facts.get("guessed_ghost"):
        world.say(
            f'"Is it a ghost?" {child.id} whispered. The question made {child.pronoun("possessive")} heart beat fast, but it also made curiosity rouse inside {child.pronoun("object")} like a small bright lantern.'
        )
    else:
        world.say(
            f'{child.id} felt a little shiver and leaned closer, trying to understand the strange thing.'
        )


def call_helper(world: World, child: Entity, helper: Entity) -> None:
    helper.memes["reassure"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{child.id} padded back to {helper.id} and tugged {helper.pronoun("possessive")} hand. "{helper.id}," {child.pronoun()} whispered, "something spooky is up there."'
    )


def reassure(world: World, helper: Entity, child: Entity) -> None:
    world.say(
        f'{helper.id} did not laugh. {helper.pronoun().capitalize()} squeezed {child.id}\'s hand and said, "Let us look carefully before we decide what it is."'
    )


def approach(world: World, child: Entity, helper: Entity, method: Method, outcome: str) -> None:
    if outcome == "investigate_now":
        world.say(
            f"With {helper.id} beside {child.pronoun('object')}, {child.id} took a slow breath and {method.lead}."
        )
    else:
        world.say(
            f"{child.id} stayed very close to {helper.id}, but after one slow breath and one more hand squeeze, {child.pronoun()} was brave enough to move forward. Together they {method.lead}."
        )


def reveal(world: World, helper: Entity, cause: Cause, method: Method) -> None:
    world.say(method.reveal_line)
    world.say(
        f"There was no ghost there at all, only {cause.reveal}. {cause.proof}"
    )
    world.say(cause.comfort)
    helper.memes["calm"] += 1
    child = world.get("child")
    child.memes["relief"] += 1
    child.memes["fear"] = 0.0
    child.memes["wonder"] += 1
    world.facts["revealed"] = True


def ending(world: World, child: Entity, helper: Entity, place: Place, cause: Cause) -> None:
    if cause.id in {"kitten", "magpie"}:
        image = "The mystery made a small cheerful sound instead of a scary one."
    elif cause.id == "draft":
        image = "The room felt ordinary again, as if the house itself had stopped holding its breath."
    else:
        image = "The pale shape looked silly in the bright daylight now that they knew the truth."
    world.say(
        f"{child.id} let out a tiny laugh that sounded much lighter than the whisper from before. {image}"
    )
    world.say(
        f"After that, {place.label} still felt old and shadowy, but not haunted. At noon or any other time, {child.id} remembered that careful looking can turn a ghost story into an answer."
    )


def tell(
    place: Place,
    sign: Sign,
    cause: Cause,
    method: Method,
    child_name: str,
    child_gender: str,
    helper_name: str,
    helper_type: str,
    trait: str,
    child_age: int,
    helper_age: int,
) -> World:
    world = World()
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            role="child",
            age=child_age,
            traits=[trait],
            attrs={"trait": trait},
            label=child_name,
        )
    )
    helper = world.add(
        Entity(
            id=helper_name,
            kind="character",
            type=helper_type,
            role="helper",
            age=helper_age,
            label=helper_name,
        )
    )
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.facts.update(
        child=child,
        helper=helper,
        place_cfg=place,
        sign_cfg=sign,
        cause_cfg=cause,
        method_cfg=method,
    )

    introduce(world, child, helper, place)
    noon_sound(world, child)

    world.para()
    notice_sign(world, child, sign)
    wonder_ghost(world, child)
    call_helper(world, child, helper)
    reassure(world, helper, child)

    world.para()
    out = outcome_of(
        StoryParams(
            place=place.id,
            sign=sign.id,
            cause=cause.id,
            method=method.id,
            child_name=child_name,
            child_gender=child_gender,
            helper_type=helper_type,
            helper_name=helper_name,
            trait=trait,
            child_age=child_age,
            helper_age=helper_age,
        )
    )
    approach(world, child, helper, method, out)
    reveal(world, helper, cause, method)

    world.para()
    ending(world, child, helper, place, cause)
    world.facts["outcome"] = out
    world.facts["guessed_ghost"] = bool(world.facts.get("guessed_ghost"))
    return world


KNOWLEDGE = {
    "ghost": [(
        "What is a ghost story?",
        "A ghost story is a spooky kind of story that makes ordinary sounds and shadows feel mysterious. Sometimes the ending shows there was a real explanation all along."
    )],
    "attic": [(
        "Why can an attic feel spooky?",
        "An attic can feel spooky because it is quiet, dusty, and full of old things with odd shapes. In dim corners, ordinary objects can look strange."
    )],
    "whisper": [(
        "How can wind make a whisper sound?",
        "When air slips through a small crack or around a curtain, it can make a soft hushing noise. That sound can seem like whispering if the room is very quiet."
    )],
    "tapping": [(
        "What can make a tapping sound on a window?",
        "A bird, a branch, or a loose cord can tap against a window. Small repeated sounds can seem spooky before you know what is making them."
    )],
    "window": [(
        "What is a window latch for?",
        "A window latch keeps the window shut tightly. If it is loose, air can slip in and make curtains move or whistle."
    )],
    "sheet": [(
        "Why can a hanging sheet look like a ghost?",
        "A hanging sheet can look like a ghost when it sways and catches the light. Our eyes sometimes turn a plain shape into a spooky one before we look closely."
    )],
    "kitten": [(
        "Why might a hidden kitten make a strange noise?",
        "A kitten can scratch, tap, or rustle when it is exploring or playing. If you cannot see it yet, the sound can feel mysterious."
    )],
    "bird": [(
        "Why do some birds peck at windows?",
        "Some birds peck at windows because they notice their reflection and think another bird is there. The tapping can sound odd inside the house."
    )],
    "investigate": [(
        "What is a careful way to check something spooky?",
        "A careful way is to stay with a grown-up or older helper, move slowly, and look closely. Guessing less and observing more helps you find the real cause."
    )],
}

KNOWLEDGE_ORDER = ["ghost", "attic", "whisper", "tapping", "window", "sheet", "kitten", "bird", "investigate"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    sign = f["sign_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the word "noon" and the word "rouse".',
        f"Tell a spooky-but-safe story where {child.id} notices {sign.label} in {place.phrase} at noon, and curiosity helps {child.pronoun('object')} learn the truth.",
        f"Write a child-facing mystery where {helper.id} helps {child.id} investigate a possible ghost by looking carefully instead of running away.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    place = f["place_cfg"]
    sign = f["sign_cfg"]
    cause = f["cause_cfg"]
    method = f["method_cfg"]
    outcome = f.get("outcome")
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, who noticed something spooky at noon, and {helper.id}, who helped investigate. The story follows their ghostly worry turning into an answer."
        ),
        (
            f"What did {child.id} notice?",
            f"{child.id} noticed {sign.appear} in {place.phrase}. It seemed ghostly at first because the room was quiet and the strange sign did not make sense yet."
        ),
        (
            f"Why did {child.id} think it might be a ghost?",
            f"{sign.suspect[0].upper()}{sign.suspect[1:]}. The still house and the strange sound or shape made imagination rush in before the real cause was known."
        ),
        (
            f"How did {helper.id} help?",
            f"{helper.id} held {child.id}'s hand and stayed calm. Instead of laughing or hurrying, {helper.pronoun()} suggested looking carefully so they could learn what was really there."
        ),
        (
            "How did they solve the mystery?",
            f"They {method.qa_text}. That careful method matched the problem and let them find the truth without making the scene rougher or scarier."
        ),
        (
            "What was the 'ghost' really?",
            f"The ghost was really {cause.reveal}. {cause.proof}"
        ),
    ]
    if outcome == "need_reassurance":
        qa.append(
            (
                f"Was {child.id} brave right away?",
                f"No. {child.id} felt scared first and needed {helper.id}'s calm help. After that reassurance, curiosity grew stronger than fear and {child.pronoun()} could move closer."
            )
        )
    else:
        qa.append(
            (
                f"What changed for {child.id} by the end?",
                f"{child.id} still remembered the spooky feeling, but it no longer controlled the room. Knowing the cause turned the noon mystery into something understandable."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "investigate"}
    tags |= set(f["place_cfg"].tags)
    tags |= set(f["sign_cfg"].tags)
    tags |= set(f["cause_cfg"].tags)
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
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        sign="shape",
        cause="sheet",
        method="lift_cloth",
        child_name="Lila",
        child_gender="girl",
        helper_type="grandmother",
        helper_name="Grandma May",
        trait="curious",
        child_age=6,
        helper_age=66,
    ),
    StoryParams(
        place="hallway",
        sign="whisper",
        cause="draft",
        method="close_window",
        child_name="Owen",
        child_gender="boy",
        helper_type="grandfather",
        helper_name="Grandpa Ned",
        trait="careful",
        child_age=5,
        helper_age=70,
    ),
    StoryParams(
        place="sunroom",
        sign="tapping",
        cause="magpie",
        method="peek_behind",
        child_name="Mia",
        child_gender="girl",
        helper_type="sister",
        helper_name="Rosa",
        trait="timid",
        child_age=5,
        helper_age=9,
    ),
    StoryParams(
        place="attic",
        sign="tapping",
        cause="kitten",
        method="peek_behind",
        child_name="Ben",
        child_gender="boy",
        helper_type="brother",
        helper_name="Evan",
        trait="wondering",
        child_age=6,
        helper_age=10,
    ),
]


def explain_combo(place: Place, sign: Sign, cause: Cause) -> str:
    if not sign_matches(place, sign):
        return f"(No story: {sign.label} does not fit {place.label} in this world.)"
    if not cause_matches(place, sign, cause):
        return (
            f"(No story: {cause.label} would not make that sign in the {place.label}. "
            f"Pick a cause that can really produce the spooky clue.)"
        )
    return "(No story: that mystery setup is not supported.)"


def explain_method(cause: Cause, method: Method) -> str:
    if method.sense < SENSE_MIN:
        return (
            f"(Refusing method '{method.id}': it is too rough or careless for this storyworld "
            f"(sense={method.sense} < {SENSE_MIN}). Choose a calmer way to investigate.)"
        )
    return (
        f"(No story: {method.label} does not match the kind of clue made by {cause.label}. "
        f"Choose a method that fits the real cause.)"
    )


ASP_RULES = r"""
fits_sign(P,S) :- place(P), sign(S), place_has_sign(P,S).
fits_cause(P,S,C) :- place(P), sign(S), cause(C),
                     cause_in_place(C,P), cause_makes_sign(C,S).
sensible_method(M) :- method(M), sense(M,V), sense_min(Min), V >= Min.
fits_method(C,M) :- cause(C), method(M), cause_category(C,K), method_category(M,K), sensible_method(M).
valid(P,S,C,M) :- fits_sign(P,S), fits_cause(P,S,C), fits_method(C,M).

curious_enough :- trait(T), curiosity(T,V), V >= 2.
outcome(investigate_now) :- curious_enough.
outcome(need_reassurance) :- not curious_enough.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for sign_id in sorted(place.signs):
            lines.append(asp.fact("place_has_sign", place_id, sign_id))
    for sign_id in SIGNS:
        lines.append(asp.fact("sign", sign_id))
    for cause_id, cause in CAUSES.items():
        lines.append(asp.fact("cause", cause_id))
        lines.append(asp.fact("cause_category", cause_id, cause.category))
        for place_id in sorted(cause.places):
            lines.append(asp.fact("cause_in_place", cause_id, place_id))
        for sign_id in sorted(cause.signs):
            lines.append(asp.fact("cause_makes_sign", cause_id, sign_id))
    for method_id, method in METHODS.items():
        lines.append(asp.fact("method", method_id))
        lines.append(asp.fact("method_category", method_id, method.category))
        lines.append(asp.fact("sense", method_id, method.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for trait in sorted(set(TRAITS)):
        lines.append(asp.fact("trait_name", trait))
        lines.append(asp.fact("curiosity", trait, int(curiosity_value(trait))))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_method/1."))
    return sorted(m for (m,) in asp.atoms(model, "sensible_method"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = f"trait({params.trait})."
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combinations:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_methods = sorted(m.id for m in METHODS.values() if m.sense >= SENSE_MIN)
    asp_methods = asp_sensible_methods()
    if py_methods == asp_methods:
        print(f"OK: sensible methods match ({', '.join(py_methods)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: python={py_methods} clingo={asp_methods}")

    cases = list(CURATED)
    for trait in TRAITS:
        cases.append(
            StoryParams(
                place="attic",
                sign="shape",
                cause="sheet",
                method="lift_cloth",
                child_name="Test",
                child_gender="girl",
                helper_type="grandmother",
                helper_name="Gran",
                trait=trait,
                child_age=6,
                helper_age=64,
            )
        )
    bad = sum(1 for p in cases if outcome_of(p) != asp_outcome(p))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story or "{" in smoke.story or "}" in smoke.story:
            raise StoryError("Smoke test produced bad story text.")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A gentle ghost-story world where curiosity helps a child solve a noon mystery."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sign", choices=SIGNS)
    ap.add_argument("--cause", choices=CAUSES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid mystery combinations from clingo")
    ap.add_argument("--verify", action="store_true", help="check clingo/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def pick_helper_name(rng: random.Random, helper_type: str) -> str:
    options = {
        "grandmother": ["Grandma May", "Grandma June", "Grandma Rose"],
        "grandfather": ["Grandpa Ned", "Grandpa Joe", "Grandpa Frank"],
        "sister": ["Rosa", "Ivy", "Nina", "Clare"],
        "brother": ["Evan", "Noah", "Luke", "Milo"],
    }
    return rng.choice(options[helper_type])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.sign:
        place = PLACES[args.place]
        sign = SIGNS[args.sign]
        if not sign_matches(place, sign):
            raise StoryError(explain_combo(place, sign, next(iter(CAUSES.values()))))
    if args.place and args.sign and args.cause:
        place = PLACES[args.place]
        sign = SIGNS[args.sign]
        cause = CAUSES[args.cause]
        if not cause_matches(place, sign, cause):
            raise StoryError(explain_combo(place, sign, cause))
    if args.cause and args.method:
        cause = CAUSES[args.cause]
        method = METHODS[args.method]
        if not method_matches(cause, method):
            raise StoryError(explain_method(cause, method))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        dummy = CAUSES[args.cause] if args.cause else next(iter(CAUSES.values()))
        raise StoryError(explain_method(dummy, METHODS[args.method]))

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.sign is None or c[1] == args.sign)
        and (args.cause is None or c[2] == args.cause)
        and (args.method is None or c[3] == args.method)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, sign_id, cause_id, method_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_type or rng.choice(HELPERS)
    child_name = args.name or pick_name(rng, gender)
    helper_name = args.helper_name or pick_helper_name(rng, helper_type)
    trait = rng.choice(TRAITS)
    child_age = rng.choice([5, 6, 7])
    helper_age = rng.choice([9, 10, 11]) if helper_type in {"sister", "brother"} else rng.choice([62, 68, 73])
    return StoryParams(
        place=place_id,
        sign=sign_id,
        cause=cause_id,
        method=method_id,
        child_name=child_name,
        child_gender=gender,
        helper_type=helper_type,
        helper_name=helper_name,
        trait=trait,
        child_age=child_age,
        helper_age=helper_age,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        sign = SIGNS[params.sign]
        cause = CAUSES[params.cause]
        method = METHODS[params.method]
    except KeyError as err:
        raise StoryError(f"(Invalid option: {err.args[0]})") from None

    if not sign_matches(place, sign) or not cause_matches(place, sign, cause):
        raise StoryError(explain_combo(place, sign, cause))
    if not method_matches(cause, method):
        raise StoryError(explain_method(cause, method))

    world = tell(
        place=place,
        sign=sign,
        cause=cause,
        method=method,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        child_age=params.child_age,
        helper_age=params.helper_age,
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
        print(asp_program("", "#show valid/4.\n#show sensible_method/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        methods = asp_sensible_methods()
        print(f"sensible methods: {', '.join(methods)}\n")
        print(f"{len(combos)} valid (place, sign, cause, method) combos:\n")
        for place, sign, cause, method in combos:
            print(f"  {place:8} {sign:8} {cause:8} {method}")
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
            header = f"### {p.child_name}: {p.sign} in the {p.place} ({p.cause}, {p.method})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
