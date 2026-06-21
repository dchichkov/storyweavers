#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/wiggle_dim_church_comfy_misunderstanding_cautionary_repetition.py
================================================================================================

A standalone story world for a tiny mystery tale about a child in a dim church
who mistakes a hidden wiggle for something spooky. The world is built around a
misunderstanding: a small, sensible hidden cause is mistaken for a scarier idea
because the place is dim and the source is partly covered by something comfy.

The story shape is intentionally small and classical:

- premise: a child waits quietly in a church while a grown-up works nearby
- tension: something in a dim corner gives a repeated wiggle and rustle
- misunderstanding: the child thinks it might be a ghost, thief, or tiny monster
- cautionary turn: instead of grabbing, poking, or sneaking closer alone, the
  child is told to get help and keep safe hands
- resolution: a grown-up checks, the real cause is revealed, and the ending
  image shows the church feeling friendly again

Run it
------
    python storyworlds/worlds/gpt-5.4/wiggle_dim_church_comfy_misunderstanding_cautionary_repetition.py
    python storyworlds/worlds/gpt-5.4/wiggle_dim_church_comfy_misunderstanding_cautionary_repetition.py --all
    python storyworlds/worlds/gpt-5.4/wiggle_dim_church_comfy_misunderstanding_cautionary_repetition.py --qa
    python storyworlds/worlds/gpt-5.4/wiggle_dim_church_comfy_misunderstanding_cautionary_repetition.py --verify
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
class Place:
    id: str
    label: str
    phrase: str
    dimness: int
    comfy_ok: set[str] = field(default_factory=set)
    sources: set[str] = field(default_factory=set)
    clue: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Cover:
    id: str
    label: str
    phrase: str
    comfy: bool = True
    hides: set[str] = field(default_factory=set)
    motion: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    motion: str
    reveal: str
    why_here: str
    caution: str
    place_ok: set[str] = field(default_factory=set)
    cover_ok: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Guess:
    id: str
    label: str
    phrase: str
    needs_dim: int = 1
    fits: set[str] = field(default_factory=set)
    line: str = ""
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


def _r_wiggle_fear(world: World) -> list[str]:
    child = world.get("child")
    hidden = world.get("hidden")
    if hidden.meters["wiggling"] < THRESHOLD:
        return []
    sig = ("wiggle_fear",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] += 1
    child.memes["curiosity"] += 1
    return []


def _r_guess_story(world: World) -> list[str]:
    child = world.get("child")
    guess = world.get("guess")
    hidden = world.get("hidden")
    if hidden.meters["wiggling"] < THRESHOLD or child.memes["fear"] < THRESHOLD:
        return []
    sig = ("guess_story", guess.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["mystery"] += 1
    return []


def _r_help_relief(world: World) -> list[str]:
    adult = world.get("adult")
    child = world.get("child")
    if adult.meters["checking"] < THRESHOLD:
        return []
    sig = ("help_relief",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="wiggle_fear", tag="emotion", apply=_r_wiggle_fear),
    Rule(name="guess_story", tag="emotion", apply=_r_guess_story),
    Rule(name="help_relief", tag="emotion", apply=_r_help_relief),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            world.say(sent)
    return produced


def valid_combo(place: Place, cover: Cover, source: Source, guess: Guess) -> bool:
    return (
        cover.comfy
        and cover.id in place.comfy_ok
        and source.id in place.sources
        and place.id in source.place_ok
        and cover.id in source.cover_ok
        and source.id in cover.hides
        and place.dimness >= guess.needs_dim
        and source.id in guess.fits
    )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out: list[tuple[str, str, str, str]] = []
    for place_id, place in PLACES.items():
        for cover_id, cover in COVERS.items():
            for source_id, source in SOURCES.items():
                for guess_id, guess in GUESSES.items():
                    if valid_combo(place, cover, source, guess):
                        out.append((place_id, cover_id, source_id, guess_id))
    return out


def explain_rejection(place: Place, cover: Cover, source: Source, guess: Guess) -> str:
    if cover.id not in place.comfy_ok:
        return (
            f"(No story: {cover.phrase} does not belong in {place.phrase}, so the church mystery "
            f"does not feel grounded there.)"
        )
    if source.id not in place.sources or place.id not in source.place_ok:
        return (
            f"(No story: {source.phrase} is not a sensible hidden cause in {place.phrase}.)"
        )
    if cover.id not in source.cover_ok or source.id not in cover.hides:
        return (
            f"(No story: {source.phrase} would not reasonably hide under {cover.phrase}.)"
        )
    if place.dimness < guess.needs_dim or source.id not in guess.fits:
        return (
            f"(No story: in this setup, mistaking it for {guess.phrase} would not be believable.)"
        )
    return "(No story: this combination does not make a sensible little mystery.)"


def predict_is_scary(world: World) -> dict:
    sim = world.copy()
    hidden = sim.get("hidden")
    hidden.meters["wiggling"] += 1
    propagate(sim, narrate=False)
    child = sim.get("child")
    return {
        "fear": child.memes["fear"],
        "mystery": child.memes["mystery"],
    }


def introduce(world: World, child: Entity, friend: Entity, adult: Entity, place: Place) -> None:
    world.say(
        f"On a quiet evening, {child.id} sat with {friend.id} in {place.phrase} while "
        f"{adult.label_word} stacked songbooks near the front."
    )
    world.say(
        f"The old church felt peaceful, but the lamps were low, and the back of the room "
        f"looked soft and wiggle-dim."
    )


def settle(world: World, child: Entity, friend: Entity, place: Place, cover: Cover) -> None:
    child.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"Beside a bench lay {cover.phrase}, looking so comfy that {friend.id} whispered "
        f"it made the stone room feel warm."
    )
    world.say(place.clue)


