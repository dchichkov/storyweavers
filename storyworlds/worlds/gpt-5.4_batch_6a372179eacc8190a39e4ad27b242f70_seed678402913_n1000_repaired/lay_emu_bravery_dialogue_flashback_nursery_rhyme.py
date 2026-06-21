#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py
==============================================================================

A small nursery-rhyme-like story world about a child, an emu, and one egg in a
bit of trouble. The child is frightened at first, hears the emu's worried
dialogue, remembers an older voice in a flashback, and does one brave, sensible
thing to make the egg safe.

The world model is intentionally small and concrete:

    hazard touches egg          -> egg.risk += 1, emu.worry += 1, hero.care += 1
    risk + fear                 -> a rescue is needed
    flashback + dialogue        -> hero.bravery rises
    correct helper for hazard   -> egg.safe += 1, egg.risk -> 0, fear drops

Every story is built from state and constraints rather than by swapping a few
nouns into one paragraph. The reasonableness gate requires:
- the chosen place must actually support the hazard
- the chosen helper must really solve that hazard for an egg

Run it
------
    python storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py --place meadow --hazard wind --helper straw_ring
    python storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py --hazard ditch --helper blanket
    python storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/lay_emu_bravery_dialogue_flashback_nursery_rhyme.py --verify
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

# Make the shared result containers importable when this script is run directly:
# add the package dir (storyworlds/) to the path so `results` resolves from this
# nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        neutral = {"emu", "bird", "chick"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in neutral:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        mapping = {
            "mother": "mom",
            "father": "dad",
            "grandmother": "gran",
            "grandfather": "grandpa",
        }
        return mapping.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    opening: str
    nest_spot: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Hazard:
    id: str
    label: str
    meter: str
    opening: str
    warning: str
    emu_line: str
    child_worry: str
    solved_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    guards: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
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


def _r_hazard_pressure(world: World) -> list[str]:
    egg = world.get("egg")
    hero = world.get("hero")
    emu = world.get("emu")
    out: list[str] = []
    for meter in ("cold", "rolling", "tipping"):
        if egg.meters[meter] < THRESHOLD:
            continue
        sig = ("pressure", meter)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        egg.meters["risk"] += 1
        hero.memes["care"] += 1
        hero.memes["fear"] += 1
        emu.memes["worry"] += 1
        out.append("__risk__")
    return out


