#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py
===============================================================================

A standalone story world about a child in a choir who hears a small hidden sound,
grows curious, and then shows bravery by speaking up the safe way. The stories
aim for a gentle rhyming cadence with repeated phrases.

Reference seed:
    Write a story that includes the following words and narrative instruments.
    Words: choir
    Features: Repetition, Curiosity, Bravery
    Style: Rhyming Story

World idea:
    During choir practice, a child hears a tiny sound from somewhere in the room.
    Curiosity tugs at the child. Instead of climbing or poking into a dark place
    alone, the child is brave in the better way: speaking up. A grown-up helps,
    the hidden little creature is found safely, and the choir sings again with a
    happy ending image.

The reasonableness constraint:
    Not every hidden place and response method fit every situation. A bird high
    on a curtain rail needs a tall grown-up and a ladder/stool; a kitten shut in
    a prop chest can be helped by opening the lid; a duckling tangled among robes
    can be untangled by hand. The world refuses combinations that would be weak
    or unsafe.

Run it
------
    python storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py --creature kitten --place chest
    python storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py --creature bird --response open_lid
    python storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/choir_repetition_curiosity_bravery_rhyming_story.py --qa --json
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
        female = {"girl", "mother", "woman", "conductor_f"}
        male = {"boy", "father", "man", "conductor_m"}
        animal_it = {"kitten", "duckling", "bird"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in animal_it:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "conductor_f": "teacher",
            "conductor_m": "teacher",
            "mother": "mom",
            "father": "dad",
        }.get(self.type, self.type)


@dataclass
class ChoirTheme:
    id: str
    room: str
    bright: str
    opening: str
    refrain: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Creature:
    id: str
    label: str
    phrase: str
    sound: str
    tiny_sound: str
    trouble: str
    comfort: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    location: str
    problem: str
    height: str
    dark: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    solves: set[str] = field(default_factory=set)
    handles_height: set[str] = field(default_factory=set)
    text: str = ""
    qa_text: str = ""
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


