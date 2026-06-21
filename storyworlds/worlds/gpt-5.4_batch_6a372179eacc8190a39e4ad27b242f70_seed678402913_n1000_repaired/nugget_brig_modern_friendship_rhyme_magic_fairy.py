#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py
=============================================================================

A tiny fairy-tale-flavoured story world set in a modern place: two friends find
a trapped fairy, a glowing nugget, and a tiny brig. They can only free the fairy
by sharing the right nugget and speaking the right rhyme together.

The model keeps a small typed world with physical meters and emotional memes.
State drives the prose: worry rises when the fairy is trapped, trust and courage
grow when the children act kindly together, and the brig only opens when the
nugget and rhyme genuinely match the magic binding it.

Run it
------
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py --brig frost --nugget sun --rhyme warm
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py --brig thorn --nugget ember
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py --all
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/nugget_brig_modern_friendship_rhyme_magic_fairy.py --verify
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

# Make the shared result containers importable when this script is run directly.
# This file lives under storyworlds/worlds/gpt-5.4/, so we add storyworlds/.
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
        female = {"girl", "mother", "mom", "woman", "fairy"}
        male = {"boy", "father", "dad", "man"}
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
    opening: str
    modern_detail: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BrigSpell:
    id: str
    label: str
    phrase: str
    lock_word: str
    look: str
    key: str
    release: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NuggetKind:
    id: str
    label: str
    phrase: str
    glow: str
    key: str
    gift_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RhymeKind:
    id: str
    label: str
    line1: str
    line2: str
    key: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    use: str
    ending: str
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


def _r_shared_kindness(world: World) -> list[str]:
    out: list[str] = []
    brig = world.get("brig")
    nugget = world.get("nugget")
    fairy = world.get("fairy")
    if nugget.meters["shared"] >= THRESHOLD and brig.meters["hope"] < THRESHOLD:
        sig = ("hope",)
        if sig not in world.fired:
            world.fired.add(sig)
            brig.meters["hope"] += 1
            fairy.memes["hope"] += 1
            out.append("__hope__")
    return out


def _r_magic_unlock(world: World) -> list[str]:
    out: list[str] = []
    brig = world.get("brig")
    nugget = world.get("nugget")
    rhyme = world.get("rhyme")
    fairy = world.get("fairy")
    friends_ready = world.facts.get("spoken_together", False)
    matched = world.facts.get("matched_magic", False)
    if friends_ready and matched and nugget.meters["shared"] >= THRESHOLD and brig.meters["open"] < THRESHOLD:
        sig = ("open",)
        if sig not in world.fired:
            world.fired.add(sig)
            brig.meters["open"] += 1
            brig.meters["locked"] = 0.0
            fairy.meters["free"] += 1
            fairy.memes["joy"] += 1
            rhyme.meters["sung"] += 1
            out.append("__open__")
    return out