def first_wiggle(world: World, child: Entity, cover: Cover, source: Source) -> None:
    hidden = world.get("hidden")
    hidden.meters["wiggling"] += 1
    hidden.meters["rustling"] += 1
    propagate(world)
    world.say(
        f"Then {cover.phrase} gave {cover.motion}, and from under it came {source.sound}."
    )
    world.say(
        f'"Wiggle-dim, wiggle-dim," {child.id} whispered, because that was exactly how the corner felt.'
    )


def misunderstanding(world: World, child: Entity, friend: Entity, guess: Guess) -> None:
    child.memes["suspecting"] += 1
    world.say(
        f'{child.id} leaned close to {friend.id} and whispered, "{guess.line}"'
    )
    world.say(
        f"{friend.id}'s eyes widened too, and for a moment the small mystery grew bigger in both of them."
    )


def caution(world: World, adult: Entity, child: Entity, cover: Cover, source: Source) -> None:
    pred = predict_is_scary(world)
    world.facts["predicted_fear"] = pred["fear"]
    adult.memes["care"] += 1
    child.memes["obedience"] += 1
    world.say(
        f'{adult.label_word.capitalize()} heard the whispering and came over softly. '
        f'"If something strange is hiding under {cover.phrase}, do not grab it and do not put your face near it," '
        f'{adult.pronoun()} said. "{source.caution}"'
    )
    world.say(
        f"That warning made the mystery feel real, but it also gave {child.id} a safer job: stand back and ask for help."
    )


def repeat_wiggle(world: World, cover: Cover, source: Source) -> None:
    hidden = world.get("hidden")
    hidden.meters["wiggling"] += 1
    hidden.meters["rustling"] += 1
    propagate(world)
    world.say(
        f"Again came the little sign: {cover.motion}, {source.sound}, {cover.motion}. Again {world.get('child').id} thought, "
        f'"Wiggle-dim, wiggle-dim."'
    )


def reveal(world: World, adult: Entity, child: Entity, friend: Entity, source: Source, cover: Cover, place: Place) -> None:
    adult.meters["checking"] += 1
    propagate(world)
    world.say(
        f"{adult.label_word.capitalize()} bent down, lifted one edge of {cover.phrase}, and looked in without hurrying."
    )
    world.say(source.reveal)
    world.say(
        f"It had never been {world.get('guess').phrase} at all. {source.why_here}"
    )
    world.say(
        f"{child.id} let out a long breath, and even the church seemed less shadowy once the true answer had a small, ordinary face."
    )