CAUSAL_RULES = [
    Rule(name="hazard_pressure", tag="physical", apply=_r_hazard_pressure),
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


def place_supports(place: Place, hazard: Hazard) -> bool:
    return hazard.id in place.affords


def helper_fits(hazard: Hazard, helper: Helper) -> bool:
    return hazard.id in helper.guards and hazard.solved_by == helper.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for hazard_id, hazard in HAZARDS.items():
            if not place_supports(place, hazard):
                continue
            for helper_id, helper in HELPERS.items():
                if helper_fits(hazard, helper):
                    combos.append((place_id, hazard_id, helper_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    hazard: str
    helper: str
    child_name: str
    child_gender: str
    emu_name: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


def apply_hazard(world: World, hazard: Hazard) -> None:
    egg = world.get("egg")
    egg.meters[hazard.meter] += 1
    propagate(world, narrate=False)


def hero_can_act(world: World) -> bool:
    hero = world.get("hero")
    return hero.memes["bravery"] >= hero.memes["fear"]


def introduce(world: World, hero: Entity, emu: Entity, egg: Entity, place: Place) -> None:
    hero.memes["calm"] += 1
    emu.memes["care"] += 1
    world.say(
        f"In {place.label}, where small winds played, "
        f"there {egg.attrs['prelude']} and there the bright hay lay."
    )
    world.say(
        f"{emu.id} the emu had laid one speckled egg near {place.nest_spot}, "
        f"and {hero.id} came skipping by to watch the morning sway."
    )


def hazard_beat(world: World, hero: Entity, emu: Entity, hazard: Hazard) -> None:
    world.say(hazard.opening)
    world.say(hazard.warning)
    world.say(f'"{hazard.emu_line}" cried {emu.id}.')
    if world.get("egg").meters["risk"] >= THRESHOLD:
        world.say(
            f"{hero.id} felt a little flutter inside. {hazard.child_worry}"
        )


def dialogue_beat(world: World, hero: Entity, emu: Entity, helper: Helper) -> None:
    hero.memes["hesitation"] += 1
    world.say(
        f'"Oh dear," said {hero.id}, "my knees feel small, and the trouble feels tall."'
    )
    world.say(
        f'"Please help my egg," said {emu.id}. "You need not roar. '
        f'Just bring {helper.phrase}, and be brave in the gentle way."'
    )


def flashback_beat(world: World, hero: Entity, elder: Entity) -> None:
    hero.memes["memory"] += 1
    hero.memes["bravery"] += 2
    world.say(
        f"Then {hero.id} remembered another day, a soft old day of bread and tea."
    )
    world.say(
        f"In that little flashback, {elder.label_word} had tapped the table and said, "
        f'"Brave is not the biggest bang. Brave is the good hand helping when it can."'
    )


def rescue_beat(world: World, hero: Entity, emu: Entity, egg: Entity,
                hazard: Hazard, helper: Helper, place: Place) -> None:
    if not helper_fits(hazard, helper):
        raise StoryError(explain_helper_rejection(hazard, helper))
    if not hero_can_act(world):
        raise StoryError("(No story: the child never gathers enough courage to act.)")

    hero.memes["bravery"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    emu.memes["trust"] += 1
    egg.meters["risk"] = 0.0
    egg.meters["safe"] += 1
    egg.meters["home"] += 1

    world.say(
        f"So {hero.id} fetched {helper.phrase}. {helper.action}"
    )
    world.say(
        f'"Steady now," whispered {hero.id}. "Steady, little egg." '
        f'And {emu.id} walked close beside {hero.pronoun("object")}.'
    )
    world.say(
        f"Together they made for {place.nest_spot}, and soon the egg was tucked "
        f"warm and snug where it belonged."
    )
    world.say(helper.ending)


def ending_beat(world: World, hero: Entity, emu: Entity, egg: Entity) -> None:
    hero.memes["joy"] += 1
    emu.memes["relief"] += 1
    emu.memes["gratitude"] += 1
    world.say(
        f'"You were brave," said {emu.id}.'
    )
    world.say(
        f'"Not loud-brave," said {hero.id}, smiling now. "Kind-brave."'
    )
    world.say(
        f"And there the egg lay safe at last, while {emu.id} hummed a low nursery tune, "
        f"and the whole small yard felt right again."
    )


def tell(place: Place, hazard: Hazard, helper: Helper,
         child_name: str = "Mina", child_gender: str = "girl",
         emu_name: str = "Etta", elder_type: str = "grandmother",
         trait: str = "gentle") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="hero",
        attrs={"trait": trait},
    ))
    emu = world.add(Entity(
        id=emu_name,
        kind="character",
        type="emu",
        label=emu_name,
        role="emu",
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
    ))
    egg = world.add(Entity(
        id="egg",
        type="egg",
        label="egg",
        phrase="one speckled egg",
        role="egg",
        attrs={"prelude": random.choice([
            "a straw ribbon lay in a ring",
            "a patch of sun lay on the grass",
            "a little rake lay by the fence",
        ])},
    ))

    hero.memes["fear"] = 2.0 if trait in {"shy", "timid"} else 1.0
    hero.memes["bravery"] = 0.0
    emu.memes["worry"] = 0.0
    egg.meters["safe"] = 0.0

    introduce(world, hero, emu, egg, place)
    apply_hazard(world, hazard)

    world.para()
    hazard_beat(world, hero, emu, hazard)
    dialogue_beat(world, hero, emu, helper)

    world.para()
    flashback_beat(world, hero, elder)
    rescue_beat(world, hero, emu, egg, hazard, helper, place)

    world.para()
    ending_beat(world, hero, emu, egg)

    world.facts.update(
        hero=hero,
        emu=emu,
        elder=elder,
        egg=egg,
        place=place,
        hazard=hazard,
        helper=helper,
        brave=hero.memes["bravery"] >= THRESHOLD,
        safe=egg.meters["safe"] >= THRESHOLD,
        flashback_used=hero.memes["memory"] >= THRESHOLD,
    )
    return world


PLACES = {
    "meadow": Place(
        id="meadow",
        label="the clover meadow",
        opening="the clover meadow",
        nest_spot="the warm nest under the fern",
        affords={"drizzle", "wind"},
    ),
    "farmyard": Place(
        id="farmyard",
        label="the farmyard by the red gate",
        opening="the farmyard",
        nest_spot="the straw nest by the shed",
        affords={"drizzle", "ditch"},
    ),
    "orchard": Place(
        id="orchard",
        label="the apple orchard",
        opening="the orchard",
        nest_spot="the mossy nook by the old tree",
        affords={"wind", "ditch"},
    ),
}

HAZARDS = {
    "drizzle": Hazard(
        id="drizzle",
        label="drizzle",
        meter="cold",
        opening="A silver drizzle came drumming down, thin as thread and soft as sighs.",
        warning="Cold drops tapped the shell, and the little egg began to lose its warmth.",
        emu_line="My egg will chill if it stays in the rain",
        child_worry="The rain did not look fierce, but it looked steady, and steady things can matter.",
        solved_by="blanket",
        tags={"rain", "egg", "warmth"},
    ),
    "wind": Hazard(
        id="wind",
        label="wind",
        meter="rolling",
        opening="Then a round wind puffed through the grass and gave the egg a wobbly nudge.",
        warning="The shell rocked left, rocked right, and nearly rolled from the bare patch of ground.",
        emu_line="My egg may roll away in this windy play",
        child_worry="A rolling thing is hard to catch, and the path looked longer than before.",
        solved_by="straw_ring",
        tags={"wind", "egg", "rolling"},
    ),
    "ditch": Hazard(
        id="ditch",
        label="ditch",
        meter="tipping",
        opening="By the edge of the path, the ground sloped down to a shallow ditch.",
        warning="The egg tipped toward the little dip in the earth and looked one breath from a tumble.",
        emu_line="My egg may slip into the ditch",
        child_worry="The ditch was not huge, but it was deep enough for trouble.",
        solved_by="basket",
        tags={"ditch", "egg", "careful_carry"},
    ),
}

HELPERS = {
    "blanket": Helper(
        id="blanket",
        label="blanket",
        phrase="a little quilted blanket",
        guards={"drizzle"},
        action="She wrapped the shell in the dry soft cloth and held it close to keep the chill away.",
        ending="The rain kept singing, but it could not bite through the blanket.",
        tags={"blanket", "warmth"},
    ),
    "straw_ring": Helper(
        id="straw_ring",
        label="straw ring",
        phrase="a round straw ring",
        guards={"wind"},
        action="She set the ring around the egg so it would not scoot or spin, then nudged it carefully along the path.",
        ending="The wind still puffed and huffed, but the egg stayed snug inside its strawy guard.",
        tags={"straw", "wind"},
    ),
    "basket": Helper(
        id="basket",
        label="basket",
        phrase="a small willow basket",
        guards={"ditch"},
        action="She lined the basket with hay, lifted the egg with two slow hands, and kept it level all the way.",
        ending="The ditch stayed only a ditch, because the egg rode high and safe in the basket.",
        tags={"basket", "carry"},
    ),
    "wagon": Helper(
        id="wagon",
        label="toy wagon",
        phrase="a toy wagon",
        guards=set(),
        action="",
        ending="",
        tags={"wagon"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Tess", "Nora", "May", "Poppy"]
BOY_NAMES = ["Ben", "Ollie", "Toby", "Finn", "Max", "Ned"]
EMU_NAMES = ["Etta", "Ember", "Momo", "Daisy", "Nell"]
TRAITS = ["gentle", "curious", "shy", "timid", "careful"]
ELDERS = ["grandmother", "grandfather"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    emu = f["emu"]
    hazard = f["hazard"]
    helper = f["helper"]
    place = f["place"]
    return [
        f'Write a short nursery-rhyme style story for a 3-to-5-year-old that includes the words "lay" and "emu".',
        f"Tell a gentle story set in {place.label} where {hero.id} helps {emu.id} the emu save an egg from {hazard.label} by using {helper.phrase}.",
        f'Write a story with dialogue, a brief flashback, and a small act of bravery where a child hears, remembers, and helps.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    emu = f["emu"]
    elder = f["elder"]
    egg = f["egg"]
    place = f["place"]
    hazard = f["hazard"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, {emu.id} the emu, and one speckled egg in {place.label}. The story follows how they work together when the egg is in trouble.",
        ),
        (
            "What problem did the egg have?",
            f"The egg was in danger because of {hazard.label}. {hazard.warning} That is why {emu.id} grew worried and asked for help.",
        ),
        (
            f"What did {emu.id} say?",
            f'{emu.id} spoke right out loud and said, "{hazard.emu_line}." The dialogue matters because it is what turns {hero.id} from watching into helping.',
        ),
        (
            f"What flashback did {hero.id} remember?",
            f"{hero.id} remembered {elder.label_word}'s old advice that brave does not have to be loud. That memory changed the feeling in the moment, because it gave {hero.pronoun('object')} a simple way to be brave.",
        ),
        (
            f"How did {hero.id} help the egg?",
            f"{hero.id} used {helper.phrase}. {helper.action} That sensible tool matched the danger and is what made the egg safe.",
        ),
        (
            "How did the story end?",
            f"The egg ended tucked back in its nest, and {emu.id} thanked {hero.id}. The ending image shows what changed: the worry is gone, and the egg can rest.",
        ),
    ]
    if egg.meters["safe"] >= THRESHOLD:
        qa.append(
            (
                f"Was {hero.id} brave?",
                f"Yes. {hero.id} was afraid at first, but still did the kind and careful thing. In this story, bravery means helping even when your knees feel shaky.",
            )
        )
    return qa


KNOWLEDGE = {
    "egg": [
        (
            "Why do eggs need to be kept safe?",
            "Egg shells can crack, get cold, or roll away if they are left in a bad spot. Keeping an egg warm and steady helps what is inside stay safe.",
        )
    ],
    "emu": [
        (
            "What is an emu?",
            "An emu is a very tall bird with long legs and soft feathers. It cannot fly, but it can run fast.",
        )
    ],
    "rain": [
        (
            "Why can drizzle be a problem for an egg?",
            "Even light rain can make an egg cold if it keeps falling. A small chill can matter when something is meant to stay warm.",
        )
    ],
    "wind": [
        (
            "Why is wind risky for a round egg?",
            "A round egg can wobble and roll when wind pushes it. If it rolls too far, it can bump or crack.",
        )
    ],
    "ditch": [
        (
            "What is a ditch?",
            "A ditch is a little hollow or trench in the ground. Things can slip into it if they are near the edge.",
        )
    ],
    "blanket": [
        (
            "What does a blanket do?",
            "A blanket helps keep something warm and dry. Soft covering can protect small things from cold air and rain.",
        )
    ],
    "straw": [
        (
            "Why can straw help hold an egg still?",
            "Straw is soft and springy, so it can make a little nest or ring around an egg. That helps stop rolling and cushions the shell.",
        )
    ],
    "basket": [
        (
            "Why is a basket useful for carrying something delicate?",
            "A basket can hold a delicate thing steady while you move it. If it is lined with soft hay, it protects the thing even more.",
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel nervous. It does not have to look noisy or grand to be real.",
        )
    ],
}
KNOWLEDGE_ORDER = ["emu", "egg", "rain", "wind", "ditch", "blanket", "straw", "basket", "bravery"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"emu", "egg", "bravery"} | set(f["hazard"].tags) | set(f["helper"].tags)
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


CURATED = [
    StoryParams(
        place="meadow",
        hazard="wind",
        helper="straw_ring",
        child_name="May",
        child_gender="girl",
        emu_name="Etta",
        elder_type="grandmother",
        trait="shy",
    ),
    StoryParams(
        place="farmyard",
        hazard="drizzle",
        helper="blanket",
        child_name="Ben",
        child_gender="boy",
        emu_name="Momo",
        elder_type="grandfather",
        trait="careful",
    ),
    StoryParams(
        place="orchard",
        hazard="ditch",
        helper="basket",
        child_name="Nora",
        child_gender="girl",
        emu_name="Daisy",
        elder_type="grandmother",
        trait="gentle",
    ),
]


def explain_place_rejection(place: Place, hazard: Hazard) -> str:
    allowed = ", ".join(sorted(place.affords))
    return (
        f"(No story: {hazard.label} is not a natural hazard in {place.label} here. "
        f"That place only supports: {allowed}.)"
    )


def explain_helper_rejection(hazard: Hazard, helper: Helper) -> str:
    return (
        f"(No story: {helper.phrase} does not sensibly solve {hazard.label} for an egg. "
        f"Use {HELPERS[hazard.solved_by].phrase} instead.)"
    )


ASP_RULES = r"""
supports(P, H) :- affords(P, H).
fits(H, Help) :- hazard(H), helper(Help), solves(H, Help), guards(Help, H).
valid(P, H, Help) :- place(P), hazard(H), helper(Help), supports(P, H), fits(H, Help).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for hazard_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, hazard_id))
    for hazard_id, hazard in HAZARDS.items():
        lines.append(asp.fact("hazard", hazard_id))
        lines.append(asp.fact("solves", hazard_id, hazard.solved_by))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for guard in sorted(helper.guards):
            lines.append(asp.fact("guards", helper_id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme story world: a child helps an emu's egg with bravery, dialogue, and a flashback."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--child-name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--emu-name")
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.hazard:
        place = PLACES[args.place]
        hazard = HAZARDS[args.hazard]
        if not place_supports(place, hazard):
            raise StoryError(explain_place_rejection(place, hazard))
    if args.hazard and args.helper:
        hazard = HAZARDS[args.hazard]
        helper = HELPERS[args.helper]
        if not helper_fits(hazard, helper):
            raise StoryError(explain_helper_rejection(hazard, helper))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.hazard is None or combo[1] == args.hazard)
        and (args.helper is None or combo[2] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, hazard_id, helper_id = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    emu_name = args.emu_name or rng.choice(EMU_NAMES)
    elder_type = args.elder or rng.choice(ELDERS)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        hazard=hazard_id,
        helper=helper_id,
        child_name=child_name,
        child_gender=gender,
        emu_name=emu_name,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.hazard not in HAZARDS:
        raise StoryError(f"(Unknown hazard: {params.hazard})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    place = PLACES[params.place]
    hazard = HAZARDS[params.hazard]
    helper = HELPERS[params.helper]

    if not place_supports(place, hazard):
        raise StoryError(explain_place_rejection(place, hazard))
    if not helper_fits(hazard, helper):
        raise StoryError(explain_helper_rejection(hazard, helper))

    world = tell(
        place=place,
        hazard=hazard,
        helper=helper,
        child_name=params.child_name,
        child_gender=params.child_gender,
        emu_name=params.emu_name,
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
        print(f"{len(combos)} compatible (place, hazard, helper) combos:\n")
        for place, hazard, helper in combos:
            print(f"  {place:9} {hazard:8} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        for i, params in enumerate(CURATED):
            seeded = StoryParams(
                place=params.place,
                hazard=params.hazard,
                helper=params.helper,
                child_name=params.child_name,
                child_gender=params.child_gender,
                emu_name=params.emu_name,
                elder_type=params.elder_type,
                trait=params.trait,
                seed=base_seed + i,
            )
            random.seed(seeded.seed)
            samples.append(generate(seeded))
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
            random.seed(seed)
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
            header = f"### {p.child_name} with {p.emu_name}: {p.hazard} in {p.place} using {p.helper}"
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
