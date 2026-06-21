#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py
======================================================================

A standalone storyworld for a small tall-tale domain: a child hears an enormous,
clattering mystery sound, chooses whether to face it bravely, and discovers that
the mighty "monster" was only something ordinary in the wind.

The required seed word appears in the core source of the sound:
venetian blinds.

Run it
------
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py --source blinds --weather gusty
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py --method stomp
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/venetian_sound_effects_bravery_tall_tale.py --verify
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
        female = {"girl", "mother", "grandmother", "woman", "aunt"}
        male = {"boy", "father", "grandfather", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def title_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    room: str
    opening: str
    ending: str
    helper_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Weather:
    id: str
    sky: str
    wind: int
    rain: int
    sound_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    giant_name: str
    cause_text: str
    needs_wind: bool = False
    needs_rain: bool = False
    loudness: int = 1
    brave_bonus: int = 0
    tags: set[str] = field(default_factory=set)


@dataclass
class Method:
    id: str
    label: str
    sense: int
    courage_bonus: int
    requires_helper: bool
    setup_text: str
    resolve_text: str
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


def _r_rattle_fear(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.role != "source" or ent.meters["rattling"] < THRESHOLD:
            continue
        sig = ("rattle_fear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero = world.get("hero")
        room = world.get("room")
        hero.memes["fear"] += ent.meters["rattling"]
        room.meters["mystery"] += 1
        out.append("__rattle__")
    return out


def _r_seen_relief(world: World) -> list[str]:
    out: list[str] = []
    source = world.get("source")
    if source.meters["seen"] < THRESHOLD:
        return out
    sig = ("seen_relief", source.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero = world.get("hero")
    room = world.get("room")
    hero.memes["fear"] = 0.0
    hero.memes["relief"] += 1
    hero.memes["wonder"] += 1
    room.meters["mystery"] = 0.0
    room.meters["calm"] += 1
    out.append("__seen__")
    return out


CAUSAL_RULES = [
    Rule(name="rattle_fear", tag="emotional", apply=_r_rattle_fear),
    Rule(name="seen_relief", tag="emotional", apply=_r_seen_relief),
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
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def source_active(weather: Weather, source: Source) -> bool:
    if source.needs_wind and weather.wind <= 0:
        return False
    if source.needs_rain and weather.rain <= 0:
        return False
    return True


def sensible_methods() -> list[Method]:
    return [m for m in METHODS.values() if m.sense >= SENSE_MIN]


def courage_total(params: "StoryParams") -> int:
    trait_bonus = TRAIT_BONUS[params.trait]
    helper_bonus = 1 if params.helper else 0
    source_bonus = SOURCES[params.source].brave_bonus
    method_bonus = METHODS[params.method].courage_bonus
    return trait_bonus + helper_bonus + source_bonus + method_bonus


def fear_total(params: "StoryParams") -> int:
    return WEATHERS[params.weather].wind + SOURCES[params.source].loudness


def outcome_of(params: "StoryParams") -> str:
    method = METHODS[params.method]
    if method.requires_helper and not params.helper:
        return "waited"
    return "solved" if courage_total(params) >= fear_total(params) else "waited"


def prediction_for(world: World, params: "StoryParams") -> dict:
    sim = world.copy()
    source = sim.get("source")
    source.meters["rattling"] += WEATHERS[params.weather].wind + SOURCES[params.source].loudness
    propagate(sim, narrate=False)
    return {
        "fear": sim.get("hero").memes["fear"],
        "mystery": sim.get("room").meters["mystery"],
        "solved": outcome_of(params) == "solved",
    }


def introduce(world: World, hero: Entity, setting: Setting) -> None:
    trait = hero.traits[0] if hero.traits else "brave"
    world.say(
        f"In {setting.place}, there lived {hero.id}, a {trait} little {hero.type} "
        f"who believed every ordinary day had room for one more impossible adventure."
    )
    world.say(setting.opening)


def set_scene(world: World, hero: Entity, weather: Weather, setting: Setting) -> None:
    world.say(
        f"That evening, {weather.sky}. {weather.sound_line} around the {setting.room}, "
        f"and {hero.id} felt the house listening with both ears."
    )


def start_noise(world: World, hero: Entity, source: Entity, src_cfg: Source, weather: Weather) -> None:
    source.meters["rattling"] += weather.wind + src_cfg.loudness
    propagate(world, narrate=False)
    world.say(
        f"Then it came -- {src_cfg.sound}! {src_cfg.sound}! {src_cfg.sound}! -- "
        f"so hard and sudden that the cups on the shelf seemed to blink."
    )
    world.say(
        f"{hero.id} jumped so high that, in tall-tale truth, {hero.pronoun()} nearly "
        f"brushed the moon with one sock."
    )


def imagine(world: World, hero: Entity, src_cfg: Source) -> None:
    hero.memes["imagination"] += 1
    hero.memes["fear"] += 1
    world.say(
        f'"That sounds like {src_cfg.giant_name}," {hero.id} whispered, and for one '
        f"grand second the dark corners looked big enough to hide a whole parade of giants."
    )


def helper_arrives(world: World, hero: Entity, helper: Optional[Entity], setting: Setting) -> None:
    if helper is None:
        world.say(
            f"But there was no one beside {hero.id} just then, only a wobbling shadow "
            f"and {hero.pronoun('possessive')} own thumping heart: thump-thump, thump-thump."
        )
        return
    hero.memes["trust"] += 1
    helper.memes["care"] += 1
    world.say(
        f"Just then {helper.id}, {hero.pronoun('possessive')} {setting.helper_word}, came near "
        f"with a steady face that did not wobble at all."
    )
    world.say(
        f'"I heard it too," {helper.id} said. "Big noises are not always big dangers."'
    )


def choose_method(world: World, hero: Entity, helper: Optional[Entity], method: Method) -> None:
    if helper is None:
        world.say(method.setup_text.replace("{helper}", "no one"))
    else:
        world.say(method.setup_text.replace("{helper}", helper.id))
    hero.memes["courage"] += method.courage_bonus


def solve(world: World, hero: Entity, helper: Optional[Entity], source: Entity,
          src_cfg: Source, method: Method) -> None:
    source.meters["seen"] += 1
    propagate(world, narrate=False)
    if helper is not None:
        helper.memes["pride"] += 1
    hero.memes["courage"] += 1
    world.say(method.resolve_text.replace("{source}", src_cfg.phrase))
    world.say(
        f"And there it was: {src_cfg.phrase}, making all that racket for the very ordinary reason "
        f"that {src_cfg.cause_text}."
    )
    world.say(
        f"{hero.id} let out a laugh that rolled across the room like marbles in a drum. "
        f'"Why, that giant is only {src_cfg.label}!" {hero.pronoun()} cried.'
    )


def wait_for_morning(world: World, hero: Entity, helper: Optional[Entity], src_cfg: Source) -> None:
    if helper is None:
        world.say(
            f"{hero.id} wanted to march toward the sound, but the night felt too wide, so "
            f"{hero.pronoun()} stayed under the quilt and waited for grown-up footsteps."
        )
    else:
        world.say(
            f"{hero.id} tried to be bold, but the sound still felt as big as a mountain wagon, "
            f"so {hero.pronoun()} squeezed close to {helper.id} and waited instead of rushing."
        )
    hero.memes["patience"] += 1
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1.0)
    world.say(
        f"In the bright morning light they found the culprit at once: {src_cfg.phrase}. "
        f"It had sounded enormous in the dark, but daylight made it honest-sized again."
    )


def ending(world: World, hero: Entity, setting: Setting, solved: bool) -> None:
    if solved:
        hero.memes["lesson"] += 1
        world.say(
            f"After that, whenever the old place boomed or banged, {hero.id} stood a little taller. "
            f"{setting.ending}"
        )
    else:
        hero.memes["lesson"] += 1
        world.say(
            f"After that, {hero.id} learned that waiting can be brave too, especially when the dark "
            f"is louder than your good sense. {setting.ending}"
        )


def tell(setting: Setting, weather: Weather, src_cfg: Source, method: Method,
         hero_name: str = "Nell", hero_type: str = "girl", trait: str = "steady",
         helper: bool = True, helper_type: str = "grandfather") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
        tags={trait},
    ))
    room = world.add(Entity(
        id="room",
        kind="thing",
        type="room",
        label=setting.room,
        phrase=setting.room,
        role="room",
        tags=set(setting.tags),
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=src_cfg.label,
        phrase=src_cfg.phrase,
        role="source",
        tags=set(src_cfg.tags),
    ))
    helper_ent: Optional[Entity] = None
    if helper:
        helper_ent = world.add(Entity(
            id="helper",
            kind="character",
            type=helper_type,
            label=helper_type,
            phrase=helper_type,
            role="helper",
        ))

    world.facts["hero_name"] = hero_name
    introduce(world, hero, setting)
    set_scene(world, hero, weather, setting)

    world.para()
    start_noise(world, hero, source, src_cfg, weather)
    imagine(world, hero, src_cfg)
    helper_arrives(world, hero, helper_ent, setting)

    world.para()
    choose_method(world, hero, helper_ent, method)
    solved = outcome_of(StoryParams(
        place=setting.id,
        weather=weather.id,
        source=src_cfg.id,
        method=method.id,
        helper=helper,
        name=hero_name,
        gender=hero_type,
        helper_type=helper_type,
        trait=trait,
        seed=None,
    )) == "solved"
    if solved:
        solve(world, hero, helper_ent, source, src_cfg, method)
    else:
        wait_for_morning(world, hero, helper_ent, src_cfg)

    world.para()
    ending(world, hero, setting, solved)

    world.facts.update(
        hero=hero,
        helper=helper_ent,
        room=room,
        source_entity=source,
        setting=setting,
        weather=weather,
        source_cfg=src_cfg,
        method=method,
        helper_present=helper,
        outcome="solved" if solved else "waited",
        predicted=prediction_for(world, StoryParams(
            place=setting.id,
            weather=weather.id,
            source=src_cfg.id,
            method=method.id,
            helper=helper,
            name=hero_name,
            gender=hero_type,
            helper_type=helper_type,
            trait=trait,
            seed=None,
        )),
    )
    return world


SETTINGS = {
    "cottage": Setting(
        id="cottage",
        place="a windy cottage at the edge of the marsh",
        room="front room",
        opening="The cottage had beams thick as tree trunks and stories tucked into every creak.",
        ending="From then on, the front room sounded less like a cave of monsters and more like a place with a story to tell.",
        helper_word="grandpa",
        tags={"home"},
    ),
    "lighthouse": Setting(
        id="lighthouse",
        place="a tall lighthouse above the harbor",
        room="lantern room stairs",
        opening="The lighthouse was so tall that gulls seemed to stop halfway up and rest their wings.",
        ending="From then on, the lighthouse did not feel haunted at all; it felt like a brave place to know by heart.",
        helper_word="grandma",
        tags={"harbor"},
    ),
    "farmhouse": Setting(
        id="farmhouse",
        place="a big farmhouse beyond the pumpkin fields",
        room="kitchen",
        opening="The farmhouse sat broad and patient, with windows that watched the fields like old friendly eyes.",
        ending="From then on, the kitchen bangs sounded less like giants and more like weather knocking on a familiar door.",
        helper_word="dad",
        tags={"farm"},
    ),
}

WEATHERS = {
    "gusty": Weather(
        id="gusty",
        sky="the wind came rushing over the roof in long gray gallops",
        wind=2,
        rain=0,
        sound_line="Whoooosh and whee-eee and hushhh swept",
        tags={"wind"},
    ),
    "stormy": Weather(
        id="stormy",
        sky="clouds stacked up like dark wagons and the storm kicked at the panes",
        wind=3,
        rain=2,
        sound_line="Boom-rumple, hissss, and whoooosh ran",
        tags={"wind", "rain"},
    ),
    "rainy": Weather(
        id="rainy",
        sky="a fine rain stitched silver lines outside the windows",
        wind=1,
        rain=2,
        sound_line="Pitter-pat and shhhhhh moved",
        tags={"rain"},
    ),
}

SOURCES = {
    "blinds": Source(
        id="blinds",
        label="the venetian blinds",
        phrase="the venetian blinds by the tall window",
        sound="clackety-clack",
        giant_name="the Blind-Clapping Giant",
        cause_text="the wind kept tapping the loose venetian slats together",
        needs_wind=True,
        needs_rain=False,
        loudness=2,
        brave_bonus=1,
        tags={"venetian", "window"},
    ),
    "bucket": Source(
        id="bucket",
        label="the porch bucket",
        phrase="the tin bucket hanging by the porch post",
        sound="clang-a-lang",
        giant_name="the Bucket-Bell Ogre",
        cause_text="a rope loop had left the bucket free to bang against the post",
        needs_wind=True,
        needs_rain=False,
        loudness=2,
        brave_bonus=0,
        tags={"metal", "porch"},
    ),
    "gutter": Source(
        id="gutter",
        label="the rain gutter",
        phrase="the crooked rain gutter above the window",
        sound="drip-bong",
        giant_name="the Drip-Drum Troll",
        cause_text="fat raindrops were falling into one bent corner and beating it like a spoon on a pan",
        needs_wind=False,
        needs_rain=True,
        loudness=1,
        brave_bonus=0,
        tags={"rain", "roof"},
    ),
}

METHODS = {
    "lantern": Method(
        id="lantern",
        label="lantern walk",
        sense=3,
        courage_bonus=2,
        requires_helper=False,
        setup_text="Instead of shouting at the dark, {helper} or no one, the child lit a lantern, held it out, and took three slow brave steps.",
        resolve_text="Lantern light slid across the wall, over the floorboards, and straight to {source}.",
        qa_text="used a lantern and walked slowly toward the sound",
        tags={"lantern", "light"},
    ),
    "listen": Method(
        id="listen",
        label="listen first",
        sense=2,
        courage_bonus=1,
        requires_helper=False,
        setup_text="First came the brave part that does not look brave at all: standing still, breathing once, and listening carefully.",
        resolve_text="After one steady breath and another, the sound showed its pattern, and careful listening led them to {source}.",
        qa_text="stood still, listened for the pattern, and followed it",
        tags={"listening"},
    ),
    "hand_in_hand": Method(
        id="hand_in_hand",
        label="hand in hand",
        sense=3,
        courage_bonus=2,
        requires_helper=True,
        setup_text="The child slipped a hand into {helper}'s hand, and together they marched toward the noise with steps as steady as drumbeats.",
        resolve_text="{helper} lifted the lamp while the child pointed, and together they discovered {source}.",
        qa_text="went hand in hand with a helper and checked the noise together",
        tags={"helper", "light"},
    ),
    "stomp": Method(
        id="stomp",
        label="stomp and yell",
        sense=1,
        courage_bonus=0,
        requires_helper=False,
        setup_text="The plan was to stomp and yell at the dark until it got embarrassed.",
        resolve_text="That foolish stomping happened to point the right way toward {source}.",
        qa_text="stomped and yelled at the noise",
        tags={"reckless"},
    ),
}

GIRL_NAMES = ["Nell", "Mara", "June", "Elsie", "Tess", "Willa", "Ruby", "Mae"]
BOY_NAMES = ["Jeb", "Cal", "Finn", "Otis", "Beau", "Nate", "Silas", "Jude"]
TRAITS = ["steady", "curious", "bold", "careful"]
TRAIT_BONUS = {"steady": 3, "curious": 2, "bold": 3, "careful": 1}
HELPER_TYPES = ["grandfather", "grandmother", "father", "mother"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for weather_id, weather in WEATHERS.items():
            for source_id, source in SOURCES.items():
                if source_active(weather, source):
                    combos.append((place, weather_id, source_id))
    return sorted(combos)


@dataclass
class StoryParams:
    place: str
    weather: str
    source: str
    method: str
    helper: bool
    name: str
    gender: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "venetian": [
        (
            "What are venetian blinds?",
            "Venetian blinds are window covers made of many thin slats. When wind moves them, the slats can tap and rattle together."
        )
    ],
    "wind": [
        (
            "Why can wind make a house sound noisy?",
            "Wind pushes on windows, doors, and loose things outside. That can make rattles, whistles, and bangs that seem much bigger at night."
        )
    ],
    "rain": [
        (
            "Why does rain sometimes sound loud on a house?",
            "Rain hits roofs, gutters, and windows over and over again. Lots of little drops together can make a surprisingly big sound."
        )
    ],
    "lantern": [
        (
            "What does a lantern help you do?",
            "A lantern gives steady light so you can see in dark places. Seeing clearly helps ordinary things stop feeling mysterious."
        )
    ],
    "listening": [
        (
            "How can listening carefully help when a sound is scary?",
            "If you listen calmly, you may notice a pattern in the sound. A pattern can help you figure out what is making it."
        )
    ],
    "helper": [
        (
            "Why can it help to check a strange noise with another person?",
            "Another person can hold a light, stay calm, and help you think clearly. Bravery often grows when people face a problem together."
        )
    ],
}
KNOWLEDGE_ORDER = ["venetian", "wind", "rain", "lantern", "listening", "helper"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    src = f["source_cfg"]
    setting = f["setting"]
    method = f["method"]
    outcome = f["outcome"]
    helper_present = f["helper_present"]
    helper_phrase = "with a helper" if helper_present else "alone"
    base = (
        f'Write a tall-tale story for a 3-to-5-year-old that includes the word '
        f'"venetian", uses sound effects, and shows bravery in {setting.place}.'
    )
    if outcome == "solved":
        return [
            base,
            f"Tell a story where a {hero.type} named {world.facts['hero_name']} hears {src.sound} in the night, imagines something huge, and bravely checks the noise {helper_phrase}.",
            f'Write a child-facing tall tale where the scary sound turns out to be ordinary, and the brave moment comes when the child {method.qa_text}.',
        ]
    return [
        base,
        f"Tell a tall-tale bedtime story where a child hears {src.sound}, feels afraid, and shows bravery by waiting for morning instead of rushing into the dark.",
        "Write a gentle story where a noisy night makes an ordinary thing sound giant-sized, and the child learns that patient bravery counts too.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    src = f["source_cfg"]
    method = f["method"]
    weather = f["weather"]
    helper = f["helper"]
    outcome = f["outcome"]
    predicted = f["predicted"]
    hero_name = f["hero_name"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero_name}, a little {hero.type} who heard a great mystery noise in the night. The story follows how {hero.pronoun()} handled that frightening sound."
        ),
        (
            "What strange sound did the child hear?",
            f"{hero_name} heard {src.sound}, loud enough to seem huge in the dark. The weather made the house noisy, so an ordinary sound felt much bigger than it really was."
        ),
        (
            f"Why did the noise seem scary to {hero_name}?",
            f"It was dark, the weather was busy around the house, and the first sound came suddenly. That made {hero_name} imagine something enormous before {hero.pronoun()} knew the true cause."
        ),
    ]
    if helper is not None:
        qa.append(
            (
                f"How did {helper.id} help?",
                f"{helper.id.capitalize()} stayed calm and came near instead of laughing at the fear. That steady company made it easier for {hero_name} to think bravely."
            )
        )
    if outcome == "solved":
        qa.append(
            (
                f"How did {hero_name} solve the mystery?",
                f"{hero_name} {method.qa_text}. That brave, sensible choice led straight to the real cause of the noise."
            )
        )
        qa.append(
            (
                "What was really making the sound?",
                f"It was {src.phrase}. It sounded monstrous only because {src.cause_text}."
            )
        )
        qa.append(
            (
                "What changed by the end?",
                f"By the end, the room felt ordinary again and {hero_name} felt taller inside. Seeing the real source turned fear into relief and wonder."
            )
        )
    else:
        qa.append(
            (
                f"Did {hero_name} rush into the dark?",
                f"No. {hero_name} waited until it felt safe to find out the truth, and that was a brave choice too."
            )
        )
        qa.append(
            (
                "What was really making the sound in the end?",
                f"In the morning they found {src.phrase}. Daylight made the cause plain, which showed that the noise had been ordinary all along."
            )
        )
        qa.append(
            (
                "Why was waiting still brave?",
                f"Waiting kept {hero_name} from doing something foolish while fear was bigger than good sense. The story shows that bravery can mean patience as well as marching forward."
            )
        )
    if predicted["fear"] >= THRESHOLD:
        qa.append(
            (
                "Was the child truly frightened?",
                f"Yes. The world around the child had turned loud and mysterious, so the fear was real even though the danger was not. Once the cause was known, that fear could shrink."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = set()
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["weather"].tags)
    tags |= set(f["method"].tags)
    if f["helper_present"]:
        tags.add("helper")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE.get(key, []))
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:8} ({ent.type:12}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="cottage",
        weather="gusty",
        source="blinds",
        method="hand_in_hand",
        helper=True,
        name="Nell",
        gender="girl",
        helper_type="grandfather",
        trait="steady",
    ),
    StoryParams(
        place="lighthouse",
        weather="stormy",
        source="gutter",
        method="lantern",
        helper=True,
        name="Finn",
        gender="boy",
        helper_type="grandmother",
        trait="bold",
    ),
    StoryParams(
        place="farmhouse",
        weather="gusty",
        source="bucket",
        method="listen",
        helper=False,
        name="Jude",
        gender="boy",
        helper_type="father",
        trait="curious",
    ),
    StoryParams(
        place="cottage",
        weather="stormy",
        source="blinds",
        method="listen",
        helper=False,
        name="Mae",
        gender="girl",
        helper_type="mother",
        trait="careful",
    ),
    StoryParams(
        place="farmhouse",
        weather="rainy",
        source="gutter",
        method="hand_in_hand",
        helper=True,
        name="Ruby",
        gender="girl",
        helper_type="father",
        trait="steady",
    ),
]