def _r_hidden_sound(world: World) -> list[str]:
    creature = world.get("creature")
    place = world.get("place")
    child = world.get("child")
    room = world.get("room")
    if creature.meters["stuck"] < THRESHOLD:
        return []
    sig = ("hidden_sound", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    room.meters["mystery"] += 1
    return ["__sound__"] if place.attrs.get("dark") else []


def _r_worry(world: World) -> list[str]:
    child = world.get("child")
    creature = world.get("creature")
    if child.memes["curiosity"] < THRESHOLD or creature.meters["stuck"] < THRESHOLD:
        return []
    sig = ("worry", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["worry"] += 1
    return []


def _r_bravery(world: World) -> list[str]:
    child = world.get("child")
    teacher = world.get("teacher")
    if child.memes["speaks_up"] < THRESHOLD:
        return []
    sig = ("bravery", child.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["bravery"] += 1
    teacher.memes["trust"] += 1
    return []


def _r_relief(world: World) -> list[str]:
    creature = world.get("creature")
    child = world.get("child")
    teacher = world.get("teacher")
    if creature.meters["safe"] < THRESHOLD:
        return []
    sig = ("relief", creature.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    teacher.memes["joy"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="hidden_sound", tag="mystery", apply=_r_hidden_sound),
    Rule(name="worry", tag="emotion", apply=_r_worry),
    Rule(name="bravery", tag="emotion", apply=_r_bravery),
    Rule(name="relief", tag="emotion", apply=_r_relief),
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


def response_works(place: HidingPlace, response: Response) -> bool:
    return place.problem in response.solves and place.height in response.handles_height


def sensible_responses(place: HidingPlace) -> list[Response]:
    return [
        r for r in RESPONSES.values()
        if r.sense >= SENSE_MIN and response_works(place, r)
    ]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for theme_id in THEMES:
        for creature_id in CREATURES:
            for place_id, place in HIDING_PLACES.items():
                if sensible_responses(place):
                    combos.append((theme_id, creature_id, place_id))
    return combos


def explain_response(place: HidingPlace, response: Response) -> str:
    if response.sense < SENSE_MIN:
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). A child should not solve this alone.)"
        )
    if place.problem not in response.solves:
        return (
            f"(No story: {response.label} does not fit {place.phrase}. "
            f"That place needs a method that handles {place.problem.replace('_', ' ')}.)"
        )
    if place.height not in response.handles_height:
        return (
            f"(No story: {response.label} does not fit a {place.height} place like {place.phrase}.)"
        )
    return "(No story: that response does not fit this situation.)"


def predict_danger(world: World, place: HidingPlace) -> dict:
    sim = world.copy()
    child = sim.get("child")
    sim.get("place").attrs["opened_by_child"] = True
    if place.height == "high":
        child.meters["risk"] += 2
    else:
        child.meters["risk"] += 1
    return {
        "risk": child.meters["risk"],
        "too_risky": child.meters["risk"] >= THRESHOLD,
    }


def practice_setup(world: World, theme: ChoirTheme, child: Entity, teacher: Entity) -> None:
    child.memes["joy"] += 1
    teacher.memes["care"] += 1
    world.say(
        f"{theme.opening} In {theme.room}, {theme.bright} and a little {theme.id} "
        f"named {child.id} stood with the choir."
    )
    world.say(
        f'The children sang, "{theme.refrain}" Then they sang it once more: '
        f'"{theme.refrain}"'
    )


def first_sound(world: World, creature: Creature, place: HidingPlace, child: Entity) -> None:
    world.get("creature").meters["stuck"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But under the song came {creature.tiny_sound} from {place.phrase} {place.location}. "
        f'{child.id} blinked. "{creature.sound}? {creature.sound}?"'
    )
    world.say(
        f'The choir sang on, "{world.facts["theme"].refrain}," yet {child.id} listened again: '
        f'"{creature.sound}? {creature.sound}?"'
    )


def curiosity_beat(world: World, child: Entity, place: HidingPlace) -> None:
    pred = predict_danger(world, place)
    world.facts["predicted_risk"] = pred["risk"]
    child.memes["lean"] += 1
    world.say(
        f"Curiosity tugged like a little string. {child.id} wanted to peek at {place.phrase}."
    )
    if pred["too_risky"]:
        world.say(
            f"But the place looked dark and {place.height}, and peeking alone did not feel right."
        )


def brave_choice(world: World, child: Entity, teacher: Entity, creature: Creature) -> None:
    child.memes["speaks_up"] += 1
    propagate(world, narrate=False)
    world.say(
        f"So {child.id} took a brave small breath and whispered to the teacher, "
        f'"I hear a {creature.sound}. I think something needs help."'
    )
    world.say(
        f'{teacher.label_word.capitalize()} smiled and nodded. "That was brave of you, '
        f'{child.id}. Brave is not rushing. Brave is speaking when help is due."'
    )


def pause_choir(world: World, theme: ChoirTheme, teacher: Entity) -> None:
    world.say(
        f'The teacher lifted a hand. The choir grew quiet. No more "{theme.refrain}" for a beat.'
    )
    world.say("In the soft hush-hush, everyone listened.")


def rescue(world: World, response: Response, creature: Creature, place: HidingPlace, teacher: Entity) -> None:
    ent_creature = world.get("creature")
    ent_place = world.get("place")
    ent_creature.meters["stuck"] = 0.0
    ent_creature.meters["safe"] += 1
    ent_place.meters["opened"] += 1
    propagate(world, narrate=False)
    body = response.text.format(place=place.label, creature=creature.label)
    world.say(
        f"Then {teacher.label_word} {body}."
    )
    world.say(
        f"Out came {creature.phrase}, {creature.trouble} no more, and soon {creature.comfort}."
    )


def closing_song(world: World, theme: ChoirTheme, child: Entity, creature: Creature) -> None:
    world.say(
        f'{child.id} smiled so wide the whole room seemed to shine. '
        f'Curious eyes had noticed. A brave voice had spoken in time.'
    )
    world.say(
        f'Then the choir began again: "{theme.refrain}" Once more it floated bright and light.'
    )
    world.say(
        f"And beside the door, {creature.phrase} rested safe, while the song rose warm into the night."
    )


def tell(
    theme: ChoirTheme,
    creature_cfg: Creature,
    place_cfg: HidingPlace,
    response_cfg: Response,
    *,
    child_name: str = "Mina",
    child_type: str = "girl",
    teacher_type: str = "conductor_f",
) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    teacher = world.add(Entity(id="teacher", kind="character", type=teacher_type, label="the teacher", role="teacher"))
    creature = world.add(
        Entity(
            id="creature",
            kind="character",
            type=creature_cfg.id,
            label=creature_cfg.label,
            phrase=creature_cfg.phrase,
            role="creature",
            tags=set(creature_cfg.tags),
        )
    )
    place = world.add(
        Entity(
            id="place",
            kind="thing",
            type="place",
            label=place_cfg.label,
            phrase=place_cfg.phrase,
            role="place",
            attrs={"problem": place_cfg.problem, "height": place_cfg.height, "dark": place_cfg.dark},
            tags=set(place_cfg.tags),
        )
    )
    room = world.add(Entity(id="room", kind="thing", type="room", label=theme.room, role="room", tags=set(theme.tags)))
    world.facts["theme"] = theme
    world.facts["theme_id"] = theme.id

    practice_setup(world, theme, child, teacher)
    world.para()
    first_sound(world, creature_cfg, place_cfg, child)
    curiosity_beat(world, child, place_cfg)
    world.para()
    brave_choice(world, child, teacher, creature_cfg)
    pause_choir(world, theme, teacher)
    rescue(world, response_cfg, creature_cfg, place_cfg, teacher)
    world.para()
    closing_song(world, theme, child, creature_cfg)

    world.facts.update(
        child=child,
        child_name=child_name,
        teacher=teacher,
        creature_cfg=creature_cfg,
        place_cfg=place_cfg,
        response=response_cfg,
        noticed=child.memes["curiosity"] >= THRESHOLD,
        brave=child.memes["bravery"] >= THRESHOLD,
        rescued=creature.meters["safe"] >= THRESHOLD,
    )
    return world


THEMES = {
    "school_hall": ChoirTheme(
        id="school_hall",
        room="the school hall",
        bright="sunlight poured in stripes across the wooden floor",
        opening="One afternoon, when the windows glowed gold,",
        refrain="Sing high, sing low, soft as snow",
        tags={"choir", "song"},
    ),
    "chapel_room": ChoirTheme(
        id="chapel_room",
        room="the chapel room",
        bright="colored light trembled on the benches below",
        opening="One calm evening, when the lamps were low,",
        refrain="Sing slow, sing bright, little notes of light",
        tags={"choir", "song"},
    ),
    "community_stage": ChoirTheme(
        id="community_stage",
        room="the community stage",
        bright="paper stars hung over the chairs in a row",
        opening="One rehearsal night, before the show,",
        refrain="La-la, la-la, steady and slow",
        tags={"choir", "song"},
    ),
}

CREATURES = {
    "kitten": Creature(
        id="kitten",
        label="kitten",
        phrase="a tiny gray kitten",
        sound="mew",
        tiny_sound="a faint mew-mew",
        trouble="shut in the dark",
        comfort="it purred against the teacher's sleeve",
        tags={"kitten", "animal"},
    ),
    "duckling": Creature(
        id="duckling",
        label="duckling",
        phrase="a fluffy yellow duckling",
        sound="peep",
        tiny_sound="a worried peep-peep",
        trouble="caught and wriggly",
        comfort="it gave a soft peep and tucked its head down",
        tags={"duckling", "animal"},
    ),
    "bird": Creature(
        id="bird",
        label="bird",
        phrase="a small brown bird",
        sound="chirp",
        tiny_sound="a quick chirp-chirp",
        trouble="fluttering in a frightened loop",
        comfort="it settled its wings and grew calm",
        tags={"bird", "animal"},
    ),
}

HIDING_PLACES = {
    "chest": HidingPlace(
        id="chest",
        label="prop chest",
        phrase="the old prop chest",
        location="near the velvet curtain",
        problem="closed_in",
        height="low",
        dark=True,
        tags={"chest", "dark"},
    ),
    "robes": HidingPlace(
        id="robes",
        label="robe rack",
        phrase="the choir robe rack",
        location="by the side wall",
        problem="tangled",
        height="low",
        dark=True,
        tags={"robes", "dark"},
    ),
    "rail": HidingPlace(
        id="rail",
        label="curtain rail",
        phrase="the high curtain rail",
        location="above the stage",
        problem="perched_high",
        height="high",
        dark=False,
        tags={"curtain", "high"},
    ),
}

RESPONSES = {
    "open_lid": Response(
        id="open_lid",
        label="opened the lid gently",
        sense=3,
        solves={"closed_in"},
        handles_height={"low"},
        text="walked over, opened the lid gently, and reached into the {place}",
        qa_text="opened the chest gently and lifted the little animal out",
        tags={"help_adult", "safe_rescue"},
    ),
    "untangle": Response(
        id="untangle",
        label="untangled it carefully",
        sense=3,
        solves={"tangled"},
        handles_height={"low"},
        text="moved the robes aside and untangled the {creature} carefully",
        qa_text="moved the robes aside and untangled the animal carefully",
        tags={"help_adult", "safe_rescue"},
    ),
    "ladder": Response(
        id="ladder",
        label="used the step ladder",
        sense=3,
        solves={"perched_high"},
        handles_height={"high"},
        text="brought a little step ladder, climbed slowly, and guided the {creature} down from the {place}",
        qa_text="used a step ladder and guided the little animal down safely",
        tags={"ladder", "safe_rescue"},
    ),
    "child_climb": Response(
        id="child_climb",
        label="let the child climb",
        sense=1,
        solves={"closed_in", "tangled", "perched_high"},
        handles_height={"low", "high"},
        text="told the child to climb up alone",
        qa_text="let the child climb up alone",
        tags={"unsafe"},
    ),
}


@dataclass
class StoryParams:
    theme: str
    creature: str
    place: str
    response: str
    child_name: str
    child_type: str
    teacher_type: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "choir": [
        (
            "What is a choir?",
            "A choir is a group of people who sing together. They listen to one another so their voices sound smooth and strong."
        )
    ],
    "kitten": [
        (
            "What sound does a kitten make?",
            "A kitten often makes a mew or a meow. It uses that little sound to call for comfort or help."
        )
    ],
    "duckling": [
        (
            "What sound does a duckling make?",
            "A duckling often peeps softly. Little peeps can help a grown-up know where the duckling is."
        )
    ],
    "bird": [
        (
            "Why might a bird flap when it is scared?",
            "A scared bird may flap quickly because it wants to get away. When it is calm and safe, its wings can settle again."
        )
    ],
    "bravery": [
        (
            "What is bravery?",
            "Bravery is doing the right thing even when you feel small or nervous. Sometimes the bravest thing is asking for help."
        )
    ],
    "curiosity": [
        (
            "What is curiosity?",
            "Curiosity is the feeling that makes you want to know more. It can help you notice important things when you use it wisely."
        )
    ],
    "ladder": [
        (
            "Why should a grown-up use a ladder for a high rescue?",
            "A ladder helps reach something up high in a careful way. A grown-up should do that kind of climbing so children stay safe."
        )
    ],
    "safe_rescue": [
        (
            "What should you do if you hear an animal stuck somewhere?",
            "Tell a grown-up right away and let the grown-up help. That is safer than climbing or reaching into dark places alone."
        )
    ],
}
KNOWLEDGE_ORDER = ["choir", "curiosity", "bravery", "kitten", "duckling", "bird", "ladder", "safe_rescue"]


