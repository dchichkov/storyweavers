#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py
======================================================================

A standalone story world about a child in a mythic valley who must solve a
sleepy mystery. People begin to drowse, a rumor of a curse spreads, and the
surprise truth is that tiny bacteria have fouled a holy water source.

The world model prefers a sensible response over a magical-sounding but weak
one, and it can also produce a bad ending when help comes too late.

Run it
------
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py --all
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py --trace
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py --qa
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py --json
    python storyworlds/worlds/gpt-5.4/drowse_hand_pl_bacteria_mystery_to_solve.py --verify
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
        female = {"girl", "mother", "woman", "priestess"}
        male = {"boy", "father", "man", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "priestess": "priestess", "priest": "priest"}.get(
            self.type, self.type
        )


@dataclass
class Place:
    id: str
    realm: str
    water_label: str
    water_phrase: str
    path_text: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    clue: str
    trail: str
    reveal: str
    severity: int
    bacteria: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class FalseBelief:
    id: str
    label: str
    line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
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


def _r_drowse(world: World) -> list[str]:
    spring = world.get("water")
    if spring.meters["tainted"] < THRESHOLD:
        return []
    sig = ("drowse", "water")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village = world.get("village")
    hero = world.get("hero")
    village.meters["drowse"] += 1
    hero.memes["worry"] += 1
    return ["__drowse__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="drowse", tag="physical", apply=_r_drowse),
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
    "sun_well": Place(
        id="sun_well",
        realm="the Valley of the Golden Reed",
        water_label="sun-well",
        water_phrase="the sun-well beneath the lion stones",
        path_text="a stair of warm yellow rock wound down to the water",
        ending_image="the lion stones shone again, and bright rings spread across the clear well",
        tags={"well", "myth"},
    ),
    "moon_spring": Place(
        id="moon_spring",
        realm="the Grove of Silver Owls",
        water_label="moon-spring",
        water_phrase="the moon-spring under the white fig tree",
        path_text="a ribbon path of pale shells led under the hanging branches",
        ending_image="the white fig leaves stopped trembling, and the spring held the moon like a clean mirror",
        tags={"spring", "myth"},
    ),
    "cloud_cistern": Place(
        id="cloud_cistern",
        realm="the Hill of Seven Bells",
        water_label="cloud-cistern",
        water_phrase="the cloud-cistern cut into the hill",
        path_text="stone steps curved past seven bronze bells to the water door",
        ending_image="the seven bells rang sharply in the clear air above the sweet cistern",
        tags={"cistern", "myth"},
    ),
}

SOURCES = {
    "hand_pl_ladle": Source(
        id="hand_pl_ladle",
        label="hand-pl ladle",
        phrase="a carved hand-pl ladle that everyone dipped into the holy water",
        clue="green slime clung to the hand-pl ladle's bowl",
        trail="small wet fingerprints marked the stones beside the basin",
        reveal="It was no moon curse at all. Tiny bacteria were hiding in the slime on the hand-pl ladle and slipping into every cup.",
        severity=2,
        bacteria=True,
        tags={"hand-pl", "bacteria", "ladle"},
    ),
    "spoiled_offering": Source(
        id="spoiled_offering",
        label="spoiled milk offering",
        phrase="a bowl of spoiled milk left too long beside the water",
        clue="a sour smell floated from a crusted offering bowl",
        trail="white drips ran from the altar lip toward the water",
        reveal="The gift on the altar had turned bad. Tiny bacteria bred in the spoiled milk and washed into the holy water.",
        severity=1,
        bacteria=True,
        tags={"bacteria", "milk"},
    ),
    "rat_in_channel": Source(
        id="rat_in_channel",
        label="dead rat in the channel",
        phrase="a dead rat trapped in the narrow water channel",
        clue="black flies hovered where the channel bent behind a stone",
        trail="the water there moved thick and slow instead of clear and quick",
        reveal="Behind the stone bend lay the hidden trouble: a dead rat in the channel. Tiny bacteria had spread from it into the village water.",
        severity=3,
        bacteria=True,
        tags={"bacteria", "channel"},
    ),
    "shadow_whisper": Source(
        id="shadow_whisper",
        label="shadow whisper",
        phrase="nothing but a rumor of shadow and wind",
        clue="there was no true clue at all",
        trail="the path held only dry dust",
        reveal="There was no living thing there to foul the water.",
        severity=0,
        bacteria=False,
        tags={"rumor"},
    ),
}

