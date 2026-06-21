#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py
========================================================================================

A gentle ghost-story storyworld about a child who notices strange signs around an
iconic aeroplane display, takes an antihistamine after a dusty sneeze, follows a
mystery clue, and solves the trouble with kindness.

The world model is intentionally small and classical:

- a place contains an iconic aeroplane and supports certain kinds of clues
- a ghost becomes restless when a keepsake is missing
- restlessness makes the room chilly and the aeroplane stir
- a dusty search makes the child sneeze until a caretaker gives antihistamine
- the child follows one clue to the hiding place of the keepsake
- a matching kindness act returns or honours the keepsake
- once the keepsake is handled kindly, the ghost settles and the haunting ends

Run it
------
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py --qa
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4/aeroplane_iconic_antihistamine_kindness_mystery_to_solve.py --verify
"""

from __future__ import annotations

import argparse
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
        female = {"girl", "woman", "mother", "aunt", "grandmother"}
        male = {"boy", "man", "father", "uncle", "grandfather"}
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
            "grandmother": "grandma",
        }.get(self.type, self.label or self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    iconic_line: str
    night_sound: str
    afford_clues: set[str] = field(default_factory=set)
    dust_level: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    hidden_in: str
    missing_from: str
    kindness_needed: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    sign: str
    points_to: str
    prose: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Kindness:
    id: str
    action: str
    result: str
    solves_for: set[str] = field(default_factory=set)
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


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_restless_haunt(world: World) -> list[str]:
    ghost = world.get("ghost")
    plane = world.get("plane")
    room = world.get("room")
    out: list[str] = []
    if ghost.meters["restless"] >= THRESHOLD:
        if ("haunt",) not in world.fired:
            world.fired.add(("haunt",))
            plane.meters["rattle"] += 1
            room.meters["chill"] += 1
            out.append("__haunt__")
    return out


def _r_medicine_calm(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.meters["medicine"] >= THRESHOLD and hero.meters["sneeze"] >= THRESHOLD:
        if ("calm",) not in world.fired:
            world.fired.add(("calm",))
            hero.meters["sneeze"] = 0.0
            hero.memes["steady"] += 1
            return ["__calm__"]
    return []


def _r_settle_ghost(world: World) -> list[str]:
    ghost = world.get("ghost")
    if ghost.meters["keepsake_returned"] >= THRESHOLD and ghost.meters["kindness_received"] >= THRESHOLD:
        if ("settled",) not in world.fired:
            world.fired.add(("settled",))
            ghost.meters["restless"] = 0.0
            ghost.meters["settled"] += 1
            world.get("room").meters["chill"] = 0.0
            world.get("plane").meters["rattle"] = 0.0
            return ["__settled__"]
    return []


CAUSAL_RULES = [
    Rule(name="restless_haunt", apply=_r_restless_haunt),
    Rule(name="medicine_calm", apply=_r_medicine_calm),
    Rule(name="settle_ghost", apply=_r_settle_ghost),
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


PLACES = {
    "museum_hall": Place(
        id="museum_hall",
        label="air museum hall",
        phrase="the old air museum hall",
        iconic_line="Above the polished floor hung an iconic silver aeroplane that every visitor looked up to see.",
        night_sound="its wires gave a tiny singing creak whenever the hall turned still",
        afford_clues={"paper_star", "window_frost"},
        dust_level=1,
        tags={"aeroplane", "museum"},
    ),
    "clock_tower": Place(
        id="clock_tower",
        label="clock tower gallery",
        phrase="the little gallery inside the clock tower",
        iconic_line="In the middle of the room stood an iconic red aeroplane model, bright against the old stone walls.",
        night_sound="the clock answered every gust with a soft hollow hum",
        afford_clues={"window_frost", "bell_echo"},
        dust_level=1,
        tags={"aeroplane", "tower"},
    ),
    "attic_hangar": Place(
        id="attic_hangar",
        label="attic hangar room",
        phrase="the attic room above the town hangar",
        iconic_line="From the beams hung an iconic patchwork aeroplane, all canvas wings and tiny brass screws.",
        night_sound="the rafters whispered whenever the wind slipped through them",
        afford_clues={"paper_star", "bell_echo"},
        dust_level=2,
        tags={"aeroplane", "attic"},
    ),
}

KEEPSAKES = {
    "photo": Keepsake(
        id="photo",
        label="photo",
        phrase="a small black-and-white photo",
        hidden_in="map_drawer",
        missing_from="the memory board",
        kindness_needed="pin_photo",
        end_image="the little photo sat straight on the memory board beneath the quiet wing",
        tags={"photo", "memory"},
    ),
    "medal": Keepsake(
        id="medal",
        label="medal",
        phrase="a star-shaped medal on a blue ribbon",
        hidden_in="window_seat",
        missing_from="the blue display cushion",
        kindness_needed="set_medal",
        end_image="the medal shone softly on its blue cushion beside the sleeping aeroplane",
        tags={"medal", "memory"},
    ),
    "scarf": Keepsake(
        id="scarf",
        label="scarf",
        phrase="a tiny pilot scarf with fading stripes",
        hidden_in="propeller_crate",
        missing_from="the pilot doll in the case",
        kindness_needed="tie_scarf",
        end_image="the striped scarf rested around the little doll's neck while the room turned warm again",
        tags={"scarf", "memory"},
    ),
}

CLUES = {
    "paper_star": Clue(
        id="paper_star",
        sign="a trail of folded paper stars",
        points_to="map_drawer",
        prose="Folded paper stars lay on the floor in a line that ended by a shallow map drawer.",
        tags={"paper", "clue"},
    ),
    "window_frost": Clue(
        id="window_frost",
        sign="a white finger mark on the frosty glass",
        points_to="window_seat",
        prose="A white finger mark curved over the frosty window and stopped above the old window seat.",
        tags={"frost", "clue"},
    ),
    "bell_echo": Clue(
        id="bell_echo",
        sign="a bell note that rang from the dark crate corner",
        points_to="propeller_crate",
        prose="Each time the tower bell sounded, the last silver note seemed to settle by the propeller crate in the corner.",
        tags={"bell", "clue"},
    ),
}

KINDNESSES = {
    "pin_photo": Kindness(
        id="pin_photo",
        action="carefully pin the photo back onto the memory board",
        result="The board looked complete again, as if someone had finally been remembered properly.",
        solves_for={"photo"},
        tags={"kindness", "memory"},
    ),
    "set_medal": Kindness(
        id="set_medal",
        action="brush the medal clean and place it on the blue display cushion",
        result="The little medal stopped hiding in the cold dark and caught the moonlight in one brave spark.",
        solves_for={"medal"},
        tags={"kindness", "memory"},
    ),
    "tie_scarf": Kindness(
        id="tie_scarf",
        action="gently tie the scarf around the pilot doll in the glass case",
        result="The small doll no longer looked lonely, and the case felt cared for instead of forgotten.",
        solves_for={"scarf"},
        tags={"kindness", "memory"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Sophie", "Nora", "Etta", "Lucy", "Hazel", "Ivy"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Miles", "Ben", "Jude", "Eli", "Noah"]
GHOST_NAMES = ["Wren", "Pip", "Mara", "Kit"]
TRAITS = ["careful", "gentle", "curious", "thoughtful", "brave"]
CARETAKERS = ["mother", "father", "aunt", "grandmother"]


def valid_combo(place_id: str, keepsake_id: str, clue_id: str, kindness_id: str) -> bool:
    if place_id not in PLACES or keepsake_id not in KEEPSAKES or clue_id not in CLUES or kindness_id not in KINDNESSES:
        return False
    place = PLACES[place_id]
    keepsake = KEEPSAKES[keepsake_id]
    clue = CLUES[clue_id]
    kindness = KINDNESSES[kindness_id]
    if clue_id not in place.afford_clues:
        return False
    if clue.points_to != keepsake.hidden_in:
        return False
    if keepsake.kindness_needed != kindness.id:
        return False
    if keepsake.id not in kindness.solves_for:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place_id in sorted(PLACES):
        for keepsake_id in sorted(KEEPSAKES):
            for clue_id in sorted(CLUES):
                for kindness_id in sorted(KINDNESSES):
                    if valid_combo(place_id, keepsake_id, clue_id, kindness_id):
                        combos.append((place_id, keepsake_id, clue_id, kindness_id))
    return combos


@dataclass
class StoryParams:
    place: str
    keepsake: str
    clue: str
    kindness: str
    hero_name: str
    hero_gender: str
    ghost_name: str
    caretaker: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="museum_hall",
        keepsake="photo",
        clue="paper_star",
        kindness="pin_photo",
        hero_name="Lila",
        hero_gender="girl",
        ghost_name="Wren",
        caretaker="grandmother",
        trait="gentle",
        seed=101,
    ),
    StoryParams(
        place="clock_tower",
        keepsake="medal",
        clue="window_frost",
        kindness="set_medal",
        hero_name="Owen",
        hero_gender="boy",
        ghost_name="Mara",
        caretaker="aunt",
        trait="thoughtful",
        seed=202,
    ),
    StoryParams(
        place="attic_hangar",
        keepsake="scarf",
        clue="bell_echo",
        kindness="tie_scarf",
        hero_name="Hazel",
        hero_gender="girl",
        ghost_name="Pip",
        caretaker="mother",
        trait="curious",
        seed=303,
    ),
]


def explain_rejection(place_id: str, keepsake_id: str, clue_id: str, kindness_id: str) -> str:
    bits: list[str] = []
    if place_id in PLACES and clue_id in CLUES and clue_id not in PLACES[place_id].afford_clues:
        bits.append(f"{PLACES[place_id].phrase} does not support the clue {CLUES[clue_id].sign}")
    if keepsake_id in KEEPSAKES and clue_id in CLUES and CLUES[clue_id].points_to != KEEPSAKES[keepsake_id].hidden_in:
        bits.append(
            f"the clue points to {CLUES[clue_id].points_to.replace('_', ' ')}, but the {KEEPSAKES[keepsake_id].label} is hidden in {KEEPSAKES[keepsake_id].hidden_in.replace('_', ' ')}"
        )
    if keepsake_id in KEEPSAKES and kindness_id in KINDNESSES and KEEPSAKES[keepsake_id].kindness_needed != kindness_id:
        bits.append(
            f"the {KEEPSAKES[keepsake_id].label} needs kindness '{KEEPSAKES[keepsake_id].kindness_needed}', not '{kindness_id}'"
        )
    if not bits:
        bits.append("that combination does not form a sensible mystery")
    return "(No story: " + "; ".join(bits) + ".)"


def hero_pool(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def introduce(world: World, hero: Entity, caretaker: Entity, place: Place) -> None:
    world.say(
        f"On a windy evening, {hero.id} went with {hero.pronoun('possessive')} {caretaker.label_word} to {place.phrase}."
    )
    world.say(
        f"{place.iconic_line} {place.night_sound.capitalize()}."
    )


def seed_mystery(world: World, hero: Entity, ghost: Entity, place: Place, keepsake: Keepsake) -> None:
    ghost.meters["restless"] += 1
    hero.memes["curiosity"] += 1
    propagate(world)
    world.say(
        f"When the lamps dimmed for closing time, a chilly breath moved through the room and the aeroplane gave the smallest shiver."
    )
    world.say(
        f'"That has happened three nights this week," said {world.get("caretaker").label_word}. "Something here still wants to be found."'
    )
    world.say(
        f"{hero.id} looked up at the shadow under the wing and wondered why a ghost would fuss over {keepsake.phrase}."
    )


def sneeze_and_medicine(world: World, hero: Entity, caretaker: Entity, place: Place) -> None:
    hero.meters["sneeze"] += float(place.dust_level)
    world.say(
        f"As {hero.id} bent to look more closely, dust tickled {hero.pronoun('possessive')} nose and {hero.pronoun()} gave a sudden sneeze."
    )
    world.say(
        f'{caretaker.label_word.capitalize()} reached into a coat pocket. "Here is your antihistamine," {caretaker.pronoun()} said. "It will calm that dusty sneeze so you can think."'
    )
    hero.meters["medicine"] += 1
    propagate(world)
    world.say(
        f"{hero.id} swallowed the antihistamine with a sip of water, and soon the itchy feeling faded."
    )


def reveal_clue(world: World, hero: Entity, clue: Clue) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Then {hero.id} noticed {clue.sign}. {clue.prose}"
    )


def find_keepsake(world: World, hero: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    hero.meters["found"] += 1
    ghost.meters["hope"] += 1
    world.say(
        f"Inside, {hero.id} found {keepsake.phrase}. At the same moment, a small pale child in an old flying cap appeared beside the aeroplane, more lonely than scary."
    )
    world.say(
        f'"I only wanted it put back," whispered {ghost.id}. "I did not know how to ask in the daytime."'
    )


def do_kindness(world: World, hero: Entity, ghost: Entity, keepsake: Keepsake, kindness: Kindness) -> None:
    hero.memes["kindness"] += 1
    ghost.meters["keepsake_returned"] += 1
    ghost.meters["kindness_received"] += 1
    world.say(
        f"{hero.id} did not run away. {hero.pronoun().capitalize()} chose to {kindness.action}."
    )
    world.say(kindness.result)
    propagate(world)


def happy_ending(world: World, hero: Entity, caretaker: Entity, ghost: Entity, keepsake: Keepsake) -> None:
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    ghost.memes["peace"] += 1
    world.say(
        f"The room lost its chill at once. The ghost child smiled, touched the wing of the aeroplane with two shining fingers, and grew soft as moon-mist."
    )
    world.say(
        f'"Thank you for being kind," {ghost.id} whispered. "Now I can rest."'
    )
    world.say(
        f"When {caretaker.label_word} came back with a lantern, {hero.id} showed {caretaker.pronoun('object')} what had been missing and told the whole mystery from start to finish."
    )
    world.say(
        f"They left the room smiling, and behind them {keepsake.end_image}."
    )


def tell(
    place: Place,
    keepsake: Keepsake,
    clue: Clue,
    kindness: Kindness,
    hero_name: str,
    hero_gender: str,
    ghost_name: str,
    caretaker_type: str,
    trait: str,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_gender,
            label=hero_name,
            role="hero",
            attrs={"trait": trait},
        )
    )
    caretaker = world.add(
        Entity(
            id="Caretaker",
            kind="character",
            type=caretaker_type,
            label="the caretaker",
            role="caretaker",
        )
    )
    ghost = world.add(
        Entity(
            id=ghost_name,
            kind="character",
            type="child",
            label=ghost_name,
            role="ghost",
        )
    )
    world.add(Entity(id="room", type="room", label=place.label))
    world.add(Entity(id="plane", type="aeroplane", label="aeroplane", phrase="the iconic aeroplane"))
    world.facts["caretaker"] = caretaker

    introduce(world, hero, caretaker, place)
    world.para()
    seed_mystery(world, hero, ghost, place, keepsake)
    sneeze_and_medicine(world, hero, caretaker, place)
    world.para()
    reveal_clue(world, hero, clue)
    find_keepsake(world, hero, ghost, keepsake)
    world.para()
    do_kindness(world, hero, ghost, keepsake, kindness)
    happy_ending(world, hero, caretaker, ghost, keepsake)

    world.facts.update(
        hero=hero,
        ghost=ghost,
        caretaker=caretaker,
        place=place,
        keepsake=keepsake,
        clue=clue,
        kindness=kindness,
        mystery_solved=hero.meters["found"] >= THRESHOLD and ghost.meters["settled"] >= THRESHOLD,
        medicine_taken=hero.meters["medicine"] >= THRESHOLD,
        chilly_started=("haunt",) in world.fired,
        settled=("settled",) in world.fired,
    )
    return world


KNOWLEDGE = {
    "aeroplane": [
        (
            "What is an aeroplane?",
            "An aeroplane is a flying machine with wings. It moves through the sky and carries people or things from one place to another.",
        )
    ],
    "antihistamine": [
        (
            "What does an antihistamine do?",
            "An antihistamine is a kind of medicine that can calm some allergy symptoms, like sneezing or itchy eyes. A grown-up should decide when a child needs it.",
        )
    ],
    "ghost": [
        (
            "What makes a ghost story feel spooky without being too scary?",
            "A gentle ghost story often uses quiet sounds, cold air, shadows, and mystery. It can feel spooky while still staying safe and kind.",
        )
    ],
    "museum": [
        (
            "What do people keep in a museum?",
            "A museum keeps important or interesting old things so people can learn from them and remember them. Sometimes those objects tell stories from long ago.",
        )
    ],
    "kindness": [
        (
            "Why can kindness solve a problem?",
            "Kindness helps people feel seen and cared for. Sometimes a gentle helpful act fixes a problem faster than fear or shouting.",
        )
    ],
    "memory": [
        (
            "Why do people keep medals, photos, or scarves?",
            "People keep little objects like these because they hold memories. They can remind us of someone important or a special day.",
        )
    ],
}
KNOWLEDGE_ORDER = ["aeroplane", "antihistamine", "ghost", "museum", "kindness", "memory"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    keepsake = f["keepsake"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "aeroplane", "iconic", and "antihistamine".',
        f"Tell a spooky-but-safe mystery where {hero.id} explores {place.phrase}, follows a clue, and solves the trouble with kindness.",
        f"Write a happy-ending ghost story in which a missing {keepsake.label} near an iconic aeroplane turns out to be a mystery to solve, not a danger.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    ghost = f["ghost"]
    caretaker = f["caretaker"]
    place = f["place"]
    keepsake = f["keepsake"]
    clue = f["clue"]
    kindness = f["kindness"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a child visiting {place.phrase}, and {ghost.id}, a lonely ghost child near the aeroplane. {caretaker.label_word.capitalize()} helps too by staying calm and caring.",
        ),
        (
            "What was the mystery to solve?",
            f"The mystery was why the room kept turning chilly and why the aeroplane seemed to stir at night. Those spooky signs happened because {ghost.id} was restless while {keepsake.phrase} was still missing from {keepsake.missing_from}.",
        ),
        (
            f"Why did {caretaker.label_word} give {hero.id} an antihistamine?",
            f"{hero.id} sneezed when dust rose during the search, so {caretaker.label_word} gave {hero.pronoun('object')} an antihistamine. The medicine calmed the sneeze so {hero.pronoun()} could keep following the clue and think clearly.",
        ),
        (
            "How did the child solve the mystery?",
            f"{hero.id} followed {clue.sign} to the right hiding place and found {keepsake.phrase}. Then {hero.pronoun()} chose to {kindness.action}, which gave the ghost the kind help it had been waiting for.",
        ),
        (
            "How did the story end?",
            f"It ended happily because the ghost settled, the room turned warm again, and everyone understood what had happened. The final change is easy to see: {keepsake.end_image}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"aeroplane", "antihistamine", "ghost", "kindness", "memory"}
    if world.facts["place"].id == "museum_hall":
        tags.add("museum")
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        parts: list[str] = []
        if ent.role:
            parts.append(f"role={ent.role}")
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                parts.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(parts)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
clue_allowed(P, C) :- place(P), clue(C), affords(P, C).
matches_hiding(K, C) :- keepsake(K), clue(C), hidden_in(K, H), points_to(C, H).
matches_kindness(K, A) :- keepsake(K), kindness(A), needs(K, A), solves(A, K).

valid(P, K, C, A) :- place(P), keepsake(K), clue(C), kindness(A),
                     clue_allowed(P, C), matches_hiding(K, C), matches_kindness(K, A).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for clue_id in sorted(place.afford_clues):
            lines.append(asp.fact("affords", place_id, clue_id))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("hidden_in", keepsake_id, keepsake.hidden_in))
        lines.append(asp.fact("needs", keepsake_id, keepsake.kindness_needed))
    for clue_id, clue in CLUES.items():
        lines.append(asp.fact("clue", clue_id))
        lines.append(asp.fact("points_to", clue_id, clue.points_to))
    for kindness_id, kindness in KINDNESSES.items():
        lines.append(asp.fact("kindness", kindness_id))
        for kid in sorted(kindness.solves_for):
            lines.append(asp.fact("solves", kindness_id, kid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between Python and ASP valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test generation succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a child solves a mystery around an iconic aeroplane with antihistamine and kindness."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--keepsake", choices=sorted(KEEPSAKES))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--kindness", choices=sorted(KINDNESSES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=sorted(CARETAKERS))
    ap.add_argument("--name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from the ASP twin")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.keepsake and args.clue and args.kindness:
        if not valid_combo(args.place, args.keepsake, args.clue, args.kindness):
            raise StoryError(explain_rejection(args.place, args.keepsake, args.clue, args.kindness))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.clue is None or combo[2] == args.clue)
        and (args.kindness is None or combo[3] == args.kindness)
    ]
    if not combos:
        place_id = args.place or next(iter(PLACES))
        keepsake_id = args.keepsake or next(iter(KEEPSAKES))
        clue_id = args.clue or next(iter(CLUES))
        kindness_id = args.kindness or next(iter(KINDNESSES))
        raise StoryError(explain_rejection(place_id, keepsake_id, clue_id, kindness_id))

    place_id, keepsake_id, clue_id, kindness_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(hero_pool(gender))
    caretaker = args.caretaker or rng.choice(CARETAKERS)
    ghost_name = rng.choice(GHOST_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        keepsake=keepsake_id,
        clue=clue_id,
        kindness=kindness_id,
        hero_name=name,
        hero_gender=gender,
        ghost_name=ghost_name,
        caretaker=caretaker,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Invalid keepsake: {params.keepsake})")
    if params.clue not in CLUES:
        raise StoryError(f"(Invalid clue: {params.clue})")
    if params.kindness not in KINDNESSES:
        raise StoryError(f"(Invalid kindness: {params.kindness})")
    if not valid_combo(params.place, params.keepsake, params.clue, params.kindness):
        raise StoryError(explain_rejection(params.place, params.keepsake, params.clue, params.kindness))

    world = tell(
        place=PLACES[params.place],
        keepsake=KEEPSAKES[params.keepsake],
        clue=CLUES[params.clue],
        kindness=KINDNESSES[params.kindness],
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        ghost_name=params.ghost_name,
        caretaker_type=params.caretaker,
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
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, keepsake, clue, kindness) combos:\n")
        for place_id, keepsake_id, clue_id, kindness_id in combos:
            print(f"  {place_id:12} {keepsake_id:8} {clue_id:12} {kindness_id}")
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
            header = f"### {p.hero_name}: {p.keepsake} at {p.place} ({p.clue}, {p.kindness})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