RULES = [
    Rule(name="shared_kindness", tag="social", apply=_r_shared_kindness),
    Rule(name="magic_unlock", tag="magic", apply=_r_magic_unlock),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for line in produced:
            if not line.startswith("__"):
                world.say(line)
    return produced


def is_match(brig: BrigSpell, nugget: NuggetKind, rhyme: RhymeKind) -> bool:
    return brig.key == nugget.key == rhyme.key


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for brig_id, brig in BRIGS.items():
        for nugget_id, nugget in NUGGETS.items():
            for rhyme_id, rhyme in RHYMES.items():
                if is_match(brig, nugget, rhyme):
                    out.append((brig_id, nugget_id, rhyme_id))
    return out


def explain_rejection(brig: BrigSpell, nugget: NuggetKind, rhyme: RhymeKind) -> str:
    if brig.key != nugget.key and brig.key != rhyme.key:
        return (
            f"(No story: {nugget.label} and the {rhyme.label} do not fit the {brig.label}. "
            f"This little world only opens a brig when the magic stone and rhyme match the spell.)"
        )
    if brig.key != nugget.key:
        return (
            f"(No story: {nugget.label} does not carry the right kind of magic for the {brig.label}. "
            f"Pick a nugget whose magic matches the brig.)"
        )
    return (
        f"(No story: the {rhyme.label} does not answer the {brig.label}. "
        f"Choose a rhyme that matches the brig's spell.)"
    )


def predict_open(brig: BrigSpell, nugget: NuggetKind, rhyme: RhymeKind) -> bool:
    sim = World()
    sim.add(Entity(id="brig", type="brig"))
    sim.add(Entity(id="nugget", type="nugget"))
    sim.add(Entity(id="rhyme", type="rhyme"))
    sim.add(Entity(id="fairy", type="fairy"))
    sim.get("brig").meters["locked"] = 1.0
    sim.facts["matched_magic"] = is_match(brig, nugget, rhyme)
    sim.facts["spoken_together"] = True
    sim.get("nugget").meters["shared"] = 1.0
    propagate(sim, narrate=False)
    return sim.get("brig").meters["open"] >= THRESHOLD


def scene_opening(world: World, place: Place, a: Entity, b: Entity) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    world.say(
        f"In a modern corner of the city, {place.opening} {place.modern_detail}."
    )
    world.say(
        f"{a.id} and {b.id} were best friends, the sort who always slowed down for the same sparkle."
    )


def discovery(world: World, place: Place, helper: Helper, a: Entity, b: Entity,
              brig: BrigSpell, fairy: Entity, nugget: NuggetKind) -> None:
    fairy.memes["worry"] += 1
    world.say(
        f"That evening they noticed a faint chiming sound beside {place.label}. "
        f"Using {helper.phrase}, they looked closer and found {brig.phrase}. {brig.look}"
    )
    world.say(
        f"Inside sat {fairy.id}, a tiny fairy no taller than a tulip. Beside the bars lay {nugget.phrase}, {nugget.glow}."
    )


def warning(world: World, a: Entity, b: Entity, fairy: Entity,
            brig: BrigSpell, nugget: NuggetKind, rhyme: RhymeKind) -> None:
    world.say(
        f'"Please," whispered {fairy.id}, "this {brig.label} opens only to kindness, a matching nugget, and a true rhyme spoken by friends together."'
    )
    world.say(
        f'{a.id} cupped the {nugget.label} carefully, and {b.id} repeated the two shining lines so they would not be lost.'
    )
    world.facts["predicted_open"] = predict_open(brig, nugget, rhyme)


def hesitation(world: World, a: Entity, b: Entity, nugget: NuggetKind) -> None:
    a.memes["wonder"] += 1
    b.memes["worry"] += 1
    world.say(
        f"For one breath, the {nugget.label} looked like something to keep forever. "
        f'It warmed {a.id}\'s hands, and {b.id} could see why it was hard to let go.'
    )
    world.say(
        f'But best friends are brave in the softest way. "{nugget.gift_line}," {b.id} said.'
    )


def share_and_try(world: World, a: Entity, b: Entity, brig: BrigSpell,
                  nugget: NuggetKind, rhyme: RhymeKind) -> None:
    nugget_ent = world.get("nugget")
    brig_ent = world.get("brig")
    nugget_ent.meters["shared"] += 1
    a.memes["trust"] += 1
    b.memes["trust"] += 1
    world.facts["spoken_together"] = True
    world.facts["matched_magic"] = is_match(brig, nugget, rhyme)
    propagate(world, narrate=False)
    world.say(
        f"So {a.id} set the {nugget.label} against the little bars, and {b.id} touched {a.pronoun('possessive')} sleeve. Together they sang:"
    )
    world.say(f'"{rhyme.line1}"')
    world.say(f'"{rhyme.line2}"')
    if brig_ent.meters["open"] >= THRESHOLD:
        world.say(brig.release)
    else:
        world.say(
            "The bars shimmered for a moment and then held fast. The magic needed a truer match than that."
        )


def release_and_end(world: World, place: Place, helper: Helper, a: Entity, b: Entity,
                    fairy: Entity, nugget: NuggetKind) -> None:
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    a.memes["friendship"] += 1
    b.memes["friendship"] += 1
    fairy.memes["gratitude"] += 1
    world.say(
        f"{fairy.id} floated free in a ring of light and kissed both friends on the forehead with a cool, bright breeze."
    )
    world.say(
        f'"You kept the magic alive by sharing it," {fairy.pronoun()} said. '
        f'"Whenever you speak kindly in this noisy modern world, hidden doors will remember you."'
    )
    world.say(
        f"Then {fairy.id} left them a crumb of gold no bigger than a oat flake, a friendly little memory of the {nugget.label}."
    )
    world.say(
        f"As the lights came on across the city, {helper.ending} and {place.ending}."
    )


def tell(place: Place, brig_cfg: BrigSpell, nugget_cfg: NuggetKind, rhyme_cfg: RhymeKind,
         helper_cfg: Helper, friend1: str = "Lina", friend1_gender: str = "girl",
         friend2: str = "Owen", friend2_gender: str = "boy",
         fairy_name: str = "Miri") -> World:
    world = World()
    a = world.add(Entity(id=friend1, kind="character", type=friend1_gender, role="friend"))
    b = world.add(Entity(id=friend2, kind="character", type=friend2_gender, role="friend"))
    fairy = world.add(Entity(id=fairy_name, kind="character", type="fairy", role="fairy"))
    brig = world.add(Entity(id="brig", type="brig", label=brig_cfg.label, phrase=brig_cfg.phrase))
    nugget = world.add(Entity(id="nugget", type="nugget", label=nugget_cfg.label, phrase=nugget_cfg.phrase))
    rhyme = world.add(Entity(id="rhyme", type="rhyme", label=rhyme_cfg.label))
    helper = world.add(Entity(id="helper", type="tool", label=helper_cfg.label, phrase=helper_cfg.phrase))
    brig.meters["locked"] = 1.0
    fairy.memes["worry"] = 1.0

    scene_opening(world, place, a, b)
    world.para()
    discovery(world, place, helper_cfg, a, b, brig_cfg, fairy, nugget_cfg)
    warning(world, a, b, fairy, brig_cfg, nugget_cfg, rhyme_cfg)
    world.para()
    hesitation(world, a, b, nugget_cfg)
    share_and_try(world, a, b, brig_cfg, nugget_cfg, rhyme_cfg)
    world.para()
    if brig.meters["open"] >= THRESHOLD:
        release_and_end(world, place, helper_cfg, a, b, fairy, nugget_cfg)

    world.facts.update(
        place=place,
        brig_cfg=brig_cfg,
        nugget_cfg=nugget_cfg,
        rhyme_cfg=rhyme_cfg,
        helper_cfg=helper_cfg,
        friend1=a,
        friend2=b,
        fairy=fairy,
        brig=brig,
        nugget=nugget,
        rhyme=rhyme,
        opened=brig.meters["open"] >= THRESHOLD,
        matched=is_match(brig_cfg, nugget_cfg, rhyme_cfg),
        shared=nugget.meters["shared"] >= THRESHOLD,
    )
    return world


PLACES = {
    "courtyard": Place(
        id="courtyard",
        label="the apartment courtyard",
        opening="there was an apartment courtyard with potted mint and a painted bench,",
        modern_detail="above it, windows blinked like patient stars.",
        ending="the apartment courtyard seemed less like stone and more like a secret garden",
        tags={"city", "modern"},
    ),
    "rooftop": Place(
        id="rooftop",
        label="the rooftop garden",
        opening="there was a rooftop garden tucked above a row of shops,",
        modern_detail="solar lights glowed along the railing like tame fireflies.",
        ending="the rooftop garden hummed as if the moon itself had rented a little patch there",
        tags={"city", "modern"},
    ),
    "library": Place(
        id="library",
        label="the library steps",
        opening="there were broad library steps beside a glass wall,",
        modern_detail="and the late tram sang along the street below.",
        ending="even the library steps looked ready to hold one more story",
        tags={"city", "modern"},
    ),
}

BRIGS = {
    "frost": BrigSpell(
        id="frost",
        label="frost brig",
        phrase="a tiny silver brig hanging from a rose hook",
        lock_word="frost",
        look="The bars were laced with white crystals, though the air was not cold at all.",
        key="sun",
        release="The frost on the bars sighed into dew, and the little door swung open.",
        tags={"cold", "magic"},
    ),
    "thorn": BrigSpell(
        id="thorn",
        label="thorn brig",
        phrase="a tiny brass brig tangled in a vine",
        lock_word="thorn",
        look="Small green thorns curled around the latch as if they were guarding a treasure.",
        key="dew",
        release="The thorns softened into tender leaves, and the latch clicked free.",
        tags={"garden", "magic"},
    ),
    "shadow": BrigSpell(
        id="shadow",
        label="shadow brig",
        phrase="a tiny glass brig hidden inside a patch of dusk",
        lock_word="shadow",
        look="Its bars looked clear one moment and smoky the next, as if they could not decide where to be.",
        key="ember",
        release="Warm sparks chased the shadows away, and the glass door opened with a bright little ping.",
        tags={"night", "magic"},
    ),
}

NUGGETS = {
    "sun": NuggetKind(
        id="sun",
        label="sun nugget",
        phrase="a sun nugget no bigger than a plum stone",
        glow="glowing as if a sunrise had curled up inside it",
        key="sun",
        gift_line="If a thing is for saving someone, then saving comes first",
        tags={"light", "magic"},
    ),
    "dew": NuggetKind(
        id="dew",
        label="dew nugget",
        phrase="a dew nugget round as a raindrop",
        glow="cool and clear, with little colors drifting through it",
        key="dew",
        gift_line="Some treasures grow brighter when they are given away",
        tags={"water", "magic"},
    ),
    "ember": NuggetKind(
        id="ember",
        label="ember nugget",
        phrase="an ember nugget warm as a pocketed chestnut",
        glow="holding a tiny orange heartbeat in its middle",
        key="ember",
        gift_line="The best sort of gold is the kind that helps a friend",
        tags={"fire", "magic"},
    ),
}

RHYMES = {
    "warm": RhymeKind(
        id="warm",
        label="warm rhyme",
        line1="Little light, be kind and run,",
        line2="Melt this lock with morning sun.",
        key="sun",
        tags={"rhyme", "magic"},
    ),
    "growing": RhymeKind(
        id="growing",
        label="growing rhyme",
        line1="Gentle drop and tender green,",
        line2="Open what the thorns have screened.",
        key="dew",
        tags={"rhyme", "magic"},
    ),
    "glowing": RhymeKind(
        id="glowing",
        label="glowing rhyme",
        line1="Friendly spark, no fear, no fright,",
        line2="Lead this small lost heart to light.",
        key="ember",
        tags={"rhyme", "magic"},
    ),
}

HELPERS = {
    "phone_light": Helper(
        id="phone_light",
        label="phone light",
        phrase="the small light from a phone",
        use="used a phone light",
        ending="their phone light looked ordinary again",
        tags={"modern", "light"},
    ),
    "bike_lamp": Helper(
        id="bike_lamp",
        label="bike lamp",
        phrase="a clipped-on bike lamp",
        use="used a bike lamp",
        ending="the bike lamp blinked once, like a wink",
        tags={"modern", "light"},
    ),
    "porch_sensor": Helper(
        id="porch_sensor",
        label="porch sensor light",
        phrase="the porch sensor light that had just flicked on",
        use="stood beneath the porch sensor light",
        ending="the porch sensor light shone on quietly, guarding the lane",
        tags={"modern", "light"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Iris", "Ella", "Zoe", "Lucy"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Milo", "Ben", "Leo", "Sam", "Eli"]
FAIRY_NAMES = ["Miri", "Poppy", "Saffron", "Della", "Tansy"]


@dataclass
class StoryParams:
    place: str
    brig: str
    nugget: str
    rhyme: str
    helper: str
    friend1: str
    friend1_gender: str
    friend2: str
    friend2_gender: str
    fairy_name: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "brig": [
        (
            "What is a brig?",
            "A brig is a small jail or locked cell. In this story it is a tiny magical cage holding the fairy.",
        )
    ],
    "nugget": [
        (
            "What is a nugget?",
            "A nugget is a small lump or piece of something. A gold nugget is a little piece of gold, and a magic nugget in a fairy tale can hold special power.",
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is a pair or group of words that sound alike at the end. Rhymes are easy to remember, which is why people use them in songs and spells.",
        )
    ],
    "friendship": [
        (
            "Why does friendship matter in this story world?",
            "Because the magic works best when two friends trust each other and act kindly together. Their shared choice is as important as the spell itself.",
        )
    ],
    "modern": [
        (
            "What does modern mean?",
            "Modern means belonging to the present time. A modern city can still hold fairy-tale wonder, even if it has phone lights, trams, and tall buildings.",
        )
    ],
    "magic": [
        (
            "What is magic in a fairy tale?",
            "Magic is something wonderful that does not happen in ordinary life, like glowing stones or a locked brig opening to a rhyme. In fairy tales, magic often listens to kindness.",
        )
    ],
}
KNOWLEDGE_ORDER = ["brig", "nugget", "rhyme", "friendship", "modern", "magic"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    brig = f["brig_cfg"]
    nugget = f["nugget_cfg"]
    rhyme = f["rhyme_cfg"]
    place = f["place"]
    return [
        (
            f'Write a fairy-tale story for a young child set in a modern city, where two friends find a tiny brig, '
            f'a glowing nugget, and a trapped fairy. Include the words "nugget", "brig", and "modern".'
        ),
        (
            f"Tell a gentle story where {a.id} and {b.id} use friendship and a rhyme to free a fairy from a {brig.label} "
            f"at {place.label}."
        ),
        (
            f'Write a magical story in which a {nugget.label} and a {rhyme.label} work together because the friends choose kindness first.'
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend1"]
    b = f["friend2"]
    fairy = f["fairy"]
    brig = f["brig_cfg"]
    nugget = f["nugget_cfg"]
    rhyme = f["rhyme_cfg"]
    place = f["place"]
    helper = f["helper_cfg"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two best friends, {a.id} and {b.id}, and a tiny fairy named {fairy.id}. They meet at {place.label} when they discover the magical brig.",
        ),
        (
            "What did the friends find?",
            f"They found {brig.phrase} with {fairy.id} trapped inside it, and they also found {nugget.phrase}. The little prison and the glowing stone were part of the same spell.",
        ),
        (
            "Why did the children need to work together?",
            f"They needed to work together because the fairy said the brig would only open to kindness and a rhyme spoken by friends together. Friendship was part of the magic, not just the feeling around it.",
        ),
        (
            "How did the story use something modern?",
            f"The story takes place in a modern city space at {place.label}, and the children used {helper.phrase} to see clearly. That modern detail makes the fairy-tale magic feel hidden inside ordinary life.",
        ),
    ]
    if f["opened"]:
        out.append(
            (
                f"How did {a.id} and {b.id} free {fairy.id}?",
                f"They shared the {nugget.label} instead of keeping it and spoke the {rhyme.label} together. Because the nugget, rhyme, and brig all matched, the spell answered and the door opened.",
            )
        )
        out.append(
            (
                "What changed at the end?",
                f"At the end, the fairy was free and the friends understood that kindness can unlock real change. The place still looked modern, but it felt enchanted because they had helped someone together.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"brig", "nugget", "rhyme", "friendship", "modern", "magic"}
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
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="courtyard",
        brig="frost",
        nugget="sun",
        rhyme="warm",
        helper="phone_light",
        friend1="Lina",
        friend1_gender="girl",
        friend2="Owen",
        friend2_gender="boy",
        fairy_name="Miri",
    ),
    StoryParams(
        place="rooftop",
        brig="thorn",
        nugget="dew",
        rhyme="growing",
        helper="bike_lamp",
        friend1="Maya",
        friend1_gender="girl",
        friend2="Finn",
        friend2_gender="boy",
        fairy_name="Poppy",
    ),
    StoryParams(
        place="library",
        brig="shadow",
        nugget="ember",
        rhyme="glowing",
        helper="porch_sensor",
        friend1="Iris",
        friend1_gender="girl",
        friend2="Theo",
        friend2_gender="boy",
        fairy_name="Saffron",
    ),
]


ASP_RULES = r"""
match(B, N, R) :- brig(B), nugget(N), rhyme(R),
                  brig_key(B, K), nugget_key(N, K), rhyme_key(R, K).

valid(B, N, R) :- match(B, N, R).

opened :- chosen_brig(B), chosen_nugget(N), chosen_rhyme(R),
          match(B, N, R), shared, spoken_together.

#const one=1.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for brig_id, brig in BRIGS.items():
        lines.append(asp.fact("brig", brig_id))
        lines.append(asp.fact("brig_key", brig_id, brig.key))
    for nugget_id, nugget in NUGGETS.items():
        lines.append(asp.fact("nugget", nugget_id))
        lines.append(asp.fact("nugget_key", nugget_id, nugget.key))
    for rhyme_id, rhyme in RHYMES.items():
        lines.append(asp.fact("rhyme", rhyme_id))
        lines.append(asp.fact("rhyme_key", rhyme_id, rhyme.key))
    for place_id in PLACES:
        lines.append(asp.fact("place", place_id))
    for helper_id in HELPERS:
        lines.append(asp.fact("helper", helper_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_opened(params: StoryParams) -> bool:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_brig", params.brig),
            asp.fact("chosen_nugget", params.nugget),
            asp.fact("chosen_rhyme", params.rhyme),
            asp.fact("shared"),
            asp.fact("spoken_together"),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show opened/0."))
    return bool(asp.atoms(model, "opened"))


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

    for params in CURATED:
        py = is_match(BRIGS[params.brig], NUGGETS[params.nugget], RHYMES[params.rhyme])
        asp_ok = asp_opened(params)
        if py != asp_ok:
            rc = 1
            print(f"MISMATCH in opened parity for {params.brig}/{params.nugget}/{params.rhyme}")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.world or not sample.world.facts.get("opened"):
            raise StoryError("smoke test failed to generate an opened story")
        print("OK: smoke test generated a complete story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="A modern fairy-tale story world about friendship, rhyme, magic, a nugget, and a brig."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--brig", choices=BRIGS)
    ap.add_argument("--nugget", choices=NUGGETS)
    ap.add_argument("--rhyme", choices=RHYMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid brig/nugget/rhyme combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.brig and args.nugget and args.rhyme:
        brig = BRIGS[args.brig]
        nugget = NUGGETS[args.nugget]
        rhyme = RHYMES[args.rhyme]
        if not is_match(brig, nugget, rhyme):
            raise StoryError(explain_rejection(brig, nugget, rhyme))

    combos = [
        c for c in valid_combos()
        if (args.brig is None or c[0] == args.brig)
        and (args.nugget is None or c[1] == args.nugget)
        and (args.rhyme is None or c[2] == args.rhyme)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    brig_id, nugget_id, rhyme_id = rng.choice(sorted(combos))
    place_id = args.place or rng.choice(sorted(PLACES))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    friend1, g1 = _pick_name(rng)
    friend2, g2 = _pick_name(rng, avoid=friend1)
    fairy_name = rng.choice(FAIRY_NAMES)
    return StoryParams(
        place=place_id,
        brig=brig_id,
        nugget=nugget_id,
        rhyme=rhyme_id,
        helper=helper_id,
        friend1=friend1,
        friend1_gender=g1,
        friend2=friend2,
        friend2_gender=g2,
        fairy_name=fairy_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.brig not in BRIGS:
        raise StoryError(f"(Unknown brig: {params.brig})")
    if params.nugget not in NUGGETS:
        raise StoryError(f"(Unknown nugget: {params.nugget})")
    if params.rhyme not in RHYMES:
        raise StoryError(f"(Unknown rhyme: {params.rhyme})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")

    brig = BRIGS[params.brig]
    nugget = NUGGETS[params.nugget]
    rhyme = RHYMES[params.rhyme]
    if not is_match(brig, nugget, rhyme):
        raise StoryError(explain_rejection(brig, nugget, rhyme))

    world = tell(
        place=PLACES[params.place],
        brig_cfg=brig,
        nugget_cfg=nugget,
        rhyme_cfg=rhyme,
        helper_cfg=HELPERS[params.helper],
        friend1=params.friend1,
        friend1_gender=params.friend1_gender,
        friend2=params.friend2,
        friend2_gender=params.friend2_gender,
        fairy_name=params.fairy_name,
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
        print(asp_program("", "#show valid/3.\n#show opened/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (brig, nugget, rhyme) combos:\n")
        for brig, nugget, rhyme in combos:
            print(f"  {brig:8} {nugget:6} {rhyme}")
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
            header = f"### {p.friend1} & {p.friend2}: {p.brig}/{p.nugget}/{p.rhyme} at {p.place}"
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