def ending(world: World, child: Entity, friend: Entity, adult: Entity, source: Source, cover: Cover) -> None:
    child.memes["wonder"] += 1
    friend.memes["wonder"] += 1
    world.say(
        f'{adult.label_word.capitalize()} smiled. "Mysteries grow when we guess in the dark," {adult.pronoun()} said, '
        f'"but they get smaller when we look carefully and safely."'
    )
    world.say(
        f"After that, {child.id} and {friend.id} helped make a neat little bed with {cover.phrase}, and the once wiggle-dim corner "
        f"looked simply comfy."
    )
    world.say(
        f"When the room went quiet again, {child.id} still heard the church creak now and then, but it no longer sounded like danger. "
        f"It sounded like an old place settling down for the night."
    )


def tell(
    place: Place,
    cover: Cover,
    source: Source,
    guess: Guess,
    child_name: str,
    child_gender: str,
    friend_name: str,
    friend_gender: str,
    adult_type: str,
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, phrase=child_name, role="child"))
    friend = world.add(Entity(id="friend", kind="character", type=friend_gender, label=friend_name, phrase=friend_name, role="friend"))
    adult = world.add(Entity(id="adult", kind="character", type=adult_type, label="the grown-up", phrase="the grown-up", role="adult"))
    hidden = world.add(Entity(id="hidden", kind="thing", type="hidden", label=source.label, phrase=source.phrase, role="hidden"))
    guess_ent = world.add(Entity(id="guess", kind="thing", type="guess", label=guess.label, phrase=guess.phrase, role="guess"))

    world.facts["place"] = place
    world.facts["cover"] = cover
    world.facts["source_cfg"] = source
    world.facts["guess_cfg"] = guess
    world.facts["child_name"] = child_name
    world.facts["friend_name"] = friend_name

    introduce(world, child, friend, adult, place)
    settle(world, child, friend, place, cover)

    world.para()
    first_wiggle(world, child, cover, source)
    misunderstanding(world, child, friend, guess)
    caution(world, adult, child, cover, source)
    repeat_wiggle(world, cover, source)

    world.para()
    reveal(world, adult, child, friend, source, cover, place)
    ending(world, child, friend, adult, source, cover)

    world.facts.update(
        child=child,
        friend=friend,
        adult=adult,
        source=hidden,
        source_cfg=source,
        guess=guess_ent,
        guess_cfg=guess,
        revealed=True,
        safe_choice=child.memes["obedience"] >= THRESHOLD,
    )
    return world


PLACES = {
    "nave": Place(
        id="nave",
        label="church nave",
        phrase="the back of a small church",
        dimness=3,
        comfy_ok={"quilt", "coat"},
        sources={"kitten", "pigeon"},
        clue="Colored window light lay in soft patches on the floor, and the far pews hid their corners in shadow.",
        tags={"church", "dim"},
    ),
    "choir_loft": Place(
        id="choir_loft",
        label="choir loft",
        phrase="the narrow choir loft of the church",
        dimness=2,
        comfy_ok={"coat", "cushion"},
        sources={"pigeon", "mouse"},
        clue="Above the empty pews, the loft felt hushed, as if every sound had to tiptoe.",
        tags={"church", "dim"},
    ),
    "vestry": Place(
        id="vestry",
        label="vestry",
        phrase="the little side room beside the church hall",
        dimness=2,
        comfy_ok={"quilt", "cushion"},
        sources={"kitten", "mouse"},
        clue="The side room smelled faintly of wood polish and old paper, and one lamp left the corners dusky.",
        tags={"church", "dim"},
    ),
}