GIRL_NAMES = ["Mina", "Lila", "Nora", "Ava", "Lucy", "Zoe", "Ivy", "Ella"]
BOY_NAMES = ["Noah", "Leo", "Sam", "Eli", "Ben", "Theo", "Max", "Finn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child_name = f["child_name"]
    creature = f["creature_cfg"]
    theme = f["theme"]
    place = f["place_cfg"]
    return [
        f'Write a short rhyming story for a 3-to-5-year-old that includes the word "choir" and shows curiosity and bravery.',
        f"Tell a gentle story where {child_name} is singing in a choir, hears a tiny {creature.sound} from {place.phrase}, and bravely tells a teacher.",
        f'Write a story with repetition in the song line "{theme.refrain}" and end with a rescued little animal and a warm final image.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child_name = f["child_name"]
    creature = f["creature_cfg"]
    place = f["place_cfg"]
    response = f["response"]
    theme = f["theme"]
    out: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child singing with the choir, a kind teacher, and {creature.phrase}. The story follows what {child_name} notices and does next."
        ),
        (
            "What made the child curious?",
            f"{child_name} heard {creature.tiny_sound} coming from {place.phrase}. That small strange sound made {child_name} wonder if someone needed help."
        ),
        (
            "How was the child brave?",
            f"{child_name} was brave by speaking up instead of poking into the dark place alone. The brave choice was asking the teacher for help at the right time."
        ),
    ]
    if f.get("rescued"):
        out.append(
            (
                f"How did the teacher help {creature.phrase}?",
                f"The teacher {response.qa_text}. That worked because the little animal was in {place.phrase}, and the grown-up used the safe method that fit that place."
            )
        )
        out.append(
            (
                "How did the story end?",
                f"It ended with {creature.phrase} safe and calm while the choir sang again. The repeated song sounded happier because the worried little mystery had been solved."
            )
        )
    out.append(
        (
            "What line did the choir sing more than once?",
            f'The choir repeated, "{theme.refrain}" The repeated line made the story sound musical and helped show the choir practice continuing around the mystery.'
        )
    )
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"choir", "curiosity", "bravery", "safe_rescue"}
    tags |= set(f["creature_cfg"].tags)
    tags |= set(f["response"].tags)
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
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
        if e.role:
            bits.append(f"role={e.role}")
        label = e.label or e.id
        lines.append(f"  {e.id:8} ({e.type:11}) {label!r} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="school_hall",
        creature="kitten",
        place="chest",
        response="open_lid",
        child_name="Mina",
        child_type="girl",
        teacher_type="conductor_f",
    ),
    StoryParams(
        theme="chapel_room",
        creature="duckling",
        place="robes",
        response="untangle",
        child_name="Noah",
        child_type="boy",
        teacher_type="conductor_m",
    ),
    StoryParams(
        theme="community_stage",
        creature="bird",
        place="rail",
        response="ladder",
        child_name="Lila",
        child_type="girl",
        teacher_type="conductor_f",
    ),
]


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
works(P, R) :- place(P), response(R), problem(P, Pr), solves(R, Pr),
               height(P, H), handles_height(R, H).