def explain_rejection(source: Source, weather: Weather) -> str:
    if source.needs_wind and weather.wind <= 0:
        return f"(No story: {source.label} needs wind to make that kind of racket.)"
    if source.needs_rain and weather.rain <= 0:
        return f"(No story: {source.label} needs rain to make that sound, but this weather is dry.)"
    return "(No story: that weather/source combination does not create a plausible mystery sound.)"


def explain_method(method_id: str) -> str:
    method = METHODS[method_id]
    better = ", ".join(sorted(m.id for m in sensible_methods()))
    return (
        f"(Refusing method '{method_id}': it scores too low on common sense "
        f"(sense={method.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


ASP_RULES = r"""
active_source(W, S) :- weather(W), source(S), not needs_wind(S), not needs_rain(S).
active_source(W, S) :- weather(W), source(S), needs_wind(S), wind(W, N), N > 0, not needs_rain(S).
active_source(W, S) :- weather(W), source(S), needs_rain(S), rain(W, N), N > 0, not needs_wind(S).
active_source(W, S) :- weather(W), source(S), needs_wind(S), wind(W, A), A > 0,
                       needs_rain(S), rain(W, B), B > 0.

valid(P, W, S) :- setting(P), active_source(W, S).

sensible(M) :- method(M), sense(M, X), sense_min(Min), X >= Min.

helper_bonus(1) :- helper_present.
helper_bonus(0) :- not helper_present.

courage_total(T + MB + HB + SB) :-
    chosen_trait(Tr), trait_bonus(Tr, T),
    chosen_method(M), courage_bonus(M, MB),
    helper_bonus(HB),
    chosen_source(S), source_bonus(S, SB).

fear_total(WN + LN) :-
    chosen_weather(W), wind(W, WN),
    chosen_source(S), loudness(S, LN).

can_attempt :- chosen_method(M), not requires_helper(M).
can_attempt :- chosen_method(M), requires_helper(M), helper_present.

outcome(solved) :- can_attempt, courage_total(C), fear_total(F), C >= F.
outcome(waited) :- not outcome(solved).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("setting", pid))
    for wid, weather in WEATHERS.items():
        lines.append(asp.fact("weather", wid))
        lines.append(asp.fact("wind", wid, weather.wind))
        lines.append(asp.fact("rain", wid, weather.rain))
    for sid, source in SOURCES.items():
        lines.append(asp.fact("source", sid))
        lines.append(asp.fact("loudness", sid, source.loudness))
        lines.append(asp.fact("source_bonus", sid, source.brave_bonus))
        if source.needs_wind:
            lines.append(asp.fact("needs_wind", sid))
        if source.needs_rain:
            lines.append(asp.fact("needs_rain", sid))
    for mid, method in METHODS.items():
        lines.append(asp.fact("method", mid))
        lines.append(asp.fact("sense", mid, method.sense))
        lines.append(asp.fact("courage_bonus", mid, method.courage_bonus))
        if method.requires_helper:
            lines.append(asp.fact("requires_helper", mid))
    for trait, bonus in TRAIT_BONUS.items():
        lines.append(asp.fact("trait_bonus", trait, bonus))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_methods() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra_lines = [
        asp.fact("chosen_weather", params.weather),
        asp.fact("chosen_source", params.source),
        asp.fact("chosen_method", params.method),
        asp.fact("chosen_trait", params.trait),
    ]
    if params.helper:
        extra_lines.append(asp.fact("helper_present"))
    model = asp.one_model(asp_program("\n".join(extra_lines), "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_test() -> None:
    sample = generate(CURATED[0])
    if not sample.story or "venetian" not in sample.story.lower():
        raise StoryError("Smoke test failed: generated story missing expected core content.")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Smoke test failed: generated sample missing QA/prompts.")
    emit(sample, trace=False, qa=False, header="")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sensible = {m.id for m in sensible_methods()}
    asp_sensible = set(asp_sensible_methods())
    if py_sensible == asp_sensible:
        print(f"OK: sensible methods match ({sorted(py_sensible)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible methods: clingo={sorted(asp_sensible)} python={sorted(py_sensible)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
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
        _smoke_test()
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: a brave child faces a giant-sounding mystery and discovers an ordinary cause."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--weather", choices=WEATHERS)
    ap.add_argument("--source", choices=SOURCES)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--helper", choices=["yes", "no"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.weather and args.source:
        if not source_active(WEATHERS[args.weather], SOURCES[args.source]):
            raise StoryError(explain_rejection(SOURCES[args.source], WEATHERS[args.weather]))
    if args.method and METHODS[args.method].sense < SENSE_MIN:
        raise StoryError(explain_method(args.method))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.weather is None or combo[1] == args.weather)
        and (args.source is None or combo[2] == args.source)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, weather, source = rng.choice(combos)
    sensible = sorted(m.id for m in sensible_methods())
    method = args.method or rng.choice(sensible)
    helper = {"yes": True, "no": False}.get(args.helper, rng.choice([True, False]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_type = args.helper_type or rng.choice(HELPER_TYPES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        weather=weather,
        source=source,
        method=method,
        helper=helper,
        name=name,
        gender=gender,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in SETTINGS:
        raise StoryError(f"(Invalid place: {params.place})")
    if params.weather not in WEATHERS:
        raise StoryError(f"(Invalid weather: {params.weather})")
    if params.source not in SOURCES:
        raise StoryError(f"(Invalid source: {params.source})")
    if params.method not in METHODS:
        raise StoryError(f"(Invalid method: {params.method})")
    if params.trait not in TRAIT_BONUS:
        raise StoryError(f"(Invalid trait: {params.trait})")
    if params.helper_type not in HELPER_TYPES:
        raise StoryError(f"(Invalid helper type: {params.helper_type})")
    if not source_active(WEATHERS[params.weather], SOURCES[params.source]):
        raise StoryError(explain_rejection(SOURCES[params.source], WEATHERS[params.weather]))
    if METHODS[params.method].sense < SENSE_MIN:
        raise StoryError(explain_method(params.method))

    world = tell(
        setting=SETTINGS[params.place],
        weather=WEATHERS[params.weather],
        src_cfg=SOURCES[params.source],
        method=METHODS[params.method],
        hero_name=params.name,
        hero_type=params.gender,
        trait=params.trait,
        helper=params.helper,
        helper_type=params.helper_type,
    )
    story = world.render().replace("hero", params.name)
    story = story.replace("helper", world.facts["helper"].id if world.facts["helper"] is not None else "")
    story = story.replace("  ", " ")
    return StorySample(
        params=params,
        story=story.replace("hero", params.name),
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
        sensible = asp_sensible_methods()
        print(f"sensible methods: {', '.join(sensible)}\n")
        print(f"{len(combos)} compatible (place, weather, source) combos:\n")
        for place, weather, source in combos:
            print(f"  {place:10} {weather:8} {source}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = (
                f"### {p.name}: {p.source} in {p.place} "
                f"({p.weather}, {p.method}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