FALSE_BELIEFS = {
    "owl_curse": FalseBelief(
        id="owl_curse",
        label="owl curse",
        line='Some said a white owl had blinked three times and laid an owl curse on the valley.',
        tags={"curse"},
    ),
    "sleep_giant": FalseBelief(
        id="sleep_giant",
        label="sleep giant",
        line='Some said a sleep giant under the earth had turned in his dreams and breathed drowse into the air.',
        tags={"giant"},
    ),
    "angry_moon": FalseBelief(
        id="angry_moon",
        label="angry moon",
        line='Some whispered that the moon herself was angry and had dimmed the minds of the people.',
        tags={"moon"},
    ),
}

RESPONSES = {
    "boil_and_scrub": Response(
        id="boil_and_scrub",
        sense=3,
        power=3,
        text="ordered the water stopped at once, set great kettles to boiling, and had the basin and channels scrubbed until the stone smelled clean",
        fail="ordered boiling and scrubbing, but by then too many people had already drunk the tainted water",
        qa_text="stopped the water, boiled what the people needed, and scrubbed the basin clean",
        tags={"boil", "clean"},
    ),
    "drain_and_stone_lime": Response(
        id="drain_and_stone_lime",
        sense=3,
        power=4,
        text="drained the holy water away, washed the channel with hot water and lime, and let the spring run fresh before anyone drank again",
        fail="drained and washed the place, but too late to spare the village from a hard sickness",
        qa_text="drained the water source and washed it so fresh water could return",
        tags={"clean", "spring"},
    ),
    "prayer_only": Response(
        id="prayer_only",
        sense=1,
        power=1,
        text="lifted both hands and prayed over the water, hoping the trouble would vanish on its own",
        fail="prayed over the water, but prayer alone did not remove the bacteria",
        qa_text="prayed over the water",
        tags={"prayer"},
    ),
}

GIRL_NAMES = ["Iris", "Nysa", "Thale", "Mira", "Rhea", "Elia", "Dora", "Lina"]
BOY_NAMES = ["Pelos", "Tarin", "Niko", "Orin", "Soren", "Ivo", "Lukas", "Theron"]
TRAITS = ["watchful", "brave", "patient", "clever", "quiet", "kind"]


def contamination_risk(source: Source) -> bool:
    return source.bacteria


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity_of(source: Source, delay: int) -> int:
    return source.severity + delay


def is_contained(response: Response, source: Source, delay: int) -> bool:
    return response.power >= severity_of(source, delay)


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place_id in PLACES:
        for source_id, source in SOURCES.items():
            if contamination_risk(source):
                combos.append((place_id, source_id))
    return combos


@dataclass
class StoryParams:
    place: str
    source: str
    response: str
    name: str
    gender: str
    elder: str
    trait: str
    false_belief: str
    delay: int = 0
    seed: Optional[int] = None


def predict_drowse(world: World, source: Source) -> dict:
    sim = world.copy()
    water = sim.get("water")
    water.meters["tainted"] += 1
    water.attrs["source"] = source.id
    propagate(sim, narrate=False)
    village = sim.get("village")
    return {
        "drowse": village.meters["drowse"],
        "worry": sim.get("hero").memes["worry"],
    }


def introduce(world: World, place: Place, hero: Entity) -> None:
    world.say(
        f"In {place.realm}, where old stories clung to stone like moss, there lived {hero.id}, "
        f"a {hero.traits[0]} {hero.type} who listened closely to small things."
    )
    world.say(
        f"Each dawn, {hero.pronoun()} carried cups to {place.water_phrase}, and people said the water there "
        f"remembered the songs of the first stars."
    )


def first_signs(world: World, place: Place, hero: Entity, belief: FalseBelief) -> None:
    village = world.get("village")
    village.meters["unease"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"Then a strange hush came over the valley. Bakers leaned on their ovens, shepherds forgot their own counting, "
        f"and even the dogs began to drowse in the shade."
    )
    world.say(belief.line)