COVERS = {
    "quilt": Cover(
        id="quilt",
        label="quilt",
        phrase="a folded comfy quilt",
        comfy=True,
        hides={"kitten", "mouse"},
        motion="a small, bumpy wiggle",
        tags={"comfy", "fabric"},
    ),
    "coat": Cover(
        id="coat",
        label="coat",
        phrase="a pile of comfy winter coats",
        comfy=True,
        hides={"kitten", "mouse", "pigeon"},
        motion="one sleepy sleeve giving a twitch",
        tags={"comfy", "coat"},
    ),
    "cushion": Cover(
        id="cushion",
        label="cushion",
        phrase="a stack of comfy choir cushions",
        comfy=True,
        hides={"mouse", "pigeon"},
        motion="the top cushion tipping just a little",
        tags={"comfy", "cushion"},
    ),
}

SOURCES = {
    "kitten": Source(
        id="kitten",
        label="kitten",
        phrase="a lost kitten",
        sound="the faintest mew",
        motion="a soft pawing wiggle",
        reveal='Out peeped a tiny gray kitten, blinking as if it could not believe so many faces were looking back at it.',
        why_here="It had slipped in through an open side door and burrowed into the soft cloth to stay warm.",
        caution="Small animals can scratch when they are scared, so we let calm grown-up hands do the checking first.",
        place_ok={"nave", "vestry"},
        cover_ok={"quilt", "coat"},
        tags={"animal", "kitten"},
    ),
    "mouse": Source(
        id="mouse",
        label="mouse",
        phrase="a church mouse",
        sound="a papery scritch-scritch",
        motion="a quick shiver underneath",
        reveal='Under the cloth darted a church mouse with a crust crumb in its mouth, then it froze as still as a button.',
        why_here="It had found a quiet place and a dropped crumb and had tucked itself where the room felt safe and warm.",
        caution="Little wild things can nip or race under your shoes, so strange rustles are for grown-ups to check.",
        place_ok={"choir_loft", "vestry"},
        cover_ok={"quilt", "coat", "cushion"},
        tags={"animal", "mouse"},
    ),
    "pigeon": Source(
        id="pigeon",
        label="pigeon",
        phrase="a trapped pigeon",
        sound="a muffled flutter",
        motion="a feathery bump from below",
        reveal='A dusty pigeon shuffled out, all neck-bobs and worried eyes, with one wing tangled in a loose ribbon from a decoration box.',
        why_here="It had blundered in through a high opening and hidden in the nearest soft-looking pile when the room felt too strange.",
        caution="A flapping bird can burst out fast, so the safe choice is to stand back and call for help.",
        place_ok={"nave", "choir_loft"},
        cover_ok={"coat", "cushion"},
        tags={"animal", "bird"},
    ),
}

GUESSES = {
    "ghost": Guess(
        id="ghost",
        label="ghost",
        phrase="a ghost",
        needs_dim=2,
        fits={"kitten", "mouse", "pigeon"},
        line="Do you think it is a ghost trying to hide in the dark?",
        tags={"mystery", "ghost"},
    ),
    "thief": Guess(
        id="thief",
        label="thief",
        phrase="a tiny thief",
        needs_dim=2,
        fits={"mouse", "pigeon"},
        line="Maybe it is a tiny thief sneaking around the church.",
        tags={"mystery", "thief"},
    ),
    "monster": Guess(
        id="monster",
        label="monster",
        phrase="a little monster",
        needs_dim=1,
        fits={"kitten", "mouse", "pigeon"},
        line="Maybe it is a little monster curled up under there.",
        tags={"mystery", "monster"},
    ),
}


@dataclass
class StoryParams:
    place: str
    cover: str
    source: str
    guess: str
    child_name: str
    child_gender: str
    friend_name: str
    friend_gender: str
    adult_type: str
    seed: Optional[int] = None


GIRL_NAMES = ["Lila", "Mara", "Nina", "Elsie", "Ruby", "Tess", "Clara", "Mina"]
BOY_NAMES = ["Owen", "Milo", "Evan", "Finn", "Theo", "Jude", "Noah", "Sam"]

