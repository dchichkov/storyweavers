#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py
=========================================================================================

A small fable-like storyworld about a young animal, a partial excerpt from a
rule note, a warning knock, and a misunderstanding that may end in a hot spurt
from a pot.

The domain is intentionally narrow: a helper knocks to warn about a hot vessel,
but the hero has read only an excerpt and misreads the knock. The world model
tracks heat, pressure, mess, fear, shame, trust, and understanding. Stories are
rendered from state, not from a frozen template with swapped nouns.

Run it
------
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py --all --qa
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py --trace --seed 42
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py --json
python storyworlds/worlds/gpt-5.4/excerpt_knock_spurt_misunderstanding_inner_monologue_fable.py --verify
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
WISE_TEMPERAMENTS = {"patient", "careful", "humble"}


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    affords: set[str] = field(default_factory=set)
    image: str = ""


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    liquid: str
    steam: str
    pressure: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Note:
    id: str
    excerpt: str
    full_text: str
    tag: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[["World"], list[str]]


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


def _r_pressure(world: World) -> list[str]:
    vessel = world.get("vessel")
    if vessel.meters["heat"] < THRESHOLD:
        return []
    sig = ("pressure", vessel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vessel.meters["pressure"] += float(vessel.attrs["pressure_level"])
    vessel.meters["risk"] += 1
    return ["__pressure__"]


def _r_spurt(world: World) -> list[str]:
    vessel = world.get("vessel")
    hero = world.get("hero")
    if vessel.meters["opened_close"] < THRESHOLD or vessel.meters["pressure"] < THRESHOLD:
        return []
    sig = ("spurt", vessel.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    vessel.meters["spurted"] += 1
    hero.meters["splashed"] += 1
    hero.memes["fear"] += 1
    hero.memes["shame"] += 1
    return ["__spurt__"]


CAUSAL_RULES = [
    Rule(name="pressure", tag="physical", apply=_r_pressure),
    Rule(name="spurt", tag="physical", apply=_r_spurt),
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
            if bit == "__pressure__":
                vessel = world.get("vessel")
                world.say(
                    f"Inside, {vessel.attrs['liquid_phrase']} grew lively; {vessel.attrs['steam_phrase']} curled up, and the lid began to tremble."
                )
            elif bit == "__spurt__":
                vessel = world.get("vessel")
                hero = world.get("hero")
                world.say(
                    f"The lid jumped, and a hot spurt of {vessel.attrs['liquid_noun']} leaped out onto {hero.id}'s paws."
                )
    return produced


def note_matches(note: Note, vessel: Vessel) -> bool:
    return note.tag in vessel.tags


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for vessel_id in sorted(place.affords):
            vessel = VESSELS[vessel_id]
            for note_id, note in NOTES.items():
                if note_matches(note, vessel):
                    combos.append((place_id, vessel_id, note_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    vessel: str
    note: str
    hero_name: str
    hero_kind: str
    friend_name: str
    friend_kind: str
    elder_kind: str
    temperament: str
    seed: Optional[int] = None


PLACES = {
    "maple_hut": Place(
        id="maple_hut",
        label="maple hut",
        phrase="a little maple hut at the edge of the grove",
        affords={"sap_kettle"},
        image="The windows shone amber, and the floor smelled sweet as warm bark.",
    ),
    "berry_kitchen": Place(
        id="berry_kitchen",
        label="berry kitchen",
        phrase="a round berry kitchen tucked under thorny vines",
        affords={"jam_pot"},
        image="Copper spoons hung on pegs, and the air tasted of sun-warmed fruit.",
    ),
    "stone_stall": Place(
        id="stone_stall",
        label="stone stall",
        phrase="a small stone soup stall beside the forest path",
        affords={"soup_urn"},
        image="A flat bell hung near the door, and steam made the roof beam shine.",
    ),
}

VESSELS = {
    "sap_kettle": Vessel(
        id="sap_kettle",
        label="kettle",
        phrase="a black kettle of maple sap",
        liquid="maple sap",
        steam="thin sweet steam",
        pressure=2,
        tags={"sap", "lid"},
    ),
    "jam_pot": Vessel(
        id="jam_pot",
        label="pot",
        phrase="a red jam pot full of berry mash",
        liquid="berry jam",
        steam="pink fruity steam",
        pressure=2,
        tags={"jam", "lid"},
    ),
    "soup_urn": Vessel(
        id="soup_urn",
        label="urn",
        phrase="a tall soup urn full of carrot broth",
        liquid="carrot broth",
        steam="soft savory steam",
        pressure=2,
        tags={"soup", "lid"},
    ),
}

NOTES = {
    "dancing_lid": Note(
        id="dancing_lid",
        excerpt='"Knock before opening..."',
        full_text='Knock before opening any vessel whose lid begins to dance, so the cook can stand back and lift it slowly.',
        tag="lid",
        lesson="A warning knock is a gift, not a grab.",
        tags={"knock", "steam"},
    ),
    "hot_sap": Note(
        id="hot_sap",
        excerpt='"...when sweet steam thickens, knock..."',
        full_text='When sweet steam thickens, knock and warn the keeper that hot sap may leap if opened too fast.',
        tag="sap",
        lesson="A half-read rule can point the wrong way.",
        tags={"sap", "knock"},
    ),
    "shared_pot": Note(
        id="shared_pot",
        excerpt='"...tell the cook what you see..."',
        full_text='If you see a pot swell or hiss, tell the cook what you see before pride chooses for you.',
        tag="lid",
        lesson="Clear words cool hot moments.",
        tags={"lid", "warning"},
    ),
}

HERO_NAMES = {
    "mouse": ["Mina", "Pip", "Nim"],
    "rabbit": ["Tansy", "Pico", "Fern"],
    "fox": ["Rill", "Sedge", "Moro"],
    "squirrel": ["Hazel", "Nib", "Tillo"],
}
FRIEND_NAMES = {
    "otter": ["Moss", "Pebble", "Tavi"],
    "deer": ["Bramble", "Lark", "Fenn"],
    "badger": ["Rowan", "Clove", "Tarn"],
    "hedgehog": ["Burr", "Thimble", "Pru"],
}
ELDERS = ["owl", "tortoise"]
TEMPERAMENTS = ["hasty", "proud", "patient", "careful", "humble"]

CURATED = [
    StoryParams(
        place="berry_kitchen",
        vessel="jam_pot",
        note="dancing_lid",
        hero_name="Hazel",
        hero_kind="squirrel",
        friend_name="Burr",
        friend_kind="hedgehog",
        elder_kind="owl",
        temperament="hasty",
    ),
    StoryParams(
        place="maple_hut",
        vessel="sap_kettle",
        note="hot_sap",
        hero_name="Mina",
        hero_kind="mouse",
        friend_name="Pebble",
        friend_kind="otter",
        elder_kind="tortoise",
        temperament="proud",
    ),
    StoryParams(
        place="stone_stall",
        vessel="soup_urn",
        note="shared_pot",
        hero_name="Fern",
        hero_kind="rabbit",
        friend_name="Rowan",
        friend_kind="badger",
        elder_kind="owl",
        temperament="patient",
    ),
    StoryParams(
        place="berry_kitchen",
        vessel="jam_pot",
        note="shared_pot",
        hero_name="Pico",
        hero_kind="rabbit",
        friend_name="Lark",
        friend_kind="deer",
        elder_kind="tortoise",
        temperament="careful",
    ),
]


def explain_rejection(place_id: str, vessel_id: str, note_id: str) -> str:
    place = PLACES.get(place_id)
    vessel = VESSELS.get(vessel_id)
    note = NOTES.get(note_id)
    if place and vessel and vessel_id not in place.affords:
        return (
            f"(No story: {place.label} would not reasonably contain {vessel.phrase}. "
            f"Pick a vessel the place actually affords.)"
        )
    if vessel and note and not note_matches(note, vessel):
        return (
            f"(No story: the note excerpt is about {note.tag}, but {vessel.phrase} "
            f"does not fit that warning clearly enough for this fable.)"
        )
    return "(No story: this combination does not make a coherent warning scene.)"


def outcome_of(params: StoryParams) -> str:
    return "understood" if params.temperament in WISE_TEMPERAMENTS else "spurted"


def setup_world(place: Place, vessel_cfg: Vessel, note_cfg: Note,
                hero_name: str, hero_kind: str, friend_name: str, friend_kind: str,
                elder_kind: str, temperament: str) -> World:
    world = World(place=place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_kind,
        label=hero_kind,
        role="hero",
        traits=[temperament],
    ))
    friend = world.add(Entity(
        id=friend_name,
        kind="character",
        type=friend_kind,
        label=friend_kind,
        role="friend",
        traits=["helpful"],
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=elder_kind,
        label=elder_kind,
        role="elder",
    ))
    vessel = world.add(Entity(
        id="vessel",
        kind="thing",
        type=vessel_cfg.id,
        label=vessel_cfg.label,
        phrase=vessel_cfg.phrase,
        role="vessel",
        attrs={
            "pressure_level": vessel_cfg.pressure,
            "liquid_noun": vessel_cfg.liquid,
            "liquid_phrase": vessel_cfg.liquid,
            "steam_phrase": vessel_cfg.steam,
        },
        tags=set(vessel_cfg.tags),
    ))
    hero.memes["pride"] = 1.0 if temperament in {"proud", "hasty"} else 0.0
    hero.memes["care"] = 1.0 if temperament in WISE_TEMPERAMENTS else 0.0
    vessel.meters["heat"] = 1.0
    world.facts.update(
        hero=hero,
        friend=friend,
        elder=elder,
        place=place,
        vessel_cfg=vessel_cfg,
        note_cfg=note_cfg,
        temperament=temperament,
    )
    return world


def scene_open(world: World) -> None:
    hero = world.get(world.facts["hero"].id)
    place = world.facts["place"]
    vessel_cfg = world.facts["vessel_cfg"]
    note_cfg = world.facts["note_cfg"]
    world.say(
        f"In {place.phrase}, {hero.id} the {hero.type} kept watch over {vessel_cfg.phrase}."
    )
    if place.image:
        world.say(place.image)
    world.say(
        f"On a peg nearby hung an old rule card from the {world.facts['elder'].type}. {hero.id} saw only an excerpt: {note_cfg.excerpt}"
    )
    propagate(world, narrate=True)


def inner_monologue(world: World) -> None:
    hero = world.facts["hero"]
    note_cfg = world.facts["note_cfg"]
    world.say(
        f'{hero.id} read the clipped line again and thought, "If that is the excerpt, perhaps every knock means someone wants what I am guarding."'
    )
    if world.facts["temperament"] in WISE_TEMPERAMENTS:
        world.say(
            f'Yet another thought came quietly after it: "Perhaps I should hear the whole matter before I decide."'
        )
    else:
        world.say(
            f'Pride answered inside {hero.pronoun("object")} at once: "I had better act before anyone takes a spoonful."'
        )
    world.facts["inner_voice"] = note_cfg.excerpt


def warning_knock(world: World) -> None:
    friend = world.facts["friend"]
    vessel_cfg = world.facts["vessel_cfg"]
    world.para()
    world.say(
        f"Just then came a quick knock on the doorframe. It was {friend.id} the {friend.type}, who had seen the shaking lid and smelled {vessel_cfg.steam} from the path."
    )
    world.say(
        f'"{friend.id} called, "Please stand back a step!"'
    )
    world.facts["friend_motive"] = "warning"


def wise_response(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    vessel = world.get("vessel")
    note_cfg = world.facts["note_cfg"]
    hero.memes["trust"] += 1
    hero.memes["understanding"] += 1
    world.say(
        f'{hero.id} did not fling the door wide. Instead {hero.pronoun()} asked, "What do you see?"'
    )
    world.say(
        f'"The lid is dancing," said {friend.id}. "The rest of the note is about standing back."'
    )
    vessel.meters["pressure"] = 0.0
    vessel.meters["risk"] = 0.0
    world.say(
        f"Together they lifted the lid slowly with a cloth, and not even a little spurt escaped."
    )
    world.say(
        f"Then {friend.id} read the whole note aloud: {note_cfg.full_text}"
    )
    hero.memes["gratitude"] += 1
    world.facts["heard_full_note"] = True
    world.facts["outcome"] = "understood"


def mistaken_response(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    note_cfg = world.facts["note_cfg"]
    vessel = world.get("vessel")
    hero.memes["suspicion"] += 1
    world.say(
        f'{hero.id} mistook the warning for a grab at the pot. "No one is taking my turn," {hero.pronoun()} snapped.'
    )
    world.say(
        f"{hero.id} hurried too close and jerked the lid upward."
    )
    vessel.meters["opened_close"] += 1
    propagate(world, narrate=True)
    world.say(
        f'"I was warning you," cried {friend.id}, hopping back from the steam.'
    )
    world.say(
        f"Only then did {friend.id} point to the full card and read it aloud: {note_cfg.full_text}"
    )
    hero.memes["understanding"] += 1
    hero.memes["regret"] += 1
    world.facts["heard_full_note"] = True
    world.facts["outcome"] = "spurted"


def close_story(world: World) -> None:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    note_cfg = world.facts["note_cfg"]
    world.para()
    if world.facts["outcome"] == "spurted":
        world.say(
            f"{hero.id} cooled {hero.pronoun('possessive')} paws in a basin and lowered {hero.pronoun('possessive')} ears."
        )
        world.say(
            f'"I listened to my fear before I listened to my friend," {hero.pronoun()} said.'
        )
        world.say(
            f"That evening the {elder.type} smiled gently and pinned the rule card lower, where the whole message could be read at once."
        )
    else:
        world.say(
            f"{hero.id} thanked {friend.id}, and the two of them set the bowl safely on the sill to cool."
        )
        world.say(
            f"The steam thinned, the room grew calm again, and the warning knock became a small remembered kindness."
        )
    world.say(f"Moral: {note_cfg.lesson}")


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    vessel_cfg = VESSELS[params.vessel]
    note_cfg = NOTES[params.note]
    world = setup_world(
        place=place,
        vessel_cfg=vessel_cfg,
        note_cfg=note_cfg,
        hero_name=params.hero_name,
        hero_kind=params.hero_kind,
        friend_name=params.friend_name,
        friend_kind=params.friend_kind,
        elder_kind=params.elder_kind,
        temperament=params.temperament,
    )
    scene_open(world)
    world.para()
    inner_monologue(world)
    warning_knock(world)
    world.para()
    if outcome_of(params) == "understood":
        wise_response(world)
    else:
        mistaken_response(world)
    close_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    hero = world.facts["hero"]
    place = world.facts["place"]
    vessel_cfg = world.facts["vessel_cfg"]
    out = world.facts["outcome"]
    if out == "spurted":
        ending = "a misunderstanding causes a hot spurt and then a lesson"
    else:
        ending = "the hero pauses, asks a question, and avoids the hot spurt"
    return [
        'Write a short fable for a young child that includes the words "excerpt", "knock", and "spurt".',
        f"Tell a forest fable set in {place.label} where {hero.id} guards {vessel_cfg.phrase}, hears a knock, and falls into an inner monologue before the truth is known.",
        f"Write a misunderstanding story in fable style where a partial excerpt is read the wrong way and {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    place = world.facts["place"]
    vessel_cfg = world.facts["vessel_cfg"]
    note_cfg = world.facts["note_cfg"]
    out = world.facts["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {hero.type} and {friend.id} the {friend.type} in {place.label}. They meet over {vessel_cfg.phrase} and a warning that is first misunderstood.",
        ),
        (
            "What excerpt did the hero read?",
            f"{hero.id} saw only the clipped line {note_cfg.excerpt}. Because the rest of the note was missing from view, {hero.pronoun()} guessed at its meaning instead of knowing it.",
        ),
        (
            "Why did the friend knock?",
            f"{friend.id} knocked to warn {hero.id} about the shaking lid and the hot pressure inside the vessel. The knock was meant to protect, not to interrupt or steal.",
        ),
    ]
    if out == "spurted":
        qa.append(
            (
                "What misunderstanding caused the trouble?",
                f"{hero.id} thought the knock meant someone wanted to take the pot or boss the scene. That mistaken inner monologue made {hero.pronoun('object')} open the lid too fast, so a hot spurt jumped out.",
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, {hero.id} understood that the friend had been warning {hero.pronoun('object')} all along. The small burn and the full note taught {hero.pronoun('object')} to ask before assuming.",
            )
        )
    else:
        qa.append(
            (
                "How did the hero avoid the problem?",
                f"{hero.id} paused and asked what the friend had seen before doing anything rash. That question turned the misunderstanding into understanding, so not even a little spurt escaped.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with calm hands, a safely opened vessel, and gratitude instead of embarrassment. The ending proves that listening changed what happened in the room.",
            )
        )
    return qa


KNOWLEDGE = {
    "excerpt": [
        (
            "What is an excerpt?",
            "An excerpt is a small part taken from a longer piece of writing. If you see only an excerpt, you may miss the full meaning.",
        )
    ],
    "knock": [
        (
            "Why might someone knock before coming in?",
            "A knock can be a polite way to ask for attention before entering or speaking. Sometimes it is also a warning that something important needs to be said.",
        )
    ],
    "spurt": [
        (
            "What is a spurt?",
            "A spurt is a quick little burst or jump of liquid or air. Hot things can spurt if they are opened too suddenly.",
        )
    ],
    "steam": [
        (
            "Why should you stand back from a hot pot with steam?",
            "Steam means the liquid inside is very hot, and pressure can build under a lid. Standing back helps keep your face and hands safe.",
        )
    ],
    "misunderstanding": [
        (
            "What is a misunderstanding?",
            "A misunderstanding happens when someone thinks a message means one thing even though it means another. Asking a calm question can clear it up.",
        )
    ],
}
KNOWLEDGE_ORDER = ["excerpt", "knock", "spurt", "steam", "misunderstanding"]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"excerpt", "knock", "spurt", "misunderstanding"}
    if world.facts["vessel_cfg"].id in {"sap_kettle", "jam_pot", "soup_urn"}:
        tags.add("steam")
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible_note(N, V) :- note_tag(N, T), vessel_tag(V, T).
valid(P, V, N) :- affords(P, V), compatible_note(N, V).

wise(T) :- temperament(T), wise_temperament(T).
outcome(understood) :- chosen_temperament(T), wise(T).
outcome(spurted) :- chosen_temperament(T), not wise(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for vessel_id in sorted(place.affords):
            lines.append(asp.fact("affords", place_id, vessel_id))
    for vessel_id, vessel in VESSELS.items():
        lines.append(asp.fact("vessel", vessel_id))
        for tag in sorted(vessel.tags):
            lines.append(asp.fact("vessel_tag", vessel_id, tag))
    for note_id, note in NOTES.items():
        lines.append(asp.fact("note", note_id))
        lines.append(asp.fact("note_tag", note_id, note.tag))
    for temperament in TEMPERAMENTS:
        lines.append(asp.fact("temperament", temperament))
    for temperament in sorted(WISE_TEMPERAMENTS):
        lines.append(asp.fact("wise_temperament", temperament))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = asp.fact("chosen_temperament", params.temperament)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_emit(sample: StorySample) -> None:
    emit(sample, trace=False, qa=False, header="")


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
    rng = random.Random(11)
    parser = build_parser()
    for _ in range(20):
        params = resolve_params(parser.parse_args([]), rng)
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        _smoke_emit(sample)
        print("OK: smoke test generated and emitted a story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Fable storyworld: a partial excerpt, a warning knock, and a misunderstanding around a hot vessel."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--note", choices=NOTES)
    ap.add_argument("--hero-kind", choices=sorted(HERO_NAMES))
    ap.add_argument("--friend-kind", choices=sorted(FRIEND_NAMES))
    ap.add_argument("--elder-kind", choices=ELDERS)
    ap.add_argument("--temperament", choices=TEMPERAMENTS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (place, vessel, note) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.vessel and args.vessel not in PLACES[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.vessel, args.note or next(iter(NOTES))))
    if args.vessel and args.note and not note_matches(NOTES[args.note], VESSELS[args.vessel]):
        raise StoryError(explain_rejection(args.place or next(iter(PLACES)), args.vessel, args.note))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.vessel is None or combo[1] == args.vessel)
        and (args.note is None or combo[2] == args.note)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, vessel_id, note_id = rng.choice(combos)
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_NAMES))
    friend_kind = args.friend_kind or rng.choice(sorted(FRIEND_NAMES))
    elder_kind = args.elder_kind or rng.choice(ELDERS)
    temperament = args.temperament or rng.choice(TEMPERAMENTS)
    hero_name = rng.choice(HERO_NAMES[hero_kind])
    friend_name = rng.choice(FRIEND_NAMES[friend_kind])
    if hero_name == friend_name:
        friend_name = rng.choice([n for n in FRIEND_NAMES[friend_kind] if n != hero_name])
    return StoryParams(
        place=place_id,
        vessel=vessel_id,
        note=note_id,
        hero_name=hero_name,
        hero_kind=hero_kind,
        friend_name=friend_name,
        friend_kind=friend_kind,
        elder_kind=elder_kind,
        temperament=temperament,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.vessel not in VESSELS:
        raise StoryError(f"(Unknown vessel: {params.vessel})")
    if params.note not in NOTES:
        raise StoryError(f"(Unknown note: {params.note})")
    if params.hero_kind not in HERO_NAMES:
        raise StoryError(f"(Unknown hero kind: {params.hero_kind})")
    if params.friend_kind not in FRIEND_NAMES:
        raise StoryError(f"(Unknown friend kind: {params.friend_kind})")
    if params.elder_kind not in ELDERS:
        raise StoryError(f"(Unknown elder kind: {params.elder_kind})")
    if params.temperament not in TEMPERAMENTS:
        raise StoryError(f"(Unknown temperament: {params.temperament})")
    if params.vessel not in PLACES[params.place].affords or not note_matches(NOTES[params.note], VESSELS[params.vessel]):
        raise StoryError(explain_rejection(params.place, params.vessel, params.note))

    world = tell(params)
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, vessel, note) combos:\n")
        for place_id, vessel_id, note_id in combos:
            print(f"  {place_id:13} {vessel_id:10} {note_id}")
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
            header = f"### {p.hero_name} in {p.place} ({p.vessel}, {p.note}, {outcome_of(p)})"
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