def ask_question(world: World, hero: Entity, elder: Entity) -> None:
    world.say(
        f'{hero.id} looked at the sleepy faces and asked {elder.label_word} {elder.id}, '
        f'"What is making everyone so heavy-eyed?"'
    )
    world.say(
        f'{elder.id} could not answer, and that made the mystery feel bigger than the morning.'
    )


def investigate(world: World, place: Place, hero: Entity, source: Source) -> None:
    pred = predict_drowse(world, source)
    world.facts["predicted_drowse"] = pred["drowse"]
    hero.memes["resolve"] += 1
    world.say(
        f"So {hero.id} went alone to the water. {place.path_text}, and {hero.pronoun()} searched with the care of a sparrow choosing one grain from many."
    )
    world.say(
        f"{hero.pronoun().capitalize()} found one sign, then another: {source.clue}, and {source.trail}."
    )


def surprise_reveal(world: World, hero: Entity, source: Source) -> None:
    water = world.get("water")
    water.meters["tainted"] += 1
    water.attrs["source"] = source.id
    propagate(world, narrate=False)
    hero.memes["surprise"] += 1
    hero.memes["understanding"] += 1
    world.say(
        f"At last the truth leaped at {hero.pronoun('object')} like a fish flashing under the surface. {source.reveal}"
    )
    world.say(
        f'"Not a curse," {hero.id} whispered. "Bacteria." The little word sounded plain beside all the grand rumors, '
        f"and that was the surprise of it."
    )


def warn_elder(world: World, hero: Entity, elder: Entity, place: Place, source: Source) -> None:
    elder.memes["alarm"] += 1
    world.say(
        f"{hero.id} ran back from {place.water_label} with wet sandals and a racing heart."
    )
    world.say(
        f'"Do not let anyone drink," {hero.pronoun()} cried. "The trouble is in the water, and it came from {source.label}."'
    )


def heal(world: World, elder: Entity, response: Response, place: Place) -> None:
    water = world.get("water")
    village = world.get("village")
    water.meters["tainted"] = 0.0
    village.meters["drowse"] = 0.0
    village.meters["sick"] = 0.0
    world.say(
        f"Then {elder.id} {response.text}."
    )
    world.say(
        f"By sunset, cups were filled only from fresh water, heads lifted, and the long sleepy spell began to break."
    )
    world.say(place.ending_image.capitalize() + ".")


def fail_response(world: World, elder: Entity, response: Response) -> None:
    village = world.get("village")
    village.meters["sick"] += 1
    village.meters["drowse"] += 1
    world.say(
        f"But {elder.id} {response.fail}."
    )
    world.say(
        "That night more lamps burned behind shuttered windows, yet fewer songs rose from the houses."
    )


def bad_ending(world: World, hero: Entity, place: Place) -> None:
    hero.memes["grief"] += 1
    world.say(
        f"Morning came gray. More people lay under blankets, too weak to work, and even the market fountain stood quiet."
    )
    world.say(
        f"{hero.id} knew the mystery had been solved too late. In {place.realm}, the story would be remembered not as a triumph but as a warning."
    )


def tell(
    place: Place,
    source: Source,
    response: Response,
    name: str = "Iris",
    gender: str = "girl",
    elder_type: str = "priestess",
    trait: str = "watchful",
    false_belief: FalseBelief = FALSE_BELIEFS["owl_curse"],
    delay: int = 0,
) -> World:
    world = World()
    hero = world.add(
        Entity(
            id=name,
            kind="character",
            type=gender,
            role="hero",
            traits=[trait],
            tags={"hero"},
        )
    )
    elder = world.add(
        Entity(
            id="Sel",
            kind="character",
            type=elder_type,
            role="elder",
            label="the elder",
            tags={"elder"},
        )
    )
    water = world.add(
        Entity(
            id="water",
            type="water",
            label=place.water_label,
            phrase=place.water_phrase,
            tags=set(place.tags),
        )
    )
    village = world.add(
        Entity(
            id="village",
            type="village",
            label="the valley people",
            tags={"village"},
        )
    )

    introduce(world, place, hero)
    first_signs(world, place, hero, false_belief)

    world.para()
    ask_question(world, hero, elder)
    investigate(world, place, hero, source)
    surprise_reveal(world, hero, source)
    warn_elder(world, hero, elder, place, source)

    contained = is_contained(response, source, delay)

    world.para()
    if contained:
        heal(world, elder, response, place)
        outcome = "healed"
    else:
        fail_response(world, elder, response)
        bad_ending(world, hero, place)
        outcome = "bad"

    world.facts.update(
        hero=hero,
        elder=elder,
        place=place,
        source=source,
        response=response,
        false_belief=false_belief,
        outcome=outcome,
        delay=delay,
        severity=severity_of(source, delay),
        discovered=True,
        bacteria=source.bacteria,
        drowse_started=True,
        contained=contained,
    )
    return world