KNOWLEDGE = {
    "church": [
        (
            "What is a church?",
            "A church is a place where people gather quietly to pray, sing, and be together. Many churches are old buildings, so they can creak and echo in ways that sound mysterious."
        )
    ],
    "dim": [
        (
            "What does dim mean?",
            "Dim means not very bright. In a dim place, shapes are harder to see clearly, so it is easier to guess wrong about what you are looking at."
        )
    ],
    "comfy": [
        (
            "What does comfy mean?",
            "Comfy means soft, warm, and nice to rest in or on. Blankets, coats, and cushions can all feel comfy."
        )
    ],
    "kitten": [
        (
            "Why might a kitten hide in cloth?",
            "A kitten may hide in soft cloth because it feels warm and safe there. Small animals often burrow into cozy places when they are scared or tired."
        )
    ],
    "mouse": [
        (
            "Why do mice make tiny rustling sounds?",
            "Mice have light little feet, so they make small scritching and rustling noises as they move. In a quiet room, those sounds can seem bigger than they are."
        )
    ],
    "bird": [
        (
            "Why should you stand back from a trapped bird?",
            "A trapped bird can flap suddenly when it is frightened. Standing back gives it space and lets a grown-up help more safely."
        )
    ],
    "ask_help": [
        (
            "What should you do if something strange moves in the dark?",
            "You should stop, keep your hands back, and get a grown-up. Asking for help is safer than poking at something you cannot see clearly."
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks something is one thing, but it is really another. In the dark, a misunderstanding can happen because your eyes and mind are both guessing."
        )
    ],
}

KNOWLEDGE_ORDER = ["church", "dim", "comfy", "kitten", "mouse", "bird", "ask_help", "misunderstanding"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    cover = f["cover"]
    source = f["source_cfg"]
    guess = f["guess_cfg"]
    child_name = f["child_name"]
    return [
        f'Write a gentle mystery for a 3-to-5-year-old set in a church that includes the words "wiggle-dim" and "comfy".',
        f"Tell a short cautionary story where {child_name} sees {cover.phrase} move in {place.phrase} and wrongly suspects {guess.phrase}, but a grown-up reveals the true cause safely.",
        f"Write a repetitive, child-facing mystery in which a hidden {source.label} makes a small wiggle, the child whispers the same phrase twice, and the ending turns fear into relief.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    friend = f["friend"]
    adult = f["adult"]
    place = f["place"]
    cover = f["cover"]
    source = f["source_cfg"]
    guess = f["guess_cfg"]
    pw = adult.label_word

    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            f"It happens in {place.phrase}. The church is quiet and dim, which is why the small movement feels mysterious at first."
        ),
        (
            f"What made {child.label} think something strange was there?",
            f"{cover.phrase} moved and made {source.sound}. In the dim room, that little wiggle was enough to make {child.label} imagine {guess.phrase}."
        ),
        (
            f"What was the misunderstanding?",
            f"{child.label} thought the hidden thing might be {guess.phrase}, but it was really {source.phrase}. The dark corner made the wrong idea feel possible until a grown-up checked."
        ),
        (
            f"What did {pw} tell the children to do?",
            f"{pw.capitalize()} told them not to grab at the hidden thing and not to put their faces near it. {adult.pronoun().capitalize()} wanted them to stand back and ask for help instead."
        ),
        (
            "Why was that good advice?",
            f"It was good advice because the children could not see clearly what was hiding there. A scared animal can scratch, nip, or flap suddenly, so slow grown-up help was safer."
        ),
        (
            "How did the story end?",
            f"{pw.capitalize()} lifted the cloth carefully and revealed {source.phrase}, so the mystery became ordinary again. At the end, the once wiggle-dim corner looked comfy instead of scary."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"church", "dim", "comfy", "ask_help", "misunderstanding"}
    source = world.facts["source_cfg"]
    if "kitten" in source.tags:
        tags.add("kitten")
    if "mouse" in source.tags:
        tags.add("mouse")
    if "bird" in source.tags:
        tags.add("bird")
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
        bits = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="nave",
        cover="quilt",
        source="kitten",
        guess="ghost",
        child_name="Lila",
        child_gender="girl",
        friend_name="Owen",
        friend_gender="boy",
        adult_type="mother",
    ),
    StoryParams(
        place="choir_loft",
        cover="cushion",
        source="pigeon",
        guess="thief",
        child_name="Milo",
        child_gender="boy",
        friend_name="Ruby",
        friend_gender="girl",
        adult_type="father",
    ),
    StoryParams(
        place="vestry",
        cover="coat",
        source="mouse",
        guess="monster",
        child_name="Elsie",
        child_gender="girl",
        friend_name="Finn",
        friend_gender="boy",
        adult_type="mother",
    ),
]


