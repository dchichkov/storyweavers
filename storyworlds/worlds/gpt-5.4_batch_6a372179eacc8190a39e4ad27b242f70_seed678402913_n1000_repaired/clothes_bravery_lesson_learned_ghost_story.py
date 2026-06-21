#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py
========================================================================

A small storyworld about a child who thinks a ghost is nearby, then bravely
checks the strange shape and learns that fluttering clothes can look spooky in
the dark.

The world model tracks simple physical meters (darkness, breeze, swaying,
distance, truth) and emotional memes (fear, bravery, relief, trust, lesson).
Stories are generated from simulated state rather than by swapping nouns into a
fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py
    python storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py --place attic --clothes sheet --light lantern
    python storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py --clothes boots
    python storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/clothes_bravery_lesson_learned_ghost_story.py --verify
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

# Make storyworlds/results.py importable when this nested script is run directly.
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "aunt", "woman"}
        male = {"boy", "father", "grandfather", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    dark_word: str
    breeze_from: str
    hanging_spot: str
    ending_image: str
    dim: bool = True
    breezy: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Clothes:
    id: str
    label: str
    phrase: str
    plural: bool
    hanging_phrase: str
    reveal_text: str
    ghostly: bool
    tags: set[str] = field(default_factory=set)

    def it(self) -> str:
        return "them" if self.plural else "it"

    def they(self) -> str:
        return "they" if self.plural else "it"

    def were(self) -> str:
        return "were" if self.plural else "was"


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    beam_text: str
    safe: bool = True
    power: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Sound:
    id: str
    text: str
    noise_word: str
    spooky: bool = True
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


def _r_flutter(world: World) -> list[str]:
    place = world.get("place")
    clothes = world.get("clothes")
    if place.meters["breeze"] < THRESHOLD or clothes.meters["hanging"] < THRESHOLD:
        return []
    sig = ("flutter", clothes.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    clothes.meters["sway"] += 1
    place.meters["rustle"] += 1
    return ["__flutter__"]


def _r_spook(world: World) -> list[str]:
    hero = world.get("hero")
    place = world.get("place")
    clothes = world.get("clothes")
    if place.meters["dark"] < THRESHOLD or clothes.meters["sway"] < THRESHOLD:
        return []
    sig = ("spook", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["fear"] += 1
    hero.memes["wonder"] += 1
    hero.meters["ghost_guess"] += 1
    return ["__spook__"]


CAUSAL_RULES = [
    Rule(name="flutter", tag="physical", apply=_r_flutter),
    Rule(name="spook", tag="emotional", apply=_r_spook),
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
        for s in produced:
            world.say(s)
    return produced


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the old attic at Grandma's house",
        dark_word="dim",
        breeze_from="a cracked round window",
        hanging_spot="a line near the rafters",
        ending_image="The attic no longer looked haunted; it looked like a place full of stories and ordinary things.",
        tags={"attic", "dark"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the long upstairs hallway",
        dark_word="shadowy",
        breeze_from="an open window at the end of the hall",
        hanging_spot="a tall coat rack",
        ending_image="The hallway felt calm again, with family things hanging quietly where they belonged.",
        tags={"hallway", "dark"},
    ),
    "porch": Place(
        id="porch",
        label="porch",
        phrase="the back porch after sunset",
        dark_word="dusky",
        breeze_from="the evening wind through the screen door",
        hanging_spot="the clothesline by the steps",
        ending_image="The porch looked friendly again, with the night air moving softly around the clean wash.",
        tags={"porch", "night"},
    ),
}

CLOTHES_REGISTRY = {
    "sheet": Clothes(
        id="sheet",
        label="sheet",
        phrase="a pale bed sheet",
        plural=False,
        hanging_phrase="hung long and loose",
        reveal_text="It was only a clean sheet, lifted and folded by the breeze.",
        ghostly=True,
        tags={"sheet", "clothes"},
    ),
    "nightgown": Clothes(
        id="nightgown",
        label="nightgown",
        phrase="a white nightgown",
        plural=False,
        hanging_phrase="hung from a hook and swayed at the hem",
        reveal_text="It was only a white nightgown waiting to be put away.",
        ghostly=True,
        tags={"nightgown", "clothes"},
    ),
    "shirts": Clothes(
        id="shirts",
        label="shirts",
        phrase="two white shirts",
        plural=True,
        hanging_phrase="hung side by side and flapped together",
        reveal_text="They were only two shirts moving on their hangers.",
        ghostly=True,
        tags={"shirt", "clothes"},
    ),
    "boots": Clothes(
        id="boots",
        label="boots",
        phrase="muddy rain boots",
        plural=True,
        hanging_phrase="sat by the wall",
        reveal_text="They were only boots by the wall.",
        ghostly=False,
        tags={"boots", "clothes"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        beam_text="clicked on the flashlight, and a bright path opened through the dark",
        power=2,
        tags={"flashlight", "light"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a camping lantern",
        beam_text="lifted the lantern, and its warm glow spread over the floorboards",
        power=2,
        tags={"lantern", "light"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a little plug-in night-light",
        beam_text="plugged in the night-light, and a gentle gold circle appeared by the wall",
        power=1,
        tags={"nightlight", "light"},
    ),
}

SOUNDS = {
    "rustle": Sound(
        id="rustle",
        text="A soft rustle came from the dark.",
        noise_word="rustle",
        tags={"rustle"},
    ),
    "tap": Sound(
        id="tap",
        text="Something tapped and brushed in the dark.",
        noise_word="tap",
        tags={"tap"},
    ),
    "whuff": Sound(
        id="whuff",
        text="The wind made a low whuffing sound nearby.",
        noise_word="whuff",
        tags={"wind"},
    ),
}

GIRL_NAMES = ["Lila", "Mia", "Nora", "Ava", "Lucy", "Ella", "Rose", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Sam", "Theo", "Max", "Finn", "Noah", "Eli"]
TRAITS = ["careful", "curious", "quiet", "thoughtful", "steady", "gentle"]


def valid_combo(place_id: str, clothes_id: str, light_id: str) -> bool:
    place = PLACES[place_id]
    clothes = CLOTHES_REGISTRY[clothes_id]
    light = LIGHTS[light_id]
    return place.dim and place.breezy and clothes.ghostly and light.safe and light.power >= 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id in PLACES:
        for clothes_id in CLOTHES_REGISTRY:
            for light_id in LIGHTS:
                if valid_combo(place_id, clothes_id, light_id):
                    combos.append((place_id, clothes_id, light_id))
    return combos


def explain_rejection(place: Place, clothes: Clothes, light: Light) -> str:
    if not clothes.ghostly:
        return (
            f"(No story: {clothes.phrase} would not plausibly look like a ghost in {place.phrase}. "
            f"Pick hanging clothes like a sheet, nightgown, or shirts.)"
        )
    if not place.dim or not place.breezy:
        return (
            f"(No story: {place.phrase} is missing the darkness or breeze that makes the mistake believable.)"
        )
    if not light.safe or light.power < 1:
        return f"(No story: {light.label} is not a reasonable safe light for checking the dark.)"
    return "(No story: this combination does not support the ghost misunderstanding.)"


@dataclass
class StoryParams:
    place: str
    clothes: str
    light: str
    sound: str
    name: str
    gender: str
    elder: str
    elder_type: str
    trait: str
    seed: Optional[int] = None


def predict_spook(place: Place, clothes: Clothes) -> bool:
    return place.dim and place.breezy and clothes.ghostly


def introduce(world: World, hero: Entity, elder: Entity, place: Place) -> None:
    world.say(
        f"One evening, {hero.id} was helping {hero.pronoun('possessive')} {elder.label_word} in {place.phrase}."
    )
    world.say(
        f"They were gathering old clothes and folding things before bed."
    )


def settle_place(world: World, place: Place, clothes: Clothes) -> None:
    room = world.get("place")
    cloth = world.get("clothes")
    room.meters["dark"] = 1.0 if place.dim else 0.0
    room.meters["breeze"] = 1.0 if place.breezy else 0.0
    cloth.meters["hanging"] = 1.0
    world.say(
        f"The air was {place.dark_word}, and a little breeze slipped in through {place.breeze_from}."
    )
    world.say(
        f"Near {place.hanging_spot}, {clothes.phrase} {clothes.hanging_phrase}."
    )


def strange_sound(world: World, sound: Sound) -> None:
    world.say(sound.text)


def fear_beat(world: World, hero: Entity, clothes: Clothes) -> None:
    propagate(world, narrate=False)
    if hero.meters["ghost_guess"] >= THRESHOLD:
        be = "They looked" if clothes.plural else "It looked"
        world.say(
            f"{hero.id} froze. In the shifting dark, {be.lower()} almost like a ghost."
        )
        world.say(
            f"A shiver ran through {hero.pronoun('object')}, and for a moment {hero.pronoun()} wanted to run back downstairs."
        )


def choose_bravery(world: World, hero: Entity, elder: Entity, light: Light) -> None:
    hero.memes["bravery"] += 1
    hero.memes["trust"] += 1
    world.say(
        f'But {hero.id} took a slow breath and whispered, "I am scared, but I can still be brave."'
    )
    world.say(
        f"{elder.label_word.capitalize()} stayed close and handed {hero.pronoun('object')} {light.phrase}."
    )


def investigate(world: World, hero: Entity, light: Light) -> None:
    hero.meters["distance"] += 1
    world.say(
        f"{hero.pronoun().capitalize()} stepped nearer, {light.beam_text}."
    )


def discover(world: World, hero: Entity, clothes: Clothes) -> None:
    hero.meters["truth"] += 1
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"Then {hero.id} saw the truth. {clothes.reveal_text}"
    )
    laugh = "They both laughed softly." if clothes.plural else "Both of them laughed softly."
    world.say(laugh)


def lesson(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f'"Sometimes dark shapes look stranger than they really are," {elder.label_word} said.'
    )
    world.say(
        f'{hero.id} nodded. "{hero.pronoun().capitalize()} will look carefully before calling something a ghost next time," {hero.pronoun()} said.'
    )


def ending(world: World, hero: Entity, place: Place, clothes: Clothes) -> None:
    hero.memes["wonder"] += 1
    world.say(
        f"Together they folded the clothes at last."
    )
    world.say(
        f"{place.ending_image}"
    )


def tell(
    place: Place,
    clothes: Clothes,
    light: Light,
    sound: Sound,
    *,
    hero_name: str,
    hero_gender: str,
    elder_name: str,
    elder_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            role="hero",
            traits=[trait],
            label=hero_name,
        )
    )
    elder = world.add(
        Entity(
            id=elder_name,
            kind="character",
            type=elder_type,
            role="elder",
            label=elder_name,
        )
    )
    room = world.add(
        Entity(
            id="place",
            kind="thing",
            type=place.id,
            label=place.label,
            phrase=place.phrase,
            tags=set(place.tags),
        )
    )
    cloth = world.add(
        Entity(
            id="clothes",
            kind="thing",
            type="clothes",
            label=clothes.label,
            phrase=clothes.phrase,
            tags=set(clothes.tags),
        )
    )
    lamp = world.add(
        Entity(
            id="light",
            kind="thing",
            type="light",
            label=light.label,
            phrase=light.phrase,
            tags=set(light.tags),
        )
    )

    introduce(world, hero, elder, place)
    settle_place(world, place, clothes)

    world.para()
    strange_sound(world, sound)
    fear_beat(world, hero, clothes)

    world.para()
    choose_bravery(world, hero, elder, light)
    investigate(world, hero, light)
    discover(world, hero, clothes)

    world.para()
    lesson(world, hero, elder)
    ending(world, hero, place, clothes)

    world.facts.update(
        hero=hero,
        elder=elder,
        place_cfg=place,
        clothes_cfg=clothes,
        light_cfg=light,
        sound_cfg=sound,
        feared=hero.memes["relief"] >= THRESHOLD,
        brave=hero.memes["bravery"] >= THRESHOLD,
        learned=hero.memes["lesson"] >= THRESHOLD,
        truth_found=hero.meters["truth"] >= THRESHOLD,
        looked_like_ghost=hero.meters["ghost_guess"] >= THRESHOLD,
        place=room,
        clothes=cloth,
        light=lamp,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "Why can something ordinary look scary in the dark?",
            "In dim light, your eyes do not show every detail clearly. A moving shape can look spooky until you get closer and see what it really is."
        )
    ],
    "clothes": [
        (
            "Why can hanging clothes look like a person?",
            "Loose clothes can make a tall shape, especially when they hang from a hook or line. If the wind moves them, they may look alive for a moment."
        )
    ],
    "wind": [
        (
            "What does wind do to clothes on a line or rack?",
            "Wind pushes and lifts cloth. That can make clothes sway, flap, or rustle."
        )
    ],
    "light": [
        (
            "Why is a flashlight or lantern helpful in the dark?",
            "A safe light helps you see details. When you can see clearly, it is easier to tell what something really is."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery means doing the careful right thing even when you feel scared. It does not mean you never feel fear."
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "clothes", "wind", "light", "bravery"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place_cfg"]
    clothes = f["clothes_cfg"]
    light = f["light_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the word "clothes" and ends with a lesson about bravery.',
        f"Tell a spooky-but-safe story where {hero.id} sees {clothes.phrase} in {place.phrase}, thinks it might be a ghost, and bravely checks with {light.phrase}.",
        f"Write a story in which a child feels scared in the dark, learns the scary shape is only clothes, and ends wiser and calmer than before.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    place = f["place_cfg"]
    clothes = f["clothes_cfg"]
    light = f["light_cfg"]
    sound = f["sound_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was helping {hero.pronoun('possessive')} {elder.label_word} in {place.phrase}. The story follows how {hero.pronoun()} moved from fear to understanding."
        ),
        (
            f"Why did {hero.id} think there might be a ghost?",
            f"{sound.text[:-1]} In the {place.dark_word} air, {clothes.phrase} moved and looked strange, so {hero.id} mistook the shape for something ghostly."
        ),
        (
            f"How was {hero.id} brave?",
            f"{hero.id} was brave because {hero.pronoun()} felt scared but still chose to look carefully instead of running away. {elder.label_word.capitalize()} stayed close, and {hero.id} used {light.phrase} to find out the truth."
        ),
        (
            "What was the ghost really?",
            f"There was no ghost at all. {clothes.reveal_text}"
        ),
        (
            "What lesson did the child learn?",
            f"{hero.id} learned to look carefully before deciding that something is scary. The dark can make ordinary things seem strange, but calm checking can show what is really there."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"ghost", "clothes", "light", "bravery"}
    if world.facts["sound_cfg"].id == "whuff":
        tags.add("wind")
    else:
        tags.add("wind")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        clothes="sheet",
        light="lantern",
        sound="whuff",
        name="Lila",
        gender="girl",
        elder="Grandma",
        elder_type="grandmother",
        trait="steady",
    ),
    StoryParams(
        place="hallway",
        clothes="nightgown",
        light="flashlight",
        sound="tap",
        name="Ben",
        gender="boy",
        elder="Grandpa",
        elder_type="grandfather",
        trait="careful",
    ),
    StoryParams(
        place="porch",
        clothes="shirts",
        light="flashlight",
        sound="rustle",
        name="Nora",
        gender="girl",
        elder="Grandma",
        elder_type="grandmother",
        trait="curious",
    ),
]


ASP_RULES = r"""
valid(P,C,L) :- place(P), clothes(C), light(L), dim(P), breezy(P), ghostly(C), safe(L), power(L, Pow), Pow >= 1.

#show valid/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.dim:
            lines.append(asp.fact("dim", pid))
        if place.breezy:
            lines.append(asp.fact("breezy", pid))
    for cid, clothes in CLOTHES_REGISTRY.items():
        lines.append(asp.fact("clothes", cid))
        if clothes.ghostly:
            lines.append(asp.fact("ghostly", cid))
    for lid, light in LIGHTS.items():
        lines.append(asp.fact("light", lid))
        if light.safe:
            lines.append(asp.fact("safe", lid))
        lines.append(asp.fact("power", lid, light.power))
    return "\n".join(lines)


def asp_program(show_override: str = "") -> str:
    show = show_override.strip() or "#show valid/3."
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story or "ghost" not in sample.story.lower() and "clothes" not in sample.story.lower():
            raise StoryError("smoke test generated an empty or unreasonable story")
        print("OK: smoke-test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child mistakes fluttering clothes for a ghost, then learns a brave lesson."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clothes", choices=CLOTHES_REGISTRY)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clothes and args.light:
        place = PLACES[args.place]
        clothes = CLOTHES_REGISTRY[args.clothes]
        light = LIGHTS[args.light]
        if not valid_combo(args.place, args.clothes, args.light):
            raise StoryError(explain_rejection(place, clothes, light))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clothes is None or combo[1] == args.clothes)
        and (args.light is None or combo[2] == args.light)
    ]
    if not combos:
        if args.place and args.clothes and args.light:
            raise StoryError(
                explain_rejection(PLACES[args.place], CLOTHES_REGISTRY[args.clothes], LIGHTS[args.light])
            )
        raise StoryError("(No valid combination matches the given options.)")

    place_id, clothes_id, light_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder_type = args.elder_type or rng.choice(["grandmother", "grandfather", "mother", "father"])
    elder = {
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
        "mother": "Mom",
        "father": "Dad",
    }[elder_type]
    sound_id = args.sound or rng.choice(sorted(SOUNDS))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        clothes=clothes_id,
        light=light_id,
        sound=sound_id,
        name=name,
        gender=gender,
        elder=elder,
        elder_type=elder_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.clothes not in CLOTHES_REGISTRY:
        raise StoryError(f"(Unknown clothes choice: {params.clothes})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Unknown light choice: {params.light})")
    if params.sound not in SOUNDS:
        raise StoryError(f"(Unknown sound choice: {params.sound})")
    if not valid_combo(params.place, params.clothes, params.light):
        raise StoryError(
            explain_rejection(PLACES[params.place], CLOTHES_REGISTRY[params.clothes], LIGHTS[params.light])
        )

    world = tell(
        PLACES[params.place],
        CLOTHES_REGISTRY[params.clothes],
        LIGHTS[params.light],
        SOUNDS[params.sound],
        hero_name=params.name,
        hero_gender=params.gender,
        elder_name=params.elder,
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
        print(f"{len(combos)} compatible (place, clothes, light) combos:\n")
        for place, clothes, light in combos:
            print(f"  {place:8} {clothes:10} {light}")
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
            header = f"### {p.name}: {p.clothes} in {p.place} with {p.light}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