KNOWLEDGE = {
    "bacteria": [
        (
            "What are bacteria?",
            "Bacteria are tiny living things so small you need a microscope to see them. Some are harmless, but some can make water or food unsafe.",
        )
    ],
    "boil": [
        (
            "Why can boiling water help?",
            "Boiling water can kill many germs that live in it. That is why people may boil unsafe water before drinking it.",
        )
    ],
    "clean": [
        (
            "Why does cleaning a water place matter?",
            "If dirt or rotten things are left in a water place, germs can spread there. Cleaning removes the dirty source and helps make the water safer.",
        )
    ],
    "well": [
        (
            "What is a well?",
            "A well is a deep place where people draw water from the ground. Villages use wells so they can drink, wash, and cook.",
        )
    ],
    "spring": [
        (
            "What is a spring?",
            "A spring is water that flows out of the ground by itself. People often gather spring water because it is fresh and clear.",
        )
    ],
    "cistern": [
        (
            "What is a cistern?",
            "A cistern is a place built to hold water. People store water there so they can use it later.",
        )
    ],
    "hand-pl": [
        (
            "What is a ladle used for?",
            "A ladle is a scoop with a handle that helps people dip water or soup. If it is dirty and shared by many people, it can spread germs.",
        )
    ],
    "prayer": [
        (
            "Why is prayer alone not enough to clean dirty water?",
            "Prayer may comfort people, but dirty water still needs practical help. If germs are in the water, someone must also remove the source and make the water safe.",
        )
    ],
}
KNOWLEDGE_ORDER = ["bacteria", "well", "spring", "cistern", "hand-pl", "boil", "clean", "prayer"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    place = f["place"]
    source = f["source"]
    outcome = f["outcome"]
    return [
        f'Write a short child-facing myth about a sleepy village mystery that includes the words "drowse", "hand-pl", and "bacteria".',
        f"Tell a myth-like story where {hero.id} discovers why people in {place.realm} drowse after drinking holy water, and the surprise is that the cause is {source.label} rather than a curse.",
        f"Write a mystery-to-solve story with a {'bad ending' if outcome == 'bad' else 'hopeful ending'} in which a child notices small clues and learns that plain truth can hide inside grand rumors.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    place = f["place"]
    source = f["source"]
    response = f["response"]
    belief = f["false_belief"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a {hero.type} in {place.realm}, and {elder.id}, the village elder. {hero.id} becomes the one who solves the mystery.",
        ),
        (
            "What was the mystery?",
            f"The people of {place.realm} began to drowse, and nobody knew why. The mystery was to learn what hidden thing was making the water unsafe.",
        ),
        (
            "What did people think at first?",
            f"At first, people believed in {belief.label}. That made the surprise stronger, because the real cause was ordinary bacteria instead of magic.",
        ),
        (
            f"How did {hero.id} solve the mystery?",
            f"{hero.id} went to the water place and followed small clues like {source.clue}. Those clues led {hero.pronoun('object')} to {source.label}, which showed where the bacteria were coming from.",
        ),
        (
            "What was the surprise truth?",
            f"The surprise was that no curse had caused the trouble. Tiny bacteria in or near the water were making people sleepy and sick.",
        ),
    ]
    if f["outcome"] == "healed":
        qa.append(
            (
                f"What did {elder.id} do once the mystery was solved?",
                f"{elder.id} {response.qa_text}. That practical help mattered because removing the source stopped more people from drinking the bad water.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the valley waking up again and the water running clear. The ending image proves that the danger changed because people acted in time.",
            )
        )
    else:
        qa.append(
            (
                f"Why is this a bad ending even though {hero.id} found the answer?",
                f"It is a bad ending because the answer came too late or the response was too weak. More people fell ill after the mystery was solved, so knowledge alone did not save the village.",
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended in sadness, with houses quiet and many villagers still weak. The valley remembers the story as a warning about acting quickly when water is unsafe.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    place = f["place"]
    source = f["source"]
    response = f["response"]
    tags = {"bacteria"} | set(place.tags) | set(source.tags)
    if f["outcome"] == "healed":
        tags |= set(response.tags)
    else:
        tags |= set(response.tags)
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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="sun_well",
        source="hand_pl_ladle",
        response="boil_and_scrub",
        name="Iris",
        gender="girl",
        elder="priestess",
        trait="watchful",
        false_belief="owl_curse",
        delay=0,
    ),
    StoryParams(
        place="moon_spring",
        source="spoiled_offering",
        response="drain_and_stone_lime",
        name="Orin",
        gender="boy",
        elder="priest",
        trait="patient",
        false_belief="angry_moon",
        delay=0,
    ),
    StoryParams(
        place="cloud_cistern",
        source="rat_in_channel",
        response="boil_and_scrub",
        name="Nysa",
        gender="girl",
        elder="priestess",
        trait="brave",
        false_belief="sleep_giant",
        delay=2,
    ),
]


def explain_rejection(source: Source) -> str:
    if not source.bacteria:
        return (
            f"(No story: {source.label} is only a rumor, not a real source of bacteria. "
            f"The mystery here needs an honest physical cause for the sleepy illness.)"
        )
    return "(No story: this source does not make the water unsafe.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = ", ".join(sorted(x.id for x in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={r.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    return "healed" if is_contained(RESPONSES[params.response], SOURCES[params.source], params.delay) else "bad"


ASP_RULES = r"""
valid(P, S) :- place(P), source(S), bacteria_source(S).

sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

severity(V) :- chosen_source(S), source_severity(S, SS), delay(D), V = SS + D.
contained :- chosen_response(R), power(R, P), severity(V), P >= V.

outcome(healed) :- contained.
outcome(bad) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("source_severity", sid, source.severity))
        if source.bacteria:
            lines.append(asp.fact("bacteria_source", sid))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        lines.append(asp.fact("power", rid, response.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_source", params.source),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
        ]
    )
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

    clingo_sense = set(asp_sensible())
    python_sense = {r.id for r in sensible_responses()}
    if clingo_sense == python_sense:
        print(f"OK: sensible responses match ({sorted(clingo_sense)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(clingo_sense)} python={sorted(python_sense)}")

    cases = list(CURATED)
    for s in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(s))
            cases.append(params)
        except StoryError:
            continue

    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic sleepy-mystery story world. Unspecified choices are picked at random (seeded)."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--elder", choices=["priestess", "priest"])
    ap.add_argument("--belief", choices=FALSE_BELIEFS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the village waits before acting")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and not contamination_risk(SOURCES[args.source]):
        raise StoryError(explain_rejection(SOURCES[args.source]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.source is None or combo[1] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, source = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["priestess", "priest"])
    belief = args.belief or rng.choice(sorted(FALSE_BELIEFS))
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)

    return StoryParams(
        place=place,
        source=source,
        response=response,
        name=name,
        gender=gender,
        elder=elder,
        trait=trait,
        false_belief=belief,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.false_belief not in FALSE_BELIEFS:
        raise StoryError(f"(Unknown belief: {params.false_belief})")
    if not contamination_risk(SOURCES[params.source]):
        raise StoryError(explain_rejection(SOURCES[params.source]))
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=PLACES[params.place],
        source=SOURCES[params.source],
        response=RESPONSES[params.response],
        name=params.name,
        gender=params.gender,
        elder_type=params.elder,
        trait=params.trait,
        false_belief=FALSE_BELIEFS[params.false_belief],
        delay=params.delay,
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
        print(asp_program("", "#show valid/2.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sensible = asp_sensible()
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, source) combos:\n")
        for place, source in combos:
            print(f"  {place:13} {source}")
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
            header = f"### {p.name}: {p.source} at {p.place} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