ASP_RULES = r"""
valid(Pl, Cv, So, Gu) :- place(Pl), cover(Cv), source(So), guess(Gu),
                         comfy(Cv), place_accepts_cover(Pl, Cv),
                         place_accepts_source(Pl, So),
                         source_place_ok(So, Pl),
                         source_cover_ok(So, Cv),
                         cover_hides(Cv, So),
                         dimness(Pl, D), guess_needs_dim(Gu, N), D >= N,
                         guess_fits(Gu, So).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("dimness", place_id, place.dimness))
        for cover_id in sorted(place.comfy_ok):
            lines.append(asp.fact("place_accepts_cover", place_id, cover_id))
        for source_id in sorted(place.sources):
            lines.append(asp.fact("place_accepts_source", place_id, source_id))
    for cover_id, cover in COVERS.items():
        lines.append(asp.fact("cover", cover_id))
        if cover.comfy:
            lines.append(asp.fact("comfy", cover_id))
        for source_id in sorted(cover.hides):
            lines.append(asp.fact("cover_hides", cover_id, source_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for place_id in sorted(source.place_ok):
            lines.append(asp.fact("source_place_ok", source_id, place_id))
        for cover_id in sorted(source.cover_ok):
            lines.append(asp.fact("source_cover_ok", source_id, cover_id))
    for guess_id, guess in GUESSES.items():
        lines.append(asp.fact("guess", guess_id))
        lines.append(asp.fact("guess_needs_dim", guess_id, guess.needs_dim))
        for source_id in sorted(guess.fits):
            lines.append(asp.fact("guess_fits", guess_id, source_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "church" not in sample.story.lower():
        raise StoryError("Smoke test failed: story lost its church setting.")


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
    try:
        smoke_test()
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tiny mystery storyworld: a wiggle in a dim church is misunderstood until a grown-up checks safely."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--cover", choices=COVERS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--guess", choices=GUESSES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--friend-name")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--adult-type", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible mystery setups from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.cover and args.source and args.guess:
        if not valid_combo(PLACES[args.place], COVERS[args.cover], SOURCES[args.source], GUESSES[args.guess]):
            raise StoryError(explain_rejection(PLACES[args.place], COVERS[args.cover], SOURCES[args.source], GUESSES[args.guess]))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.cover is None or combo[1] == args.cover)
        and (args.source is None or combo[2] == args.source)
        and (args.guess is None or combo[3] == args.guess)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, cover_id, source_id, guess_id = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or _pick_name(rng, child_gender)
    friend_name = args.friend_name or _pick_name(rng, friend_gender, avoid=child_name)
    adult_type = args.adult_type or rng.choice(["mother", "father"])
    return StoryParams(
        place=place_id,
        cover=cover_id,
        source=source_id,
        guess=guess_id,
        child_name=child_name,
        child_gender=child_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        adult_type=adult_type,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        cover = COVERS[params.cover]
        source = SOURCES[params.source]
        guess = GUESSES[params.guess]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err})") from err

    if not valid_combo(place, cover, source, guess):
        raise StoryError(explain_rejection(place, cover, source, guess))

    world = tell(
        place=place,
        cover=cover,
        source=source,
        guess=guess,
        child_name=params.child_name,
        child_gender=params.child_gender,
        friend_name=params.friend_name,
        friend_gender=params.friend_gender,
        adult_type=params.adult_type,
    )
    story = world.render().replace(" child ", f" {params.child_name} ").replace(" friend ", f" {params.friend_name} ")
    story = story.replace("child", params.child_name).replace("friend", params.friend_name)
    return StorySample(
        params=params,
        story=story,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, cover, source, guess) combos:\n")
        for place, cover, source, guess in combos:
            print(f"  {place:10} {cover:8} {source:8} {guess}")
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
            header = f"### {p.child_name}: {p.source} under {p.cover} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