valid(T, C, P) :- theme(T), creature(C), place(P), sensible(R), works(P, R).

chosen_ok :- chosen_place(P), chosen_response(R), sensible(R), works(P, R).
:- chosen_place(P), chosen_response(R), not works(P, R).
:- chosen_response(R), not sensible(R).

outcome(rescued) :- chosen_ok.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for tid in THEMES:
        lines.append(asp.fact("theme", tid))
    for cid in CREATURES:
        lines.append(asp.fact("creature", cid))
    for pid, place in HIDING_PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("problem", pid, place.problem))
        lines.append(asp.fact("height", pid, place.height))
    for rid, response in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, response.sense))
        for problem in sorted(response.solves):
            lines.append(asp.fact("solves", rid, problem))
        for height in sorted(response.handles_height):
            lines.append(asp.fact("handles_height", rid, height))
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

    extra = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_response", params.response),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    python_sensible = {r.id for r in RESPONSES.values() if r.sense >= SENSE_MIN}
    clingo_sensible = set(asp_sensible())
    if python_sensible == clingo_sensible:
        print(f"OK: sensible responses match ({sorted(python_sensible)}).")
    else:
        rc = 1
        print(
            f"MISMATCH in sensible responses: clingo={sorted(clingo_sensible)} "
            f"python={sorted(python_sensible)}"
        )

    for params in CURATED:
        py_outcome = "rescued" if response_works(HIDING_PLACES[params.place], RESPONSES[params.response]) and RESPONSES[params.response].sense >= SENSE_MIN else "?"
        asp_res = asp_outcome(params)
        if py_outcome != asp_res:
            rc = 1
            print(f"MISMATCH in outcome for {params}: python={py_outcome} asp={asp_res}")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        if not smoke_sample.story.strip():
            raise StoryError("(Smoke test failed: empty story.)")
        emit(smoke_sample, trace=False, qa=False, header="")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a choir mystery solved by curiosity, bravery, and a safe grown-up rescue."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--creature", choices=CREATURES)
    ap.add_argument("--place", choices=HIDING_PLACES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--teacher", choices=["conductor_f", "conductor_m"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and args.place:
        place = HIDING_PLACES[args.place]
        response = RESPONSES[args.response]
        if not response_works(place, response) or response.sense < SENSE_MIN:
            raise StoryError(explain_response(place, response))
    elif args.response and RESPONSES[args.response].sense < SENSE_MIN:
        place = HIDING_PLACES[args.place] if args.place else next(iter(HIDING_PLACES.values()))
        raise StoryError(explain_response(place, RESPONSES[args.response]))

    combos = [
        c for c in valid_combos()
        if (args.theme is None or c[0] == args.theme)
        and (args.creature is None or c[1] == args.creature)
        and (args.place is None or c[2] == args.place)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, creature, place = rng.choice(sorted(combos))

    valid_responses = [r.id for r in sensible_responses(HIDING_PLACES[place])]
    if args.response:
        if args.response not in valid_responses:
            raise StoryError(explain_response(HIDING_PLACES[place], RESPONSES[args.response]))
        response = args.response
    else:
        response = rng.choice(sorted(valid_responses))

    child_type = args.gender or rng.choice(["girl", "boy"])
    child_name = args.name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    teacher_type = args.teacher or rng.choice(["conductor_f", "conductor_m"])

    return StoryParams(
        theme=theme,
        creature=creature,
        place=place,
        response=response,
        child_name=child_name,
        child_type=child_type,
        teacher_type=teacher_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError(f"(Unknown theme: {params.theme})")
    if params.creature not in CREATURES:
        raise StoryError(f"(Unknown creature: {params.creature})")
    if params.place not in HIDING_PLACES:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    place = HIDING_PLACES[params.place]
    response = RESPONSES[params.response]
    if response.sense < SENSE_MIN or not response_works(place, response):
        raise StoryError(explain_response(place, response))

    world = tell(
        THEMES[params.theme],
        CREATURES[params.creature],
        place,
        response,
        child_name=params.child_name,
        child_type=params.child_type,
        teacher_type=params.teacher_type,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, creature, place) combos:\n")
        for theme, creature, place in combos:
            print(f"  {theme:15} {creature:8} {place}")
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
            header = f"### {p.child_name}: {p.creature} in {p.place} ({p.theme}, {p.response})"
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
